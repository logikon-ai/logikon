from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class BaseCTModel(BaseModel):
    """Base model for all entities processed or created through logical analysis."""

    id: str
    description: str
    metadata: Optional[dict] = None


class Artifact(BaseCTModel):
    """An artifact serving as input and/or generated through logical debugging."""

    data: Any
    dtype: Optional[str] = None


class Score(BaseCTModel):
    """A score for a completion / reasoning trace."""

    value: Union[float, str]
    comment: Optional[str] = None


class DebugResults(BaseModel):
    """Scores for the completion."""

    artifacts: list[Artifact] = []
    scores: list[Score] = []
