from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import copy
import uuid

import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import matplotlib.colors
import seaborn as sns
from unidecode import unidecode

import logikon
import logikon.schemas.argument_mapping as am
from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.results import Artifact, DebugState

MAX_LABEL_LEN = 12


class SVGSunburstExporter(AbstractArtifactDebugger):
    """SVGSunburstExporter Debugger

    This debugger exports an a networkx graph as svg sunburst vial plotly express.

    It requires the following artifacts:
    - fuzzy_argmap_nx, OR
    - networkx_graph
    """

    __pdescription__ = "Exports a networkx graph as a SVG sunburst"
    __product__ = "svg_sunburst"
    __requirements__ = [
        {"fuzzy_argmap_nx", "issue"},
        {"networkx_graph", "issue"},
    ]  # alternative requirements sets, first set takes precedence when automatically building pipeline

    def _to_tree_data(self, digraph: nx.DiGraph, issue: str) -> tuple[list[dict], dict]:
        """builds svg sunburst from nx graph"""

        tree_data = []
        color_map = {}
        legend_lines: List[str] = []

        # issue_id = str(uuid.uuid4())
        # tree_data.append(dict(
        #     id=issue_id,
        #     name=issue,
        #     parent="",
        #     value=1,
        # ))
        # color_map[issue_id] = "white"

        enum = 0
        for node, nodedata in digraph.nodes.items():
            enum += 1
            name = f"#{enum}"
            label = nodedata.get("label", "No label")
            legend_lines.append(f"{name}: {label}")

            if digraph.out_degree(node) == 0:
                parent = ""  # issue_id
                color = "goldenrod"
            else:
                # get parent with highest link weight
                neighbors = [(n, digraph[node][n].get("weight", 1)) for n in digraph[node]]
                parent, weight = max(neighbors, key=lambda x: x[1])
                valence = digraph[node][parent].get("valence")
                cmap = (
                    sns.color_palette("blend:darkgrey,red", as_cmap=True)
                    if valence == am.ATTACK
                    else sns.color_palette("blend:darkgrey,darkgreen", as_cmap=True)
                )
                color = cmap(0.2 + weight)
                color = matplotlib.colors.to_hex(color)

            if digraph.in_degree(node) == 0:
                value = 1
            else:
                value = 0

            tree_data.append(
                dict(
                    id=node,
                    name=name,
                    parent=parent,
                    value=value,
                )
            )
            color_map[node] = color

        legend = "<br>".join(legend_lines)

        return tree_data, color_map, legend

    def _to_svg(self, tree_data: list[dict], color_map: dict, issue: str, legend: str) -> str:
        """builds svg sunburst from tree data"""

        fig = px.sunburst(
            tree_data,
            ids='id',
            names='name',
            parents='parent',
            values='value',
            color='id',
            color_discrete_map=color_map,
            title=issue,
            # branchvalues="total",
        )
        fig.update_traces(marker_line_width=2)
        fig.update_layout(
            annotations=[
                go.layout.Annotation(
                    text=legend,
                    align='left',
                    showarrow=False,
                    xref='paper',
                    yref='paper',
                    x=1.1,
                    y=0.2,
                    bgcolor='white',
                    bordercolor='black',
                    borderwidth=0,
                )
            ]
        )

        svg = fig.to_image(format="svg").decode("utf-8")

        return svg

    def _debug(self, debug_state: DebugState):
        """Reconstruct reasoning as argmap."""

        issue = next(a.data for a in debug_state.artifacts if a.id == "issue")

        networkx_graph: Optional[nx.DiGraph] = next(
            (artifact.data for artifact in debug_state.artifacts if artifact.id == "fuzzy_argmap_nx"), None
        )
        if networkx_graph is None:
            networkx_graph = next(
                (artifact.data for artifact in debug_state.artifacts if artifact.id == "networkx_graph"), None
            )

        if networkx_graph is None:
            msg = f"Missing any of the required artifacts: {self.get_requirements()}"
            raise ValueError(msg)

        tree_data, color_map, legend = self._to_tree_data(networkx_graph, issue)

        svg_sunburst = self._to_svg(tree_data, color_map, issue, legend)

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=svg_sunburst,
        )

        debug_state.artifacts.append(artifact)
