from __future__ import annotations

from typing import List

from pydantic import BaseModel

CENTRAL_CLAIM = "central_claim"
REASON = "reason"

ATTACK = "attack"
SUPPORT = "support"

class AnnotationSpan(BaseModel):
    start: int
    end: int


class ArgMapNode(BaseModel):
    id: str
    text: str
    label: str
    annotations: list[AnnotationSpan] = []
    nodeType: str = REASON


class ArgMapEdge(BaseModel):
    source: str
    target: str
    valence: str


class InformalArgMap(BaseModel):
    nodelist: list[ArgMapNode] = []
    edgelist: list[ArgMapEdge] = []


class FuzzyArgMapEdge(ArgMapEdge):
    weight: float


class FuzzyArgMap(BaseModel):
    nodelist: list[ArgMapNode] = []
    edgelist: list[FuzzyArgMapEdge] = []
