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
from typing import Any, Dict, List

from llm import get_llm
from monitoring import enable_monitoring, clear_trace, get_trace


def load_cases(path: str | None) -> List[Dict[str, Any]]:
    if not path:
        # Default minimal set; expand in your repo-specific dataset as needed
        return [
            {"question": "What is the category of SKU001?"},
            {"question": "What country is SKU001 from?"},
            {"question": "Show me all SKUs"},
            {"question": "Show me supply chain gaps across SKUs"},
        ]
    with open(path, "r") as f:
        return json.load(f)


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
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set; cannot run evaluation.")
        return 2

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
            record = {
                "question": q,
                "answer": answer,
                "trace": trace_summary,
                "scores": scores,
            }
            out_f.write(json.dumps(record) + "\n")
            total += 1
            if isinstance(scores, dict) and scores.get("verdict") == "PASS":
                passed += 1
            print(f"[{total}] verdict={scores.get('verdict')} overall={scores.get('overall')}  q='{q[:60]}'")

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


