from __future__ import annotations

import networkx as nx  # type: ignore
from pydantic import BaseModel

CENTRAL_CLAIM = "central_claim"
REASON = "reason"

ATTACK = "attack"
SUPPORT = "support"
NEUTRAL = "neutral"

IN_FOREST = "in_forest"  # name of edge attribute indicating that edge is in argument maps spanning tree (forest)


class AnnotationSpan(BaseModel):
    start: int
    end: int


class ArgMapNode(BaseModel):
    id: str
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


class FuzzyArgGraph(nx.DiGraph):
    """Wrapper for networkx DiGraph with fuzzy argument map data."""

    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)
        # check that every edge has valence attribute
        for _, data in self.edges.items():
            valence = data.get("valence")
            if valence not in [ATTACK, SUPPORT]:
                msg = f"Invalid edge valence: {valence}"
                raise ValueError(msg)
        # check that every node has node_type attribute
        for _, data in self.nodes.items():
            node_type = data.get("node_type")
            if node_type not in [CENTRAL_CLAIM, REASON]:
                msg = f"Invalid node type: {node_type}"
                raise ValueError(msg)

    def central_claims(self) -> list[str]:
        """Get list of central claims (node_ids)."""
        central_claims = [node for node, data in self.nodes.items() if data.get("node_type") == CENTRAL_CLAIM]
        return central_claims

    def supporting_reasons(self, node: str) -> list[str]:
        """Get list of supporting reasons for node."""
        supporting_reasons = [
            source
            for source, target, data in self.edges(data=True)
            if target == node and data.get("valence") == SUPPORT
        ]
        return supporting_reasons

    def attacking_reasons(self, node: str) -> list[str]:
        """Get list of attacking reasons for node."""
        attacking_reasons = [
            source for source, target, data in self.edges(data=True) if target == node and data.get("valence") == ATTACK
        ]
        return attacking_reasons
