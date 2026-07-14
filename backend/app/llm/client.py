"""Provider-agnostic structured LLM client.

Design rules (locked):
- No agent ever touches a provider SDK. Everything goes through
  `LLMClient.structured()`, which takes a Pydantic schema and returns a
  validated instance.
- Providers are OpenAI-compatible endpoints (Gemini's compat layer, vLLM,
  OpenAI). Switching = config change.
- Every LLM agent supplies a deterministic `fallback` generator. It IS the
  implementation in mock mode, and the safety net when a real provider fails
  after retries — so the pipeline never dies on a malformed LLM response.
- Every call emits an `agent_llm` event (prompt/response previews, latency)
  so the UI can show the model's actual work.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel

from ..config import Settings
from ..pipeline.events import RunRecord

T = TypeVar("T", bound=BaseModel)

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> Any:
    """Parse a JSON object out of a model response (tolerates ``` fences)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        m = _JSON_RE.search(cleaned)
        if not m:
            raise
        return json.loads(m.group(0))


class LLMClient:
    def __init__(self, settings: Settings, run: RunRecord):
        self.settings = settings
        self.run = run
        self.provider = run.llm_provider or settings.llm_provider
        self._semaphore = asyncio.Semaphore(settings.llm_max_concurrency)
        self._client = None
        if self.provider != "mock":
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=settings.llm_api_key or "EMPTY",
                base_url=settings.llm_base_url or None,
            )

    async def structured(
        self,
        *,
        agent_id: str,
        label: str,
        system: str,
        user: str,
        schema: Type[T],
        fallback: Callable[[], T],
    ) -> T:
        """Return a schema-validated response; never raises on LLM failure."""
        if self.provider == "mock":
            result = fallback()
            self.run.emit("agent_llm", agent_id, label=label, provider="mock",
                          model="heuristic-fallback", durationMs=0,
                          promptPreview=user[:600],
                          responsePreview=result.model_dump_json()[:600])
            return result

        schema_json = json.dumps(schema.model_json_schema(), indent=None)
        messages = [
            {"role": "system", "content": system
                + "\nRespond ONLY with a JSON object that validates against this JSON Schema:\n"
                + schema_json},
            {"role": "user", "content": user},
        ]
        last_error: Exception | None = None
        for attempt in range(self.settings.llm_max_retries + 1):
            start = time.time()
            try:
                async with self._semaphore:
                    kwargs: dict[str, Any] = dict(
                        model=self.settings.llm_model,
                        messages=messages,
                        temperature=0.2,
                    )
                    if self.provider == "vllm":
                        # vLLM guided decoding: constrain generation to the schema.
                        kwargs["extra_body"] = {"guided_json": schema.model_json_schema()}
                    else:
                        kwargs["response_format"] = {"type": "json_object"}
                    resp = await self._client.chat.completions.create(**kwargs)
                text = resp.choices[0].message.content or ""
                result = schema.model_validate(_extract_json(text))
                self.run.emit("agent_llm", agent_id, label=label, provider=self.provider,
                              model=self.settings.llm_model,
                              durationMs=int((time.time() - start) * 1000),
                              promptPreview=user[:600], responsePreview=text[:600])
                return result
            except Exception as e:  # noqa: BLE001 — resilience is the contract here
                last_error = e
                self.run.emit("agent_llm", agent_id, label=f"{label} (retry {attempt + 1})",
                              provider=self.provider, model=self.settings.llm_model,
                              durationMs=int((time.time() - start) * 1000),
                              promptPreview=user[:600], error=str(e)[:400])
                # nudge the model on validation retries
                messages.append({"role": "user",
                                 "content": f"Your previous response was invalid ({e}). "
                                            "Return ONLY the corrected JSON object."})
        result = fallback()
        self.run.emit("agent_thought", agent_id,
                      text=f"⚠️ LLM failed after retries ({last_error}); using deterministic fallback for: {label}")
        return result
