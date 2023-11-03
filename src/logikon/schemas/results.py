from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Tuple

from pydantic import BaseModel


class _INPUT_KWS:
    prompt = "INPUT_KW_PROMPT"
    messages = "INPUT_KW_MESSAGES"
    completion = "INPUT_KW_COMPLETION"


INPUT_KWS = _INPUT_KWS()


class BaseCTModel(BaseModel):
    """Base model for all entities processed or created through logical analysis."""

    id: str
    description: str
    metadata: Optional[dict] = None


class Artifact(BaseCTModel):
    """An artifact serving as input and/or generated through logical analysis."""

    data: Any
    dtype: Optional[str] = None


class Score(BaseCTModel):
    """A score for a completion / reasoning trace."""

    value: Union[float, str]
    comment: Optional[str] = None


class AnalysisState(BaseModel):
    """Scores for the completion."""

    inputs: list[Artifact] = []
    artifacts: list[Artifact] = []
    scores: list[Score] = []

    def get_prompt_completion(self) -> Tuple[Optional[str], Optional[str]]:
        """convenience method that returns prompt and completion from inputs"""
        prompt = next((a.data for a in self.inputs if a.id == INPUT_KWS.prompt), None)
        completion = next((a.data for a in self.inputs if a.id == INPUT_KWS.completion), None)
        if prompt is not None and not isinstance(prompt, str):
            raise ValueError(f"Data type of input artifact prompt is {type(prompt)}, expected string.")
        if completion is not None and not isinstance(completion, str):
            raise ValueError(f"Data type of input artifact prompt is {type(completion)}, expected string.")
        return prompt, completion

