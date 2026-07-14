"""Agent 11 · Synonym & Alias Mapper — consolidates every synonym produced
upstream (A4 descriptions, A5 glossary, A9 metric variants) into the master
NL-term → KG-entity lookup, plus multi-word phrase mappings derived from
relationships. This is the hottest lookup at text2sql runtime."""
from __future__ import annotations

from ..context import AgentContext

AID = "a11"


async def run(ctx: AgentContext, state: dict) -> dict:
    descs = state["a4"]["descriptions"]
    domain = state["a5"]["domain_mappings"]
    metrics = state["a9"]["discovered_metrics"]
    rels = state["a8"]["enriched_relationships"]

    ctx.think(AID, "Consolidating synonyms from descriptions (A4), glossary matches (A5) and metric variants (A9)…")

    mappings: list[dict] = []

    glossary_by_col = {(m["table_name"], c["column_name"]): c.get("business_glossary_mapping")
                       for m in domain for c in m["columns"]}

    for d in descs:
        tname = d["table_name"]
        mappings.append(_mapping(tname, "table", tname, d["table_synonyms"]))
        for c in d["columns"]:
            syns = list(c["synonyms"])
            gm = glossary_by_col.get((tname, c["column_name"]))
            if gm:
                syns.append(gm["term"])
            mappings.append(_mapping(c["descriptions"]["short"] or c["column_name"], "column",
                                     f"{tname}.{c['column_name']}", syns))

    for m in metrics:
        mappings.append(_mapping(m["business_name"], "metric", m["metric_id"],
                                 m["natural_language_variants"]))

    # phrase mappings from 1:N relationships: "customers who ordered" style
    phrases = []
    for r in rels:
        if r["cardinality"] not in ("1:N", "N:1", "N:M"):
            continue
        tgt = r["target_table"].replace("_", " ")
        src = r["source_table"].replace("_", " ")
        phrases.append({
            "natural_phrase": f"{tgt} with {src}",
            "maps_to": {"tables": [r["target_table"], r["source_table"]],
                        "columns": [f"{r['source_table']}.{r['source_column']}"],
                        "relationships": [r["relationship_id"]],
                        "filters": []},
        })

    total_syns = sum(len(m["synonyms"]) for m in mappings)
    ctx.think(AID, f"Master lookup ready: {len(mappings)} canonical terms, {total_syns} synonyms, "
                   f"{len(phrases)} phrase mappings.")
    examples = [m for m in mappings if len(m["synonyms"]) >= 2][:3]
    for e in examples:
        ctx.think(AID, f"“{e['canonical_term']}” ← {[s['synonym'] for s in e['synonyms'][:4]]}")

    return {"synonym_mappings": mappings, "phrase_mappings": phrases,
            "_summary": f"{len(mappings)} terms · {total_syns} synonyms · {len(phrases)} phrases"}


def _mapping(canonical: str, entity_type: str, ref: str, synonyms: list[str]) -> dict:
    uniq = list(dict.fromkeys(s.strip().lower() for s in synonyms if s and s.strip()))
    return {
        "canonical_term": canonical,
        "entity_type": entity_type,
        "entity_reference": ref,
        "synonyms": [{"synonym": s, "context": "business", "confidence": 0.85, "language": "en"}
                     for s in uniq],
        "acronyms": [],
        "abbreviations": [],
        "related_terms": [],
    }
