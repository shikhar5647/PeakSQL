"""Agent 5 · Domain Knowledge Integrator — v1 behavior (locked decision):
near pass-through when no glossary is supplied, but it still does real work:
deterministic compliance tagging (PII/financial) from data-profile patterns.
If a glossary is provided in run options, terms are matched via the LLM."""
from __future__ import annotations

import json

from pydantic import BaseModel, Field

from ..context import AgentContext

AID = "a5"

FINANCIAL_HINTS = ("price", "amount", "amt", "cost", "salary", "balance", "revenue", "payment")
PII_NAME_HINTS = ("name", "email", "phone", "address", "addr", "zip", "dob", "ssn", "birth")


class GlossaryMatch(BaseModel):
    column_name: str
    glossary_term: str
    definition: str = ""
    confidence: float = Field(ge=0, le=1, default=0.8)


class GlossaryMatches(BaseModel):
    table_name: str
    matches: list[GlossaryMatch] = Field(default_factory=list)


async def run(ctx: AgentContext, state: dict) -> dict:
    descriptions = state["a4"]["descriptions"]
    profiles = {p["table_name"]: p for p in state.get("a2", {}).get("table_profiles", [])}
    glossary = (state.get("options") or {}).get("glossary") or []
    industry = (state.get("options") or {}).get("industry", "general")

    if glossary:
        ctx.think(AID, f"Business glossary supplied ({len(glossary)} terms, industry: {industry}). "
                       "Matching schema elements against glossary via LLM…")
    else:
        ctx.think(AID, "No external glossary supplied — running in v1 pass-through mode. "
                       "Still applying deterministic compliance tagging (PII / financial) from data patterns.")

    mappings = []
    n_pii = n_fin = 0
    for d in descriptions:
        tname = d["table_name"]
        prof_by_col = {c["column_name"]: c for c in profiles.get(tname, {}).get("column_profiles", [])}

        glossary_matches: dict[str, GlossaryMatch] = {}
        if glossary:
            result = await ctx.llm.structured(
                agent_id=AID, label=f"glossary-match `{tname}`",
                system="You map database columns to business glossary terms. Only map confident matches.",
                user=(f"Table `{tname}` columns: "
                      f"{[c['column_name'] for c in d['columns']]}\n"
                      f"Glossary: {json.dumps(glossary)[:4000]}\nReturn matches."),
                schema=GlossaryMatches,
                fallback=lambda: GlossaryMatches(table_name=tname),
            )
            glossary_matches = {m.column_name: m for m in result.matches}

        cols = []
        for c in d["columns"]:
            cname = c["column_name"]
            low = cname.lower()
            p = prof_by_col.get(cname, {})
            patterns = p.get("value_patterns", {})
            tags = []
            if patterns.get("is_email") or patterns.get("is_phone") or any(h in low for h in PII_NAME_HINTS):
                tags.append("PII")
                n_pii += 1
            if any(h in low for h in FINANCIAL_HINTS):
                tags.append("financial")
                n_fin += 1
            gm = glossary_matches.get(cname)
            cols.append({
                "column_name": cname,
                "domain_concept": c["descriptions"]["short"],
                "business_glossary_mapping": ({"term": gm.glossary_term, "definition": gm.definition,
                                               "governed_by": None} if gm else None),
                "compliance_tags": tags,
            })
        tagged = [c["column_name"] for c in cols if c["compliance_tags"]]
        if tagged:
            ctx.think(AID, f"`{tname}`: compliance tags on {tagged}")
        mappings.append({
            "table_name": tname,
            "domain_category": industry,
            "industry_concepts": [],
            "columns": cols,
        })

    return {
        "domain_mappings": mappings,
        "_summary": (f"{n_pii} PII + {n_fin} financial tags"
                     + (f" · {sum(1 for m in mappings for c in m['columns'] if c['business_glossary_mapping'])} glossary matches"
                        if glossary else " · pass-through (no glossary)")),
    }
