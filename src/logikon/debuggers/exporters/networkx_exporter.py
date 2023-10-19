from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from abc import abstractmethod

import networkx as nx
from unidecode import unidecode

from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.argument_mapping import AnnotationSpan, ArgMapEdge, ArgMapNode, InformalArgMap
from logikon.schemas.results import Artifact, DebugState


class AbstractNetworkXExporter(AbstractArtifactDebugger):
    """AbstractNetworkXExporter Debugger

    Provides base functionality to handle different argument maps
    and to export them as a networkx graph.

    """

    @property
    @abstractmethod
    def __input_class__(self) -> type:
        """Returns the class of input data."""

    def _to_nx(self, argmap_data) -> nx.DiGraph:
        """builds nx graph from nodes-links argument map"""

        if "nodelist" not in argmap_data or "edgelist" not in argmap_data:
            raise ValueError(f"Invalid argument map. Missing nodelist or edgelist: {argmap_data}")
        nodes = argmap_data["nodelist"]  # type: ignore
        links = argmap_data["edgelist"]  # type: ignore

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
            argmap_data = next(
                artifact.data for artifact in debug_state.artifacts if artifact.id == self.get_requirements()[0]
            )
        except StopIteration:
            msg = "Missing required artifact: informal_argmap"
            raise ValueError(msg)

        try:
            self.__input_class__(**argmap_data)
        except:
            msg = f"Invalid argument map. Cannot parse data {argmap_data} as {self.__input_class__}"
            raise ValueError(msg)

        networkx_graph = self._to_nx(argmap_data)

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=networkx_graph,
        )

        debug_state.artifacts.append(artifact)


class NetworkXExporter(AbstractNetworkXExporter):
    """NetworkXExporter Debugger

    This debugger exports an informal argmap as a networkx graph.

    It requires the following artifacts:
    - informal_argmap
    """

    __pdescription__ = "Exports an informal argmap as a networkx graph"
    __product__ = "networkx_graph"
    __requirements__ = ["informal_argmap"]

    @property
    def __input_class__(self) -> type:
        return InformalArgMap
