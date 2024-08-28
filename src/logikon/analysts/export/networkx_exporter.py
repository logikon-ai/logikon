from __future__ import annotations

from abc import abstractmethod
from typing import ClassVar

import networkx as nx

from logikon.analysts.base import AbstractArtifactAnalyst
from logikon.schemas.argument_mapping import FuzzyArgMap
from logikon.schemas.results import AnalysisState, Artifact


class AbstractNetworkXExporter(AbstractArtifactAnalyst):
    """AbstractNetworkXExporter Analyst

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
            msg = f"Invalid argument map. Missing nodelist or edgelist: {argmap_data}"
            raise ValueError(msg)
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

    async def _analyze(self, analysis_state: AnalysisState):
        """Reconstruct reasoning as argmap."""

        try:
            argmap_data = next(
                artifact.data for artifact in analysis_state.artifacts if artifact.id == self.get_requirements()[0]
            )
        except StopIteration as err:
            msg = "Missing required artifact: informal_argmap"
            raise ValueError(msg) from err

        try:
            self.__input_class__(**argmap_data)
        except Exception as err:
            msg = f"Invalid argument map. Cannot parse data {argmap_data} as {self.__input_class__}"
            raise ValueError(msg) from err

        networkx_graph = self._to_nx(argmap_data)

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=networkx_graph,
        )

        analysis_state.artifacts.append(artifact)


# class NetworkXExporter(AbstractNetworkXExporter):
#     """NetworkXExporter Analyst
#
#     This analyst exports an informal argmap as a networkx graph.
#
#     It requires the following artifacts:
#     - informal_argmap
#     """
#
#     __pdescription__ = "Informal argmap rendered as a networkx graph"
#     __product__ = "networkx_graph"
#     __requirements__ = ["informal_argmap"]
#
#     @property
#     def __input_class__(self) -> type:
#         return InformalArgMap


class RelevanceNetworkNXExporter(AbstractNetworkXExporter):
    """RelevanceNetworkNXExporter Analyst

    This analyst exports a relevance nets as a networkx graph.

    It requires the following artifacts:
    - relevance_network
    """

    __pdescription__ = "Relevance network rendered as a networkx graph"
    __product__ = "relevance_network_nx"
    __requirements__: ClassVar[list[str | set]] = ["relevance_network"]

    @property
    def __input_class__(self) -> type:
        return FuzzyArgMap
