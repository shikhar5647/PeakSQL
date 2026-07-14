"""Agent 8 · Semantic Relationship Enricher 🔗 (join barrier) — merges explicit
+ implicit relationships, classifies each semantically via one batched LLM
call, and emits the reusable SQL join condition the text2sql runtime will use."""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..context import AgentContext

AID = "a8"


class RelClassification(BaseModel):
    relationship_id: str
    semantic_type: str = Field(description="dependency|aggregation|association|composition|inheritance")
    relationship_strength: str = Field(default="strong", description="strong|weak")
    business_meaning: str = ""
    is_temporal: bool = False
    temporal_type: str | None = Field(default=None, description="snapshot|slowly_changing|event|null")


class RelClassifications(BaseModel):
    classifications: list[RelClassification] = Field(default_factory=list)


async def run(ctx: AgentContext, state: dict) -> dict:
    explicit = state["a6"]["explicit_relationships"]
    implicit = state["a7"]["implicit_relationships"]
    junctions = {j["table_name"] for j in state["a6"]["junction_tables"]}
    desc_by_table = {d["table_name"]: d for d in state["a4"]["descriptions"]}

    merged = _merge(explicit, implicit)
    ctx.think(AID, f"Join barrier reached — merging {len(explicit)} explicit + {len(implicit)} implicit "
                   f"relationships → {len(merged)} unique. Classifying semantically…")

    if merged:
        summaries = [{
            "relationship_id": r["relationship_id"],
            "join": f"{r['source_table']}.{r['source_column']} -> {r['target_table']}.{r['target_column']}",
            "source_is_junction": r["source_table"] in junctions,
            "source_table_description": _short_desc(desc_by_table, r["source_table"]),
            "target_table_description": _short_desc(desc_by_table, r["target_table"]),
        } for r in merged]
        result = await ctx.llm.structured(
            agent_id=AID, label=f"classify {len(merged)} relationships",
            system=("You classify database relationships semantically for a knowledge graph. "
                    "For each, choose semantic_type and write a one-sentence business_meaning "
                    "(e.g. 'an order is placed by a customer')."),
            user=f"Relationships to classify:\n{summaries}",
            schema=RelClassifications,
            fallback=lambda: _fallback(merged, junctions, desc_by_table),
        )
        by_id = {c.relationship_id: c for c in result.classifications}
    else:
        by_id = {}

    enriched = []
    for r in merged:
        c = by_id.get(r["relationship_id"]) or _heuristic_one(r, junctions, desc_by_table)
        enriched.append({
            "relationship_id": r["relationship_id"],
            "source_table": r["source_table"], "source_column": r["source_column"],
            "target_table": r["target_table"], "target_column": r["target_column"],
            "semantic_type": c.semantic_type,
            "cardinality": r.get("cardinality") or r.get("suggested_cardinality", "1:N"),
            "relationship_strength": c.relationship_strength,
            "business_meaning": c.business_meaning,
            "join_path": {
                "join_condition": f"{r['source_table']}.{r['source_column']} = "
                                  f"{r['target_table']}.{r['target_column']}",
                "is_direct": True,
                "intermediate_tables": None,
            },
            "temporal_nature": {"is_temporal": c.is_temporal, "temporal_type": c.temporal_type},
            "directionality": "unidirectional",
            "confidence_score": r.get("confidence_score", 1.0),
            "origin": r["_origin"],
        })
        ctx.think(AID, f"`{r['source_table']}` → `{r['target_table']}`: {c.semantic_type} — “{c.business_meaning}”")

    return {"enriched_relationships": enriched,
            "_summary": f"{len(enriched)} relationships enriched with join conditions"}


def _merge(explicit: list[dict], implicit: list[dict]) -> list[dict]:
    merged, seen = [], set()
    for r in explicit:
        key = (r["source_table"], r["source_column"], r["target_table"])
        seen.add(key)
        merged.append({**r, "confidence_score": 1.0, "_origin": "explicit"})
    for r in implicit:
        key = (r["source_table"], r["source_column"], r["target_table"])
        if key not in seen:
            seen.add(key)
            merged.append({**r, "_origin": f"implicit ({r['detection_method']})"})
    return merged


def _short_desc(desc_by_table: dict, table: str) -> str:
    d = desc_by_table.get(table)
    return d["table_descriptions"]["short"] if d else table


def _heuristic_one(r: dict, junctions: set[str], desc_by_table: dict) -> RelClassification:
    sem = "aggregation" if r["source_table"] in junctions else "association"
    src = _short_desc(desc_by_table, r["source_table"]).lower().rstrip("s") or r["source_table"]
    tgt = _short_desc(desc_by_table, r["target_table"]).lower().rstrip("s") or r["target_table"]
    return RelClassification(
        relationship_id=r["relationship_id"], semantic_type=sem,
        relationship_strength="strong" if r.get("confidence_score", 1.0) >= 0.8 else "weak",
        business_meaning=f"each record in {r['source_table']} ({src}) references one {tgt} in {r['target_table']}",
        is_temporal=False, temporal_type=None)


def _fallback(merged: list[dict], junctions: set[str], desc_by_table: dict) -> RelClassifications:
    return RelClassifications(classifications=[_heuristic_one(r, junctions, desc_by_table) for r in merged])
