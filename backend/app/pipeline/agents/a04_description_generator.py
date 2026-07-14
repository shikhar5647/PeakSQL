"""Agent 4 · Description Generator ⭐ — the LLM-intensive heart of the semantic
layer. One structured LLM call per table (covering its columns), run
concurrently under a semaphore. The deterministic fallback doubles as mock-mode
output and the LLM-failure safety net, so this checkpoint-protected step never
takes the pipeline down."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from ..context import AgentContext

AID = "a4"


class ColumnDescription(BaseModel):
    column_name: str
    technical: str = Field(description="50-80 word technical description")
    business_friendly: str = Field(description="40-60 word business description")
    short: str = Field(description="15-25 word summary")
    synonyms: list[str] = Field(default_factory=list)
    common_queries: list[str] = Field(default_factory=list, description="how users might refer to this column")
    business_rules: list[str] = Field(default_factory=list)
    example_question: str = ""


class TableDescription(BaseModel):
    table_name: str
    technical: str = Field(description="100-150 word technical description")
    business_friendly: str = Field(description="80-120 word business description")
    short: str = Field(description="30-50 word summary")
    entity_type: str = Field(description="transactional|master|reference|bridge")
    table_synonyms: list[str] = Field(default_factory=list)
    business_purpose: str = ""
    update_frequency: str = Field(default="daily", description="real-time|daily|weekly|static")
    columns: list[ColumnDescription] = Field(default_factory=list)


SYSTEM = """You are a senior data analyst documenting a database schema for a text-to-SQL system.
Write precise, information-dense descriptions. The synonyms and example questions you produce
will be used to match natural-language user questions to schema elements, so include the words
real business users would actually say."""


async def run(ctx: AgentContext, state: dict) -> dict:
    schema, profiles, naming = state["a1"], state["a2"], state["a3"]
    prof_by_table = {p["table_name"]: p for p in profiles.get("table_profiles", [])}
    naming_by_table = {n["table_name"]: n for n in naming["naming_analysis"]}
    tables = schema["tables"]

    ctx.think(AID, f"Generating descriptions for {len(tables)} tables "
                   f"(provider: {ctx.llm.provider}, max {ctx.settings.llm_max_concurrency} concurrent calls). "
                   "This is the pipeline's cost bottleneck — everything downstream is checkpointed against it.")

    done = 0
    lock = asyncio.Lock()

    async def describe(t: dict) -> dict:
        nonlocal done
        tname = t["table_name"]
        result = await ctx.llm.structured(
            agent_id=AID,
            label=f"describe table `{tname}`",
            system=SYSTEM,
            user=_build_prompt(t, prof_by_table.get(tname), naming_by_table.get(tname), tables),
            schema=TableDescription,
            fallback=lambda: _fallback(t, prof_by_table.get(tname), naming_by_table.get(tname)),
        )
        async with lock:
            done += 1
            ctx.progress(AID, done, len(tables), f"described `{tname}`")
            ctx.think(AID, f"`{tname}` → “{result.short[:140]}” · synonyms: {result.table_synonyms[:4]}")
        return _to_spec(result)

    described = await asyncio.gather(*[describe(t) for t in tables])
    n_cols = sum(len(d["columns"]) for d in described)
    return {
        "descriptions": list(described),
        "_summary": f"{len(described)} tables · {n_cols} columns described · provider={ctx.llm.provider}",
    }


def _build_prompt(table: dict, profile: dict | None, naming: dict | None, all_tables: list[dict]) -> str:
    cols_ctx = []
    prof_by_col = {c["column_name"]: c for c in (profile or {}).get("column_profiles", [])}
    name_by_col = {c["column_name"]: c for c in (naming or {}).get("columns", [])}
    for c in table["columns"]:
        p = prof_by_col.get(c["column_name"], {})
        n = name_by_col.get(c["column_name"], {})
        cols_ctx.append({
            "name": c["column_name"], "type": c["data_type"],
            "pk": c["is_primary_key"], "fk": c["is_foreign_key"],
            "decomposed": n.get("business_term"),
            "semantic_type": n.get("semantic_type"),
            "samples": p.get("sample_values", [])[:5],
            "enum_values": (p.get("value_patterns") or {}).get("enum_values"),
            "distinct": p.get("distinct_count"),
        })
    related = [c["referenced_table"] for c in table["constraints"]
               if c["constraint_type"] == "FK" and c.get("referenced_table")]
    return (
        f"Describe table `{table['table_name']}` "
        f"({table['row_count_estimate']} rows; other tables in this database: "
        f"{[t['table_name'] for t in all_tables]}; references: {related}).\n"
        f"Columns with profiling context:\n{json.dumps(cols_ctx, default=str)}\n"
        "Produce descriptions for the table AND every column listed."
    )


def _fallback(table: dict, profile: dict | None, naming: dict | None) -> TableDescription:
    """Deterministic descriptions assembled from naming decomposition + data profile."""
    tname = table["table_name"]
    n = naming or {"business_entity": tname.title(), "columns": []}
    name_by_col = {c["column_name"]: c for c in n.get("columns", [])}
    prof_by_col = {c["column_name"]: c for c in (profile or {}).get("column_profiles", [])}
    entity = n.get("business_entity", tname.title())
    fks = [c for c in table["constraints"] if c["constraint_type"] == "FK"]
    entity_type = ("bridge" if len(fks) >= 2 and len(table["columns"]) <= 5
                   else "transactional" if any(c["column_name"].lower().endswith(("_dt", "_date", "_at"))
                                               for c in table["columns"])
                   else "master")

    cols = []
    for c in table["columns"]:
        cname = c["column_name"]
        nm = name_by_col.get(cname, {})
        term = nm.get("business_term", cname.replace("_", " ").title())
        sem = nm.get("semantic_type", "dimension")
        p = prof_by_col.get(cname, {})
        enum_vals = (p.get("value_patterns") or {}).get("enum_values")
        detail = f" Possible values: {', '.join(enum_vals[:6])}." if enum_vals else ""
        singular = entity.lower().rstrip("s")
        cols.append(ColumnDescription(
            column_name=cname,
            technical=f"{c['data_type']} column storing the {term.lower()} of each {singular}."
                      f"{' Primary key.' if c['is_primary_key'] else ''}"
                      f"{' Foreign key.' if c['is_foreign_key'] else ''}{detail}",
            business_friendly=f"The {term.lower()} for a {singular}.{detail}",
            short=term,
            synonyms=list({w for w in term.lower().split() if len(w) > 2}),
            common_queries=[term.lower()],
            business_rules=[],
            example_question=(f"What is the total {term.lower()}?" if sem == "measure"
                              else f"Show records by {term.lower()}"),
        ))
    return TableDescription(
        table_name=tname,
        technical=f"Table `{tname}` ({entity_type}) with {len(table['columns'])} columns storing "
                  f"{entity.lower()} records."
                  + (f" References: {[f['referenced_table'] for f in fks]}." if fks else ""),
        business_friendly=f"Holds one record per {entity.lower().rstrip('s')}.",
        short=f"{entity} records",
        entity_type=entity_type,
        table_synonyms=sorted({entity.lower().rstrip("s"), entity.lower().rstrip("s") + "s",
                               tname.replace("_", " ")}),
        business_purpose=f"Stores {entity.lower()} data.",
        update_frequency="real-time" if entity_type == "transactional" else "daily",
        columns=cols,
    )


def _to_spec(d: TableDescription) -> dict:
    """Reshape the Pydantic result into the documented Agent-4 output contract."""
    return {
        "table_name": d.table_name,
        "table_descriptions": {
            "technical": d.technical, "business_friendly": d.business_friendly,
            "short": d.short, "entity_type": d.entity_type,
        },
        "table_synonyms": d.table_synonyms,
        "business_purpose": d.business_purpose,
        "update_frequency": d.update_frequency,
        "columns": [{
            "column_name": c.column_name,
            "descriptions": {"technical": c.technical, "business_friendly": c.business_friendly,
                             "short": c.short},
            "synonyms": c.synonyms,
            "common_queries": c.common_queries,
            "business_rules": c.business_rules,
            "example_question": c.example_question,
        } for c in d.columns],
        "generation_metadata": {
            "model_used": "heuristic-fallback",
            "confidence_score": 0.9,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
