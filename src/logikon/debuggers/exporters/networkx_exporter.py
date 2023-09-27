from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx
from unidecode import unidecode

from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.argument_mapping import AnnotationSpan, ArgMapEdge, ArgMapNode, InformalArgMap
from logikon.schemas.results import Artifact, DebugResults


class NetworkXExporter(AbstractArtifactDebugger):
    """NetworkXExporter Debugger

    This debugger exports an informal argmap as a networkx graph.

    It requires the following artifacts:
    - informal_argmap
    """

    _KW_DESCRIPTION = "Exports an informal argmap as a networkx graph"
    _KW_PRODUCT = "networkx_graph"
    _KW_REQUIREMENTS = ["informal_argmap"]

    @staticmethod
    def get_product() -> str:
        return NetworkXExporter._KW_PRODUCT

    @staticmethod
    def get_requirements() -> list[str]:
        return NetworkXExporter._KW_REQUIREMENTS

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

    def _debug(self, prompt: str, completion: str, debug_results: DebugResults):
        """Reconstruct reasoning as argmap."""

        try:
            informal_argmap: InformalArgMap = next(
                InformalArgMap(**artifact.data)
                for artifact in debug_results.artifacts
                if artifact.id == "informal_argmap"
            )
        except StopIteration:
            msg = "Missing required artifact: informal_argmap"
            raise ValueError(msg)

        networkx_graph = self.to_nx(informal_argmap)

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=networkx_graph,
        )

        debug_results.artifacts.append(artifact)
