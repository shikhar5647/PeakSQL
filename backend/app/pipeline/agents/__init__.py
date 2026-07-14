"""Agent implementations, keyed by catalog id."""
from .a01_schema_parser import run as a1
from .a02_data_profiler import run as a2
from .a03_naming_analyzer import run as a3
from .a04_description_generator import run as a4
from .a05_domain_integrator import run as a5
from .a06_explicit_relationships import run as a6
from .a07_implicit_relationships import run as a7
from .a08_semantic_enricher import run as a8
from .a09_metric_discoverer import run as a9
from .a10_query_patterns import run as a10
from .a11_synonym_mapper import run as a11
from .a12_graph_builder import run as a12
from .a13_validator import run as a13

IMPLEMENTATIONS = {
    "a1": a1, "a2": a2, "a3": a3, "a4": a4, "a5": a5, "a6": a6, "a7": a7,
    "a8": a8, "a9": a9, "a10": a10, "a11": a11, "a12": a12, "a13": a13,
}
