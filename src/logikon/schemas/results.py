from __future__ import annotations

from typing import List, Optional, Union, Any, Dict

from pydantic import BaseModel


class Artifact(BaseModel):
    """An artifact generated through logical debugging."""
    name: str
    id: str
    data: Any
    metadata: Optional[Dict] = None


class Score(BaseModel):
    """A score for a completion."""
    name: str
    id: str
    score: Union[float, str]
    comment: Optional[str] = None
    metadata: Optional[Dict] = None


class DebugResults(BaseModel):
    """Scores for the completion."""
    artifacts: List[Artifact] = []
    scores: List[Score] = []
