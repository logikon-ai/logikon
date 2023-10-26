from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import copy
import textwrap
import uuid

import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import matplotlib.colors
import seaborn as sns
from unidecode import unidecode

import logikon
import logikon.schemas.argument_mapping as am
from logikon.analysts.base import AbstractArtifactAnalyst
from logikon.schemas.results import Artifact, AnalysisState

MAX_LABEL_LEN = 12
WITH_LEGEND = False


class HTMLSunburstExporter(AbstractArtifactAnalyst):
    """HTMLSunburstExporter Analyst

    This analyst exports an a networkx graph as html sunburst vial plotly express.

    It requires the following artifacts:
    - fuzzy_argmap_nx, OR
    - networkx_graph
    """

    __pdescription__ = "Exports a networkx graph as a HTML sunburst"
    __product__ = "html_sunburst"
    __requirements__ = [
        {"fuzzy_argmap_nx", "issue"},
        {"networkx_graph", "issue"},
    ]  # alternative requirements sets, first set takes precedence when automatically building pipeline

    def _trunc_to_tree(self, digraph: nx.DiGraph) -> nx.DiGraph:
        """truncate graph to maximal spanning tree (forest)"""

        digraph = copy.deepcopy(digraph)

        # Use am.IN_FOREST attribute to truncate graph
        if all(am.IN_FOREST in data for _, data in digraph.edges.items()):
            ebunch = [(u, v) for u, v, data in digraph.edges(data=True) if not data[am.IN_FOREST]]
            digraph.remove_edges_from(ebunch)
            return digraph
        
        # Use nx.maximum_branching to truncate graph
        mbr = nx.maximum_branching(digraph.reverse(copy=True), preserve_attrs=True)
        mbr = mbr.reverse(copy=True)


        # re-add attributes to nodes
        for node, data in digraph.nodes.items():
            if mbr.has_node(node):
                mbr.add_node(node, **data)

        return mbr


    def _to_tree_data(self, digraph: nx.DiGraph, issue: str) -> tuple[list[dict], dict, str]:
        """converts nx graph to tree data for sunburst"""

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
        n_roots = 0
        for node, nodedata in digraph.nodes.items():
            enum += 1
            number = f"#{enum}" if WITH_LEGEND else ""
            label = nodedata.get("label", "No label")
            text = nodedata.get("text", "No text")
            text = "<BR>".join(textwrap.wrap(text, width=30))
            legend_lines.append(f"{number}: {label}")

            if digraph.out_degree(node) == 0:
                parent = ""  # issue_id
                color = px.colors.sequential.Blues[(2*n_roots + 4) % len(px.colors.sequential.Blues)]
                #color = px.colors.qualitative.Pastel[n_roots % len(px.colors.qualitative.Pastel2)]
                n_roots += 1
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
                    number=number,
                    label=label,
                    text=text,
                    parent=parent,
                    value=value,
                )
            )
            color_map[node] = color

        legend = "<br>".join(legend_lines)

        return tree_data, color_map, legend

    def _to_html(self, tree_data: list[dict], color_map: dict, issue: str, legend: str) -> str:
        """builds html sunburst from tree data"""

        fig = px.sunburst(
            tree_data,
            ids='id',
            names='number',
            hover_name='label',
            hover_data={'text': True, 'value': False, 'parent': False, 'id': False, 'label': False, 'number': False},
            parents='parent',
            values='value',
            color='id',
            color_discrete_map=color_map,
            title=issue,
            width=800,
            height=640,
            # branchvalues="total",
        )
        fig.update_traces(marker_line_width=2)

        if WITH_LEGEND:
            fig.update_layout(
                annotations=[
                    go.layout.Annotation(
                        text=legend,
                        align='left',
                        valign='middle',
                        width=100,
                        height=640,
                        xref='paper',
                        yref='paper',
                        x=1.1,
                        y=0.5,
                        bgcolor='white',
                        bordercolor='black',
                        borderwidth=0,
                        showarrow=False,
                    )
                ]
            )

        html = fig.to_html(full_html=True, include_plotlyjs="cdn")

        return html

    def _analyze(self, analysis_state: AnalysisState):
        """Reconstruct reasoning as argmap."""

        issue = next(a.data for a in analysis_state.artifacts if a.id == "issue")

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

        networkx_graph = self._trunc_to_tree(networkx_graph)

        tree_data, color_map, legend = self._to_tree_data(networkx_graph, issue)

        html_sunburst = self._to_html(tree_data, color_map, issue, legend)

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=html_sunburst,
        )

        analysis_state.artifacts.append(artifact)
