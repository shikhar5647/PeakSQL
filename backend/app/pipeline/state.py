"""Shared LangGraph state.

One key per agent output — parallel agents write only their own key, so
LangGraph's concurrent update merge is conflict-free (locked design decision).
Values are plain JSON-serializable dicts so the checkpointer can persist them.
"""
from __future__ import annotations

from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    # run inputs
    run_id: str
    input_path: str
    input_type: str          # db | csv | json
    options: dict[str, Any]  # e.g. {"glossary": [...], "industry": "retail"}

    # one slot per agent (spec-shaped JSON)
    a1: dict[str, Any]   # unified schema
    a2: dict[str, Any]   # table/column profiles + potential relationships
    a3: dict[str, Any]   # naming analysis
    a4: dict[str, Any]   # descriptions (LLM)
    a5: dict[str, Any]   # domain mappings / compliance tags
    a6: dict[str, Any]   # explicit relationships + junction tables
    a7: dict[str, Any]   # implicit + hierarchical relationships
    a8: dict[str, Any]   # enriched relationships
    a9: dict[str, Any]   # discovered metrics + KPI candidates
    a10: dict[str, Any]  # query patterns + join paths
    a11: dict[str, Any]  # synonym + phrase mappings
    a12: dict[str, Any]  # graph statistics + construction log
    a13: dict[str, Any]  # validation report
