from __future__ import annotations

from abc import abstractmethod
from typing import Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np

from logikon.debuggers.base import AbstractScoreDebugger
from logikon.schemas.results import DebugResults, Score


class AbstractGraphScorer(AbstractScoreDebugger):
    """AbstractGraphScorer Debugger

    Base class for graph scorers.

    Requires the following artifacts:
    - networkx_graph
    """

    _KW_REQUIREMENTS = ["networkx_graph"]

    @staticmethod
    def get_requirements() -> list[str]:
        return AbstractGraphScorer._KW_REQUIREMENTS

    @staticmethod
    @abstractmethod
    def get_description() -> str:
        pass

    @abstractmethod
    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[str | float, str, dict | None]:
        pass

    def _debug(self, prompt: str = "", completion: str = "", debug_results: DebugResults | None = None):
        """Score the argmap."""

        assert debug_results is not None

        try:
            networkx_graph: nx.DiGraph = next(
                artifact.data for artifact in debug_results.artifacts if artifact.id == "networkx_graph"
            )
        except StopIteration:
            msg = "Missing required artifact: networkx_graph"
            raise ValueError(msg)

        value, comment, metadata = self._calculate_score(networkx_graph)

        score = Score(
            id=self.get_product(),
            description=self.get_description(),
            score=value,
            comment=comment,
            metadata=metadata,
        )

        debug_results.scores.append(score)


class ArgMapGraphSizeScorer(AbstractGraphScorer):
    _KW_DESCRIPTION = "Measure the size of the argument map (number of nodes)"
    _KW_PRODUCT = "argmap_size"

    @staticmethod
    def get_product() -> str:
        return ArgMapGraphSizeScorer._KW_PRODUCT

    @staticmethod
    def get_description() -> str:
        return ArgMapGraphSizeScorer._KW_DESCRIPTION

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[str | float, str, dict | None]:
        return len(digraph.nodes), "", None


class ArgMapGraphAvgKatzCScorer(AbstractGraphScorer):
    _KW_DESCRIPTION = "Average Katz centrality of all nodes in the graph"
    _KW_PRODUCT = "argmap_avg_katz_centrality"

    @staticmethod
    def get_product() -> str:
        return ArgMapGraphAvgKatzCScorer._KW_PRODUCT

    @staticmethod
    def get_description() -> str:
        return ArgMapGraphAvgKatzCScorer._KW_DESCRIPTION

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[str | float, str, dict | None]:
        centrality = nx.katz_centrality(digraph)
        avg_centrality = np.mean(list(centrality.values()))

        return avg_centrality, "", None


class ArgMapGraphAttackRatioScorer(AbstractGraphScorer):
    _KW_DESCRIPTION = "Ratio of attacking reasons (cons) in the informal argmap"
    _KW_PRODUCT = "argmap_attack_ratio"

    @staticmethod
    def get_product() -> str:
        return ArgMapGraphAttackRatioScorer._KW_PRODUCT

    @staticmethod
    def get_description() -> str:
        return ArgMapGraphAttackRatioScorer._KW_DESCRIPTION

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[str | float, str, dict | None]:
        edge_data = digraph.edges.data("valence")
        attack_ratio = [val for _, _, val in edge_data].count("con") / len(edge_data)

        return attack_ratio, "", None
