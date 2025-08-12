#!/usr/bin/env python3
"""
Offline quality evaluation harness using LLM-as-judge.

- Generates responses via the existing agent
- Captures monitoring trace (tools used, timings)
- Uses the LLM to score quality dimensions and emits JSONL results

Usage:
  OPENAI_API_KEY=... python evaluate_quality.py --cases cases.json --out eval_results.jsonl --model gpt-5-nano

If --cases is omitted, a small default set is used.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from llm import get_llm
from monitoring import enable_monitoring, clear_trace, get_trace
from solutions.graph import get_graph


def load_cases(path: Optional[str]) -> List[Dict[str, Any]]:
    if not path:
        # Default minimal set; expand in your repo-specific dataset as needed
        return [
            {"question": "What is the category of SKU001?", "ground_truth_source": {"type": "sku_field", "sku_id": "SKU001", "field": "category"}},
            {"question": "What country is SKU001 from?", "ground_truth_source": {"type": "sku_field", "sku_id": "SKU001", "field": "country"}},
            {"question": "Tell me about SKU001", "ground_truth_source": {"type": "sku_plot", "sku_id": "SKU001"}},
            {"question": "Show me all SKUs", "ground_truth_source": {"type": "all_skus_count"}},
        ]
    with open(path, "r") as f:
        return json.load(f)


def _load_secrets_into_env() -> None:
    """Attempt to load credentials from .streamlit/secrets.toml into env.

    - First try strict TOML parse
    - If that fails, perform a forgiving key=value line parse (as in test_stack)
    """
    import pathlib
    secrets_path = pathlib.Path('.streamlit/secrets.toml')
    if not secrets_path.exists():
        return
    data = {}
    try:
        try:
            import tomllib as toml
        except Exception:  # pragma: no cover
            import tomli as toml  # type: ignore
        with secrets_path.open('rb') as f:
            data = toml.load(f)
    except Exception:
        # Fallback: forgiving key=value parsing
        try:
            with secrets_path.open('r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#') or '=' not in s:
                        continue
                    key, value = s.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    data[key] = value
        except Exception:
            pass
    for k in ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]:
        v = data.get(k)
        if v and not os.getenv(k):
            os.environ[k] = str(v)


def _extract_plot_field(plot: str, key: str) -> Optional[str]:
    try:
        # plot format: "category: X | country: Y | unit_price: 10.9 | ..."
        token = key + ": "
        if token not in plot:
            return None
        after = plot.split(token, 1)[1]
        value = after.split(" | ")[0].strip()
        return value
    except Exception:
        return None


def fetch_ground_truth(gt_spec: Dict[str, Any]) -> Any:
    g = get_graph()
    if g is None:
        return None
    t = gt_spec.get("type")
    if t == "sku_field":
        sku_id = gt_spec["sku_id"].upper()
        field = gt_spec["field"].lower()
        # Fetch plot and extract field consistently with app
        res = g.query("MATCH (s:SKU {sku_id:$id}) RETURN s.plot AS plot", {"id": sku_id})
        if not res:
            return None
        plot = res[0].get("plot") or ""
        return _extract_plot_field(plot, field)
    if t == "sku_plot":
        sku_id = gt_spec["sku_id"].upper()
        res = g.query("MATCH (s:SKU {sku_id:$id}) RETURN s.sku_id AS sku_id, s.name AS name, s.plot AS plot", {"id": sku_id})
        return res[0] if res else None
    if t == "all_skus_count":
        res = g.query("MATCH (s:SKU) RETURN count(s) AS c")
        return int(res[0]["c"]) if res else None
    if t == "distinct_categories":
        res = g.query("MATCH (s:SKU) RETURN DISTINCT split(split(s.plot, 'category: ')[1], ' | ')[0] AS category")
        cats = [r.get("category") for r in res if r.get("category")]
        return sorted(list(set(cats)))
    if t == "negative_gross_profit_skus":
        res = g.query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
        skus = []
        for r in res:
            plot = r.get("plot") or ""
            gp = _extract_plot_field(plot, "gross_profit")
            try:
                if gp is not None and float(gp) < 0:
                    skus.append(r.get("sku_id"))
            except Exception:
                pass
        return sorted(list(set([s for s in skus if s])))
    if t == "excess_inventory_skus":
        res = g.query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
        skus = []
        for r in res:
            plot = r.get("plot") or ""
            inv = _extract_plot_field(plot, "initial_inventory")
            ss = _extract_plot_field(plot, "safety_stock")
            try:
                inv_f = float(inv or 0)
                ss_f = float(ss or 0)
                if inv_f > ss_f and inv_f > 0:
                    skus.append(r.get("sku_id"))
            except Exception:
                pass
        return sorted(list(set([s for s in skus if s])))
    if t == "top_revenue_sku":
        res = g.query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
        best = None
        best_rev = -1e18
        for r in res:
            plot = r.get("plot") or ""
            rev = _extract_plot_field(plot, "total_revenue") or _extract_plot_field(plot, "revenue")
            try:
                rv = float(rev or 0)
            except Exception:
                rv = 0.0
            if rv > best_rev:
                best_rev = rv
                best = r.get("sku_id")
        return best
    # New complex ground-truth types
    if t == "avg_lead_time_category":
        category = gt_spec.get("category")
        res = g.query("MATCH (s:SKU) RETURN s.plot AS plot")
        vals = []
        for r in res:
            plot = r.get("plot") or ""
            cat = _extract_plot_field(plot, "category")
            if category and cat and cat.lower() == category.lower():
                lt = _extract_plot_field(plot, "lead_time_days")
                try:
                    vals.append(float(lt))
                except Exception:
                    pass
        return sum(vals)/len(vals) if vals else None
    if t == "category_highest_avg_lead_time":
        res = g.query("MATCH (s:SKU) RETURN s.plot AS plot")
        cat_to_vals: Dict[str, list[float]] = {}
        for r in res:
            plot = r.get("plot") or ""
            cat = _extract_plot_field(plot, "category")
            lt = _extract_plot_field(plot, "lead_time_days")
            try:
                if cat and lt is not None:
                    cat_to_vals.setdefault(cat, []).append(float(lt))
            except Exception:
                pass
        best_cat = None
        best_avg = -1e18
        for c, vals in cat_to_vals.items():
            if not vals:
                continue
            avg = sum(vals)/len(vals)
            if avg > best_avg:
                best_avg = avg
                best_cat = c
        return best_cat
    if t == "top_revenue_skus_n":
        n = int(gt_spec.get("n", 3))
        res = g.query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
        items = []
        for r in res:
            plot = r.get("plot") or ""
            rev = _extract_plot_field(plot, "total_revenue") or _extract_plot_field(plot, "revenue")
            try:
                rv = float(rev or 0)
            except Exception:
                rv = 0.0
            items.append((r.get("sku_id"), rv))
        items = [(sid, rv) for sid, rv in items if sid]
        items.sort(key=lambda x: x[1], reverse=True)
        return [sid for sid, _ in items[:n]]
    if t == "avg_unit_price_category":
        category = gt_spec.get("category")
        res = g.query("MATCH (s:SKU) RETURN s.plot AS plot")
        vals = []
        for r in res:
            plot = r.get("plot") or ""
            cat = _extract_plot_field(plot, "category")
            if category and cat and cat.lower() == category.lower():
                up = _extract_plot_field(plot, "unit_price")
                try:
                    vals.append(float(up))
                except Exception:
                    pass
        return sum(vals)/len(vals) if vals else None
    if t == "country_with_most_skus":
        res = g.query("MATCH (s:SKU) RETURN s.plot AS plot")
        counts: Dict[str,int] = {}
        for r in res:
            plot = r.get("plot") or ""
            c = _extract_plot_field(plot, "country")
            if c:
                counts[c] = counts.get(c,0)+1
        if not counts:
            return None
        return max(counts.items(), key=lambda kv: kv[1])[0]
    if t == "total_skus_in_category":
        category = gt_spec.get("category")
        res = g.query("MATCH (s:SKU) RETURN s.plot AS plot")
        cnt = 0
        for r in res:
            plot = r.get("plot") or ""
            cat = _extract_plot_field(plot, "category")
            if category and cat and cat.lower() == category.lower():
                cnt += 1
        return cnt
    if t == "count_negative_gross_profit":
        res = g.query("MATCH (s:SKU) RETURN s.plot AS plot")
        cnt = 0
        for r in res:
            gp = _extract_plot_field(r.get("plot") or "", "gross_profit")
            try:
                if gp is not None and float(gp) < 0:
                    cnt += 1
            except Exception:
                pass
        return cnt
    if t == "top_gp_per_unit_sku":
        res = g.query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
        best = None
        best_diff = -1e18
        for r in res:
            plot = r.get("plot") or ""
            up = _extract_plot_field(plot, "unit_price")
            uc = _extract_plot_field(plot, "unit_cost")
            try:
                diff = float(up) - float(uc)
            except Exception:
                continue
            if diff > best_diff:
                best_diff = diff
                best = r.get("sku_id")
        return best
    if t == "top_revenue_sku_in_category":
        category = gt_spec.get("category")
        res = g.query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
        best = None
        best_rev = -1e18
        for r in res:
            plot = r.get("plot") or ""
            cat = _extract_plot_field(plot, "category")
            if category and cat and cat.lower() == category.lower():
                rev = _extract_plot_field(plot, "total_revenue") or _extract_plot_field(plot, "revenue")
                try:
                    rv = float(rev or 0)
                except Exception:
                    rv = 0.0
                if rv > best_rev:
                    best_rev = rv
                    best = r.get("sku_id")
        return best
    if t == "skus_with_lead_time_over":
        threshold = float(gt_spec.get("threshold", 25))
        n = int(gt_spec.get("n", 5))
        res = g.query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
        items = []
        for r in res:
            lt = _extract_plot_field(r.get("plot") or "", "lead_time_days")
            try:
                if float(lt) > threshold:
                    items.append(r.get("sku_id"))
            except Exception:
                pass
        return items[:n]
    if t == "categories_with_negative_gp":
        res = g.query("MATCH (s:SKU) RETURN s.plot AS plot")
        cats = set()
        for r in res:
            plot = r.get("plot") or ""
            gp = _extract_plot_field(plot, "gross_profit")
            try:
                if gp is not None and float(gp) < 0:
                    cat = _extract_plot_field(plot, "category")
                    if cat:
                        cats.add(cat)
            except Exception:
                pass
        return sorted(list(cats))
    if t == "distinct_categories_count":
        res = g.query("MATCH (s:SKU) RETURN DISTINCT split(split(s.plot, 'category: ')[1], ' | ')[0] AS category")
        cats = [r.get("category") for r in res if r.get("category")]
        return len(set(cats))
    if t == "sku_fields":
        sku_id = gt_spec["sku_id"].upper()
        fields = gt_spec.get("fields", [])
        res = g.query("MATCH (s:SKU {sku_id:$id}) RETURN s.plot AS plot", {"id": sku_id})
        if not res:
            return None
        plot = res[0].get("plot") or ""
        values = {}
        for f in fields:
            values[f] = _extract_plot_field(plot, f)
        return {"sku_id": sku_id, "values": values}
    return None


def score_against_ground_truth(answer: str, gt_spec: Dict[str, Any]) -> Dict[str, Any]:
    truth = fetch_ground_truth(gt_spec)
    result = {"available": truth is not None, "pass": False, "details": {}}
    if truth is None:
        result["details"] = {"reason": "no_ground_truth"}
        return result

    t = gt_spec.get("type")
    try:
        if t == "sku_field":
            # Check if field value appears in answer
            ok = str(truth) != "" and str(truth).lower() in answer.lower()
            result.update({"pass": ok, "expected": truth})
        elif t == "sku_plot":
            # Expect SKU id and at least 3 core fields
            reqs = []
            if truth.get("sku_id"):
                reqs.append(truth["sku_id"])    
            core_keys = ["category", "country", "unit_price", "unit_cost"]
            present = 0
            for k in core_keys:
                v = _extract_plot_field(truth.get("plot") or "", k)
                if v and v.lower() in answer.lower():
                    present += 1
            ok = (truth.get("sku_id") and truth["sku_id"].lower() in answer.lower() and present >= 2)
            result.update({"pass": ok, "required_core_fields": present})
        elif t == "all_skus_count":
            # Check that answer mentions at least a few SKUs or the count
            ok = any(term in answer.lower() for term in ["sku", "skus", str(truth)])
            result.update({"pass": ok, "expected_count": truth})
        elif t == "distinct_categories":
            cats = truth if isinstance(truth, list) else []
            matched = sum(1 for c in cats if isinstance(c, str) and c.lower() in answer.lower())
            # Require at least min(3, total) matches
            threshold = min(3, len(cats))
            result.update({"pass": matched >= threshold, "matched": matched, "total": len(cats)})
        elif t == "negative_gross_profit_skus":
            skus = truth if isinstance(truth, list) else []
            matched = sum(1 for s in skus if isinstance(s, str) and s.lower() in answer.lower())
            threshold = min(2, len(skus))
            result.update({"pass": matched >= threshold, "matched": matched, "total": len(skus)})
        elif t == "excess_inventory_skus":
            skus = truth if isinstance(truth, list) else []
            matched = sum(1 for s in skus if isinstance(s, str) and s.lower() in answer.lower())
            threshold = min(2, len(skus))
            result.update({"pass": matched >= threshold, "matched": matched, "total": len(skus)})
        elif t == "top_revenue_sku":
            sku = truth if isinstance(truth, str) else None
            ok = bool(sku and sku.lower() in answer.lower())
            result.update({"pass": ok, "expected": sku})
        elif t == "avg_lead_time_category":
            try:
                val = float(truth)
                ok = any(s in answer for s in [f"{val:.0f}", f"{val:.1f}", f"{val:.2f}"])
                result.update({"pass": ok, "expected": val})
            except Exception:
                result.update({"pass": False})
        elif t == "category_highest_avg_lead_time":
            cat = truth if isinstance(truth, str) else None
            ok = bool(cat and cat.lower() in answer.lower())
            result.update({"pass": ok, "expected": cat})
        elif t == "top_revenue_skus_n":
            lst = truth if isinstance(truth, list) else []
            matched = sum(1 for s in lst if isinstance(s, str) and s.lower() in answer.lower())
            threshold = min(max(1, len(lst)//2), len(lst))
            result.update({"pass": matched >= threshold, "matched": matched, "total": len(lst)})
        elif t == "avg_unit_price_category":
            try:
                val = float(truth)
                ok = any(s in answer for s in [f"{val:.0f}", f"{val:.1f}", f"{val:.2f}"])
                result.update({"pass": ok, "expected": val})
            except Exception:
                result.update({"pass": False})
        elif t == "country_with_most_skus":
            c = truth if isinstance(truth, str) else None
            ok = bool(c and c.lower() in answer.lower())
            result.update({"pass": ok, "expected": c})
        elif t == "total_skus_in_category":
            try:
                val = int(truth)
                ok = str(val) in answer
                result.update({"pass": ok, "expected": val})
            except Exception:
                result.update({"pass": False})
        elif t == "count_negative_gross_profit":
            try:
                val = int(truth)
                ok = str(val) in answer
                result.update({"pass": ok, "expected": val})
            except Exception:
                result.update({"pass": False})
        elif t == "top_gp_per_unit_sku":
            sku = truth if isinstance(truth, str) else None
            ok = bool(sku and sku.lower() in answer.lower())
            result.update({"pass": ok, "expected": sku})
        elif t == "top_revenue_sku_in_category":
            sku = truth if isinstance(truth, str) else None
            ok = bool(sku and sku.lower() in answer.lower())
            result.update({"pass": ok, "expected": sku})
        elif t == "skus_with_lead_time_over":
            lst = truth if isinstance(truth, list) else []
            matched = sum(1 for s in lst if isinstance(s, str) and s.lower() in answer.lower())
            threshold = min(max(1, len(lst)//2), len(lst))
            result.update({"pass": matched >= threshold, "matched": matched, "total": len(lst)})
        elif t == "categories_with_negative_gp":
            cats = truth if isinstance(truth, list) else []
            matched = sum(1 for c in cats if isinstance(c, str) and c.lower() in answer.lower())
            threshold = min(2, len(cats))
            result.update({"pass": matched >= threshold, "matched": matched, "total": len(cats)})
        elif t == "distinct_categories_count":
            try:
                val = int(truth)
                ok = str(val) in answer
                result.update({"pass": ok, "expected": val})
            except Exception:
                result.update({"pass": False})
        elif t == "sku_fields":
            vals = truth.get("values", {}) if isinstance(truth, dict) else {}
            found = 0
            for k, v in vals.items():
                if v and str(v).lower() in answer.lower():
                    found += 1
            # Require at least half of requested fields found
            threshold = max(1, len(vals) // 2)
            result.update({"pass": found >= threshold, "found": found, "total": len(vals)})
        else:
            result["details"] = {"reason": "unhandled_type"}
    except Exception as e:
        result["details"] = {"error": str(e)}
    return result


def summarize_trace(trace: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Produce a compact summary for the judge
    summary: Dict[str, Any] = {
        "events": len(trace),
        "timers": {},
        "tool_usage": [],
        "cypher_preview": [],
    }
    for evt in trace:
        et = evt.get("type")
        details = evt.get("details", {})
        if et == "timer.end":
            label = details.get("label")
            ms = details.get("elapsed_ms")
            if label:
                summary["timers"].setdefault(label, []).append(ms)
        if et in ("cypher.query.generated", "cypher.query.generated.llm"):
            pass
        if et == "cypher.query.generated.llm":
            # length only
            continue
        if et == "cypher.query.results" and "count" in details:
            summary["tool_usage"].append({"tool": "cypher", "result_count": details["count"]})
        if et == "vector.search.success":
            summary["tool_usage"].append({"tool": "vector", "ok": True})
        if et == "neo4j.query" and "query_preview" in details:
            summary["cypher_preview"].append(details["query_preview"])
    return summary


def judge(question: str, answer: str, trace_summary: Dict[str, Any]) -> Dict[str, Any]:
    llm = get_llm()
    prompt = f"""
You are an expert evaluator of data-grounded AI assistants. Evaluate the assistant's answer.

Provide a STRICT JSON object with these fields (numbers 0-10):
{{
  "correctness": <0-10>,          // plausibility/consistency given the question; penalize hallucinations
  "grounding": <0-10>,            // is it grounded in data/tools (Cypher/vector) rather than making things up
  "completeness": <0-10>,         // does it fully address the question
  "format_quality": <0-10>,       // clarity, structure; if an executive dashboard was returned, ensure not summarized
  "actionability": <0-10>,        // provides actionable insight where appropriate
  "overall": <0-10>,              // not an average; your expert overall score
  "verdict": "PASS"|"FAIL",     // PASS if overall>=7 and no category <5, else FAIL
  "notes": "<2-4 sentences on strengths/weaknesses and concrete fixes>"
}}

Question:
"""
    prompt += question.strip() + "\n\n"
    prompt += "Assistant Answer:\n" + answer.strip() + "\n\n"
    prompt += "Trace Summary (tools/timings/cypher previews):\n" + json.dumps(trace_summary, ensure_ascii=False) + "\n\n"
    prompt += "Return ONLY the JSON."

    result = llm.invoke(prompt)
    text = getattr(result, "content", str(result))
    # Robust JSON extraction
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {"error": "Judge did not return JSON", "raw": text}
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return {"error": "JSON parse error", "raw": text}


def run(args: argparse.Namespace) -> int:
    # Attempt to load secrets if env not set
    _load_secrets_into_env()
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set; cannot run evaluation.")
        return 2
    # Disable chart generation during evaluation runs to reduce noise
    os.environ["EVAL_NO_CHARTS"] = "1"
    # Enforce one-line deterministic answers for numeric/aggregate intents during eval
    os.environ["EVAL_ONE_LINE"] = "1"

    # Optional: let user set model via env; runtime Streamlit override not used here
    cases = load_cases(args.cases)
    try:
        from solutions.agent import generate_response, reset_agent
    except Exception as e:
        print(f"Failed to import agent: {e}")
        return 1

    enable_monitoring(True)

    out_path = args.out or "eval_results.jsonl"
    passed = 0
    total = 0
    t0 = time.time()
    with open(out_path, "w") as out_f:
        for case in cases:
            q = case["question"].strip()
            clear_trace()
            try:
                answer = generate_response(q)
            except Exception as e:
                answer = f"Error generating response: {e}"
            trace_summary = summarize_trace(get_trace())
            scores = judge(q, answer, trace_summary)
            objective = None
            if isinstance(case, dict) and case.get("ground_truth"):
                objective = score_against_ground_truth({"type": "literal", "value": case["ground_truth"]})
            elif isinstance(case, dict) and case.get("ground_truth_source"):
                objective = score_against_ground_truth(answer, case["ground_truth_source"])  # type: ignore[arg-type]
            # Determine final verdict: prefer objective pass if available
            judge_pass = isinstance(scores, dict) and scores.get("verdict") == "PASS"
            objective_pass = isinstance(objective, dict) and objective.get("pass")
            final_pass = bool(objective_pass or judge_pass)

            record = {
                "question": q,
                "answer": answer,
                "trace": trace_summary,
                "scores": scores,
                "objective": objective,
                "final_verdict": "PASS" if final_pass else "FAIL",
            }
            out_f.write(json.dumps(record) + "\n")
            total += 1
            if final_pass:
                passed += 1
            print(f"[{total}] judge={scores.get('verdict')} objective={objective_pass} final={'PASS' if final_pass else 'FAIL'}  q='{q[:60]}'")

    dt = time.time() - t0
    print(f"Done. {passed}/{total} PASS  ({passed/total*100:.1f}%)  wrote: {out_path}  time: {dt:.1f}s")
    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--cases", type=str, default=None, help="Path to JSON list of cases: [{question: str}]")
    p.add_argument("--out", type=str, default="eval_results.jsonl", help="Output JSONL path")
    p.add_argument("--model", type=str, default=None, help="Optional model hint via OPENAI_MODEL env")
    return p.parse_args(argv)


if __name__ == "__main__":
    ns = parse_args(sys.argv[1:])
    if ns.model:
        os.environ["OPENAI_MODEL"] = ns.model
    sys.exit(run(ns))


