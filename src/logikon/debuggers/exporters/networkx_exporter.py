from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx
from unidecode import unidecode

from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.argument_mapping import AnnotationSpan, ArgMapEdge, ArgMapNode, InformalArgMap
from logikon.schemas.results import Artifact, DebugState


class NetworkXExporter(AbstractArtifactDebugger):
    """NetworkXExporter Debugger

    This debugger exports an informal argmap as a networkx graph.

    It requires the following artifacts:
    - informal_argmap
    """

    __pdescription__ = "Exports an informal argmap as a networkx graph"
    __product__ = "networkx_graph"
    __requirements__ = ["informal_argmap"]


    def to_nx(self, argument_map: InformalArgMap) -> nx.DiGraph:
        """builds nx graph from nodes-links argument map"""
        try:
            nodes = argument_map.model_dump()["nodelist"]  # type: ignore
            links = argument_map.model_dump()["edgelist"]  # type: ignore
        except AttributeError:
            nodes = argument_map.dict()["nodelist"]
            links = argument_map.dict()["edgelist"]

        data = {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": nodes,
            "links": links,
        }

        digraph = nx.node_link_graph(data)

        return digraph

    def _debug(self, debug_state: DebugState):
        """Reconstruct reasoning as argmap."""

        try:
            informal_argmap: InformalArgMap = next(
                InformalArgMap(**artifact.data)
                for artifact in debug_state.artifacts
                if artifact.id == "informal_argmap"
            )
        except StopIteration:
            msg = "Missing required artifact: informal_argmap"
            raise ValueError(msg)

        networkx_graph = self.to_nx(informal_argmap)

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=networkx_graph,
        )

        debug_state.artifacts.append(artifact)
