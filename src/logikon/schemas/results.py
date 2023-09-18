from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class Artifact(BaseModel):
    """An artifact generated through logical debugging."""

    id: str
    description: str
    data: Any
    dtype: Optional[str] = None
    metadata: Optional[dict] = None


class Score(BaseModel):
    """A score for a completion."""

    id: str
    description: str
    score: Union[float, str]
    comment: Optional[str] = None
    metadata: Optional[dict] = None


class DebugResults(BaseModel):
    """Scores for the completion."""

    artifacts: list[Artifact] = []
    scores: list[Score] = []
