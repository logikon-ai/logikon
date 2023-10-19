from __future__ import annotations

import copy
import textwrap
from typing import Dict, List, Optional, Tuple

import graphviz
import networkx as nx
from unidecode import unidecode

import logikon
from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import Artifact, DebugState


class SVGMapExporter(AbstractArtifactDebugger):
    """SVGMapExporter Debugger

    This debugger exports an a networkx graph as svg via graphviz.

    It requires the following artifacts:
    - networkx_graph
    """

    __pdescription__ = "Exports an informal argmap as a networkx graph"
    __product__ = "svg_argmap"
    __requirements__ = ["networkx_graph"]

    _NODE_TEMPLATE = """<
    <TABLE BORDER="0" COLOR="#444444" CELLPADDING="8" CELLSPACING="2"><TR><TD BORDER="0" BGCOLOR="{bgcolor}" STYLE="rounded" ALIGN="center"><FONT FACE="Arial, Helvetica, sans-serif" POINT-SIZE="12.0"><B>[{label}]</B><br/>{text}</FONT></TD></TR></TABLE>
    >"""

    def __init__(self, debug_config: DebugConfig):
        super().__init__(debug_config)
        # check if graphviz is available
        try:
            import subprocess

            subprocess.run(["dot", "-V"])
        except:
            self.logger.error("Graphviz command dot not found.")
            raise ValueError(
                "Graphviz dot command not found. To create SVG argument map, install graphviz on this system."
            )


    def _preprocess_string(self, value: str) -> str:
        new_value = unidecode(value)
        if ":" in new_value:
            new_value = new_value.replace(":", " --")
        if "&" in new_value:
            new_value = new_value.replace("&", "+")
        return new_value

    def _preprocess_graph(self, digraph: nx.DiGraph) -> nx.DiGraph:
        """preprocess graph for graphviz layout"""
        digraph = copy.deepcopy(digraph)

        for _, nodedata in digraph.nodes.items():
            for key, value in nodedata.items():
                if isinstance(value, str):
                    nodedata[key] = self._preprocess_string(value)

            textlines = textwrap.wrap(nodedata["text"], width=30)
            text = "<BR/>".join(textlines)
            textlines = textwrap.wrap(nodedata["label"], width=25)
            label = "<BR/>".join(textlines)

            nodedata["label"] = self._NODE_TEMPLATE.format(
                text=text,
                label=label,
                bgcolor="lightblue",
            )
            nodedata.pop("text")
            nodedata.pop("annotations")
            nodedata["shape"] = "plaintext"
            nodedata["tooltip"] = text

        for _, linkdata in digraph.edges.items():
            linkdata["color"] = "red" if linkdata["valence"] == "con" else "darkgreen"
            linkdata["penwidth"] = "1.5"

        return digraph

    def _to_svg(self, digraph: nx.DiGraph) -> str:
        """builds svg from nx graph"""

        digraph = self._preprocess_graph(digraph)

        dot = graphviz.Digraph(
            'logikon informal argument map',
            comment=f'Created with `logikon` python module version {logikon.__version__}',
            graph_attr=dict(
                format="svg",
                rankdir="RL",
                ratio="compress",
                orientation="portrait",
                overlap="compress",
            ),
        )

        for node, nodedata in digraph.nodes.items():
            dot.node(str(node), **nodedata)

        for edge, edgedata in digraph.edges.items():
            dot.edge(str(edge[0]), str(edge[-1]), **edgedata)

        # dot: pydot.Graph = nx.nx_pydot.to_pydot(digraph)
        # dot.set("rankdir", "RL")
        # dot.set("ratio", "compress")
        # # dot.set("size", "24")
        # dot.set("orientation", "portrait")
        # dot.set("overlap", "compress")

        # gv = graphviz.Source(str(dot))

        dot.format = "svg"
        svg = dot.pipe(encoding="utf-8")
        # svg = dot.create_svg(prog=["dot"])

        return svg

    def _debug(self, debug_state: DebugState):
        """Reconstruct reasoning as argmap."""

        try:
            networkx_graph: nx.DiGraph = next(
                artifact.data for artifact in debug_state.artifacts if artifact.id == "networkx_graph"
            )
        except StopIteration:
            msg = "Missing required artifact: networkx_graph"
            raise ValueError(msg)

        svg_argmap = self._to_svg(networkx_graph)

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=svg_argmap,
        )

        debug_state.artifacts.append(artifact)
