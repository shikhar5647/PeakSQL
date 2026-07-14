"""Agent 2 · Data Profiler — samples real data: cardinality, patterns, enums,
and cross-table value overlap (the seed for implicit relationship discovery)."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

from ..context import AgentContext

AID = "a2"

PATTERNS = {
    "is_email": re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$"),
    "is_phone": re.compile(r"^\+?[\d\s().-]{7,15}$"),
    "is_url": re.compile(r"^https?://"),
    "is_date": re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$"),
}
NUMERIC_TYPES = {"INTEGER", "REAL", "NUMERIC", "FLOAT", "DOUBLE", "DECIMAL", "INT", "BIGINT"}


async def run(ctx: AgentContext, state: dict) -> dict:
    schema = state["a1"]
    input_type = state["input_type"]
    path = Path(state["input_path"])
    sample_size = ctx.settings.profile_sample_size

    if input_type == "json":
        ctx.think(AID, "Schema-only input (.json) — no data available to profile. "
                       "Emitting empty profiles; downstream agents will rely on schema + naming signals only.")
        return {"table_profiles": [], "_summary": "no data to profile (schema-only input)"}

    frames = _load_frames(ctx, path, input_type, schema, sample_size)

    profiles = []
    for t in schema["tables"]:
        name = t["table_name"]
        df = frames.get(name)
        if df is None:
            continue
        col_profiles = [_profile_column(df, c["column_name"], c["data_type"], t["row_count_estimate"])
                        for c in t["columns"] if c["column_name"] in df.columns]
        enums = [c for c in col_profiles if c["value_patterns"]["is_enum"]]
        for c in enums:
            ctx.think(AID, f"`{name}.{c['column_name']}` looks like an enum: {c['value_patterns']['enum_values'][:6]}")
        typed = [(c["column_name"], k) for c in col_profiles
                 for k, v in c["value_patterns"].items() if v is True and k not in ("is_enum",)]
        if typed:
            ctx.think(AID, f"`{name}`: detected patterns — " + ", ".join(f"{col} ({k[3:]})" for col, k in typed))
        profiles.append({"table_name": name, "total_rows": int(t["row_count_estimate"]),
                         "column_profiles": col_profiles, "potential_relationships": []})

    _detect_overlaps(ctx, schema, frames, profiles)

    n_enums = sum(1 for p in profiles for c in p["column_profiles"] if c["value_patterns"]["is_enum"])
    n_rels = sum(len(p["potential_relationships"]) for p in profiles)
    return {"table_profiles": profiles,
            "_summary": f"{sum(len(p['column_profiles']) for p in profiles)} columns profiled · "
                        f"{n_enums} enums · {n_rels} overlap candidates"}


def _load_frames(ctx: AgentContext, path: Path, input_type: str, schema: dict,
                 sample_size: int) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    if input_type == "db":
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            for t in schema["tables"]:
                name = t["table_name"]
                frames[name] = pd.read_sql_query(f'SELECT * FROM "{name}" LIMIT {sample_size}', conn)
            ctx.think(AID, f"Sampled up to {sample_size} rows from each of {len(frames)} tables.")
        finally:
            conn.close()
    else:  # csv — single table
        name = schema["tables"][0]["table_name"]
        frames[name] = pd.read_csv(path, nrows=sample_size)
        ctx.think(AID, f"Sampled {len(frames[name])} rows from the CSV.")
    return frames


def _profile_column(df: pd.DataFrame, col: str, data_type: str, total_rows: int) -> dict:
    s = df[col]
    non_null = s.dropna()
    distinct = int(non_null.nunique())
    null_pct = float(round(s.isna().mean() * 100, 2))

    dist: dict = {"min": None, "max": None, "mean": None, "median": None, "mode": None}
    if data_type.split("(")[0] in NUMERIC_TYPES and len(non_null):
        nums = pd.to_numeric(non_null, errors="coerce").dropna()
        if len(nums):
            dist = {"min": float(nums.min()), "max": float(nums.max()),
                    "mean": float(round(nums.mean(), 4)), "median": float(nums.median()),
                    "mode": float(nums.mode().iloc[0]) if len(nums.mode()) else None}
    elif len(non_null):
        as_str = non_null.astype(str)
        dist["min"], dist["max"] = str(as_str.min()), str(as_str.max())
        mode = as_str.mode()
        dist["mode"] = str(mode.iloc[0]) if len(mode) else None

    samples = [_jsonable(v) for v in non_null.head(8).tolist()]
    str_sample = non_null.astype(str).head(200)
    patterns = {key: bool(len(str_sample) and str_sample.str.match(rx).mean() > 0.85)
                for key, rx in PATTERNS.items()}
    is_enum = bool(distinct and distinct <= 20 and len(non_null) >= max(20, distinct * 3)
                   and not patterns["is_date"])
    return {
        "column_name": col,
        "distinct_count": distinct,
        "null_percentage": null_pct,
        "value_distribution": dist,
        "sample_values": samples,
        "value_patterns": {
            "is_enum": is_enum,
            "enum_values": sorted(non_null.astype(str).unique().tolist())[:20] if is_enum else None,
            "regex_pattern": next((k[3:] for k, v in patterns.items() if v), None),
            **patterns,
        },
        "data_quality": {
            "completeness_score": round(1 - null_pct / 100, 3),
            "uniqueness_score": round(distinct / len(s), 3) if len(s) else 0.0,
        },
    }


def _detect_overlaps(ctx: AgentContext, schema: dict, frames: dict[str, pd.DataFrame],
                     profiles: list[dict]) -> None:
    """Cross-table value containment between id-ish columns → implicit FK candidates."""
    declared = {(c2["columns"][0], t["table_name"])
                for t in schema["tables"] for c2 in t["constraints"]
                if c2["constraint_type"] == "FK" and c2["columns"]}
    pk_cols: list[tuple[str, str, set]] = []   # (table, column, values)
    id_cols: list[tuple[str, str, set]] = []
    for t in schema["tables"]:
        name = t["table_name"]
        df = frames.get(name)
        if df is None:
            continue
        table_pk = next((c2["columns"] for c2 in t["constraints"] if c2["constraint_type"] == "PK"), [])
        for c in t["columns"]:
            col = c["column_name"]
            if col not in df.columns:
                continue
            values = set(df[col].dropna().astype(str).head(2000))
            if not values:
                continue
            if c["is_primary_key"] and len(table_pk) == 1:
                pk_cols.append((name, col, values))
            # id-ish columns are FK candidates — including members of a COMPOSITE
            # PK (junction tables are exactly where undeclared FKs live)
            if col.lower().endswith(("_id", "id")) and not (c["is_primary_key"] and len(table_pk) == 1):
                id_cols.append((name, col, values))

    # Rank candidates by overlap × naming affinity and keep only the best target
    # per source column — raw containment alone is trivially 100% between any two
    # small integer id ranges, which would flood A7 with false positives.
    from difflib import SequenceMatcher

    by_table = {p["table_name"]: p for p in profiles}
    candidates: dict[tuple[str, str], list[tuple[float, float, str, str]]] = {}
    for src_table, src_col, src_vals in id_cols:
        for tgt_table, tgt_col, tgt_vals in pk_cols:
            if tgt_table == src_table or (src_col, src_table) in declared:
                continue
            overlap = len(src_vals & tgt_vals) / len(src_vals)
            if overlap < 0.6:
                continue
            name_sim = SequenceMatcher(None, src_col.lower(), tgt_col.lower()).ratio()
            score = overlap * (0.4 + 0.6 * name_sim)
            candidates.setdefault((src_table, src_col), []).append((score, overlap, tgt_table, tgt_col))

    for (src_table, src_col), cands in candidates.items():
        score, overlap, tgt_table, tgt_col = max(cands)
        if score < 0.65:
            continue
        by_table[src_table]["potential_relationships"].append({
            "source_column": src_col, "target_table": tgt_table, "target_column": tgt_col,
            "overlap_percentage": round(overlap * 100, 1),
            "confidence": round(min(0.98, score), 2),
        })
        ctx.think(AID, f"Value overlap: `{src_table}.{src_col}` ⊆ `{tgt_table}.{tgt_col}` "
                       f"at {overlap * 100:.0f}% (best of {len(cands)} candidate targets) "
                       "— candidate implicit relationship.")


def _jsonable(v):
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v if isinstance(v, (int, float, bool)) else str(v)
