"""Application settings.

Every LLM call in the pipeline goes through one OpenAI-compatible client, so
switching between Gemini, a vLLM-served open-source model, or OpenAI is purely
a configuration change (see llm/client.py).
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_prefix="PEAKSQL_", extra="ignore")

    # --- LLM ---
    # provider: "gemini" | "vllm" | "openai" | "mock"
    # "mock" runs the whole pipeline with deterministic heuristic outputs (no API key needed).
    llm_provider: str = "mock"
    llm_model: str = "gemini-3-pro"
    llm_api_key: str = ""
    # Base URL of an OpenAI-compatible endpoint.
    #   Gemini:  https://generativelanguage.googleapis.com/v1beta/openai/
    #   vLLM:    http://localhost:8001/v1
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_max_concurrency: int = 4
    llm_max_retries: int = 2

    # --- Neo4j (optional; pipeline runs fully without it using the in-memory KG) ---
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    # --- Storage ---
    data_dir: Path = BACKEND_DIR / "data"

    # --- Profiling ---
    profile_sample_size: int = 1000

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def runs_dir(self) -> Path:
        return self.data_dir / "runs"

    @property
    def checkpoints_path(self) -> Path:
        return self.data_dir / "checkpoints.sqlite"

    def ensure_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
