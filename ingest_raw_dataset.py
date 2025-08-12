#!/usr/bin/env python3
"""
Ingest the external Raw Dataset into Neo4j with a faithful and queryable schema.

This script reads data from `external/Raw Dataset/Homogenoeus/...` and builds:

- (:Product {code}) nodes for each item code in Nodes.csv
- (:Group {code}) and (:SubGroup {code}) classification nodes
- (:Plant {id}) and (:StorageLocation {id}) facility nodes
- Pairwise co-membership edges to preserve original edge semantics:
  - (p1)-[:SAME_GROUP {group_code}]->(p2)
  - (p1)-[:SAME_SUBGROUP {subgroup_code}]->(p2)
  - (p1)-[:CO_PRODUCED_AT {plant_id}]->(p2)
  - (p1)-[:CO_STORED_AT {storage_id}]->(p2)
- Membership edges for normalized navigation:
  - (Product)-[:IN_GROUP]->(Group)
  - (Product)-[:IN_SUBGROUP]->(SubGroup)
  - (Product)-[:AT_PLANT]->(Plant)
  - (Product)-[:AT_STORAGE]->(StorageLocation)
- (:TimeSeries {process, measure, values_json, start_date, end_date}) nodes
  per product and process/measure pair, connected via (Product)-[:HAS_SERIES]->(TimeSeries)

Idempotency: Uses MERGE and deterministic direction for pairwise edges (min(code)->max(code)).

This preserves existing app functionality; it does not modify SKU/Category or plan nodes.
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd


def _get_neo4j_config(key: str, default: str = "") -> str:
    """Fetch Neo4j config from env, fallback to .streamlit/secrets.toml if present."""
    env_value = os.getenv(key)
    if env_value:
        return env_value
    try:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            with open(secrets_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        if k.strip() == key:
                            return v.strip().strip('"')
    except Exception:
        pass
    return default


def get_graph():
    """Create a Neo4j graph connection, raising on failure."""
    from langchain_neo4j import Neo4jGraph

    graph = Neo4jGraph(
        url=_get_neo4j_config("NEO4J_URI"),
        username=_get_neo4j_config("NEO4J_USERNAME", "neo4j"),
        password=_get_neo4j_config("NEO4J_PASSWORD"),
    )
    # Sanity check
    graph.query("RETURN 1 AS ok")
    return graph


RAW_BASE = os.path.join("external", "Raw Dataset", "Homogenoeus")
EXCEL_PATH_DEFAULT = "Enhanced_FMCG_SOP_Dataset.xlsx"


def _csv(path_rel: str) -> str:
    return os.path.join(RAW_BASE, path_rel)


def _excel_sheet(df_or_xl: pd.ExcelFile | str, name: str) -> pd.DataFrame:
    xl = df_or_xl if isinstance(df_or_xl, pd.ExcelFile) else pd.ExcelFile(df_or_xl)
    return pd.read_excel(xl, sheet_name=name)


def read_nodes(excel_path: str | None = None) -> pd.DataFrame:
    csv_path = _csv(os.path.join("Nodes", "Nodes.csv"))
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    # Fallback to Excel
    excel_path = excel_path or EXCEL_PATH_DEFAULT
    return _excel_sheet(excel_path, "Raw - Nodes")


def read_node_types(excel_path: str | None = None) -> pd.DataFrame:
    csv_path = _csv(os.path.join("Nodes", "Node Types (Product Group and Subgroup).csv"))
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    excel_path = excel_path or EXCEL_PATH_DEFAULT
    return _excel_sheet(excel_path, "Raw - Node Types")


def read_edges_product_group(excel_path: str | None = None) -> pd.DataFrame:
    csv_path = _csv(os.path.join("Edges", "Edges (Product Group).csv"))
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    excel_path = excel_path or EXCEL_PATH_DEFAULT
    return _excel_sheet(excel_path, "Raw - Edges Group")


def read_edges_product_subgroup(excel_path: str | None = None) -> pd.DataFrame:
    csv_path = _csv(os.path.join("Edges", "Edges (Product Sub-Group).csv"))
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    excel_path = excel_path or EXCEL_PATH_DEFAULT
    return _excel_sheet(excel_path, "Raw - Edges SubGroup")


def read_edges_plant(excel_path: str | None = None) -> pd.DataFrame:
    csv_path = _csv(os.path.join("Edges", "Edges (Plant).csv"))
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    excel_path = excel_path or EXCEL_PATH_DEFAULT
    return _excel_sheet(excel_path, "Raw - Edges Plant")


def read_edges_storage_location(excel_path: str | None = None) -> pd.DataFrame:
    csv_path = _csv(os.path.join("Edges", "Edges (Storage Location).csv"))
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    excel_path = excel_path or EXCEL_PATH_DEFAULT
    # Storage sheet name
    return _excel_sheet(excel_path, "Raw - Edges Storage")


def _read_temporal(process: str, measure: str, excel_path: str | None = None) -> pd.DataFrame | None:
    """Read a temporal dataframe for given process/measure from CSV if present, else from Excel."""
    # CSV location first
    csv_rel = None
    if measure == "Unit":
        if process == "DeliveryToDistributor":
            csv_rel = os.path.join("Temporal Data", "Unit", "Delivery To distributor.csv")
        elif process == "FactoryIssue":
            csv_rel = os.path.join("Temporal Data", "Unit", "Factory Issue.csv")
        elif process == "Production":
            csv_rel = os.path.join("Temporal Data", "Unit", "Production .csv")
        elif process == "SalesOrder":
            csv_rel = os.path.join("Temporal Data", "Unit", "Sales Order.csv")
    elif measure == "Weight":
        if process == "DeliveryToDistributor":
            csv_rel = os.path.join("Temporal Data", "Weight", "Delivery to Distributor.csv")
        elif process == "FactoryIssue":
            csv_rel = os.path.join("Temporal Data", "Weight", "Factory Issue.csv")
        elif process == "Production":
            csv_rel = os.path.join("Temporal Data", "Weight", "Production .csv")
        elif process == "SalesOrder":
            csv_rel = os.path.join("Temporal Data", "Weight", "Sales Order .csv")
    if csv_rel:
        csv_path = _csv(csv_rel)
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
    # Excel fallback
    excel_path = excel_path or EXCEL_PATH_DEFAULT
    xl = pd.ExcelFile(excel_path)
    # full name and abbreviated name
    full = f"Raw - {process} - {measure}"
    short = f"Raw - {process[:10]}-{measure[:5]}"
    name = full if full in xl.sheet_names else (short if short in xl.sheet_names else None)
    if name is None:
        return None
    return pd.read_excel(xl, sheet_name=name)


def _read_temporal_tables(excel_path: str | None = None) -> List[Tuple[str, str, pd.DataFrame]]:
    """Return list of (process, measure, df), trying CSV first then Excel 'Raw - ' sheets."""
    combos = [(p, m) for p in ("DeliveryToDistributor", "FactoryIssue", "Production", "SalesOrder") for m in ("Unit", "Weight")]
    out: List[Tuple[str, str, pd.DataFrame]] = []
    for process, measure in combos:
        df = _read_temporal(process, measure, excel_path=excel_path)
        if df is not None:
            out.append((process, measure, df))
    return out


def create_indexes(graph) -> None:
    """Create helpful constraints/indexes if not exist (best-effort)."""
    stmts = [
        "CREATE CONSTRAINT product_code IF NOT EXISTS FOR (p:Product) REQUIRE p.code IS UNIQUE",
        "CREATE CONSTRAINT group_code IF NOT EXISTS FOR (g:Group) REQUIRE g.code IS UNIQUE",
        "CREATE CONSTRAINT subgroup_code IF NOT EXISTS FOR (s:SubGroup) REQUIRE s.code IS UNIQUE",
        "CREATE CONSTRAINT plant_id IF NOT EXISTS FOR (p:Plant) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT storage_id IF NOT EXISTS FOR (s:StorageLocation) REQUIRE s.id IS UNIQUE",
    ]
    for q in stmts:
        try:
            graph.query(q)
        except Exception:
            # Non-fatal
            pass


def ingest_products(graph, nodes_df: pd.DataFrame) -> None:
    q = """
    UNWIND $rows AS row
    MERGE (:Product {code: row.code})
    """
    rows = [{"code": str(code).strip()} for code in nodes_df["Node"].dropna().unique()]
    if rows:
        graph.query(q, {"rows": rows})


def ingest_groups(graph, node_types_df: pd.DataFrame) -> None:
    # Group nodes
    q_group_nodes = """
    UNWIND $codes AS code
    MERGE (:Group {code: code})
    """
    # SubGroup nodes
    q_subgroup_nodes = """
    UNWIND $codes AS code
    MERGE (:SubGroup {code: code})
    """
    # Membership
    q_membership = """
    UNWIND $rows AS row
    MATCH (p:Product {code: row.code})
    MERGE (g:Group {code: row.group})
    MERGE (s:SubGroup {code: row.subgroup})
    MERGE (p)-[:IN_GROUP]->(g)
    MERGE (p)-[:IN_SUBGROUP]->(s)
    """
    # Prepare data
    df = node_types_df.dropna(subset=["Node"]).copy()
    df["Group"] = df["Group"].astype(str)
    df["Sub-Group"] = df["Sub-Group"].astype(str)
    group_codes = sorted(df["Group"].dropna().unique().tolist())
    subgroup_codes = sorted(df["Sub-Group"].dropna().unique().tolist())
    rows = [
        {"code": r["Node"], "group": r["Group"], "subgroup": r["Sub-Group"]}
        for _, r in df.iterrows()
    ]
    if group_codes:
        graph.query(q_group_nodes, {"codes": group_codes})
    if subgroup_codes:
        graph.query(q_subgroup_nodes, {"codes": subgroup_codes})
    if rows:
        graph.query(q_membership, {"rows": rows})


def _pair_rows_from_df(df: pd.DataFrame, col1: str, col2: str) -> List[Tuple[str, str]]:
    pairs = []
    for _, r in df.dropna(subset=[col1, col2]).iterrows():
        a = str(r[col1]).strip()
        b = str(r[col2]).strip()
        if not a or not b:
            continue
        if a == b:
            continue
        a_, b_ = (a, b) if a < b else (b, a)
        pairs.append((a_, b_))
    return list({(a, b) for a, b in pairs})  # dedupe


def ingest_group_edges(graph, df: pd.DataFrame) -> None:
    q = """
    UNWIND $rows AS row
    MATCH (a:Product {code: row.a})
    MATCH (b:Product {code: row.b})
    MERGE (a)-[r:SAME_GROUP {group_code: row.group}]->(b)
    """
    rows = []
    for _, r in df.dropna(subset=["node1", "node2", "GroupCode"]).iterrows():
        a, b = str(r["node1"]).strip(), str(r["node2"]).strip()
        if a == b:
            continue
        a_, b_ = (a, b) if a < b else (b, a)
        rows.append({"a": a_, "b": b_, "group": str(r["GroupCode"]).strip()})
    if rows:
        graph.query(q, {"rows": rows})


def ingest_subgroup_edges(graph, df: pd.DataFrame) -> None:
    q = """
    UNWIND $rows AS row
    MATCH (a:Product {code: row.a})
    MATCH (b:Product {code: row.b})
    MERGE (a)-[r:SAME_SUBGROUP {subgroup_code: row.subgroup}]->(b)
    """
    rows = []
    for _, r in df.dropna(subset=["node1", "node2", "SubGroupCode"]).iterrows():
        a, b = str(r["node1"]).strip(), str(r["node2"]).strip()
        if a == b:
            continue
        a_, b_ = (a, b) if a < b else (b, a)
        rows.append({"a": a_, "b": b_, "subgroup": str(r["SubGroupCode"]).strip()})
    if rows:
        graph.query(q, {"rows": rows})


def ingest_plant_edges_and_membership(graph, df: pd.DataFrame) -> None:
    # Membership via Plant node
    q_membership = """
    UNWIND $rows AS row
    MERGE (pl:Plant {id: row.plant_id})
    WITH pl, row
    MATCH (a:Product {code: row.a})
    MATCH (b:Product {code: row.b})
    MERGE (a)-[:AT_PLANT]->(pl)
    MERGE (b)-[:AT_PLANT]->(pl)
    """
    # Pairwise edge with context
    q_pair = """
    UNWIND $rows AS row
    MATCH (a:Product {code: row.a})
    MATCH (b:Product {code: row.b})
    MERGE (a)-[:CO_PRODUCED_AT {plant_id: row.plant_id}]->(b)
    """
    rows = []
    for _, r in df.dropna(subset=["Plant", "node1", "node2"]).iterrows():
        a, b = str(r["node1"]).strip(), str(r["node2"]).strip()
        if a == b:
            continue
        a_, b_ = (a, b) if a < b else (b, a)
        rows.append({"a": a_, "b": b_, "plant_id": str(r["Plant"]).strip()})
    if rows:
        graph.query(q_membership, {"rows": rows})
        graph.query(q_pair, {"rows": rows})


def ingest_storage_edges_and_membership(graph, df: pd.DataFrame) -> None:
    q_membership = """
    UNWIND $rows AS row
    MERGE (sl:StorageLocation {id: row.storage_id})
    WITH sl, row
    MATCH (a:Product {code: row.a})
    MATCH (b:Product {code: row.b})
    MERGE (a)-[:AT_STORAGE]->(sl)
    MERGE (b)-[:AT_STORAGE]->(sl)
    """
    q_pair = """
    UNWIND $rows AS row
    MATCH (a:Product {code: row.a})
    MATCH (b:Product {code: row.b})
    MERGE (a)-[:CO_STORED_AT {storage_id: row.storage_id}]->(b)
    """
    rows = []
    # Storage Location column name may contain a space; pandas will read as 'Storage Location'
    storage_col = "Storage Location" if "Storage Location" in df.columns else df.columns[0]
    for _, r in df.dropna(subset=[storage_col, "node1", "node2"]).iterrows():
        a, b = str(r["node1"]).strip(), str(r["node2"]).strip()
        if a == b:
            continue
        a_, b_ = (a, b) if a < b else (b, a)
        rows.append({"a": a_, "b": b_, "storage_id": str(r[storage_col]).strip()})
    if rows:
        graph.query(q_membership, {"rows": rows})
        graph.query(q_pair, {"rows": rows})


def ingest_temporal_series(graph, excel_path: str | None = None) -> None:
    q = """
    UNWIND $rows AS row
    MATCH (p:Product {code: row.code})
    MERGE (ts:TimeSeries {owner: row.code, process: row.process, measure: row.measure})
      ON CREATE SET ts.values_json = row.values_json, ts.start_date = row.start_date, ts.end_date = row.end_date
      ON MATCH  SET ts.values_json = row.values_json, ts.start_date = row.start_date, ts.end_date = row.end_date
    MERGE (p)-[:HAS_SERIES]->(ts)
    """
    temporal_sets = _read_temporal_tables(excel_path=excel_path)
    # Build product->series map for each (process, measure)
    rows: List[Dict] = []
    for process, measure, df in temporal_sets:
        if "Date" not in df.columns:
            continue
        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"])  # parse dates
        date_strs = df["Date"].dt.strftime("%Y-%m-%d").tolist()
        data_cols = [c for c in df.columns if c != "Date"]
        for code in data_cols:
            # Build values dict of date->value (skip NaNs)
            values: Dict[str, float] = {}
            series = df[["Date", code]].dropna()
            for i, row in series.iterrows():
                val = row[code]
                try:
                    if pd.isna(val):
                        continue
                except Exception:
                    pass
                values[row["Date"].strftime("%Y-%m-%d")] = float(val)
            if not values:
                continue
            start_date = min(values.keys())
            end_date = max(values.keys())
            rows.append({
                "code": str(code).strip(),
                "process": process,
                "measure": measure,
                "values_json": json.dumps(values, separators=(",", ":")),
                "start_date": start_date,
                "end_date": end_date,
            })
    if rows:
        graph.query(q, {"rows": rows})


def ingest_all(excel_path: str | None = None, prefer_excel: bool = False) -> Dict[str, int]:
    graph = get_graph()
    create_indexes(graph)

    # When prefer_excel is True, bypass CSVs by passing excel_path and ignoring CSV existence
    excel_path = excel_path or EXCEL_PATH_DEFAULT

    nodes_df = read_nodes(excel_path if (prefer_excel or not os.path.exists(RAW_BASE)) else None)
    node_types_df = read_node_types(excel_path if (prefer_excel or not os.path.exists(RAW_BASE)) else None)
    edges_group_df = read_edges_product_group(excel_path if (prefer_excel or not os.path.exists(RAW_BASE)) else None)
    edges_subgroup_df = read_edges_product_subgroup(excel_path if (prefer_excel or not os.path.exists(RAW_BASE)) else None)
    edges_plant_df = read_edges_plant(excel_path if (prefer_excel or not os.path.exists(RAW_BASE)) else None)
    edges_storage_df = read_edges_storage_location(excel_path if (prefer_excel or not os.path.exists(RAW_BASE)) else None)

    ingest_products(graph, nodes_df)
    ingest_groups(graph, node_types_df)
    ingest_group_edges(graph, edges_group_df)
    ingest_subgroup_edges(graph, edges_subgroup_df)
    ingest_plant_edges_and_membership(graph, edges_plant_df)
    ingest_storage_edges_and_membership(graph, edges_storage_df)
    ingest_temporal_series(graph, excel_path=excel_path if (prefer_excel or not os.path.exists(RAW_BASE)) else None)

    return {
        "products": int(nodes_df["Node"].nunique()),
        "group_edges": int(len(edges_group_df)),
        "subgroup_edges": int(len(edges_subgroup_df)),
        "plant_rows": int(len(edges_plant_df)),
        "storage_rows": int(len(edges_storage_df)),
    }


def augment_excel_with_raw_data(excel_path: str) -> str:
    """Append raw dataset sheets to an existing Enhanced_FMCG_SOP_Dataset.xlsx.

    This does not modify existing sheets; it adds new sheets prefixed with "Raw - ".
    """
    # Read raw CSVs
    nodes = read_nodes()
    node_types = read_node_types()
    e_group = read_edges_product_group()
    e_subgroup = read_edges_product_subgroup()
    e_plant = read_edges_plant()
    e_storage = read_edges_storage_location()
    temporal = _read_temporal_csvs()

    # Write/append sheets
    # Use mode='a' if file exists; else create
    mode = "a" if os.path.exists(excel_path) else "w"
    with pd.ExcelWriter(excel_path, engine="openpyxl", mode=mode, if_sheet_exists="replace") as writer:
        nodes.to_excel(writer, sheet_name="Raw - Nodes", index=False)
        node_types.to_excel(writer, sheet_name="Raw - Node Types", index=False)
        e_group.to_excel(writer, sheet_name="Raw - Edges Group", index=False)
        e_subgroup.to_excel(writer, sheet_name="Raw - Edges SubGroup", index=False)
        e_plant.to_excel(writer, sheet_name="Raw - Edges Plant", index=False)
        e_storage.to_excel(writer, sheet_name="Raw - Edges Storage", index=False)
        for process, measure, df in temporal:
            safe_name = f"Raw - {process} - {measure}"
            # Excel sheet name max 31 chars; abbreviate if necessary
            if len(safe_name) > 31:
                safe_name = f"Raw - {process[:10]}-{measure[:5]}"
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return excel_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest external Raw Dataset into Neo4j and/or augment Excel.")
    parser.add_argument("--ingest", action="store_true", help="Ingest raw dataset into Neo4j")
    parser.add_argument("--augment-excel", metavar="PATH", help="Append raw dataset sheets to given Excel file")
    parser.add_argument("--excel-path", metavar="PATH", help="Excel path for reading 'Raw -' sheets (fallback or forced)")
    parser.add_argument("--prefer-excel", action="store_true", help="Force reading from Excel even if CSVs exist")
    args = parser.parse_args()

    if not args.ingest and not args.augment_excel:
        parser.print_help()
        raise SystemExit(0)

    if args.ingest:
        stats = ingest_all(excel_path=args.excel_path, prefer_excel=args.prefer_excel)
        print("✅ Raw dataset ingestion complete:")
        for k, v in stats.items():
            print(f"- {k}: {v}")

    if args.augment_excel:
        out = augment_excel_with_raw_data(args.augment_excel)
        print(f"✅ Raw dataset sheets appended to: {out}")


