"""LangGraph wiring for Stage 1.

Edges come from catalog.EDGES — dependency-driven parallelism with barrier
(list-source) edges at A8 and A12, exactly matching the locked wave design:

  wave 1: A1          wave 4: A4 ‖ A7      wave 7: A10 ‖ A11
  wave 2: A2          wave 5: A5 ‖ A8      wave 8: A12
  wave 3: A3 ‖ A6     wave 6: A9           wave 9: A13

Checkpointing (SQLite) snapshots state after every node so a downstream
failure never forces re-running the LLM-expensive Agent 4.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .agents import IMPLEMENTATIONS
from .catalog import AGENTS, EDGES
from .context import AgentContext, make_node
from .state import PipelineState


def build_graph(ctx: AgentContext):
    builder = StateGraph(PipelineState)
    for agent in AGENTS:
        builder.add_node(agent.id, make_node(agent, IMPLEMENTATIONS[agent.id], ctx))

    builder.add_edge(START, "a1")
    for source, target in EDGES:
        builder.add_edge(source, target)
    builder.add_edge("a13", END)
    return builder
