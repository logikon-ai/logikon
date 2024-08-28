from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class _InputKws:
    prompt = "INPUT_KW_PROMPT"
    messages = "INPUT_KW_MESSAGES"
    completion = "INPUT_KW_COMPLETION"


INPUT_KWS = _InputKws()


class BaseCTModel(BaseModel):
    """Base model for all entities processed or created through logical analysis."""

    id: str
    description: str
    metadata: dict | None = None


class Artifact(BaseCTModel):
    """An artifact serving as input and/or generated through logical analysis."""

    data: Any
    dtype: str | None = None


class Score(BaseCTModel):
    """A score for a completion / reasoning trace."""

    value: float | str
    comment: str | None = None


class AnalysisState(BaseModel):
    """Scores for the completion."""

    inputs: list[Artifact] = []
    artifacts: list[Artifact] = []
    scores: list[Score] = []

    def get_prompt_completion(self) -> tuple[str | None, str | None]:
        """convenience method that returns prompt and completion from inputs"""
        prompt = next((a.data for a in self.inputs if a.id == INPUT_KWS.prompt), None)
        completion = next((a.data for a in self.inputs if a.id == INPUT_KWS.completion), None)
        if prompt is not None and not isinstance(prompt, str):
            msg = f"Data type of input artifact prompt is {type(prompt)}, expected string."
            raise ValueError(msg)
        if completion is not None and not isinstance(completion, str):
            msg = f"Data type of input artifact prompt is {type(completion)}, expected string."
            raise ValueError(msg)
        return prompt, completion
