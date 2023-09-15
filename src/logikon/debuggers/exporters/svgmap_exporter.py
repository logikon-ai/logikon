
from __future__ import annotations
from typing import List, Optional, Dict, Tuple

import copy
import textwrap

import networkx as nx
import pydot
from unidecode import unidecode

from logikon.debuggers.base import AbstractDebugger
from logikon.schemas.results import DebugResults, Artifact



class SVGMapExporter(AbstractDebugger):
    """SVGMapExporter Debugger
    
    This debugger exports an a networkx graph as svg via graphviz.
    
    It requires the following artifacts:
    - networkx_graph
    """
    
    _KW_DESCRIPTION = "Exports an informal argmap as a networkx graph"
    _KW_PRODUCT = "svg_argmap"
    _KW_REQUIREMENTS = ["networkx_graph"]

    _NODE_TEMPLATE = """<
    <TABLE BORDER="0" COLOR="#444444" CELLPADDING="8" CELLSPACING="2"><TR><TD BORDER="0" BGCOLOR="{bgcolor}" STYLE="rounded" ALIGN="center"><FONT FACE="Arial;Helvetica;" POINT-SIZE="10.0"><B>[{label}]</B><br/>{text}</FONT></TD></TR></TABLE>
    >"""

    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT

    @classmethod
    def get_requirements(cls) -> List[str]:
        return cls._KW_REQUIREMENTS    


    def _preprocess_graph(self, digraph: nx.DiGraph) -> nx.DiGraph:
        """preprocess graph for graphviz layout"""
        digraph = copy.deepcopy(digraph)

        for _, nodedata in digraph.nodes.items():
            text = nodedata["text"]
            text = unidecode(text)
            label = nodedata["label"]
            label = unidecode(label)

            if ":" in text:
                text = text.replace(":"," --")
            if ":" in label:
                label = label.replace(":"," --")
            if "&" in text:
                text = text.replace("&","+")
            if "&" in label:
                label = label.replace("&","+")
                
            textlines = textwrap.wrap(text, width=30)
            text = "<BR/>".join(textlines)
            textlines = textwrap.wrap(label, width=25)
            label = "<BR/>".join(textlines)

            nodedata["label"] = self._NODE_TEMPLATE.format(
                text=text,
                label=label,
                bgcolor="lightblue",
            )
            nodedata.pop("text")
            nodedata["shape"] = "plaintext"
            nodedata["tooltip"] = text

        for _, linkdata in digraph.edges.items():
            linkdata["color"] = "red" if linkdata["valence"]=="con" else "darkgreen"
            linkdata["penwidth"] = "1.5"

        return digraph



    def _to_svg(self, digraph: nx.DiGraph) -> bytes:
        """builds svg from nx graph"""

        digraph = self._preprocess_graph(digraph)

        dot: pydot.Graph = nx.nx_pydot.to_pydot(digraph)
        dot.set("rankdir", "RL")
        dot.set("ratio", "compress")
        dot.set("size", "24")
        dot.set("orientation", "portrait")
        dot.set("overlay", "compress")
        svg = dot.create_svg(prog=["dot"])

        return svg


    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Reconstruct reasoning as argmap."""

        assert debug_results is not None

        try:
            networkx_graph: nx.DiGraph = next(
                artifact.data
                for artifact in debug_results.artifacts
                if artifact.id == "networkx_graph"
            )
        except StopIteration:
            raise ValueError("Missing required artifact: networkx_graph")

        svg_argmap = self._to_svg(networkx_graph)

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=svg_argmap,
        )

        debug_results.artifacts.append(artifact)
