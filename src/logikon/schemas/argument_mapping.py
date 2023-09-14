from __future__ import annotations

from typing import List

from pydantic import BaseModel


class AnnotationSpan(BaseModel):
    start: int
    end: int

class ArgMapNode(BaseModel):
    id: str
    text: str
    label: str
    annotations: List[AnnotationSpan] = []
    nodeType: str ="proposition"

class ArgMapEdge(BaseModel):
    source: str
    target: str
    valence: str

class InformalArgMap(BaseModel):
    nodelist: List[ArgMapNode] = []
    edgelist: List[ArgMapEdge] = []
