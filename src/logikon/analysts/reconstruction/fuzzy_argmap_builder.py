"""Module with analyst for reducing fuzzy nx graph to deterministic nx graph.

The analyst proceeds as follows:

1. Add an intra-root pseudo edge
2. Find an optimal branching of the fuzzy nx graph
3. Remove pseudo edges from branching
4. Add all other attack / support edges with weight above threshold weight

"""

from __future__ import annotations

import copy
import uuid
from typing import Any, ClassVar

import networkx as nx
import numpy as np

import logikon.schemas.argument_mapping as am
from logikon.analysts.base import AbstractArtifactAnalyst
from logikon.schemas.results import AnalysisState, Artifact

_FIX_WEIGHT_INTRA_ROOTS = 1.0  # weight of intra-root edges in relevance graphs
_DEFAULT_WEIGHT = 0  # default weight for edges in relevance graphs
_MAX_OUT_DEGREE = 3  # maximum out degree of nodes in fuzzy argmap


class FuzzyArgMapBuilder(AbstractArtifactAnalyst):
    """FuzzyArgMapBuilder

    This LMQLAnalyst is responsible for reducing a quasi-complete relevance network to a fuzzy argument map (nx graph).

    """

    __product__ = "fuzzy_argmap_nx"
    __requirements__: ClassVar[list[str | set]] = ["relevance_network_nx"]
    __pdescription__ = "Informal argument map (nx graph) with weighted support and attack relations"

    def _sanity_checks(self, relevance_network: nx.DiGraph):
        """basic sanity checks"""
        if not isinstance(relevance_network, nx.DiGraph):
            msg = f"Invalid relevance graph data. Expected nx.DiGraph, got {type(relevance_network)}."
            raise ValueError(msg)
        for u, v, data in relevance_network.edges(data=True):
            if "weight" not in data:
                self.logger.warning(f"Missing weight in edge {u} -> {v}. Using default value: {_DEFAULT_WEIGHT}.")
        for node, data in relevance_network.nodes.items():
            if "node_type" not in data:
                msg = f"Invalid relevance graph data. Missing node_type in node {node}."
                raise ValueError(msg)
        root_nodes = [node for node, data in relevance_network.nodes.items() if data["node_type"] == am.CENTRAL_CLAIM]
        # check if there are any intra-root edges
        for node1 in root_nodes:
            for node2 in root_nodes:
                if node1 == node2:
                    continue
                if relevance_network.has_edge(node1, node2) or relevance_network.has_edge(node2, node1):
                    self.logger.warning(
                        f"Relevance network already contains intra-root edge {node1} -> {node2} or {node2} -> {node1}."
                    )

    def _preprocess_network(self, relevance_network: nx.DiGraph) -> nx.DiGraph:
        """preprocess relevance network,

        1. Add pseudo super-root
        2. Add pseudo edges from root nodes to super-root
        3. Reverse edge direction (root_claims are technically sinks, not roots)

        Args:
            relevance_network (nx.DiGraph): original relevance network

        Returns:
            nx.DiGraph: relevance network with added intra-root edges
        """
        G = copy.deepcopy(relevance_network)  # noqa: N806

        root_nodes = [node for node, data in G.nodes.items() if data["node_type"] == am.CENTRAL_CLAIM]

        # add pseudo super-root
        pseudo_root = f"super-root-{uuid.uuid4()}"
        G.add_node(pseudo_root, node_type=am.CENTRAL_CLAIM, pseudo=True)

        # add pseudo edges
        for node in root_nodes:
            G.add_edge(node, pseudo_root, weight=_FIX_WEIGHT_INTRA_ROOTS, valence=am.SUPPORT, pseudo=True)

        # reverse edge direction (root_claims are technically sinks, not roots)
        G = G.reverse(copy=True)  # noqa: N806

        return G

    def _post_process_fuzzy_argmap(self, fuzzy_argmap: nx.DiGraph, relevance_network: nx.DiGraph) -> nx.DiGraph:
        """remove pseudo nodes and edges from fuzzy argmap, and undo edge reversal (inplace)

        Args:
            fuzzy_argmap (nx.DiGraph): _description_
        """
        G = fuzzy_argmap  # noqa: N806

        # add attributes to nodes
        for node, data in relevance_network.nodes.items():
            if G.has_node(node):
                G.add_node(node, **data)

        # remove pseudo entities
        pseudo_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get("pseudo", False)]
        for u, v in pseudo_edges:
            G.remove_edge(u, v)

        pseudo_nodes = [node for node, data in G.nodes.items() if data.get("pseudo", False)]
        if not pseudo_nodes:
            self.logger.warning("No pseudo nodes found while postprocessing fuzzy argmap.")
        for node in pseudo_nodes:
            G.remove_node(node)

        # reverse edges
        G = G.reverse(copy=True)  # noqa: N806

        return G

    def _add_above_threshold_edges(
        self, fuzzy_argmap: nx.DiGraph, relevance_network: nx.DiGraph
    ) -> list[tuple[Any, Any]]:
        """add edges with weight above threshold from relevance network to fuzzy argmap (inplace)

        Args:
            fuzzy_argmap (nx.DiGraph): _description_
            relevance_network (nx.DiGraph): _description_

        Returns:
            adges_added (list[str]): list of edges that were added to fuzzy argmap
        """

        is_forest = nx.is_forest(fuzzy_argmap.reverse())
        if is_forest:
            nx.set_edge_attributes(fuzzy_argmap, True, am.IN_FOREST)
        else:
            self.logger.warning("Fuzzy argmap is not a branching. Cannot set attribute 'in_branching' for edges.")

        support_weights = [
            data["weight"]
            for _, _, data in fuzzy_argmap.edges(data=True)
            if data["valence"] == am.SUPPORT and not data.get("pseudo", False)
        ]
        attack_weights = [
            data["weight"]
            for _, _, data in fuzzy_argmap.edges(data=True)
            if data["valence"] == am.ATTACK and not data.get("pseudo", False)
        ]

        thrsh_support_w = np.median(support_weights) if support_weights else None
        thrsh_attack_w = np.median(attack_weights) if attack_weights else None

        self.logger.debug(f"Minimum support weight: {thrsh_support_w}")
        self.logger.debug(f"Minimum attack weight: {thrsh_attack_w}")

        if thrsh_support_w is None and thrsh_attack_w is None:
            return []

        edges_added = []

        # TODO: if there are more than _MAX_OUT_DEGREE outgoing edges from a node,
        # we should only add the _MAX_OUT_DEGREE edges with the highest weights
        for u, v, edgedata in relevance_network.edges(data=True):
            if fuzzy_argmap.has_edge(u, v) or fuzzy_argmap.has_edge(v, u):
                continue
            # check out-degree
            if fuzzy_argmap.out_degree(u) >= _MAX_OUT_DEGREE:
                continue
            data = {**edgedata, am.IN_FOREST: False} if is_forest else edgedata
            if data["valence"] == am.SUPPORT and thrsh_support_w is not None and data["weight"] > thrsh_support_w:
                fuzzy_argmap.add_edge(u, v, **data)
            elif data["valence"] == am.ATTACK and thrsh_attack_w is not None and data["weight"] > thrsh_attack_w:
                fuzzy_argmap.add_edge(u, v, **data)
            edges_added.append((u, v))

        self.logger.debug(f"Added {len(edges_added)} edges to fuzzy argmap.")

        return edges_added

    def _analyze(self, analysis_state: AnalysisState):
        """Build fuzzy argmap from pros and cons.

        Args:
            analysis_state (AnalysisState): current analysis_state to which new artifact is added

        Raises:
            ValueError: Failure to create Fuzzy argument map

        Proceeds as follows:

        1. Add intra-root pseudo edge
        2. Find an optimal branching of the fuzzy nx graph
        3. Remove pseudo edges from branching
        4. Add all other attack / support edges with weight above threshold weight

        """

        relevance_network = next((a.data for a in analysis_state.artifacts if a.id == "relevance_network_nx"), None)
        if relevance_network is None:
            raise ValueError(
                "Missing required artifact: relevance_network. Available artifacts: " + str(analysis_state.artifacts)
            )

        self._sanity_checks(relevance_network)

        relevance_network = self._preprocess_network(relevance_network)

        fuzzy_argmap = nx.maximum_branching(
            relevance_network, attr="weight", default=_DEFAULT_WEIGHT, preserve_attrs=True, partition=None
        )

        edges_added = self._add_above_threshold_edges(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

        fuzzy_argmap = self._post_process_fuzzy_argmap(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

        if fuzzy_argmap is None:
            self.logger.warning("Failed to build fuzzy argument map (fuzzy_argmap is None).")

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=fuzzy_argmap,
            metadata={"edges_added": edges_added},
        )

        analysis_state.artifacts.append(artifact)
