from __future__ import annotations

from abc import abstractmethod
from typing import Optional, Union

import networkx as nx
import numpy as np

import logikon.schemas.argument_mapping as am
from logikon.analysts.base import AbstractScoreAnalyst
from logikon.schemas.results import AnalysisState, Score


class AbstractGraphScorer(AbstractScoreAnalyst):
    """AbstractGraphScorer Analyst

    Base class for graph scorers.

    Requires the following artifacts:
    - networkx_graph
    """

    __requirements__ = [
        {"fuzzy_argmap_nx"},
        {"networkx_graph"},
    ]  # alternative requirements sets, first set takes precedence when automatically building pipeline

    @abstractmethod
    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[Union[str, float], str, Optional[dict]]:
        pass

    def _analyze(self, analysis_state: AnalysisState):
        """Score the argmap."""

        networkx_graph: Optional[nx.DiGraph] = next(
            (artifact.data for artifact in analysis_state.artifacts if artifact.id == "fuzzy_argmap_nx"), None
        )
        if networkx_graph is None:
            networkx_graph = next(
                (artifact.data for artifact in analysis_state.artifacts if artifact.id == "networkx_graph"), None
            )

        if networkx_graph is None:
            msg = f"Missing any of the required artifacts: {self.get_requirements()}"
            raise ValueError(msg)

        value, comment, metadata = self._calculate_score(networkx_graph)

        score = Score(
            id=self.get_product(),
            description=self.get_description(),
            value=value,
            comment=comment,
            metadata=metadata,
        )

        analysis_state.scores.append(score)


class ArgMapGraphSizeScorer(AbstractGraphScorer):
    __pdescription__ = "Measure the size of the argument map (number of nodes)"
    __product__ = "argmap_size"

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[Union[str, float], str, Optional[dict]]:
        return len(digraph.nodes), "", None


class ArgMapRootCountScorer(AbstractGraphScorer):
    __pdescription__ = "Cont the number of root nodes in argument map (out degree = 0)"
    __product__ = "n_root_nodes"

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[Union[str, float], str, Optional[dict]]:
        root_nodes = [n for n, d in digraph.out_degree() if d == 0]
        return len(root_nodes), "", None


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
            attack_ratio = [val for _, _, val in edge_data].count(am.ATTACK) / len(edge_data)
        else:
            attack_ratio = 0

        return attack_ratio, "", None


class MeanReasonStrengthScorer(AbstractGraphScorer):
    __pdescription__ = "Mean strength (absolute weight) of support and attack reasons (cons) in the fuzzy argmap"
    __product__ = "mean_reason_strength"

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[Union[str, float], str, Optional[dict]]:
        edge_data = digraph.edges.data("weight", 1)
        if edge_data:
            mean_weight = np.mean([w for _, _, w in edge_data])
        else:
            mean_weight = 0

        return mean_weight, "", None
