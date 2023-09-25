from __future__ import annotations

from typing import Any, Optional, Union, Type

from pydantic import BaseModel

from logikon.schemas.results import Artifact, Score
from logikon.debuggers.interface import Debugger


class DebugConfig(BaseModel):
    """Configuration for scoring."""

    expert_model: str = "text-ada-001"
    expert_model_kwargs: dict[str, Any] = {"temperature": 0.7}
    llm_framework: str = "OpenAI"
    generation_kwargs: Optional[dict] = None
    inputs: list[Union[Artifact, Score]] = []
    metrics: list[Union[str, Type[Debugger]]] = []
    artifacts: list[Union[str, Type[Debugger]]] = ["informal_argmap"]
    report_to: list[str] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._check_unique_ids()

    def _check_unique_ids(self):
        """Check if all inputs, metrics and artifacts have unique ids."""
        ids = [inpt.id for inpt in self.inputs]
        if len(set(ids)) != len(ids):
            raise ValueError("Inconsistent configuration. All inputs must have unique ids.")
        ids = [metric if isinstance(metric, str) else metric.get_product() for metric in self.metrics]
        if len(set(ids)) != len(ids):
            raise ValueError("Inconsistent configuration. All metrics must have unique ids.")
        ids = [artifact if isinstance(artifact, str) else artifact.get_product() for artifact in self.artifacts]
        if len(set(ids)) != len(ids):
            raise ValueError("Inconsistent configuration. All artifacts must have unique ids.")
