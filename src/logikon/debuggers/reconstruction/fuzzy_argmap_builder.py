"""Module with debugger for reducing fuzzy nx graph to deterministic nx graph.

1. Find an optimal branching of the fuzzy nx graph
2. Determine minimum weight of attack / support edges in branching
3. Add all other attack / support edges with weight above respective minimum from fuzzy graph  to deterministic graph

"""

from __future__ import annotations

import copy
import uuid

import networkx as nx

from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.results import Artifact, DebugState
import logikon.schemas.argument_mapping as am


_FIX_WEIGHT_INTRA_ROOTS = 1.0  # weight of intra-root edges in relevance graphs
_DEFAULT_WEIGHT = 0  # default weight for edges in relevance graphs


class FuzzyArgMapBuilder(AbstractArtifactDebugger):
    """FuzzyArgMapBuilder

    This LMQLDebugger is responsible for reducing a quasi-complete relevance network to a fuzzy argument map (nx graph).

    """

    __product__ = "fuzzy_argmap_nx"
    __requirements__ = ["relevance_network_nx"]
    __pdescription__ = "Informal argument map (nx graph) with weighted support and attack relations"

    def _sanity_checks(self, relevance_network: nx.DiGraph):
        """basic sanity checks"""
        if not isinstance(relevance_network, nx.DiGraph):
            raise ValueError(f"Invalid relevance graph data. Expected nx.DiGraph, got {type(relevance_network)}.")
        for u, v, data in relevance_network.edges(data=True):
            if 'weight' not in data:
                self.logger.warning(f"Missing weight in edge {u} -> {v}. Using default value: {_DEFAULT_WEIGHT}.")
        for node, data in relevance_network.nodes.items():
            if 'nodeType' not in data:
                raise ValueError(f"Invalid relevance graph data. Missing nodeType in node {node}.")
        root_nodes = [node for node, data in relevance_network.nodes.items() if data['nodeType'] == am.CENTRAL_CLAIM]
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
        G = copy.deepcopy(relevance_network)

        root_nodes = [node for node, data in G.nodes.items() if data['nodeType'] == am.CENTRAL_CLAIM]

        if len(root_nodes) <= 1:
            return G

        # add pseudo super-root
        pseudo_root = f"super-root-{uuid.uuid4()}"
        G.add_node(pseudo_root, nodeType=am.CENTRAL_CLAIM, pseudo=True)

        # add pseudo edges
        for node in root_nodes:
            G.add_edge(node, pseudo_root, weight=_FIX_WEIGHT_INTRA_ROOTS, valence=am.SUPPORT, pseudo=True)

        # reverse edge direction (root_claims are technically sinks, not roots)
        G = G.reverse(copy=True)

        return G

    def _post_process_fuzzy_argmap(self, fuzzy_argmap: nx.DiGraph, relevance_network: nx.DiGraph) -> nx.DiGraph:
        """remove pseudo nodes and edges from fuzzy argmap, and undo edge reversal (inplace)

        Args:
            fuzzy_argmap (nx.DiGraph): _description_
        """
        G = fuzzy_argmap

        # add attributes to nodes
        for node, data in relevance_network.nodes.items():
            if G.has_node(node):
                G.add_node(node, **data)

        # remove pseudo entities
        pseudo_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get('pseudo', False)]
        for u, v in pseudo_edges:
            G.remove_edge(u, v)

        pseudo_nodes = [node for node, data in G.nodes.items() if data.get('pseudo', False)]
        if not pseudo_nodes:
            self.logger.warning("No pseudo nodes found while postprocessing fuzzy argmap.")
        for node in pseudo_nodes:
            G.remove_node(node)

        # reverse edges
        G = G.reverse(copy=True)

        return G

    def _add_above_min_edges(self, fuzzy_argmap: nx.DiGraph, relevance_network: nx.DiGraph):
        """add edges with weight above minimum from relevance network to fuzzy argmap (inplace)

        Args:
            fuzzy_argmap (nx.DiGraph): _description_
            relevance_network (nx.DiGraph): _description_
        """

        support_weights = [
            data['weight']
            for _, _, data in fuzzy_argmap.edges(data=True)
            if data['valence'] == am.SUPPORT and not data.get('pseudo', False)
        ]
        attack_weights = [
            data['weight']
            for _, _, data in fuzzy_argmap.edges(data=True)
            if data['valence'] == am.ATTACK and not data.get('pseudo', False)
        ]

        min_support_w = min(support_weights) if support_weights else None
        min_attack_w = min(attack_weights) if attack_weights else None

        if min_support_w is None and min_attack_w is None:
            return

        for u, v, data in relevance_network.edges(data=True):
            if data['valence'] == am.SUPPORT and min_support_w is not None and data['weight'] > min_support_w:
                fuzzy_argmap.add_edge(u, v, **data)
            elif data['valence'] == am.ATTACK and min_attack_w is not None and data['weight'] > min_attack_w:
                fuzzy_argmap.add_edge(u, v, **data)

    def _debug(self, debug_state: DebugState):
        """Build fuzzy argmap from pros and cons.

        Args:
            debug_state (DebugState): current debug_state to which new artifact is added

        Raises:
            ValueError: Failure to create Fuzzy argument map

        Proceeds as follows:

        1. Add intra-root pseudo edges
        2. Find an optimal branching of the fuzzy nx graph
        3. Remove pseudo edges from branching
        4. Determine minimum weight of attack / support edges in branching and add all other attack / support edges with weight above respective minimum

        """

        relevance_network = next((a.data for a in debug_state.artifacts if a.id == "relevance_network_nx"), None)
        if relevance_network is None:
            raise ValueError(
                "Missing required artifact: relevance_network. Available artifacts: " + str(debug_state.artifacts)
            )

        self._sanity_checks(relevance_network)

        relevance_network = self._preprocess_network(relevance_network)

        fuzzy_argmap = nx.maximum_branching(
            relevance_network, attr='weight', default=_DEFAULT_WEIGHT, preserve_attrs=True, partition=None
        )

        self._add_above_min_edges(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

        fuzzy_argmap = self._post_process_fuzzy_argmap(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

        if fuzzy_argmap is None:
            self.logger.warning("Failed to build fuzzy argument map (fuzzy_argmap is None).")

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=fuzzy_argmap,
        )

        debug_state.artifacts.append(artifact)
