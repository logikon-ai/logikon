
from __future__ import annotations
from typing import List, Optional, Dict, Tuple

import networkx as nx
from unidecode import unidecode

from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.results import DebugResults, Artifact
from logikon.schemas.argument_mapping import InformalArgMap, ArgMapNode, ArgMapEdge, AnnotationSpan



class NetworkXExporter(AbstractArtifactDebugger):
    """NetworkXExporter Debugger
    
    This debugger exports an informal argmap as a networkx graph.
    
    It requires the following artifacts:
    - informal_argmap
    """
    
    _KW_DESCRIPTION = "Exports an informal argmap as a networkx graph"
    _KW_PRODUCT = "networkx_graph"
    _KW_REQUIREMENTS = ["informal_argmap"]

    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT

    @classmethod
    def get_requirements(cls) -> List[str]:
        return cls._KW_REQUIREMENTS    

    def to_nx(self, argument_map: InformalArgMap) -> nx.DiGraph:
        """builds nx graph from nodes-links argument map"""
        data = {
            'directed': True,
            'multigraph': False,
            'graph': {},
            'nodes': argument_map.dict()["nodelist"],
            'links': argument_map.dict()["edgelist"],
        }

        digraph = nx.node_link_graph(data)

        return digraph



    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Reconstruct reasoning as argmap."""

        assert debug_results is not None

        try:
            informal_argmap: InformalArgMap = next(
                artifact.data
                for artifact in debug_results.artifacts
                if artifact.id == "informal_argmap"
            )
        except StopIteration:
            raise ValueError("Missing required artifact: informal_argmap")

        networkx_graph = self.to_nx(informal_argmap)

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=networkx_graph,
        )

        debug_results.artifacts.append(artifact)
