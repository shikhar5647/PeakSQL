"""Agent 3 · Naming Convention Analyzer — deterministic (no LLM) decomposition
of technical names into business terms. Gives Agent 4 a clean starting point
and acts as the fallback vocabulary when the LLM is unavailable."""
from __future__ import annotations

import re

from ..context import AgentContext

AID = "a3"

ABBREVIATIONS = {
    "acct": "account", "addr": "address", "amt": "amount", "avg": "average",
    "bal": "balance", "cat": "category", "cd": "code", "cnt": "count",
    "co": "company", "cust": "customer", "dept": "department", "desc": "description",
    "dob": "date of birth", "dt": "date", "emp": "employee", "fk": "foreign key",
    "id": "identifier", "inv": "invoice", "loc": "location", "mgr": "manager",
    "nm": "name", "no": "number", "num": "number", "ord": "order", "org": "organization",
    "pct": "percent", "phn": "phone", "pmt": "payment", "prod": "product",
    "qty": "quantity", "ref": "reference", "seq": "sequence", "src": "source",
    "std": "standard", "tel": "telephone", "tot": "total", "txn": "transaction",
    "usr": "user", "val": "value", "yr": "year", "zip": "zip code",
}
FLAG_PREFIXES = ("is_", "has_", "can_", "should_")
DATE_SUFFIXES = ("_dt", "_date", "_at", "_ts", "_time", "_timestamp")
ID_SUFFIXES = ("_id", "_key", "_no", "_num", "_code")
MEASURE_HINTS = ("amt", "amount", "price", "cost", "total", "qty", "quantity",
                 "count", "balance", "revenue", "salary", "rate", "score", "value")


def split_name(name: str) -> list[str]:
    if "_" in name:
        parts = name.split("_")
    else:  # camelCase / PascalCase
        parts = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", name)
    return [p.lower() for p in parts if p]


def expand(term: str) -> str:
    return ABBREVIATIONS.get(term, term)


def classify(column: str, data_type: str, is_pk: bool, is_fk: bool) -> str:
    low = column.lower()
    if is_pk or is_fk or low.endswith(ID_SUFFIXES):
        return "identifier"
    if low.startswith(FLAG_PREFIXES) or data_type == "BOOLEAN":
        return "flag"
    if low.endswith(DATE_SUFFIXES) or "TIMESTAMP" in data_type or "DATE" in data_type:
        return "timestamp"
    if any(h in low for h in MEASURE_HINTS) and data_type.split("(")[0] in (
            "INTEGER", "REAL", "NUMERIC", "FLOAT", "DOUBLE", "DECIMAL", "BIGINT"):
        return "measure"
    return "dimension"


def detect_convention(names: list[str]) -> str:
    if any("_" in n for n in names):
        return "snake_case"
    if any(re.search(r"[a-z][A-Z]", n) for n in names):
        return "camelCase"
    if any(n[:1].isupper() for n in names):
        return "PascalCase"
    return "snake_case"


async def run(ctx: AgentContext, state: dict) -> dict:
    schema = state["a1"]
    ctx.think(AID, "Decomposing table and column names against the abbreviation dictionary "
                   f"({len(ABBREVIATIONS)} known abbreviations)…")

    analysis = []
    all_names: list[str] = []
    for t in schema["tables"]:
        tname = t["table_name"]
        terms = [expand(p) for p in split_name(tname)]
        base_concept = terms[0].rstrip("s").title() if terms else tname.title()
        cols = []
        for c in t["columns"]:
            parts = split_name(c["column_name"])
            expanded = [expand(p) for p in parts]
            expansions = {p: expand(p) for p in parts if expand(p) != p}
            sem = classify(c["column_name"], c["data_type"], c["is_primary_key"], c["is_foreign_key"])
            cols.append({
                "column_name": c["column_name"],
                "decomposed_terms": expanded,
                "abbreviation_expansions": [{"original": k, "expanded": v} for k, v in expansions.items()],
                "semantic_type": sem,
                "business_term": " ".join(expanded).title(),
            })
            all_names.append(c["column_name"])
        n_expanded = sum(len(c["abbreviation_expansions"]) for c in cols)
        if n_expanded:
            example = next(c for c in cols if c["abbreviation_expansions"])
            ctx.think(AID, f"`{tname}`: expanded {n_expanded} abbreviations — e.g. "
                           f"`{example['column_name']}` → “{example['business_term']}”.")
        analysis.append({
            "table_name": tname,
            "decomposition": {"base_concept": base_concept, "prefixes": [], "suffixes": []},
            "business_entity": " ".join(terms).title(),
            "naming_pattern": detect_convention([tname]),
            "columns": cols,
        })

    sem_counts: dict[str, int] = {}
    for a in analysis:
        for c in a["columns"]:
            sem_counts[c["semantic_type"]] = sem_counts.get(c["semantic_type"], 0) + 1
    ctx.think(AID, "Semantic classification: " + ", ".join(f"{v} {k}s" for k, v in sorted(sem_counts.items())))

    return {
        "naming_analysis": analysis,
        "conventions_detected": {
            "id_pattern": "suffix",
            "date_patterns": [s for s in DATE_SUFFIXES],
            "flag_patterns": [p for p in FLAG_PREFIXES],
            "overall": detect_convention(all_names),
        },
        "_summary": ", ".join(f"{v} {k}" for k, v in sorted(sem_counts.items())),
    }
