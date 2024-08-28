from __future__ import annotations

import copy
import textwrap
from typing import ClassVar

import graphviz
import matplotlib.colors
import networkx as nx
import seaborn as sns
from unidecode import unidecode

import logikon
import logikon.schemas.argument_mapping as am
from logikon.analysts.base import AbstractArtifactAnalyst
from logikon.schemas.results import AnalysisState, Artifact

_ARROWWIDTH = "2"


class SVGMapExporter(AbstractArtifactAnalyst):
    """SVGMapExporter Analyst

    This analyst exports an a networkx graph as svg via graphviz.

    It requires the following artifacts:
    - fuzzy_argmap_nx, OR
    - networkx_graph
    """

    __pdescription__ = "Exports a networkx graph as a graphviz argument map (svg)"
    __product__ = "svg_argmap"
    __requirements__: ClassVar[list[str | set]] = [
        {"fuzzy_argmap_nx"},
        {"networkx_graph"},
    ]  # alternative requirements sets, first set takes precedence when automatically building pipeline

    _NODE_TEMPLATE = """<
    <TABLE BORDER="4" COLOR="{bgcolor}" CELLPADDING="2" CELLSPACING="2" BGCOLOR="{bgcolor}" STYLE="rounded" ALIGN="center">
    <TR><TD BORDER="0"><FONT FACE="Arial, Helvetica, sans-serif" POINT-SIZE="12.0"><B>{label}</B></FONT></TD></TR>
    <TR><TD BORDER="0"><FONT FACE="Arial, Helvetica, sans-serif" POINT-SIZE="12.0">{text}</FONT></TD></TR>
    </TABLE>
    >"""  # noqa: E501
    _CLAIM_NODE_TEMPLATE = """<
    <TABLE BORDER="4" COLOR="{bgcolor}" CELLPADDING="2" CELLSPACING="2" BGCOLOR="white" STYLE="rounded" ALIGN="center">
    <TR><TD BORDER="0"><FONT FACE="Arial, Helvetica, sans-serif" POINT-SIZE="12.0"><B>{label}</B></FONT></TD></TR>
    <TR><TD BORDER="0"><FONT FACE="Arial, Helvetica, sans-serif" POINT-SIZE="12.0">{text}</FONT></TD></TR>
    </TABLE>
    >"""

    def __init__(self, config):
        super().__init__(config)
        # check if graphviz is available
        try:
            import subprocess

            subprocess.run("command -v dot", shell=True, check=True)  # noqa: S607, S602
        except Exception as err:
            self.logger.error("Graphviz command dot not found.")
            msg = (
                "Graphviz dot command not found. To create SVG argument map, "
                "install graphviz on this system. Or remove `svg_argmap` from "
                "the analyst pipeline."
            )
            raise ValueError(msg) from err

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

            if nodedata.get("node_type") == am.CENTRAL_CLAIM:
                template = self._CLAIM_NODE_TEMPLATE
            else:
                template = self._NODE_TEMPLATE

            nodedata["label"] = template.format(
                text=text if text else "NO TEXT",
                label=label if label else "NO LABEL",
                bgcolor="lightblue",
            )
            nodedata.pop("text")
            nodedata.pop("annotations")
            nodedata["shape"] = "plaintext"
            nodedata["tooltip"] = text

        for _, linkdata in digraph.edges.items():
            if "weight" in linkdata:
                cmap = (
                    sns.color_palette("blend:darkgrey,red", as_cmap=True)
                    if linkdata["valence"] == am.ATTACK
                    else sns.color_palette("blend:darkgrey,darkgreen", as_cmap=True)
                )
                color = cmap(linkdata.pop("weight"))  # dropping weight from edge data
                linkdata["color"] = matplotlib.colors.to_hex(color)
            else:
                linkdata["color"] = "red" if linkdata["valence"] == am.ATTACK else "darkgreen"

            if am.IN_FOREST in linkdata:
                del linkdata[am.IN_FOREST]

            linkdata["penwidth"] = _ARROWWIDTH

        return digraph

    def _to_svg(self, digraph: nx.DiGraph) -> str:
        """builds svg from nx graph"""

        digraph = self._preprocess_graph(digraph)

        dot = graphviz.Digraph(
            "logikon informal argument map",
            comment=f"Created with `logikon` python module version {logikon.__version__}",
            graph_attr={
                "format": "svg",
                "rankdir": "BT",
                "ratio": "compress",
                "orientation": "portrait",
                # overlap="compress",
            },
        )
        # subgraph with central claims on same rank
        with dot.subgraph(name="central_claims", graph_attr={"rank": "sink"}) as subgraph:
            for node, nodedata in digraph.nodes.items():
                if nodedata.get("node_type") == am.CENTRAL_CLAIM:
                    subgraph.node(str(node), **nodedata)

        for node, nodedata in digraph.nodes.items():
            if nodedata.get("node_type") != am.CENTRAL_CLAIM:
                dot.node(str(node), **nodedata)

        for edge, edgedata in digraph.edges.items():
            dot.edge(str(edge[0]), str(edge[-1]), **edgedata)

        dot.format = "svg"
        svg = dot.pipe(encoding="utf-8")

        return svg

    async def _analyze(self, analysis_state: AnalysisState):
        """Reconstruct reasoning as argmap."""

        networkx_graph: nx.DiGraph | None = next(
            (artifact.data for artifact in analysis_state.artifacts if artifact.id == "fuzzy_argmap_nx"), None
        )
        if networkx_graph is None:
            networkx_graph = next(
                (artifact.data for artifact in analysis_state.artifacts if artifact.id == "networkx_graph"), None
            )

        if networkx_graph is None:
            msg = f"Missing any of the required artifacts: {self.get_requirements()}"
            raise ValueError(msg)

        svg_argmap = self._to_svg(networkx_graph)

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=svg_argmap,
        )

        analysis_state.artifacts.append(artifact)
