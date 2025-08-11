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


def load_secrets_if_any() -> bool:
    try:
        from evaluate_quality import _load_secrets_into_env
        _load_secrets_into_env()
    except Exception:
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


def main() -> int:
    # Skip cleanly if secrets unavailable (do not block commits)
    if not load_secrets_if_any():
        print("SMOKE_SKIPPED: Missing OPENAI_API_KEY/NEO4J_URI; skipping chatbot smoke test.")
        return 0

    passed, total, results = run_cases()
    print({"passed": passed, "total": total})
    for q, ok, msg in results:
        status = "OK" if ok else "FAIL"
        print(f"\nQ: {q}\n{status}: {msg}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())


