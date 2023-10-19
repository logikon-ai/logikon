from __future__ import annotations

from abc import abstractmethod
from typing import Optional, Union

import networkx as nx
import numpy as np

from logikon.debuggers.base import AbstractScoreDebugger
from logikon.schemas.results import DebugState, Score


class AbstractGraphScorer(AbstractScoreDebugger):
    """AbstractGraphScorer Debugger

    Base class for graph scorers.

    Requires the following artifacts:
    - networkx_graph
    """

    __requirements__ = ["networkx_graph"]


    @abstractmethod
    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[Union[str, float], str, Optional[dict]]:
        pass

    def _debug(self, debug_state: DebugState):
        """Score the argmap."""

        try:
            networkx_graph: nx.DiGraph = next(
                artifact.data for artifact in debug_state.artifacts if artifact.id == "networkx_graph"
            )
        except StopIteration:
            msg = "Missing required artifact: networkx_graph"
            raise ValueError(msg)

        value, comment, metadata = self._calculate_score(networkx_graph)

        score = Score(
            id=self.get_product(),
            description=self.get_description(),
            value=value,
            comment=comment,
            metadata=metadata,
        )

        debug_state.scores.append(score)


class ArgMapGraphSizeScorer(AbstractGraphScorer):

    __pdescription__ = "Measure the size of the argument map (number of nodes)"
    __product__ = "argmap_size"


    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[Union[str, float], str, Optional[dict]]:
        return len(digraph.nodes), "", None


class ArgMapGraphAvgKatzCScorer(AbstractGraphScorer):

    __pdescription__ = "Average Katz centrality of all nodes in the graph"
    __product__ = "argmap_avg_katz_centrality"


    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[Union[str, float], str, Optional[dict]]:
        centrality = nx.katz_centrality(digraph)
        avg_centrality = np.mean(list(centrality.values()))

        return avg_centrality, "", None


class ArgMapGraphAttackRatioScorer(AbstractGraphScorer):

    __pdescription__ = "Ratio of attacking reasons (cons) in the informal argmap"
    __product__ = "argmap_attack_ratio"


    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[Union[str, float], str, Optional[dict]]:
        edge_data = digraph.edges.data("valence")
        if edge_data:
            attack_ratio = [val for _, _, val in edge_data].count("con") / len(edge_data)
        else:
            attack_ratio = 0

        return attack_ratio, "", None
