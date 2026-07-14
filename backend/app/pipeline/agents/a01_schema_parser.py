"""Agent 1 · Schema Parser — .db / .csv / .json → unified schema JSON."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..context import AgentContext

AID = "a1"


async def run(ctx: AgentContext, state: dict) -> dict:
    path = Path(state["input_path"])
    input_type = state["input_type"]
    ctx.think(AID, f"Received `{path.name}` (type: .{input_type}). Extracting a unified schema representation…")

    if input_type == "db":
        tables = _parse_sqlite(ctx, path)
    elif input_type == "csv":
        tables = _parse_csv(ctx, path)
    else:
        tables = _parse_json(ctx, path)

    n_cols = sum(len(t["columns"]) for t in tables)
    n_fks = sum(1 for t in tables for c in t["constraints"] if c["constraint_type"] == "FK")
    ctx.think(AID, f"Unified schema ready: {len(tables)} tables, {n_cols} columns, {n_fks} declared foreign keys.")

    return {
        "schema_metadata": {
            "database_name": path.stem,
            "source_type": input_type,
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "tables": tables,
        "_summary": f"{len(tables)} tables · {n_cols} columns · {n_fks} FKs",
    }


def _parse_sqlite(ctx: AgentContext, path: Path) -> list[dict]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        names = [r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        ctx.think(AID, f"SQLite database opened. Found {len(names)} tables/views: {', '.join(names)}.")

        tables = []
        for name in names:
            kind = cur.execute("SELECT type FROM sqlite_master WHERE name=?", (name,)).fetchone()[0]
            cols_info = cur.execute(f'PRAGMA table_info("{name}")').fetchall()      # cid,name,type,notnull,dflt,pk
            fks = cur.execute(f'PRAGMA foreign_key_list("{name}")').fetchall()      # id,seq,table,from,to,...
            fk_cols = {fk[3] for fk in fks}
            try:
                row_count = cur.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            except sqlite3.Error:
                row_count = 0

            columns = [{
                "column_name": c[1],
                "data_type": (c[2] or "TEXT").upper(),
                "is_nullable": not bool(c[3]) and not bool(c[5]),
                "is_primary_key": bool(c[5]),
                "is_foreign_key": c[1] in fk_cols,
                "default_value": c[4],
                "max_length": None,
            } for c in cols_info]

            constraints = []
            pk_cols = [c[1] for c in cols_info if c[5]]
            if pk_cols:
                constraints.append({"constraint_type": "PK", "columns": pk_cols,
                                    "referenced_table": None, "referenced_columns": None})
            # group FK rows by constraint id (composite FK support)
            by_id: dict[int, dict] = {}
            for fk in fks:
                entry = by_id.setdefault(fk[0], {"constraint_type": "FK", "columns": [],
                                                 "referenced_table": fk[2], "referenced_columns": []})
                entry["columns"].append(fk[3])
                entry["referenced_columns"].append(fk[4] or fk[3])
            constraints.extend(by_id.values())

            indexes = []
            for idx in cur.execute(f'PRAGMA index_list("{name}")').fetchall():
                idx_cols = [r[2] for r in cur.execute(f'PRAGMA index_info("{idx[1]}")').fetchall()]
                indexes.append({"index_name": idx[1], "columns": idx_cols, "is_unique": bool(idx[2])})
                if idx[2] and not idx[1].startswith("sqlite_autoindex"):
                    constraints.append({"constraint_type": "UNIQUE", "columns": idx_cols,
                                        "referenced_table": None, "referenced_columns": None})

            if fks:
                ctx.think(AID, f"`{name}`: {len(columns)} columns, PK ({', '.join(pk_cols) or '—'}), "
                               f"{len(by_id)} FK constraint(s) → {sorted({fk[2] for fk in fks})}.")
            tables.append({"table_name": name, "table_type": kind, "row_count_estimate": row_count,
                           "columns": columns, "constraints": constraints, "indexes": indexes})
        return tables
    finally:
        conn.close()


def _parse_csv(ctx: AgentContext, path: Path) -> list[dict]:
    df = pd.read_csv(path, nrows=5000)
    ctx.think(AID, f"CSV loaded ({len(df)} sampled rows). Inferring column types from data…")
    type_map = {"int64": "INTEGER", "float64": "REAL", "bool": "BOOLEAN",
                "datetime64[ns]": "TIMESTAMP", "object": "TEXT"}
    columns = [{
        "column_name": col,
        "data_type": type_map.get(str(df[col].dtype), "TEXT"),
        "is_nullable": bool(df[col].isna().any()),
        "is_primary_key": False,
        "is_foreign_key": False,
        "default_value": None,
        "max_length": None,
    } for col in df.columns]
    # a fully-unique, non-null column is a PK candidate
    for c in columns:
        s = df[c["column_name"]]
        if s.notna().all() and s.is_unique:
            c["is_primary_key"] = True
            ctx.think(AID, f"Column `{c['column_name']}` is unique and non-null → primary key candidate.")
            break
    return [{"table_name": path.stem, "table_type": "table", "row_count_estimate": len(df),
             "columns": columns,
             "constraints": ([{"constraint_type": "PK",
                               "columns": [c["column_name"] for c in columns if c["is_primary_key"]],
                               "referenced_table": None, "referenced_columns": None}]
                             if any(c["is_primary_key"] for c in columns) else []),
             "indexes": []}]


def _parse_json(ctx: AgentContext, path: Path) -> list[dict]:
    raw = json.loads(path.read_text())
    tables_in = raw.get("tables", raw if isinstance(raw, list) else [])
    ctx.think(AID, f"JSON schema definition loaded. Normalizing {len(tables_in)} table definitions…")
    tables = []
    for t in tables_in:
        columns = [{
            "column_name": c.get("column_name") or c.get("name"),
            "data_type": (c.get("data_type") or c.get("type") or "TEXT").upper(),
            "is_nullable": bool(c.get("is_nullable", c.get("nullable", True))),
            "is_primary_key": bool(c.get("is_primary_key", c.get("primary_key", False))),
            "is_foreign_key": bool(c.get("is_foreign_key", False)),
            "default_value": c.get("default_value"),
            "max_length": c.get("max_length"),
        } for c in t.get("columns", [])]
        tables.append({
            "table_name": t.get("table_name") or t.get("name"),
            "table_type": t.get("table_type", "table"),
            "row_count_estimate": int(t.get("row_count_estimate", 0)),
            "columns": columns,
            "constraints": t.get("constraints", []),
            "indexes": t.get("indexes", []),
        })
    return tables
