#!/usr/bin/env python3
"""
Lightweight chatbot smoke test for pre-commit or local runs.

- Loads secrets from .streamlit/secrets.toml (via evaluate_quality helper)
- Runs a small set of real data questions through generate_response()
- Validates deterministic first-line outputs using regex
- Exits 0 on pass, 0 on skip (missing secrets), 1 on failure

Usage:
  python scripts/smoke_chatbot.py
"""

from __future__ import annotations

import os
import re
import sys
from typing import List, Tuple

# Ensure project root is on sys.path when running from scripts/
import pathlib
ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def load_secrets_if_any() -> bool:
    """Load secrets from .streamlit/secrets.toml into environment.

    This function is intentionally forgiving because the secrets file in this
    repo may not be strict TOML. We attempt, in order:
      1) Use evaluate_quality._load_secrets_into_env if available
      2) Fallback to a simple key=value parser for .streamlit/secrets.toml
    """
    # If already set, we're done
    if os.getenv("OPENAI_API_KEY") and os.getenv("NEO4J_URI"):
        return True

    # First attempt: helper (handles TOML and forgiving parsing)
    try:
        from evaluate_quality import _load_secrets_into_env
        _load_secrets_into_env()
    except Exception:
        pass

    # If still missing, parse as key=value lines (non-strict TOML)
    if not (os.getenv("OPENAI_API_KEY") and os.getenv("NEO4J_URI")):
        try:
            import pathlib
            p = pathlib.Path('.streamlit/secrets.toml')
            if p.exists():
                with p.open('r', encoding='utf-8') as f:
                    for line in f:
                        s = line.strip()
                        if not s or s.startswith('#') or '=' not in s:
                            continue
                        key, value = s.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value and not os.getenv(key):
                            os.environ[key] = value
        except Exception:
            # Best-effort only; the test will skip if still missing
            pass

    # Minimal required secrets to run end-to-end
    return bool(os.getenv("OPENAI_API_KEY") and os.getenv("NEO4J_URI"))


def run_cases() -> Tuple[int, int, List[Tuple[str, bool, str]]]:
    # Deterministic one-liner mode for numeric/aggregate answers during smoke
    os.environ["EVAL_ONE_LINE"] = "1"

    from solutions.agent import generate_response

    cases: List[Tuple[str, re.Pattern]] = [
        (
            "List the distinct product categories",
            re.compile(r"^From database: Categories \(\d+\): ", re.I),
        ),
        (
            "What is the category of SKU001?",
            re.compile(r"^From database: Category of SKU001: \w+", re.I),
        ),
        (
            "Tell me about SKU001",
            re.compile(r"^From database: SKU SKU001: .*", re.I),
        ),
        (
            "Which SKU has the highest gross profit per unit?",
            re.compile(r"^From database: SKU with highest gross profit per unit: SKU\d+", re.I),
        ),
        (
            "How many distinct categories are there?",
            re.compile(r"^From database: Distinct categories count: \d+$", re.I),
        ),
        (
            "Which country has the most SKUs?",
            re.compile(r"^From database: Country with most SKUs: .+", re.I),
        ),
    ]

    results: List[Tuple[str, bool, str]] = []
    passed = 0
    for q, pattern in cases:
        try:
            ans = generate_response(q) or ""
            first = (ans.strip().splitlines() or [""])[0]
            ok = bool(pattern.search(first))
            results.append((q, ok, first))
            if ok:
                passed += 1
        except Exception as e:
            results.append((q, False, f"ERROR: {e}"))
    return passed, len(cases), results


def run_dashboard_sanity() -> Tuple[bool, str]:
    """Lightweight dashboard checks without streamlit runtime.

    - Ensures secrets are loaded and DB reachable
    - Validates monthly_df shape and demand coverage
    - Accepts partial supply/inventory/financials but flags if both supply and inventory are zero
    - Confirms response generator returns the dashboard header
    """
    try:
        from dashboard_component import get_dashboard_data, generate_dashboard_response
    except Exception as e:
        return False, f"import failed: {e}"

    monthly_df, category_summary, financial_summary, sku_df = get_dashboard_data()
    if monthly_df is None or monthly_df.empty:
        return False, "monthly_df empty"
    # Demand must exist
    try:
        if float(monthly_df['demand'].sum()) <= 0:
            return False, "no demand data"
    except Exception:
        return False, "demand column missing"

    # At least one of supply/inventory should be present at non-zero
    supply_ok = False
    inventory_ok = False
    try:
        supply_ok = float(monthly_df.get('supply', 0).sum()) > 0
    except Exception:
        pass
    try:
        inventory_ok = float(monthly_df.get('inventory', 0).sum()) > 0
    except Exception:
        pass
    if not (supply_ok or inventory_ok):
        return False, "no supply or inventory coverage"

    # Minimum months coverage (>= 12 months)
    try:
        if len(set(monthly_df['month'].unique())) < 12:
            return False, "insufficient month coverage"
    except Exception:
        return False, "month column missing"

    # Response generator should produce the dashboard heading and not hard error
    try:
        text = generate_dashboard_response()
        if "FMCG S&OP Dashboard" not in text:
            return False, "response missing dashboard heading"
        if "Analysis Encountered Issues" in text:
            return False, "response indicates analysis issues"
    except Exception as e:
        return False, f"response generation failed: {e}"

    return True, "ok"


def main() -> int:
    # Skip cleanly if secrets unavailable (do not block commits)
    if not load_secrets_if_any():
        print("SMOKE_SKIPPED: Missing OPENAI_API_KEY/NEO4J_URI; skipping chatbot smoke test.")
        return 0

    passed, total, results = run_cases()
    # Dashboard sanity (does not require streamlit run)
    d_ok, d_msg = run_dashboard_sanity()
    total += 1
    if d_ok:
        passed += 1
    results.append(("Dashboard sanity", d_ok, d_msg))
    print({"passed": passed, "total": total})
    for q, ok, msg in results:
        status = "OK" if ok else "FAIL"
        print(f"\nQ: {q}\n{status}: {msg}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())


