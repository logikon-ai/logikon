from __future__ import annotations

from pydantic import BaseModel

CENTRAL_CLAIM = "central_claim"
REASON = "reason"

ATTACK = "attack"
SUPPORT = "support"

IN_FOREST = "in_forest"  # name of edge attribute indicating that edge is in argument maps spanning tree (forest)


class AnnotationSpan(BaseModel):
    start: int
    end: int


class ArgMapNode(BaseModel):
    id: str  # noqa: A003
    text: str
    label: str
    annotations: list[AnnotationSpan] = []
    node_type: str = REASON


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

    def get_node(self, node_id: str) -> ArgMapNode:
        """Get node by node id."""
        for node in self.nodelist:
            if node.id == node_id:
                return node
        msg = f"Node with id {node_id} not found."
        raise ValueError(msg)

    def get_node_type(self, node_id: str) -> str:
        """Get node type by node id."""
        node = self.get_node(node_id)
        return node.node_type
