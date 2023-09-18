from __future__ import annotations

from typing import Any, Optional, Union

from pydantic import BaseModel


class DebugConfig(BaseModel):
    """Configuration for scoring."""

    expert_model: str = "text-ada-001"
    expert_model_kwargs: dict[str, Any] = {"temperature": 0.9}
    llm_framework: str = "OpenAI"
    generation_kwargs: Optional[dict] = None
    metrics: list[Union[str, Any]] = []
    artifacts: list[Union[str, Any]] = ["informal_argmap"]
    report_to: list[str] = []
