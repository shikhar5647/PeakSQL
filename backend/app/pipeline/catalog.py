"""The single source of truth for the Stage-1 pipeline shape.

Both the LangGraph wiring (graph.py) and the frontend DAG view consume this
catalog, so the picture the user sees is exactly the graph that runs.

Waves reflect dependency-driven parallelism (locked design decision):
cross-phase parallel execution, with A8 and A12 as join barriers.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentSpec:
    id: str            # state key + node name, e.g. "a4"
    num: int
    name: str
    phase: int
    phase_name: str
    wave: int          # execution wave for UI layout (1-based)
    uses_llm: bool
    is_barrier: bool
    description: str
    depends_on: tuple[str, ...] = field(default_factory=tuple)


PHASES = {
    1: "Ingestion & Extraction",
    2: "Semantic Enrichment",
    3: "Relationship Discovery",
    4: "Business Context & Intelligence",
    5: "KG Construction & Validation",
}

AGENTS: list[AgentSpec] = [
    AgentSpec("a1", 1, "Schema Parser", 1, PHASES[1], 1, False, False,
              "Parses .db / .csv / .json input into a unified schema JSON (tables, columns, types, constraints, indexes).",
              ()),
    AgentSpec("a2", 2, "Data Profiler", 1, PHASES[1], 2, False, False,
              "Samples real data: cardinality, nulls, distributions, enum/email/date patterns, cross-table value overlap.",
              ("a1",)),
    AgentSpec("a3", 3, "Naming Convention Analyzer", 2, PHASES[2], 3, False, False,
              "Rule-based decomposition of technical names into business terms (cust_addr_zip → Customer / Address / Zip).",
              ("a1", "a2")),
    AgentSpec("a6", 6, "Explicit Relationship Extractor", 3, PHASES[3], 3, False, False,
              "Extracts declared FKs, junction tables, unique constraints and cardinality — the ground truth relationships.",
              ("a1", "a2")),
    AgentSpec("a4", 4, "Description Generator", 2, PHASES[2], 4, True, False,
              "⭐ CRITICAL — LLM writes technical/business/short descriptions, synonyms and example questions for every table & column.",
              ("a1", "a2", "a3")),
    AgentSpec("a7", 7, "Implicit Relationship Detector", 3, PHASES[3], 4, False, False,
              "Finds undeclared relationships via naming patterns, value overlap and semantic similarity, with confidence scores.",
              ("a1", "a2", "a3")),
    AgentSpec("a5", 5, "Domain Knowledge Integrator", 2, PHASES[2], 5, True, False,
              "Layers business glossary / industry context / compliance tags (PII, financial) on top of generated descriptions.",
              ("a4",)),
    AgentSpec("a8", 8, "Semantic Relationship Enricher", 3, PHASES[3], 5, True, True,
              "🔗 JOIN BARRIER — merges explicit+implicit relationships, classifies them semantically, emits reusable join conditions.",
              ("a4", "a6", "a7")),
    AgentSpec("a9", 9, "Business Metric Discoverer", 4, PHASES[4], 6, True, False,
              "Discovers metrics & KPIs (revenue = SUM(ord_amt)…) with natural-language variants users will actually say.",
              ("a1", "a2", "a4", "a8")),
    AgentSpec("a10", 10, "Query Pattern Analyzer", 4, PHASES[4], 7, True, False,
              "Synthesizes common query shapes — join paths, filters, group-bys — as reusable templates for the text2sql runtime.",
              ("a8", "a9")),
    AgentSpec("a11", 11, "Synonym & Alias Mapper", 4, PHASES[4], 7, True, False,
              "Builds the master NL-term → KG-entity lookup, including multi-word phrase mappings.",
              ("a4", "a5", "a9")),
    AgentSpec("a12", 12, "Neo4j Graph Builder", 5, PHASES[5], 8, False, True,
              "🔗 JOIN BARRIER — materializes everything from A1–A11 as the knowledge graph (in-memory + optional Neo4j write).",
              ("a10", "a11")),
    AgentSpec("a13", 13, "Validation & QA", 5, PHASES[5], 9, False, False,
              "Gates the KG: completeness scores, orphan checks, confidence audit. Critical failures fail the run.",
              ("a12",)),
]

AGENTS_BY_ID = {a.id: a for a in AGENTS}

# Explicit LangGraph edges. Barrier nodes use list-sources so LangGraph waits
# for ALL of them; linear edges omit dependencies already implied upstream.
EDGES: list[tuple[list[str] | str, str]] = [
    ("a1", "a2"),
    ("a2", "a3"),
    ("a2", "a6"),
    ("a3", "a4"),
    ("a3", "a7"),
    ("a4", "a5"),
    (["a4", "a6", "a7"], "a8"),
    ("a8", "a9"),
    ("a9", "a10"),
    (["a5", "a9"], "a11"),
    (["a10", "a11"], "a12"),
    ("a12", "a13"),
]


def catalog_json() -> dict:
    """Serialized catalog for the frontend."""
    return {
        "phases": PHASES,
        "agents": [
            {
                "id": a.id, "num": a.num, "name": a.name,
                "phase": a.phase, "phaseName": a.phase_name,
                "wave": a.wave, "usesLlm": a.uses_llm, "isBarrier": a.is_barrier,
                "description": a.description, "dependsOn": list(a.depends_on),
            }
            for a in AGENTS
        ],
        "waves": max(a.wave for a in AGENTS),
    }
