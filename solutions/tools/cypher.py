import streamlit as st
import os
from typing import Dict, List, Optional, Any
from llm import get_llm
from monitoring import record_event, timeit
from solutions.graph import get_graph
from langchain_core.prompts import ChatPromptTemplate
import re

def execute_query(query: str, params: Optional[Dict[str, Any]] = None):
    """Execute a raw Cypher query and return results list."""
    graph = get_graph()
    if graph is None:
        return []
    with timeit("neo4j.query", {"query_preview": query[:140]}):
        return graph.query(query, params or {})

def extract_analytical_intent(question: str) -> dict:
    """Map analytical English questions to supported analytical intents.

    Returns dict with keys: intent and optional parameters.
    This uses the LLM but constrains to a small set we can handle with our schema.
    """
    try:
        llm = get_llm()
        prompt = f"""
Return STRICT JSON selecting the best analytical intent for this question.
Allowed intents:
  - EXCESS_INVENTORY_FOR_PROMOTIONS
  - REGIONAL_DEMAND_VARIATIONS
  - MANUFACTURING_CONSTRAINTS_PROXY      // threshold optional (default 25 days)
  - LEAD_TIME_PLANNING_DATA
  - SKUS_TO_TRIM_PROXY                   // sort by low gross_profit then low revenue
  - CUSTOMER_ORDER_PRIORITIZATION        // requires order/customer schema (unsupported)
  - PRIORITIZE_LIMITED_SUPPLY_ACROSS_ORDERS  // unsupported
  - PLANT_UTILIZATION                    // unsupported
  - AVAILABLE_CAPACITY                   // unsupported
  - EXCEED_PRODUCTION_CAPACITY           // unsupported
  - CUSTOMER_PRIORITIZATION_MATRIX       // unsupported
  - CUSTOMER_RELATIONSHIP_IMPACT         // unsupported
  - REGIONAL_SERVICE_LEVELS              // unsupported
  - INVENTORY_BALANCING_LOCATIONS        // unsupported

Question: "{question}"

Rules:
- Choose the single best intent name.
- If the question is clearly about orders, customers, plants, or capacity, pick the matching unsupported intent.
- If the question is about promotions/excess inventory, pick EXCESS_INVENTORY_FOR_PROMOTIONS.
- If about demand differences across countries/regions, pick REGIONAL_DEMAND_VARIATIONS.
- If about long lead times or constraints, pick MANUFACTURING_CONSTRAINTS_PROXY.
- If about which SKUs to cut/trim, pick SKUS_TO_TRIM_PROXY.
"""
        res = llm.invoke(prompt)
        txt = res.content if hasattr(res, 'content') else str(res)
        s = txt.find('{'); e = txt.rfind('}')
        if s != -1 and e != -1 and e > s:
            import json as _json
            try:
                data = _json.loads(txt[s:e+1])
                if isinstance(data, dict) and data.get('intent'):
                    return data
            except Exception:
                pass
    except Exception:
        pass
    return {"intent": "UNKNOWN"}

def extract_structured_data_intent(question: str) -> dict:
    """Use LLM to extract a structured data intent and parameters.

    Returns a dict with keys: intent (str) and optional params like category, n, threshold.
    Allowed intents:
      - DISTINCT_CATEGORIES_COUNT
      - TOTAL_SKUS_IN_CATEGORY
      - COUNT_NEGATIVE_GROSS_PROFIT
      - TOP_GP_PER_UNIT_SKU
      - TOP_REVENUE_SKUS_N
      - AVG_LEAD_TIME_CATEGORY
      - AVG_UNIT_PRICE_CATEGORY
      - COUNTRY_WITH_MOST_SKUS
      - SKUS_WITH_LEAD_TIME_OVER
      - CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME
    """
    try:
        llm = get_llm()
        prompt = f"""
Return a STRICT JSON object describing the user's data intent about FMCG SKUs.
Only use these intents:
  DISTINCT_CATEGORIES_COUNT,
  TOTAL_SKUS_IN_CATEGORY,            // requires: category
  COUNT_NEGATIVE_GROSS_PROFIT,
  TOP_GP_PER_UNIT_SKU,
  TOP_REVENUE_SKUS_N,                // requires: n (integer)
  AVG_LEAD_TIME_CATEGORY,            // requires: category
  AVG_UNIT_PRICE_CATEGORY,           // requires: category
  COUNTRY_WITH_MOST_SKUS,
  SKUS_WITH_LEAD_TIME_OVER,          // requires: threshold (number), optional n (integer)
  CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME

User query: "{question}"

Rules:
- Choose the single best intent
- Provide only fields needed by that intent
- Return JSON with keys: intent, and any parameters

 Examples (map query -> intent JSON):
 - "Which category has the highest average lead time?" -> {"intent":"CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME"}
 - "Which SKU has the highest gross profit per unit?" -> {"intent":"TOP_GP_PER_UNIT_SKU"}
 - "Give me the top 3 SKUs by total revenue" -> {"intent":"TOP_REVENUE_SKUS_N","n":3}
 - "How many SKUs are in the Grains category?" -> {"intent":"TOTAL_SKUS_IN_CATEGORY","category":"Grains"}
  - "top skus" or "top products" (metric unspecified) -> {"intent":"TOP_REVENUE_SKUS_N","n":5}
        """
        res = llm.invoke(prompt)
        text = res.content if hasattr(res, 'content') else str(res)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            import json as _json
            try:
                data = _json.loads(text[start:end+1])
                if isinstance(data, dict) and 'intent' in data:
                    return data
            except Exception:
                pass
    except Exception as _:
        pass
    return {"intent": "UNKNOWN"}

def refine_structured_intent(question: str, sd: dict, coarse_intent: Optional[str] = None) -> dict:
    """Use LLM to reconcile/repair the structured intent when ambiguous.

    Inputs include the original question, initial structured parse, and a coarse class intent.
    Returns a dict with a best-fit allowed intent and parameters.
    """
    try:
        llm = get_llm()
        allowed = (
            "DISTINCT_CATEGORIES_COUNT, TOTAL_SKUS_IN_CATEGORY, COUNT_NEGATIVE_GROSS_PROFIT, "
            "TOP_GP_PER_UNIT_SKU, TOP_REVENUE_SKUS_N, AVG_LEAD_TIME_CATEGORY, AVG_UNIT_PRICE_CATEGORY, "
            "COUNTRY_WITH_MOST_SKUS, SKUS_WITH_LEAD_TIME_OVER, CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME"
        )
        prompt = f"""
Return STRICT JSON. Map the user's question to the BEST-FIT intent from:
{allowed}

Guidance:
- If the question asks for "highest gross profit per unit", choose TOP_GP_PER_UNIT_SKU
- If it asks for "which category has highest average lead time", choose CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME
- If it asks "how many SKUs in <category>", choose TOTAL_SKUS_IN_CATEGORY with category
- If it asks for "country with most SKUs", choose COUNTRY_WITH_MOST_SKUS
- If it asks for top-k by revenue, choose TOP_REVENUE_SKUS_N with n
- If user says "top skus" or "top products" without metric, default to TOP_REVENUE_SKUS_N with n=5

User question: "{question}"
Initial structured intent: {sd}
Coarse intent hint: {coarse_intent}

Return JSON with keys: intent (required), and any needed parameters.
"""
        res = llm.invoke(prompt)
        text = res.content if hasattr(res, 'content') else str(res)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            import json as _json
            try:
                data = _json.loads(text[start:end+1])
                if isinstance(data, dict) and 'intent' in data:
                    return data
            except Exception:
                pass
    except Exception:
        pass
    return sd if isinstance(sd, dict) else {"intent": "UNKNOWN"}

def extract_numeric_intent(question: str) -> dict:
    """Secondary LLM extraction focused on numeric intents (averages, counts, thresholds).

    Helps disambiguate cases like averages by category or counts in category.
    """
    try:
        llm = get_llm()
        prompt = f"""
Return STRICT JSON for numeric data intents from this set:
- AVG_UNIT_PRICE_CATEGORY (requires: category)
- AVG_LEAD_TIME_CATEGORY (requires: category)
- TOTAL_SKUS_IN_CATEGORY (requires: category)
- DISTINCT_CATEGORIES_COUNT

User question: "{question}"

Rules:
- Do NOT classify queries about "top", "highest", "most" here. Return {"intent":"UNKNOWN"} for those.
 - If the question asks to LIST categories (e.g., "list distinct product categories"), do NOT return a COUNT intent here; return {"intent":"UNKNOWN"}.
- If question contains phrasing like "average unit price for <category>", choose AVG_UNIT_PRICE_CATEGORY and set category accordingly.
- If question asks "average lead time for <category>", choose AVG_LEAD_TIME_CATEGORY.
- If question asks "how many SKUs in <category>", choose TOTAL_SKUS_IN_CATEGORY with that category.
- If question asks total distinct categories count, choose DISTINCT_CATEGORIES_COUNT.

Return only JSON with keys: intent and parameters.
"""
        res = llm.invoke(prompt)
        text = res.content if hasattr(res, 'content') else str(res)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            import json as _json
            try:
                data = _json.loads(text[start:end+1])
                if isinstance(data, dict) and 'intent' in data:
                    return data
            except Exception:
                pass
    except Exception:
        pass
    return {"intent": "UNKNOWN"}

def _intent_requires_params(intent: str) -> set[str]:
    req: dict[str, set[str]] = {
        "AVG_UNIT_PRICE_CATEGORY": {"category"},
        "AVG_LEAD_TIME_CATEGORY": {"category"},
        "TOTAL_SKUS_IN_CATEGORY": {"category"},
        "TOP_REVENUE_SKUS_N": set(),
        "SKUS_WITH_LEAD_TIME_OVER": {"threshold"},
    }
    return req.get(intent.upper(), set())

def _validate_intent(sd: dict) -> dict:
    """Validate structured intent has required non-empty params; otherwise return UNKNOWN."""
    try:
        if not isinstance(sd, dict):
            return {"intent": "UNKNOWN"}
        intent = (sd.get("intent") or "").upper()
        if not intent or intent == "UNKNOWN":
            return {"intent": "UNKNOWN"}
        required = _intent_requires_params(intent)
        for p in required:
            v = sd.get(p)
            if v is None:
                return {"intent": "UNKNOWN"}
            if isinstance(v, str) and v.strip() == "":
                return {"intent": "UNKNOWN"}
        # Coerce defaults
        if intent == "TOP_REVENUE_SKUS_N" and not sd.get("n"):
            sd["n"] = 3
        return sd
    except Exception:
        return {"intent": "UNKNOWN"}

def resolve_structured_intent(question: str) -> dict:
    """Deterministically resolve a structured data intent for a question.

    Numeric-first, then general structured, then refinement with coarse hint, then numeric rescue.
    Always returns a dict with at least {"intent": <...>} where unknown maps to "UNKNOWN".
    """
    try:
        sd = _validate_intent(extract_numeric_intent(question))
        if (sd.get("intent") or "").upper() != "UNKNOWN":
            return sd
        sd2 = _validate_intent(extract_structured_data_intent(question))
        if (sd2.get("intent") or "").upper() != "UNKNOWN":
            return sd2
        coarse = classify_data_query_intent(question)
        sd3 = _validate_intent(refine_structured_intent(question, sd2 or {"intent": "UNKNOWN"}, coarse))
        if (sd3.get("intent") or "").upper() != "UNKNOWN":
            return sd3
        sd4 = _validate_intent(extract_numeric_intent(question))
        return sd4
    except Exception:
        return {"intent": "UNKNOWN"}

def _extract_sku_id_from_row(row: dict) -> Optional[str]:
    """Best-effort SKU id extraction from a Neo4j row dict."""
    if not isinstance(row, dict):
        return None
    for k in ("sku_id", "s.sku_id", "sku.sku_id"):
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # Fallback: scan any string value for an SKU pattern
    import re as _re
    for v in row.values():
        if isinstance(v, str):
            m = _re.search(r"SKU\d{3,}", v, _re.IGNORECASE)
            if m:
                return m.group(0).upper()
    return None

def _infer_category_from_question(question: str) -> Optional[str]:
    q = (question or "").lower()
    import re as _re
    m = _re.search(r"for the ([a-zA-Z\s]+) category", q)
    if m:
        return m.group(1).strip().title()
    m = _re.search(r"for ([a-zA-Z\s]+) category", q)
    if m:
        return m.group(1).strip().title()
    m = _re.search(r"in the ([a-zA-Z\s]+) category", q)
    if m:
        return m.group(1).strip().title()
    m = _re.search(r"in ([a-zA-Z\s]+) category", q)
    if m:
        return m.group(1).strip().title()
    return None

def generate_dynamic_cypher_query(question, available_data=None):
    """
    Generate a dynamic Cypher query based on the user's question using LLM classification.
    """
    print(f"🔍 DEBUG: generate_dynamic_cypher_query() called with question: '{question}'")

    # Numeric/aggregate fast-path: deterministically resolve structured intent first
    try:
        sd_pre = resolve_structured_intent(question)
        intent_pre = (sd_pre.get("intent") or "").upper()
        if intent_pre == "AVG_LEAD_TIME_CATEGORY":
            category = (sd_pre.get("category") or "").replace("'", "\'")
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                f"WHERE toLower(category) = toLower('{category}') RETURN avg(lt) AS avg_lead_time"
            )
        if intent_pre == "AVG_UNIT_PRICE_CATEGORY":
            category = (sd_pre.get("category") or "").replace("'", "\'")
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up "
                f"WHERE toLower(category) = toLower('{category}') RETURN avg(up) AS avg_unit_price"
            )
        if intent_pre == "TOTAL_SKUS_IN_CATEGORY":
            category = (sd_pre.get("category") or "").replace("'", "\'")
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category "
                f"WHERE toLower(category) = toLower('{category}') RETURN count(*) AS count"
            )
        if intent_pre == "DISTINCT_CATEGORIES_COUNT":
            return (
                "MATCH (s:SKU) RETURN count(DISTINCT split(split(s.plot, 'category: ')[1], ' | ')[0]) AS count"
            )
        if intent_pre == "COUNT_NEGATIVE_GROSS_PROFIT":
            return (
                "MATCH (s:SKU) WITH toFloat(split(split(s.plot, 'gross_profit: ')[1], ' | ')[0]) AS gp "
                "WHERE gp IS NOT NULL AND gp < 0 RETURN count(*) AS count"
            )
        if intent_pre == "TOP_GP_PER_UNIT_SKU":
            return (
                "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up, "
                "toFloat(split(split(s.plot, 'unit_cost: ')[1], ' | ')[0]) AS uc "
                "WITH s, (up - uc) AS gp_per_unit RETURN s.sku_id AS sku_id, gp_per_unit ORDER BY gp_per_unit DESC LIMIT 1"
            )
        if intent_pre == "COUNTRY_WITH_MOST_SKUS":
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'country: ')[1], ' | ')[0] AS country "
                "RETURN country, count(*) AS c ORDER BY c DESC LIMIT 1"
            )
        if intent_pre == "CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME":
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                "WITH category, avg(lt) AS avg_lt RETURN category, avg_lt ORDER BY avg_lt DESC LIMIT 1"
            )
    except Exception:
        pass

    # Use LLM to classify the query type instead of hard-coded patterns
    query_classification = classify_query_with_llm(question)
    print(f"🔍 DEBUG: LLM classified query as: {query_classification}")
    record_event("cypher.query.classified", {"class": query_classification})

    # Handle based on LLM classification
    if query_classification == "SKU_SPECIFIC":
        # Detect SKU IDs in the question
        sku_pattern = r"SKU\d{3,}"
        sku_ids = re.findall(sku_pattern, question.upper())
        sku_ids = list(set(sku_ids))
        
        if len(sku_ids) >= 1:
            if len(sku_ids) == 1:
                cypher_query = f"MATCH (sku:SKU) WHERE toUpper(sku.sku_id) = '{sku_ids[0].upper()}' RETURN sku.sku_id, sku.name, sku.plot"
                print(f"🔍 DEBUG: Single SKU query: {cypher_query}")
                record_event("cypher.query.generated", {"type": "single_sku"})
                return cypher_query
            else:
                sku_list = ', '.join([f"'{sku.upper()}'" for sku in sku_ids])
                cypher_query = f"MATCH (sku:SKU) WHERE toUpper(sku.sku_id) IN [{sku_list}] RETURN sku.sku_id, sku.name, sku.plot"
                print(f"🔍 DEBUG: Multi-SKU query: {cypher_query}")
                record_event("cypher.query.generated", {"type": "multi_sku", "count": len(sku_ids)})
                return cypher_query
    
    elif query_classification == "ALL_SKUS":
        # Special-case distinct categories requests inside ALL_SKUS branch
        if re.search(r"\b(categories|category list|distinct categories)\b", question, re.IGNORECASE):
            cypher_query = "MATCH (sku:SKU) RETURN DISTINCT split(split(sku.plot, 'category: ')[1], ' | ')[0] AS category ORDER BY category"
            print(f"🔍 DEBUG: Distinct categories query: {cypher_query}")
            record_event("cypher.query.generated", {"type": "distinct_categories"})
            return cypher_query
        # Use LLM to determine if financial data is needed
        financial_classification = classify_financial_data_needed(question)
        if financial_classification == "FINANCIAL_DATA_NEEDED":
            cypher_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot ORDER BY sku.sku_id"
            print(f"🔍 DEBUG: All SKUs with financial data query: {cypher_query}")
        else:
            cypher_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category ORDER BY sku.sku_id"
            print(f"🔍 DEBUG: All SKUs query: {cypher_query}")
        record_event("cypher.query.generated", {"type": "all_skus"})
        return cypher_query
    
    elif query_classification == "DATA_QUERY":
        # PRIORITY: Numeric extraction first for precise counts/averages
        sd_numeric = extract_numeric_intent(question)
        sd = _validate_intent(sd_numeric)
        if (sd.get("intent") or "").upper() == "UNKNOWN":
            sd = _validate_intent(extract_structured_data_intent(question))
        if not isinstance(sd, dict) or not sd.get("intent") or sd.get("intent").upper() == "UNKNOWN":
            # Attempt refinement using the coarse classifier as hint
            coarse = classify_data_query_intent(question)
            sd = _validate_intent(refine_structured_intent(question, sd or {"intent": "UNKNOWN"}, coarse))
        # If refinement still unknown, try numeric pass as a rescue override
        if not isinstance(sd, dict) or (sd.get("intent") or "").upper() == "UNKNOWN":
            rescue = _validate_intent(extract_numeric_intent(question))
            if isinstance(rescue, dict) and (rescue.get("intent") or "").upper() != "UNKNOWN":
                sd = rescue
        intent = (sd.get("intent") or "").upper()
        if intent == "DISTINCT_CATEGORIES_COUNT":
            return (
                "MATCH (s:SKU) RETURN count(DISTINCT split(split(s.plot, 'category: ')[1], ' | ')[0]) AS count"
            )
        # If user asked to list distinct categories, force list query (not count)
        if re.search(r"\b(list|show)\b.*\b(distinct )?categories\b", question, re.IGNORECASE):
            return (
                "MATCH (sku:SKU) RETURN DISTINCT split(split(sku.plot, 'category: ')[1], ' | ')[0] AS category ORDER BY category"
            )
        if intent == "TOTAL_SKUS_IN_CATEGORY":
            category = (sd.get("category") or "").replace("'", "\'")
            return (
                f"MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category "
                f"WHERE toLower(category) = toLower('{category}') RETURN count(*) AS count"
            )
        if intent == "COUNT_NEGATIVE_GROSS_PROFIT":
            return (
                "MATCH (s:SKU) WITH toFloat(split(split(s.plot, 'gross_profit: ')[1], ' | ')[0]) AS gp "
                "WHERE gp IS NOT NULL AND gp < 0 RETURN count(*) AS count"
            )
        if intent == "TOP_GP_PER_UNIT_SKU":
            return (
                "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up, "
                "toFloat(split(split(s.plot, 'unit_cost: ')[1], ' | ')[0]) AS uc "
                "WITH s, (up - uc) AS gp_per_unit RETURN s.sku_id AS sku_id, gp_per_unit ORDER BY gp_per_unit DESC LIMIT 1"
            )
        if intent == "TOP_REVENUE_SKUS_N":
            try:
                n = int(sd.get("n", 3))
            except Exception:
                n = 3
            return (
                "MATCH (s:SKU) "
                "WITH s, "
                "toFloat(coalesce(split(split(s.plot, 'total_revenue: ')[1], ' | ')[0], split(split(s.plot, 'revenue: ')[1], ' | ')[0])) AS rev_raw, "
                "toFloat(split(split(s.plot, 'forecasted_volume: ')[1], ' | ')[0]) AS fv, "
                "toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up "
                "WITH s, coalesce(rev_raw, fv*up) AS rev "
                f"RETURN s.sku_id AS sku_id, rev AS revenue ORDER BY rev DESC LIMIT {n}"
            )
        if intent == "AVG_LEAD_TIME_CATEGORY":
            category = (sd.get("category") or "").replace("'", "\'")
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                f"WHERE toLower(category) = toLower('{category}') RETURN avg(lt) AS avg_lead_time"
            )
        if intent == "AVG_UNIT_PRICE_CATEGORY":
            category = (sd.get("category") or "").replace("'", "\'")
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up "
                f"WHERE toLower(category) = toLower('{category}') RETURN avg(up) AS avg_unit_price"
            )
        if intent == "COUNTRY_WITH_MOST_SKUS":
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'country: ')[1], ' | ')[0] AS country "
                "RETURN country, count(*) AS c ORDER BY c DESC LIMIT 1"
            )
        if intent == "CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME":
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                "WITH category, avg(lt) AS avg_lt RETURN category, avg_lt ORDER BY avg_lt DESC LIMIT 1"
            )
        if intent == "SKUS_WITH_LEAD_TIME_OVER":
            try:
                threshold = float(sd.get("threshold", 25))
            except Exception:
                threshold = 25
            try:
                n = int(sd.get("n", 5))
            except Exception:
                n = 5
            return (
                "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                f"WHERE lt > {threshold} RETURN s.sku_id AS sku_id, lt AS lead_time ORDER BY lead_time DESC LIMIT {n}"
            )
        # Then try robust intent templates
        data_intent = classify_data_query_intent(question)
        print(f"🔍 DEBUG: Data query intent: {data_intent}")
        if data_intent == "ALL_SKUS_LIST":
            return "MATCH (sku:SKU) RETURN sku.sku_id, sku.name ORDER BY sku.sku_id LIMIT 100"
        if data_intent == "DISTINCT_CATEGORIES":
            return "MATCH (sku:SKU) RETURN DISTINCT split(split(sku.plot, 'category: ')[1], ' | ')[0] AS category ORDER BY category"
        if data_intent == "EXCESS_INVENTORY_LIST":
            return (
                "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'initial_inventory: ')[1], ' | ')[0]) AS inv, "
                "toFloat(split(split(s.plot, 'safety_stock: ')[1], ' | ')[0]) AS ss "
                "WHERE inv IS NOT NULL AND ss IS NOT NULL AND inv > ss "
                "RETURN s.sku_id AS sku_id, s.name AS name, inv AS initial_inventory, ss AS safety_stock "
                "ORDER BY (inv - ss) DESC LIMIT 100"
            )
        if data_intent == "NEGATIVE_GROSS_PROFIT_LIST":
            return (
                "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'gross_profit: ')[1], ' | ')[0]) AS gp "
                "WHERE gp IS NOT NULL AND gp < 0 RETURN s.sku_id AS sku_id, s.name AS name, gp AS gross_profit ORDER BY gp ASC LIMIT 100"
            )
        if data_intent == "TOP_REVENUE_SKU":
            return (
                "MATCH (s:SKU) WITH s, toFloat(coalesce(split(split(s.plot, 'total_revenue: ')[1], ' | ')[0], "
                "split(split(s.plot, 'revenue: ')[1], ' | ')[0])) AS rev "
                "RETURN s.sku_id AS sku_id, s.name AS name, rev AS revenue ORDER BY rev DESC LIMIT 1"
            )
        # Structured extraction for more complex intents
        sd = extract_structured_data_intent(question)
        intent = (sd.get("intent") or "").upper()
        if intent == "DISTINCT_CATEGORIES_COUNT":
            return (
                "MATCH (s:SKU) RETURN count(DISTINCT split(split(s.plot, 'category: ')[1], ' | ')[0]) AS count"
            )
        if intent == "TOTAL_SKUS_IN_CATEGORY":
            category = (sd.get("category") or "").replace("'", "\'")
            return (
                f"MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category "
                f"WHERE toLower(category) = toLower('{category}') RETURN count(*) AS count"
            )
        if intent == "COUNT_NEGATIVE_GROSS_PROFIT":
            return (
                "MATCH (s:SKU) WITH toFloat(split(split(s.plot, 'gross_profit: ')[1], ' | ')[0]) AS gp "
                "WHERE gp IS NOT NULL AND gp < 0 RETURN count(*) AS count"
            )
        if intent == "TOP_GP_PER_UNIT_SKU":
            return (
                "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up, "
                "toFloat(split(split(s.plot, 'unit_cost: ')[1], ' | ')[0]) AS uc "
                "WITH s, (up - uc) AS gp_per_unit RETURN s.sku_id AS sku_id, gp_per_unit ORDER BY gp_per_unit DESC LIMIT 1"
            )
        if intent == "TOP_REVENUE_SKUS_N":
            try:
                n = int(sd.get("n", 3))
            except Exception:
                n = 3
            return (
                "MATCH (s:SKU) "
                "WITH s, "
                "toFloat(coalesce(split(split(s.plot, 'total_revenue: ')[1], ' | ')[0], split(split(s.plot, 'revenue: ')[1], ' | ')[0])) AS rev_raw, "
                "toFloat(split(split(s.plot, 'forecasted_volume: ')[1], ' | ')[0]) AS fv, "
                "toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up "
                "WITH s, coalesce(rev_raw, fv*up) AS rev "
                f"RETURN s.sku_id AS sku_id, rev AS revenue ORDER BY rev DESC LIMIT {n}"
            )
        if intent == "AVG_LEAD_TIME_CATEGORY":
            category = (sd.get("category") or "").replace("'", "\'")
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                f"WHERE toLower(category) = toLower('{category}') RETURN avg(lt) AS avg_lead_time"
            )
        if intent == "AVG_UNIT_PRICE_CATEGORY":
            category = (sd.get("category") or "").replace("'", "\'")
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up "
                f"WHERE toLower(category) = toLower('{category}') RETURN avg(up) AS avg_unit_price"
            )
        if intent == "COUNTRY_WITH_MOST_SKUS":
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'country: ')[1], ' | ')[0] AS country "
                "RETURN country, count(*) AS c ORDER BY c DESC LIMIT 1"
            )
        if intent == "CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME":
            return (
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                "WITH category, avg(lt) AS avg_lt RETURN category, avg_lt ORDER BY avg_lt DESC LIMIT 1"
            )
        if intent == "SKUS_WITH_LEAD_TIME_OVER":
            try:
                threshold = float(sd.get("threshold", 25))
            except Exception:
                threshold = 25
            try:
                n = int(sd.get("n", 5))
            except Exception:
                n = 5
            return (
                "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                f"WHERE lt > {threshold} RETURN s.sku_id AS sku_id, lt AS lead_time ORDER BY lead_time DESC LIMIT {n}"
            )
        # Otherwise, use financial classification
        financial_classification = classify_financial_data_needed(question)
        if financial_classification == "FINANCIAL_DATA_NEEDED":
            cypher_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot ORDER BY sku.sku_id"
            print(f"🔍 DEBUG: Data query with financial data: {cypher_query}")
            return cypher_query
        q = generate_cypher_with_llm(question)
        record_event("cypher.query.generated", {"type": "data_query"})
        return q
    
    elif query_classification == "ANALYTICAL":
        # Try to map analytical intents to concrete, data-backed queries
        print(f"🔍 DEBUG: Analytical query detected; mapping to analytical intent")
        record_event("cypher.query.analytical", {"note": "attempt_mapping"})

        ai = extract_analytical_intent(question)
        intent = (ai.get("intent") or "").upper()

        # Intents we can answer directly from SKU.plot fields
        if intent == "EXCESS_INVENTORY_FOR_PROMOTIONS":
            return (
                "MATCH (s:SKU) "
                "WITH s, "
                "toFloat(split(split(s.plot, 'initial_inventory: ')[1], ' | ')[0]) AS inv, "
                "toFloat(split(split(s.plot, 'safety_stock: ')[1], ' | ')[0]) AS ss, "
                "toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS price, "
                "toFloat(split(split(s.plot, 'forecasted_volume: ')[1], ' | ')[0]) AS fv "
                "WITH s, inv, ss, price, fv, (inv - ss) AS excess "
                "WHERE inv IS NOT NULL AND ss IS NOT NULL AND excess > 0 "
                "RETURN s.sku_id AS sku_id, s.name AS name, excess, inv, ss, price, fv "
                "ORDER BY excess DESC LIMIT 20"
            )
        if intent == "REGIONAL_DEMAND_VARIATIONS":
            # Use forecasted_volume if present; otherwise approximate by counting SKUs per country
            return (
                "CALL { "
                "  WITH 1 as x "
                "  MATCH (s:SKU) "
                "  WITH split(split(s.plot, 'country: ')[1], ' | ')[0] AS country, "
                "       toFloat(split(split(s.plot, 'forecasted_volume: ')[1], ' | ')[0]) AS fv "
                "  WHERE country IS NOT NULL "
                "  RETURN country, sum(fv) AS total_volume, count(*) AS c "
                "} "
                "RETURN country, (CASE WHEN total_volume IS NULL OR total_volume = 0 THEN c*1.0 ELSE total_volume END) AS total_volume "
                "ORDER BY total_volume DESC"
            )
        if intent == "MANUFACTURING_CONSTRAINTS_PROXY":
            threshold = float(ai.get("threshold", 25))
            return (
                "MATCH (s:SKU) "
                "WITH s, toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt, "
                "toFloat(split(split(s.plot, 'forecasted_volume: ')[1], ' | ')[0]) AS fv "
                f"WHERE lt IS NOT NULL AND lt > {threshold} "
                "RETURN s.sku_id AS sku_id, s.name AS name, lt AS lead_time_days, fv AS forecasted_volume "
                "ORDER BY lead_time_days DESC, forecasted_volume DESC LIMIT 20"
            )
        if intent == "LEAD_TIME_PLANNING_DATA":
            return (
                "MATCH (s:SKU) "
                "WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                "RETURN category, avg(lt) AS avg_lead_time, max(lt) AS max_lead_time, min(lt) AS min_lead_time "
                "ORDER BY avg_lead_time DESC"
            )
        if intent == "SKUS_TO_TRIM_PROXY":
            return (
                "MATCH (s:SKU) "
                "WITH s, toFloat(split(split(s.plot, 'gross_profit: ')[1], ' | ')[0]) AS gp, "
                "toFloat(split(split(s.plot, 'total_revenue: ')[1], ' | ')[0]) AS rev "
                "WITH s, coalesce(gp,0) AS gp, coalesce(rev,0) AS rev "
                "RETURN s.sku_id AS sku_id, s.name AS name, gp AS gross_profit, rev AS revenue "
                "ORDER BY gp ASC, revenue ASC LIMIT 20"
            )

        # Intents that require data not in the graph schema -> explicit message
        unsupported = {
            "CUSTOMER_ORDER_PRIORITIZATION",
            "PRIORITIZE_LIMITED_SUPPLY_ACROSS_ORDERS",
            "PLANT_UTILIZATION",
            "AVAILABLE_CAPACITY",
            "EXCEED_PRODUCTION_CAPACITY",
            "CUSTOMER_PRIORITIZATION_MATRIX",
            "CUSTOMER_RELATIONSHIP_IMPACT",
            "REGIONAL_SERVICE_LEVELS",
            "INVENTORY_BALANCING_LOCATIONS",
        }
        if intent in unsupported:
            return (
                "MESSAGE:This analysis requires order/customer/plant/capacity entities which are not present in the current graph. "
                "I can provide grounded proxies using SKU-level fields (lead_time_days, safety_stock, initial_inventory, forecasted_volume). "
                "Ask for 'Show me safety stock and reorder analysis', 'Which SKUs have manufacturing constraints?', or 'Analyze regional demand variations'."
            )

        # If we could not map, fall back to generic LLM handling for now
        print("🔍 DEBUG: Analytical mapping unknown; falling back to LLM")
        return None
    
    else:
        # Default to LLM generation
        q = generate_cypher_with_llm(question)
        record_event("cypher.query.generated", {"type": "default"})
        return q

def classify_query_with_llm(question):
    """
    Use LLM to classify the query type instead of hard-coded patterns.
    """
    try:
        from llm import get_llm
        llm = get_llm()
        
        prompt = f"""
        Classify this FMCG supply chain query into one of these categories:
        
        - SKU_SPECIFIC: Queries about specific SKU IDs (e.g., "Tell me about SKU001", "What is SKU002's category?")
        - ALL_SKUS: Queries asking for all SKUs or general data (e.g., "Show me all SKUs", "List all products")
        - DATA_QUERY: Queries that can be answered with direct data lookup (e.g., "Which SKUs have negative profit?", "Show me profitable SKUs")
        - ANALYTICAL: Queries requiring complex calculations or what-if scenarios (e.g., "What if we increase prices by 10%?", "How would demand change if...")
        
        User Query: "{question}"
        
        Return only the category name (SKU_SPECIFIC, ALL_SKUS, DATA_QUERY, or ANALYTICAL):
        """
        
        result = llm.invoke(prompt)
        if hasattr(result, 'content'):
            result_text = result.content
        elif hasattr(result, 'strip'):
            result_text = result.strip()
        else:
            result_text = str(result)
        
        # Clean up the response
        category = result_text.strip().upper()
        valid_categories = ["SKU_SPECIFIC", "ALL_SKUS", "DATA_QUERY", "ANALYTICAL"]
        
        if category in valid_categories:
            return category
        else:
            return "DATA_QUERY"  # Default to data query
            
    except Exception as e:
        print(f"🔍 DEBUG: Query classification failed: {e}")
        return "DATA_QUERY"  # Default to data query

def classify_financial_data_needed(question):
    """
    Use LLM to determine if financial data is needed for the query.
    """
    try:
        from llm import get_llm
        llm = get_llm()
        
        prompt = f"""
        Determine if this FMCG supply chain query requires financial data (revenue, profit, cost, margin, etc.).
        
        Return ONLY one of these classifications:
        - FINANCIAL_DATA_NEEDED: Query explicitly asks for financial metrics, money, revenue, profit, cost, margin, pricing, financial analysis, supply chain gaps, performance analysis, or profitability assessment
        - GENERAL_DATA_ONLY: Query asks for general information like categories, names, basic data without financial focus
        
        Examples:
        - "Show me all SKUs with revenue" → FINANCIAL_DATA_NEEDED
        - "List all products with profit data" → FINANCIAL_DATA_NEEDED  
        - "Show me all SKUs" → GENERAL_DATA_ONLY
        - "What categories do we have?" → GENERAL_DATA_ONLY
        - "Which SKUs are profitable?" → FINANCIAL_DATA_NEEDED
        - "Show me supply chain gaps" → FINANCIAL_DATA_NEEDED
        - "Analyze supply chain performance" → FINANCIAL_DATA_NEEDED
        - "Which products are loss-making?" → FINANCIAL_DATA_NEEDED
        
        User Query: "{question}"
        
        Return only the classification (FINANCIAL_DATA_NEEDED or GENERAL_DATA_ONLY):
        """
        
        result = llm.invoke(prompt)
        if hasattr(result, 'content'):
            result_text = result.content
        elif hasattr(result, 'strip'):
            result_text = result.strip()
        else:
            result_text = str(result)
        
        # Clean up the response
        classification = result_text.strip().upper()
        valid_classifications = ["FINANCIAL_DATA_NEEDED", "GENERAL_DATA_ONLY"]
        
        if classification in valid_classifications:
            return classification
        else:
            return "GENERAL_DATA_ONLY"  # Default to general data
            
    except Exception as e:
        print(f"🔍 DEBUG: Financial classification failed: {e}")
        return "GENERAL_DATA_ONLY"  # Default to general data

def classify_data_query_intent(question: str) -> str:
    """LLM classification for known data-query intents to enforce robust templates.

    Returns: ALL_SKUS_LIST, DISTINCT_CATEGORIES, EXCESS_INVENTORY_LIST,
    NEGATIVE_GROSS_PROFIT_LIST, TOP_REVENUE_SKU, or UNKNOWN.
    """
    try:
        llm = get_llm()
        prompt = f"""
        Classify this user query into one of the following intents:
        - ALL_SKUS_LIST: asking to list all SKUs, master data, or products
        - DISTINCT_CATEGORIES: asking for categories list
        - EXCESS_INVENTORY_LIST: asking which SKUs have excess inventory
        - NEGATIVE_GROSS_PROFIT_LIST: asking which SKUs have negative gross profit
        - TOP_REVENUE_SKU: asking which SKU has highest revenue
        - UNKNOWN: none of the above

        Query: "{question}"

        Return ONLY the intent name.
        """
        result = llm.invoke(prompt)
        text = result.content if hasattr(result, 'content') else str(result)
        intent = text.strip().upper()
        valid = {
            "ALL_SKUS_LIST",
            "DISTINCT_CATEGORIES",
            "EXCESS_INVENTORY_LIST",
            "NEGATIVE_GROSS_PROFIT_LIST",
            "TOP_REVENUE_SKU",
        }
        return intent if intent in valid else "UNKNOWN"
    except Exception as e:
        print(f"🔍 DEBUG: Data intent classification failed: {e}")
        return "UNKNOWN"

def build_sku_field_query(sku_id: str, fields: list[str]) -> str:
    """Build a direct Cypher query to fetch specific fields for a SKU.

    Supported fields include: category, country, unit_price, unit_cost, lead_time_days.
    """
    projections = ["sku.sku_id AS sku_id"]
    field_map = {
        "category": "split(split(sku.plot, 'category: ')[1], ' | ')[0] AS category",
        "country": "split(split(sku.plot, 'country: ')[1], ' | ')[0] AS country",
        "unit_price": "split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] AS unit_price",
        "unit_cost": "split(split(sku.plot, 'unit_cost: ')[1], ' | ')[0] AS unit_cost",
        "lead_time_days": "split(split(sku.plot, 'lead_time_days: ')[1], ' | ')[0] AS lead_time_days",
    }
    for f in fields:
        clause = field_map.get(f.lower())
        if clause:
            projections.append(clause)
    projection_str = ", ".join(projections)
    return f"MATCH (sku:SKU {{sku_id: '{sku_id.upper()}'}}) RETURN {projection_str}"
    
def generate_cypher_with_llm(question):
    """
    Generate Cypher query using LLM instead of hard-coded patterns.
    """
    print(f"🔍 DEBUG: Generating Cypher query with LLM for: '{question}'")

    # Create a prompt for the LLM to generate Cypher queries
    cypher_generation_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Cypher query expert for Neo4j. Your task is to generate precise Cypher queries based on user questions.

IMPORTANT: The data structure is different than typical. SKU nodes have this structure:
- sku_id: The SKU identifier
- name: Product name  
- plot: A pipe-separated string containing all data (category, country, unit_price, unit_cost, etc.)
- data_type: Type of data
- plotEmbedding: Vector embedding (don't return this)

The plot field contains data like: "category: Legumes | country: Country B | unit_price: 10.9 | unit_cost: 5.24 | lead_time_days: 22 | ..."

To extract data from the plot field, use Cypher string functions with proper syntax:
- To get category: split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
- To get unit_price: split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as unit_price
- To get unit_cost: split(split(sku.plot, 'unit_cost: ')[1], ' | ')[0] as unit_cost
- To get country: split(split(sku.plot, 'country: ')[1], ' | ')[0] as country

Example queries:
- ALL SKUs: MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot LIMIT 10
- Specific SKU: MATCH (sku:SKU {{sku_id: 'SKU001'}}) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
- SKU category: MATCH (sku:SKU {{sku_id: 'SKU001'}}) RETURN sku.sku_id, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
- Price analysis: MATCH (sku:SKU) WITH sku, split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as price RETURN sku.sku_id, sku.name, price WHERE price IS NOT NULL
- Category count: MATCH (sku:SKU) RETURN split(split(sku.plot, 'category: ')[1], ' | ')[0] as category, count(*) as count

Analytical Query Examples:
- Top selling product:
  MATCH (sku:SKU) WITH sku, toFloat(split(split(sku.plot, 'total_revenue: ')[1], ' | ')[0]) AS revenue RETURN sku.sku_id, sku.name, revenue ORDER BY revenue DESC LIMIT 1
- SKUs with negative gross profit:
  MATCH (sku:SKU) WITH sku, toFloat(split(split(sku.plot, 'gross_profit: ')[1], ' | ')[0]) AS gp WHERE gp < 0 RETURN sku.sku_id, sku.name, gp
- Average lead time by category:
  MATCH (sku:SKU) WITH split(split(sku.plot, 'category: ')[1], ' | ')[0] AS category, toFloat(split(split(sku.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lead_time RETURN category, avg(lead_time) AS avg_lead_time
- Warehouse with highest inventory value:
  MATCH (sku:SKU) WITH split(split(sku.plot, 'warehouse: ')[1], ' | ')[0] AS warehouse, toFloat(split(sku.plot, 'unit_price: ')[1], ' | ')[0]) AS price, toFloat(split(split(sku.plot, 'initial_inventory: ')[1], ' | ')[0]) AS inv RETURN warehouse, sum(price * inv) AS inventory_value ORDER BY inventory_value DESC LIMIT 1
- SKUs with forecasted volume above 10,000:
  MATCH (sku:SKU) WITH sku, toFloat(split(split(sku.plot, 'forecasted_volume: ')[1], ' | ')[0]) AS fv WHERE fv > 10000 RETURN sku.sku_id, sku.name, fv

IMPORTANT RULES:
- DO NOT return plotEmbedding as it contains large data
- Use proper nested split syntax: split(split(sku.plot, 'field: ')[1], ' | ')[0]
- Handle cases where data might not exist in the plot
- Generate ONLY the Cypher query, no explanations
- Make queries specific to the user's question

CRITICAL: When the user asks about a SPECIFIC SKU (e.g., "Tell me about SKU001", "What is the category of SKU001?"), use:
MATCH (sku:SKU {{sku_id: 'SKU001'}}) RETURN sku.sku_id, sku.name, sku.plot

When the user asks about ALL SKUs with financial data (e.g., "Show me all SKUs with revenue", "List all products with profit data"), use:
MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot LIMIT 10

When the user asks about ALL SKUs without financial data (e.g., "What SKUs are in the Master Data?", "Show me all SKUs"), use:
MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category LIMIT 10

When the user asks about countries (e.g., "Which countries are our products from?"), use:
MATCH (sku:SKU) RETURN DISTINCT split(split(sku.plot, 'country: ')[1], ' | ')[0] as country

IMPORTANT: Look for specific SKU IDs in the question (like SKU001, SKU002, etc.) and use the specific SKU query pattern.

Generate the Cypher query:"""),
        ("human", "{question}")
    ])
    
    try:
        # Generate the query using the LLM
        chain = cypher_generation_prompt | get_llm()
        with timeit("llm.generate_cypher", {"preview": question[:120]}):
            response = chain.invoke({
                "question": question
            })
        
        # Extract the query from the response
        query = response.content.strip()
        
        # Clean up the query (remove markdown formatting if present)
        if query.startswith("```cypher"):
            query = query.replace("```cypher", "").replace("```", "").strip()
        elif query.startswith("```"):
            query = query.replace("```", "").strip()
        
        # Validate the query has basic Cypher structure
        if not query.upper().startswith("MATCH"):
            # Generate a safe fallback query
            query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category LIMIT 10"
        
        # Ensure we don't return large fields
        if "plotEmbedding" in query:
            # Remove plotEmbedding from the query
            query = query.replace("plotEmbedding", "").replace("sku.plotEmbedding", "")
        
        print(f"🔍 DEBUG: Final query: {query}")
        record_event("cypher.query.generated.llm", {"length": len(query)})
        return query
    except Exception as e:
        print(f"❌ DEBUG: Error generating Cypher query: {e}")
        # Return a safe fallback query
        fallback_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category LIMIT 5"
        print(f"🔍 DEBUG: Using error fallback query: {fallback_query}")
        record_event("cypher.query.fallback", {})
        return fallback_query

def execute_dynamic_query(question, available_data=None):
    """
    Execute a dynamically generated Cypher query and return structured results
    """
    try:
        # Generate the query
        query = generate_dynamic_cypher_query(question, available_data)
        
        if not query:
            return {"error": "Failed to generate query"}
        
        print(f"Generated Cypher query: {query}")
        
        # Execute the query
        with timeit("neo4j.query", {"query_preview": query[:140]}):
            results = get_graph().query(query)
        
        payload = {
            "query": query,
            "results": results,
            "count": len(results) if results else 0
        }
        record_event("cypher.query.results", {"count": payload["count"]})
        return payload
    except Exception as e:
        record_event("cypher.query.error", {"message": str(e)})
        return {"error": f"Query execution failed: {str(e)}"}

def analyze_and_format_results(question, results, count):
    """
    Format query results with executive-level analysis and insights.
    """
    if not results or count == 0:
        return "No results found."

    # Check if this is a non-SKU query (like country, category, etc.)
    if results and isinstance(results[0], dict):
        first_row = results[0]
        # Regional demand variations: country + total volume → render ranked table
        if 'country' in first_row and any(k in first_row for k in ('total_volume', 'total', 'sum')):
            # Normalize keys
            rows = []
            for r in results:
                if not isinstance(r, dict):
                    continue
                country = r.get('country')
                total = r.get('total_volume')
                if total is None:
                    total = r.get('total') if r.get('total') is not None else r.get('sum')
                try:
                    total = float(total or 0)
                except Exception:
                    total = 0.0
                if country is not None:
                    rows.append((country, total))
            rows.sort(key=lambda x: x[1], reverse=True)
            grand = sum(v for _, v in rows) or 1.0
            lines = ["# 📊 Regional Demand by Country\n",
                     "| Country | Forecasted Volume | Share |\n",
                     "|---------|--------------------|-------|\n"]
            for country, total in rows:
                share = total / grand * 100.0
                lines.append(f"| {country} | {total:,.0f} | {share:.1f}% |\n")
            return "".join(lines)
        # If the query doesn't return SKU fields and doesn't match a richer formatter, use simple list
        if 'sku.sku_id' not in first_row and 'sku_id' not in first_row:
            return generate_simple_list_response(question, results)

    # Parse the data for executive insights
    parsed_data = []
    for row in results:
        if isinstance(row, dict):
            parsed_row = {}
            for key, value in row.items():
                if key == 'sku.plot' and value:
                    # Parse the complex plot data
                    sku_id = row.get('sku.sku_id') or row.get('sku_id')
                    plot_data = parse_sku_plot_data(value, sku_id)
                    parsed_row.update(plot_data)
                elif key == 'sku.sku_id':
                    # Ensure sku_id is set even when plot data is not available
                    parsed_row['sku_id'] = value
                elif key == 'sku.name':
                    # Ensure name is set
                    parsed_row['name'] = value
                else:
                    parsed_row[key] = value
            parsed_data.append(parsed_row)
        else:
            parsed_data.append(row)

    # Generate executive-level response
    if count == 1:
        return generate_executive_single_sku_response(question, parsed_data[0])
    else:
        return generate_executive_multi_sku_response(question, parsed_data)

def parse_sku_plot_data(plot_string, sku_id=None):
    """
    Parse the complex plot data string into structured data
    """
    data = {}
    if not plot_string:
        return data
    
    # Set the sku_id if provided
    if sku_id:
        data['sku_id'] = sku_id
    
    # Split by | and parse key-value pairs
    parts = plot_string.split(' | ')
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Handle special cases
            if key in ['jan_2024', 'feb_2024', 'mar_2024', 'apr_2024', 'may_2024', 'jun_2024',
                      'jul_2024', 'aug_2024', 'sep_2024', 'oct_2024', 'nov_2024', 'dec_2024',
                      'jan_2025', 'feb_2025', 'mar_2025', 'apr_2025', 'may_2025', 'jun_2025']:
                try:
                    data[f'demand_{key}'] = int(value)
                except:
                    data[f'demand_{key}'] = value
            elif key in ['unit_price', 'unit_cost', 'distribution_cost']:
                try:
                    data[key] = float(value)
                except:
                    data[key] = value
            elif key in ['initial_inventory', 'safety_stock', 'forecasted_volume', 'total_revenue', 'total_cogs', 'gross_profit', 'revenue', 'cogs']:
                try:
                    data[key] = float(value)
                except:
                    data[key] = value
            else:
                data[key] = value
    
    return data

def generate_executive_single_sku_response(question, sku_data):
    """
    Generate executive-level response for single SKU queries with rich visualizations
    """
    # Import chart generation
    charts = {}
    try:
        from solutions.tools.charts import generate_executive_charts, embed_charts_in_response
        charts = generate_executive_charts(sku_data)
    except ImportError:
        print("🔍 DEBUG: Chart generation not available (matplotlib not installed)")
    except Exception as e:
        print(f"❌ DEBUG: Chart generation failed: {e}")
    
    response = f"# 📊 Executive Summary: {sku_data.get('sku_id', 'SKU')}\n\n"
    
    # Basic Information
    response += f"## 🏷️ Product Overview\n"
    response += f"- **Product Name:** {sku_data.get('name', 'N/A')}\n"
    response += f"- **Category:** {sku_data.get('category', 'N/A')}\n"
    response += f"- **Country of Origin:** {sku_data.get('country', 'N/A')}\n"
    response += f"- **Unit of Measure:** {sku_data.get('uom', 'N/A')}\n"
    response += f"- **Warehouse:** {sku_data.get('warehouse', 'N/A')}\n\n"
    
    # Financial Metrics
    response += f"## 💰 Financial Performance\n"
    unit_price = sku_data.get('unit_price', 0)
    unit_cost = sku_data.get('unit_cost', 0)
    # Use correct field names with fallbacks and ensure numeric types
    revenue = float(sku_data.get('total_revenue', sku_data.get('revenue', 0)) or 0)
    cogs = float(sku_data.get('total_cogs', sku_data.get('cogs', 0)) or 0)
    gross_profit = float(sku_data.get('gross_profit', 0) or 0)
    distribution_cost = float(sku_data.get('distribution_cost', 0) or 0)
    
    response += f"- **Unit Price:** ${unit_price:.2f}\n"
    response += f"- **Unit Cost:** ${unit_cost:.2f}\n"
    response += f"- **Gross Profit per Unit:** ${unit_price - unit_cost:.2f}\n"
    
    # Calculate margin safely
    margin = ((unit_price - unit_cost) / unit_price * 100) if unit_price > 0 else 0
    response += f"- **Gross Profit Margin:** {margin:.1f}%\n"
    
    response += f"- **Total Revenue:** ${revenue:,.2f}\n"
    response += f"- **Cost of Goods Sold:** ${cogs:,.2f}\n"
    response += f"- **Gross Profit:** ${gross_profit:,.2f}\n"
    response += f"- **Distribution Cost:** ${distribution_cost:,.2f}\n\n"
    
    # Inventory Management
    response += f"## 📦 Inventory Management\n"
    response += f"- **Initial Inventory:** {sku_data.get('initial_inventory', 0):,} units\n"
    response += f"- **Safety Stock:** {sku_data.get('safety_stock', 0):,} units\n"
    response += f"- **Forecasted Volume:** {sku_data.get('forecasted_volume', 0):,} units\n"
    response += f"- **Lead Time:** {sku_data.get('lead_time_days', 0)} days\n\n"
    
    # Monthly Demand Analysis
    response += f"## 📈 Monthly Demand Analysis (2024-2025)\n"
    months = ['jan_2024', 'feb_2024', 'mar_2024', 'apr_2024', 'may_2024', 'jun_2024',
              'jul_2024', 'aug_2024', 'sep_2024', 'oct_2024', 'nov_2024', 'dec_2024',
              'jan_2025', 'feb_2025', 'mar_2025', 'apr_2025', 'may_2025', 'jun_2025']
    
    response += "| Month | Demand | Supply Plan | Inventory Plan |\n"
    response += "|------|--------|-------------|----------------|\n"
    
    for month in months:
        demand = sku_data.get(f'demand_{month}', 0)
        supply = sku_data.get(f'supply_{month}', 0)
        inventory = sku_data.get(f'inventory_{month}', 0)
        month_name = month.replace('_', ' ').title()
        response += f"| {month_name} | {demand:,} | {supply:,} | {inventory:,} |\n"
    
    response += "\n"
    
    # Strategic Insights
    response += f"## 🎯 Strategic Insights\n"
    
    # Calculate key metrics
    avg_demand = sum(float(sku_data.get(f'demand_{month}', 0) or 0) for month in months) / len(months)
    avg_inventory = sum(float(sku_data.get(f'inventory_{month}', 0) or 0) for month in months) / len(months)
    total_revenue = float(sku_data.get('total_revenue', sku_data.get('revenue', 0)) or 0)
    total_profit = float(sku_data.get('gross_profit', 0) or 0)
    forecasted_volume = float(sku_data.get('forecasted_volume', 1) or 1)
    
    response += f"- **Average Monthly Demand:** {avg_demand:,.0f} units\n"
    response += f"- **Average Monthly Inventory:** {avg_inventory:,.0f} units\n"
    response += f"- **Inventory Turnover Ratio:** {avg_demand / avg_inventory if avg_inventory > 0 else 0:.2f}\n"
    response += f"- **Revenue per Unit:** ${total_revenue / forecasted_volume:.2f}\n"
    response += f"- **Profit per Unit:** ${total_profit / forecasted_volume:.2f}\n\n"
    
    # Recommendations
    response += f"## 💡 Executive Recommendations\n"
    
    if avg_inventory > avg_demand * 1.5:
        ratio = avg_inventory/avg_demand if avg_demand > 0 else 0
        response += f"- ⚠️ **Inventory Optimization Needed:** Current inventory levels are {ratio:.1f}x higher than demand\n"
    elif avg_inventory < avg_demand * 0.8:
        ratio = avg_demand/avg_inventory if avg_inventory > 0 else 0
        response += f"- ⚠️ **Stockout Risk:** Inventory levels are {ratio:.1f}x lower than demand\n"
    else:
        response += f"- ✅ **Optimal Inventory Levels:** Inventory is well-balanced with demand\n"
    
    if sku_data.get('gross_profit', 0) > 0:
        unit_price = sku_data.get('unit_price', 0)
        unit_cost = sku_data.get('unit_cost', 0)
        margin = ((unit_price - unit_cost) / unit_price * 100) if unit_price > 0 else 0
        response += f"- ✅ **Profitable Product:** Strong gross profit margin of {margin:.1f}%\n"
    else:
        response += f"- ❌ **Loss-Making Product:** Negative gross profit margin\n"
    
    response += f"- 📊 **Market Position:** {sku_data.get('category', 'N/A')} category with {sku_data.get('country', 'N/A')} sourcing\n"
    
    # Embed charts if available
    if charts:
        response = embed_charts_in_response(response, charts)
    
    return response

def generate_executive_multi_sku_response(question, sku_data_list):
    """
    Generate executive-level response for multiple SKU queries
    """
    response = f"# 📊 Executive Dashboard: {len(sku_data_list)} SKUs\n\n"
    
    # Filter out corrupted records and use correct field names
    valid_skus = [sku for sku in sku_data_list if sku.get('sku_id') and sku.get('sku_id') != 'None']
    
    # Summary Statistics with safe coercion
    def _num(v):
        try:
            return float(v or 0)
        except Exception:
            return 0.0
    total_revenue = sum(_num(sku.get('total_revenue', sku.get('revenue', 0))) for sku in valid_skus)
    total_profit = sum(_num(sku.get('gross_profit', 0)) for sku in valid_skus)
    total_volume = sum(_num(sku.get('forecasted_volume', 0)) for sku in valid_skus)
    
    response += f"## 📈 Portfolio Overview\n"
    response += f"- **Total Revenue:** ${total_revenue:,.2f}\n"
    response += f"- **Total Gross Profit:** ${total_profit:,.2f}\n"
    response += f"- **Total Forecasted Volume:** {total_volume:,.0f} units\n"
    avg_margin = (total_profit/total_revenue*100) if total_revenue > 0 else 0
    response += f"- **Average Profit Margin:** {avg_margin:.1f}%\n\n"
    
    # Category Analysis
    categories = {}
    for sku in valid_skus:
        category = sku.get('category', 'Unknown')
        if category not in categories:
            categories[category] = {'revenue': 0, 'profit': 0, 'volume': 0, 'count': 0}
        categories[category]['revenue'] += _num(sku.get('total_revenue', sku.get('revenue', 0)))
        categories[category]['profit'] += _num(sku.get('gross_profit', 0))
        categories[category]['volume'] += _num(sku.get('forecasted_volume', 0))
        categories[category]['count'] += 1
    
    response += f"## 🏷️ Category Performance\n"
    response += "| Category | SKUs | Revenue | Profit | Volume | Margin |\n"
    response += "|----------|------|---------|--------|--------|--------|\n"
    
    for category, data in categories.items():
        margin = (data['profit'] / data['revenue'] * 100) if data['revenue'] > 0 else 0
        response += f"| {category} | {data['count']} | ${data['revenue']:,.0f} | ${data['profit']:,.0f} | {data['volume']:,.0f} | {margin:.1f}% |\n"
    
    response += "\n"
    
    # Top Performers
    response += f"## 🏆 Top Performers\n"
    sorted_by_revenue = sorted(valid_skus, key=lambda x: _num(x.get('total_revenue', x.get('revenue', 0))), reverse=True)
    
    response += "| Rank | SKU | Revenue | Profit | Margin | Category |\n"
    response += "|------|-----|---------|--------|--------|----------|\n"
    
    for i, sku in enumerate(sorted_by_revenue[:5], 1):
        revenue = _num(sku.get('total_revenue', sku.get('revenue', 0)))
        profit = _num(sku.get('gross_profit', 0))
        margin = (profit / revenue * 100) if revenue > 0 else 0
        response += f"| {i} | {sku.get('sku_id', 'N/A')} | ${revenue:,.0f} | ${profit:,.0f} | {margin:.1f}% | {sku.get('category', 'N/A')} |\n"
    
    response += "\n"
    
    # Strategic Insights
    response += f"## 🎯 Strategic Insights\n"
    
    # Profitability analysis
    profitable_skus = [sku for sku in valid_skus if float(sku.get('gross_profit', 0) or 0) > 0]
    loss_making_skus = [sku for sku in valid_skus if float(sku.get('gross_profit', 0) or 0) <= 0]
    
    valid_count = len(valid_skus)
    if valid_count > 0:
        response += f"- **Profitable SKUs:** {len(profitable_skus)} ({len(profitable_skus)/valid_count*100:.1f}% of portfolio)\n"
        response += f"- **Loss-Making SKUs:** {len(loss_making_skus)} ({len(loss_making_skus)/valid_count*100:.1f}% of portfolio)\n"
    else:
        response += f"- **No valid SKUs found**\n"
    
    # Category insights
    best_category = max(categories.items(), key=lambda x: x[1]['profit']) if categories else None
    if best_category:
        response += f"- **Best Performing Category:** {best_category[0]} (${best_category[1]['profit']:,.0f} profit)\n"
    
    response += f"- **Portfolio Health:** {'Strong' if len(profitable_skus) > len(loss_making_skus) else 'Needs Attention'}\n"
    
    return response

def generate_simple_list_response(question, results):
    """
    Generate a simple response for non-SKU queries (like country, category lists)
    """
    if not results:
        return "No results found."
    
    # Extract the main field from the results
    if isinstance(results[0], dict):
        # Get the first non-None field
        first_row = results[0]
        main_field = None
        main_values = []
        
        for key, value in first_row.items():
            if value is not None and value != '':
                main_field = key
                break
        
        if main_field:
            # Extract all values for this field
            for row in results:
                if isinstance(row, dict) and row.get(main_field):
                    main_values.append(row[main_field])
            
            # Remove duplicates and None values
            main_values = list(set([v for v in main_values if v is not None]))
            
            if main_values:
                response = f"# 📊 {question.title()}\n\n"
                response += f"Found **{len(main_values)}** unique {main_field.replace('_', ' ').title()}:\n\n"
                
                for i, value in enumerate(main_values, 1):
                    response += f"{i}. **{value}**\n"
                
                return response
    
    # Fallback for unexpected data structure
    return f"# 📊 Query Results\n\nFound **{len(results)}** results for your query."

def enhanced_cypher_qa(question):
    print(f"🔍 DEBUG: ===== ENHANCED_CYPHER_QA CALLED =====")
    print(f"🔍 DEBUG: enhanced_cypher_qa() called with question: '{question}'")
    try:
        # Ultra-early handling for single-SKU field questions to avoid any misrouting
        try:
            sku_match_early = re.search(r"\b(SKU\d{3,})\b", question, re.IGNORECASE)
            if sku_match_early and any(k in question.lower() for k in ["category", "country", "lead time", "unit price", "unit cost"]):
                from solutions.tools.cypher import build_sku_field_query  # local import to avoid cycles
                fields = []
                ql = question.lower()
                if "category" in ql:
                    fields.append("category")
                if "country" in ql:
                    fields.append("country")
                if "lead time" in ql:
                    fields.append("lead_time_days")
                if "unit price" in ql:
                    fields.append("unit_price")
                if "unit cost" in ql:
                    fields.append("unit_cost")
                query_direct = build_sku_field_query(sku_match_early.group(1).upper(), fields)
                rows_direct = execute_query(query_direct)
                if rows_direct:
                    row = rows_direct[0]
                    sid = (row.get("sku_id") or sku_match_early.group(1)).upper()
                    if fields == ["category"]:
                        return f"From database: Category of {sid}: {row.get('category')}"
                    if fields == ["country"]:
                        return f"From database: Country of {sid}: {row.get('country')}"
                    if fields == ["lead_time_days"]:
                        return f"From database: Lead time for {sid}: {row.get('lead_time_days')} days"
                    pieces = []
                    for k in ["category", "country", "unit_price", "unit_cost", "lead_time_days"]:
                        if k in row and row[k] is not None:
                            pieces.append(f"{k}: {row[k]}")
                    if pieces:
                        return f"From database: SKU {sid}: " + ", ".join(pieces)
        except Exception:
            pass

        # Ultra-early deterministic path for gross profit per unit to avoid any LLM routing flakiness
        qlower = (question or "").lower()
        # Ultra-early handling for category listing vs counting
        if re.search(r"\b(list|show)\b.*\b(distinct )?categories\b", qlower):
            rows = execute_query("MATCH (s:SKU) RETURN DISTINCT split(split(s.plot, 'category: ')[1], ' | ')[0] AS category ORDER BY category")
            cats = [r.get('category') for r in rows if isinstance(r, dict) and r.get('category')]
            cats = sorted(list(set(cats)))
            return f"From database: Categories ({len(cats)}): {', '.join(cats)}"

        # Ultra-early handling for distinct categories COUNT
        if re.search(r"\bhow\s+many\b.*\bdistinct\b.*\bcategories\b", qlower):
            rows = execute_query(
                "MATCH (s:SKU) RETURN count(DISTINCT split(split(s.plot, 'category: ')[1], ' | ')[0]) AS count"
            )
            c = 0
            if rows and isinstance(rows[0], dict):
                try:
                    c = int(rows[0].get('count') or 0)
                except Exception:
                    c = 0
            line = f"From database: Distinct categories count: {c}"
            return line

        # Ultra-early handling for avg lead time for a given category
        if re.search(r"average\s+lead\s+time\s+for\s+.*category", qlower):
            cat = _infer_category_from_question(question) or ''
            if cat:
                r = execute_query(
                    "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                    "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                    f"WHERE toLower(category) = toLower('{cat}') RETURN avg(lt) AS avg_lead_time"
                )
                val = 0.0
                if r and isinstance(r[0], dict):
                    try:
                        val = float(r[0].get('avg_lead_time') or 0)
                    except Exception:
                        val = 0.0
                line = f"From database: Average lead time for '{cat}': {val:.1f} days"
                if os.getenv("EVAL_ONE_LINE") == "1":
                    return line
                return line

        # Ultra-early handling for category with highest average lead time
        if re.search(r"which\s+category\s+has\s+the\s+highest\s+average\s+lead\s+time", qlower):
            r = execute_query(
                "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                "WITH category, avg(lt) AS avg_lt RETURN category, avg_lt ORDER BY avg_lt DESC LIMIT 1"
            )
            cat = r[0].get('category') if r and isinstance(r[0], dict) else 'N/A'
            line = f"From database: Category with highest average lead time: {cat}"
            if os.getenv("EVAL_ONE_LINE") == "1":
                return line
            return line
        if "gross profit per unit" in qlower:
            q_gp = (
                "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up, "
                "toFloat(split(split(s.plot, 'unit_cost: ')[1], ' | ')[0]) AS uc "
                "WITH s, (up - uc) AS gp_per_unit RETURN s.sku_id AS sku_id, gp_per_unit ORDER BY gp_per_unit DESC LIMIT 1"
            )
            r_gp = execute_query(q_gp)
            if r_gp and isinstance(r_gp[0], dict):
                sku = _extract_sku_id_from_row(r_gp[0])
                if sku:
                    return f"From database: SKU with highest gross profit per unit: {sku}"
            # Python fallback: scan plots directly
            rows_all = execute_query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
            best_sku = None
            best_diff = float('-inf')
            for r in rows_all:
                plot = (r or {}).get('plot') or ''
                try:
                    up = float(plot.split("unit_price: ",1)[1].split(" | ",1)[0])
                    uc = float(plot.split("unit_cost: ",1)[1].split(" | ",1)[0])
                    diff = up - uc
                    if diff > best_diff and r.get('sku_id'):
                        best_diff = diff
                        best_sku = r.get('sku_id')
                except Exception:
                    continue
            if best_sku:
                return f"From database: SKU with highest gross profit per unit: {best_sku}"

        cypher_query = generate_dynamic_cypher_query(question)
        
        # If analytical query detected, return a user-friendly message
        if cypher_query is None:
            print(f"🔍 DEBUG: Analytical query detected, returning message for LLM handling")
            return "I understand you're looking for analytical insights. Let me analyze the available data to provide you with a comprehensive response."
            
        print(f"🔍 DEBUG: Final Cypher query to execute: {cypher_query}")
        
        # Execute
        result = execute_query(cypher_query)
        print(f"🔍 DEBUG: Query returned {len(result)} results")
        record_event("cypher.query.results", {"count": len(result)})

        # Intelligent empty-result recovery for common analytics
        if (not result) or len(result) == 0:
            try:
                ai_try = extract_analytical_intent(question)
                ai_name = (ai_try.get("intent") or "").upper()
            except Exception:
                ai_name = "UNKNOWN"
            # Manufacturing constraints proxy: relax threshold → top-N by lead time
            if ai_name in {"MANUFACTURING_CONSTRAINTS_PROXY", "SKUS_WITH_LEAD_TIME_OVER"}:
                print("🔍 DEBUG: Empty result for constraints; falling back to top-N by lead time")
                q_fallback_lt = (
                    "MATCH (s:SKU) "
                    "WITH s, toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                    "WHERE lt IS NOT NULL "
                    "RETURN s.sku_id AS sku_id, lt AS lead_time ORDER BY lead_time DESC LIMIT 10"
                )
                result = execute_query(q_fallback_lt)
                record_event("cypher.query.results.fallback", {"count": len(result)})
                if result:
                    pairs = []
                    for r in result:
                        sid = r.get("sku_id") or r.get("s.sku_id")
                        lt = r.get("lead_time") or r.get("lt")
                        if sid is not None and lt is not None:
                            pairs.append(f"{sid} ({lt} days)")
                    if pairs:
                        return "From database: Long lead time SKUs: " + ", ".join(pairs)
            # Regional variations: re-run with count fallback (should already be covered but be safe)
            if ai_name == "REGIONAL_DEMAND_VARIATIONS":
                print("🔍 DEBUG: Empty result for regional variations; applying count fallback")
                q_reg = (
                    "CALL () { WITH 1 as x RETURN 1 } "  # no-op scoped subquery for Neo4j >=5
                    "WITH 1 as x "
                    "MATCH (s:SKU) "
                    "WITH split(split(s.plot, 'country: ')[1], ' | ')[0] AS country "
                    "RETURN country, count(*) AS total_volume ORDER BY total_volume DESC"
                )
                result = execute_query(q_reg)
                record_event("cypher.query.results.fallback", {"count": len(result)})
                if result:
                    return analyze_and_format_results("regional variations (count)", result, len(result))

        # Strong safety fallback for TOP_GP_PER_UNIT_SKU: if structured intent says so but result unusable, rerun deterministic query
        try:
            structured_intent = (resolve_structured_intent(question).get("intent") or "").upper()
        except Exception:
            structured_intent = "UNKNOWN"
        if structured_intent == "TOP_GP_PER_UNIT_SKU":
            sku_try = None
            if result and isinstance(result[0], dict):
                sku_try = _extract_sku_id_from_row(result[0])
            if not result or not sku_try:
                q_gp = (
                    "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up, "
                    "toFloat(split(split(s.plot, 'unit_cost: ')[1], ' | ')[0]) AS uc "
                    "WITH s, (up - uc) AS gp_per_unit RETURN s.sku_id AS sku_id, gp_per_unit ORDER BY gp_per_unit DESC LIMIT 1"
                )
                r_gp = execute_query(q_gp)
                if r_gp and isinstance(r_gp[0], dict):
                    sku = _extract_sku_id_from_row(r_gp[0])
                    if sku:
                        return f"From database: SKU with highest gross profit per unit: {sku}"

        # Heuristic first: if the result clearly represents a top gp-per-unit query, output deterministic one-liner
        if result and isinstance(result[0], dict):
            r0 = result[0]
            if "gp_per_unit" in r0 and (r0.get("sku_id") or r0.get("s.sku_id") or r0.get("sku.sku_id")):
                sku = r0.get("sku_id") or r0.get("s.sku_id") or r0.get("sku.sku_id")
                return f"From database: SKU with highest gross profit per unit: {sku}"
            # Heuristic: average unit price by category
            if "avg_unit_price" in r0:
                try:
                    val = float(r0.get("avg_unit_price") or 0)
                except Exception:
                    val = 0.0
                cat = (resolve_structured_intent(question).get("category")
                       or _infer_category_from_question(question) or "")
                line = f"From database: Average unit price for '{cat}': {val:.2f}"
                if os.getenv("EVAL_ONE_LINE") == "1":
                    return line
                return line
            # Heuristic: total SKUs in a category (count-only result with category phrasing)
            if "count" in r0 and ("how many" in question.lower() and "category" in question.lower()):
                try:
                    cnt = int(r0.get("count") or 0)
                except Exception:
                    cnt = 0
                cat = (resolve_structured_intent(question).get("category")
                       or _infer_category_from_question(question) or "")
                line = f"From database: Total SKUs in category '{cat}': {cnt}"
                if os.getenv("EVAL_ONE_LINE") == "1":
                    return line
                return line

        # Prefer SKU-specific concise formatting when a specific SKU is requested
        sku_match = re.search(r"\b(SKU\d{3,})\b", question, re.IGNORECASE)
        if sku_match and len(result) == 1:
            row = result[0]
            sku_id = (row.get('sku.sku_id') or row.get('sku_id') or sku_match.group(1)).upper()
            plot = row.get('sku.plot') or row.get('plot') or ''
            def _get(field):
                try:
                    return plot.split(f"{field}: ",1)[1].split(" | ",1)[0]
                except Exception:
                    return None
            # Single field specialization (e.g., category of SKU001)
            ql = question.lower()
            if 'category' in ql:
                cat = _get('category')
                if cat:
                    return f"From database: Category of {sku_id}: {cat}"
            if 'country' in ql:
                c = _get('country')
                if c:
                    return f"From database: Country of {sku_id}: {c}"
            if 'lead time' in ql:
                lt = _get('lead_time_days')
                if lt:
                    return f"From database: Lead time for {sku_id}: {lt} days"
            if 'unit price' in ql or 'unit cost' in ql:
                up = _get('unit_price')
                uc = _get('unit_cost')
                pieces = []
                if up:
                    pieces.append(f"unit_price: {up}")
                if uc:
                    pieces.append(f"unit_cost: {uc}")
                if pieces:
                    return f"From database: SKU {sku_id}: " + ", ".join(pieces)
            # Default concise multi-field line for single-SKU
            cat = _get('category')
            c = _get('country')
            up = _get('unit_price')
            uc = _get('unit_cost')
            pieces = []
            if cat:
                pieces.append(f"category: {cat}")
            if c:
                pieces.append(f"country: {c}")
            if up:
                pieces.append(f"unit_price: {up}")
            if uc:
                pieces.append(f"unit_cost: {uc}")
            if pieces:
                return f"From database: SKU {sku_id}: " + ", ".join(pieces[:4])

        # Intent-aware concise formatting for data-listing intents (only when not single-SKU)
        intent = classify_data_query_intent(question)
        structured = resolve_structured_intent(question)
        if intent == "TOP_REVENUE_SKU":
            if not result:
                return "No revenue data found."
            r0 = result[0]
            sku = r0.get("sku_id") or r0.get("s.sku_id")
            rev = r0.get("revenue")
            return f"From database: SKU with highest total revenue: {sku} (revenue: {rev})"
        if structured.get("intent") == "TOP_REVENUE_SKUS_N":
            if not result:
                return "From database: No revenue data found."
            ids = [r.get("sku_id") for r in result if r.get("sku_id")]
            return "From database: Top SKUs by revenue: " + ", ".join(ids)
        if structured.get("intent") == "DISTINCT_CATEGORIES_COUNT":
            if not result:
                return "From database: Distinct categories count: 0"
            c = result[0].get("count") or 0
            line = f"From database: Distinct categories count: {int(c)}"
            if os.getenv("EVAL_ONE_LINE") == "1":
                return line
            return line
        if intent == "DISTINCT_CATEGORIES" or re.search(r"\b(list|show)\b.*\b(distinct )?categories\b", question, re.IGNORECASE):
            # Ensure we list categories, not just count
            cats = [r.get("category") for r in result if isinstance(r, dict) and r.get("category")]
            cats = sorted(list(set(cats)))
            return f"From database: Categories ({len(cats)}): {', '.join(cats)}"
        if structured.get("intent") == "TOTAL_SKUS_IN_CATEGORY":
            if not result:
                return "From database: Total SKUs in category: 0"
            c = result[0].get("count") or 0
            cat = structured.get("category") or ""
            line = f"From database: Total SKUs in category '{cat}': {int(c)}"
            if os.getenv("EVAL_ONE_LINE") == "1":
                return line
            # Otherwise append generic summary
            return line
        if structured.get("intent") == "COUNT_NEGATIVE_GROSS_PROFIT":
            if not result:
                return "From database: Negative GP SKUs count: 0"
            c = result[0].get("count") or 0
            line = f"From database: Negative GP SKUs count: {int(c)}"
            if os.getenv("EVAL_ONE_LINE") == "1":
                return line
            return line
        if structured.get("intent") == "TOP_GP_PER_UNIT_SKU":
            if not result:
                # final fallback deterministic query
                r_gp = execute_query(
                    "MATCH (s:SKU) WITH s, toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up, "
                    "toFloat(split(split(s.plot, 'unit_cost: ')[1], ' | ')[0]) AS uc WITH s, (up - uc) AS gp_per_unit "
                    "RETURN s.sku_id AS sku_id, gp_per_unit ORDER BY gp_per_unit DESC LIMIT 1"
                )
                if r_gp and isinstance(r_gp[0], dict):
                    sku = _extract_sku_id_from_row(r_gp[0])
                    if sku:
                        return f"From database: SKU with highest gross profit per unit: {sku}"
                return "From database: No data found."
            sku = _extract_sku_id_from_row(result[0])
            if not sku:
                return "From database: No data found."
            return f"From database: SKU with highest gross profit per unit: {sku}"
        # As a final safeguard, if the user explicitly asks for gross profit per unit, compute against plots directly
        if "gross profit per unit" in question.lower():
            rows = execute_query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
            best_sku = None
            best_diff = float('-inf')
            for r in rows:
                plot = r.get('plot') or ''
                try:
                    up = float(plot.split("unit_price: ",1)[1].split(" | ",1)[0])
                    uc = float(plot.split("unit_cost: ",1)[1].split(" | ",1)[0])
                    diff = up - uc
                    if diff > best_diff and r.get('sku_id'):
                        best_diff = diff
                        best_sku = r.get('sku_id')
                except Exception:
                    continue
            if best_sku:
                return f"From database: SKU with highest gross profit per unit: {best_sku}"
        # Heuristic formatting based on returned fields to avoid dependence on intent parser
        if result and isinstance(result[0], dict):
            r0 = result[0]
            if "gp_per_unit" in r0:
                sku = _extract_sku_id_from_row(r0)
                if not sku:
                    return "From database: No data found."
                return f"From database: SKU with highest gross profit per unit: {sku}"
        if structured.get("intent") == "AVG_LEAD_TIME_CATEGORY":
            if not result:
                inferred = _infer_category_from_question(question)
                if inferred:
                    q_inline = (
                        "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                        "toFloat(split(split(s.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lt "
                        f"WHERE toLower(category) = toLower('{inferred}') RETURN avg(lt) AS avg_lead_time"
                    )
                    r = execute_query(q_inline)
                    if r:
                        try:
                            val = float(r[0].get('avg_lead_time') or 0)
                        except Exception:
                            val = 0.0
                        line = f"From database: Average lead time for '{inferred}': {val:.1f} days"
                        if os.getenv("EVAL_ONE_LINE") == "1":
                            return line
                        return line
                return "From database: Average lead time for 'N/A': 0.0 days"
            avg = result[0].get("avg_lead_time") or 0
            cat = structured.get("category") or _infer_category_from_question(question) or ""
            try:
                avg_f = float(avg)
            except Exception:
                avg_f = 0.0
            line = f"From database: Average lead time for '{cat}': {avg_f:.1f} days"
            if os.getenv("EVAL_ONE_LINE") == "1":
                return line
            return line
        if structured.get("intent") == "AVG_UNIT_PRICE_CATEGORY":
            if not result:
                inferred = _infer_category_from_question(question)
                if inferred:
                    q_inline = (
                        "MATCH (s:SKU) WITH split(split(s.plot, 'category: ')[1], ' | ')[0] AS category, "
                        "toFloat(split(split(s.plot, 'unit_price: ')[1], ' | ')[0]) AS up "
                        f"WHERE toLower(category) = toLower('{inferred}') RETURN avg(up) AS avg_unit_price"
                    )
                    r = execute_query(q_inline)
                    if r:
                        try:
                            val = float(r[0].get('avg_unit_price') or 0)
                        except Exception:
                            val = 0.0
                        line = f"From database: Average unit price for '{inferred}': {val:.2f}"
                        if os.getenv("EVAL_ONE_LINE") == "1":
                            return line
                        return line
                return "From database: Average unit price: 0"
            avg = result[0].get("avg_unit_price") or 0
            cat = structured.get("category") or _infer_category_from_question(question) or ""
            try:
                avg_f = float(avg)
            except Exception:
                avg_f = 0.0
            line = f"From database: Average unit price for '{cat}': {avg_f:.2f}"
            if os.getenv("EVAL_ONE_LINE") == "1":
                return line
            return line
        if structured.get("intent") == "COUNTRY_WITH_MOST_SKUS":
            if not result:
                return "From database: Country with most SKUs: N/A"
            country = result[0].get("country") or result[0].get("country")
            line = f"From database: Country with most SKUs: {country}"
            if os.getenv("EVAL_ONE_LINE") == "1":
                return line
            return line
        if structured.get("intent") == "CATEGORY_WITH_HIGHEST_AVG_LEAD_TIME":
            if not result:
                return "From database: Category with highest average lead time: N/A"
            cat = result[0].get("category")
            if not cat and isinstance(result[0], dict):
                # Try common aliases
                cat = result[0].get("category") or result[0].get("c")
            return f"From database: Category with highest average lead time: {cat}"
        # Heuristic fallback: if query returned category with avg_lt, format accordingly
        if result and isinstance(result[0], dict) and "avg_lt" in result[0] and result[0].get("category"):
            return f"From database: Category with highest average lead time: {result[0].get('category')}"
        if structured.get("intent") == "SKUS_WITH_LEAD_TIME_OVER":
            if not result:
                return "From database: No SKUs found over the threshold."
            pairs = []
            for r in result:
                sid = r.get("sku_id") or r.get("s.sku_id")
                lt = r.get("lead_time") or r.get("lt")
                if sid and lt is not None:
                    pairs.append(f"{sid} ({lt})")
            return "From database: Long lead time SKUs: " + ", ".join(pairs[:10])
        if intent == "ALL_SKUS_LIST":
            total = len(result)
            ids = []
            for r in result[:20]:
                ids.append(r.get("sku.sku_id") or r.get("sku_id"))
            ids = [i for i in ids if i]
            return f"From database: Total SKUs: {total}. First 20: {', '.join(ids)}"
        if intent == "DISTINCT_CATEGORIES":
            cats = [r.get("category") for r in result if r.get("category")]
            cats = sorted(list(set(cats)))
            return f"From database: Categories ({len(cats)}): {', '.join(cats)}"
        if intent == "EXCESS_INVENTORY_LIST":
            if not result:
                # Try robust fallback by scanning plots and recomputing
                rows = execute_query("MATCH (s:SKU) RETURN s.sku_id AS sku_id, s.plot AS plot")
                items = []
                for r in rows:
                    plot = r.get('plot') or ''
                    try:
                        inv = float(plot.split("initial_inventory: ",1)[1].split(" | ",1)[0])
                        ss = float(plot.split("safety_stock: ",1)[1].split(" | ",1)[0])
                        if inv > ss and inv > 0:
                            items.append((r.get('sku_id'), inv, ss))
                    except Exception:
                        continue
                if not items:
                    return "From database: No SKUs with excess inventory found."
                items.sort(key=lambda x: (x[1]-x[2]), reverse=True)
                first = [f"{sku}: inv={inv}, ss={ss}" for sku,inv,ss in items[:10]]
                return "From database: SKUs with excess inventory: " + "; ".join(first)
            rows = []
            for r in result[:10]:
                rows.append(f"{r.get('sku_id')}: inv={r.get('initial_inventory')}, ss={r.get('safety_stock')}")
            return "From database: SKUs with excess inventory: " + "; ".join(rows)
        if intent == "NEGATIVE_GROSS_PROFIT_LIST":
            if not result:
                return "From database: No SKUs with negative gross profit found."
            rows = []
            for r in result[:10]:
                rows.append(f"{r.get('sku_id')}: gp={r.get('gross_profit')}")
            return "From database: SKUs with negative gross profit: " + "; ".join(rows)

        # If the user asked "Tell me about <SKU>", ensure at least two core fields are echoed
        if re.search(r"\bSKU\d{3,}\b", question, re.IGNORECASE) and len(result) == 1:
            row = result[0]
            plot = row.get('sku.plot') or row.get('plot') or ''
            def _get(field):
                try:
                    return plot.split(f"{field}: ",1)[1].split(" | ",1)[0]
                except Exception:
                    return None
            sku_id = row.get('sku.sku_id') or row.get('sku_id')
            pieces = []
            for k in ['category','country','unit_price','unit_cost']:
                v = _get(k)
                if v:
                    pieces.append(f"{k}: {v}")
            if pieces:
                return f"SKU {sku_id}: " + ", ".join(pieces[:4])

        # Default executive formatting
        formatted_response = analyze_and_format_results(question, result, len(result))
        return formatted_response
        
    except Exception as e:
        print(f"❌ DEBUG: Error in enhanced_cypher_qa: {e}")
        record_event("cypher.qa.error", {"message": str(e)})
        return "I'm having trouble accessing the data right now. Please try again or rephrase your question."

# Keep the original simple cypher_search for backward compatibility
def cypher_search(query):
    """Simple keyword-based search (legacy function)"""
    if not get_graph():
        return []
    
    try:
        # Simple keyword-based search
        cypher_query = """
        MATCH (sku:SKU)
        WHERE toLower(sku.name) CONTAINS toLower($query) 
           OR toLower(sku.plot) CONTAINS toLower($query)
        RETURN sku.name, sku.plot, sku.sku_id
        LIMIT 10
        """
        
        results = get_graph().query(cypher_query, {'query': query})
        return results
    except Exception as e:
        print(f"Cypher search error: {e}")
        return []

def cypher_qa(question):
    """
    Legacy function for backward compatibility - now uses enhanced version
    """
    return enhanced_cypher_qa(question)