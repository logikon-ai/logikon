
from __future__ import annotations
from typing import List, Optional, Dict, Tuple, Union

from abc import abstractmethod

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

    @classmethod
    def get_requirements(cls) -> List[str]:
        return cls._KW_REQUIREMENTS    

    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        pass
    
    @abstractmethod
    def _calculate_score(self, digraph: nx.DiGraph) -> Tuple[Union[str, float], str, Optional[Dict]]:
        pass

    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Score the argmap."""

        assert debug_results is not None

        try:
            networkx_graph: nx.DiGraph = next(
                artifact.data
                for artifact in debug_results.artifacts
                if artifact.id == "networkx_graph"
            )
        except StopIteration:
            raise ValueError("Missing required artifact: networkx_graph")

        score, comment, metadata = self._calculate_score(networkx_graph)

        artifact = Score(
            id=self.get_product(),
            description=self.get_description(),
            score=score,
            comment=comment,
            metadata=metadata,
        )

        debug_results.artifacts.append(artifact)


class ArgMapGraphSizeScorer(AbstractGraphScorer):

    _KW_DESCRIPTION = "Measure the size of the argument map (number of nodes)"
    _KW_PRODUCT = "argmap_size"

    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT

    @classmethod
    def get_description(cls) -> List[str]:
        return cls._KW_DESCRIPTION    

    def _calculate_score(self, digraph: nx.DiGraph) -> Tuple[str | float, str, Dict | None]:
        return len(digraph.nodes), "", None
    

class ArgMapGraphAvgKatzCScorer(AbstractGraphScorer):

    _KW_DESCRIPTION = "Average Katz centrality of all nodes in the graph"
    _KW_PRODUCT = "argmap_avg_katz_centrality"

    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT

    @classmethod
    def get_description(cls) -> List[str]:
        return cls._KW_DESCRIPTION    

    def _calculate_score(self, digraph: nx.DiGraph) -> Tuple[str | float, str, Dict | None]:
        centrality = nx.katz_centrality(digraph)
        avg_centrality = np.mean(list(centrality.values()))

        return avg_centrality, "", None
    

class ArgMapGraphAttackRatioScorer(AbstractGraphScorer):

    _KW_DESCRIPTION = "Ratio of attacking reasons (cons) in the informal argmap"
    _KW_PRODUCT = "argmap_attack_ratio"

    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT

    @classmethod
    def get_description(cls) -> List[str]:
        return cls._KW_DESCRIPTION    

    def _calculate_score(self, digraph: nx.DiGraph) -> Tuple[str | float, str, Dict | None]:
        edge_data = digraph.edges.data("valence")
        attack_ratio = [val for _,_,val in edge_data].count("con") / len(edge_data)

        return attack_ratio, "", None
    
