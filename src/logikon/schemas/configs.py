from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DebugConfig(BaseModel):
    """Configuration for scoring."""

    expert_model: str = "text-ada-001"
    expert_model_kwargs: dict[str, Any] = {"temperature": 0.9}
    llm_framework: str = "OpenAI"
    generation_kwargs: dict | None = None
    metrics: list[str | Any] = []
    artifacts: list[str | Any] = ["informal_argmap"]
    report_to: list[str] = []
