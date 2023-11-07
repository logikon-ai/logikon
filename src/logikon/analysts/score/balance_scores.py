"""Provides analysts for computing balance scores.

Balance scores are computed from a (fuzzy) argmap nx graph.

## Motivation

The balance scores defined and computed here generalize the primitive notion of
a balanced pros and cons list to fuzzy argmaps, i.e., weighted directed bipolar
argumentation networks with multiple root claims.


## Basic Concepts

A fuzzy argument map is a *weighted* DAG $G=<N,E,W>$.
Negative weights represent attack relations, positive weights support relations.

A "root node" is any node with out-degree 0. (In graph-theory, these "root nodes"
are sinks.) The set of root nodes is denoted $N^r$, and the set non-root nodes is
referred to as $N^*$:=$N \setminus N^r$.

The set of all paths from node n1 to node n2 is denoted by $P_{n1,n2}_$.

## Marginal root support of a single argument node

Let $t$ be a root and $n$ be a non-root node in $G$. The *marginal root support* of
$n$ wrt. $t$ is the average weight of all paths from $t$ to $n$:

MRS(n,t) := $\frac{1}{|P_{n,t}|} \sum_{p \in P_{n,t}} \product_{e \in p} w(e)$

where $w(e)$ is the weight of edge $e$, if $|P_{n,t}|$>0. If $|P_{n,t}|$=0, then

MRS(n,t) := 0.

Informally, MRS(n,t) measures the valence and weight of n in a simple pros cons list
with root claim t.

## Root support

The *root support* of a root $t$ is the average marginal root support of
all non-root nodes $n \in N^*$ wrt. $t$:

RS(t) = $\frac{1}{|N^*|} \sum_{n \in N^*} MRS(n,t)$

## Mean root support and mean absolute root

The *mean root support* of $G$ is the average root support of all roots $t$:

ARS(G) = $\frac{1}{|N^r|} \sum_{t \in N^r} RS(t)$

ARS measure to which extent is a fuzzy argument map is globally balanced, where
substantial imbalances per root may cancel each other out.

The *mean absolute root support* of $G$ is the average absolute root support
of all roots $t$:

AARS(G) := $\frac{1}{|N^r|} \sum_{t \in N^r} |RS(t)|$

AARS measures to which extent a fuzzy argument map is locally balanced.
Local imbalances (e.g., proponderance of pros for first root and
proponderance of cons for second root) are not cancelled out.

## Global balance

If we assume that all root claims are mutually exclusive and collectively exhaustive,
every argument in a fuzzy argmap that supports (or attacks), indirectely, a root claim
eo ipso attacks (supports) the remaining root claims.

We define MRS' to capture this assumption as

MRS'(n,t) := MRS(n,t) if |P(n,t)|>0, else:
$-\frac{1}{|\{t'\in N^r: P(n,t')=0\}|}mean_{t' \in N^r \setminus t}$(MRS(n,t'))

If we define RS', AARS' accordingly, we can define the *global balance* of a fuzzy
argmap as

GB(G) := AARS'(G)

"""  # noqa: W605

from __future__ import annotations

import networkx as nx
import numpy as np

import logikon.schemas.argument_mapping as am
from logikon.analysts.score.argmap_graph_scores import AbstractGraphScorer


class AbstractBalanceScorer(AbstractGraphScorer):
    def _preprocess_graph(self, digraph: nx.DiGraph) -> nx.DiGraph:
        """set negative weights for attack edges and reverse edges"""
        digraph_r = digraph.reverse(copy=True)

        for u, v, data in digraph_r.edges(data=True):
            if data["valence"] == "attack":
                digraph_r[u][v]["weight"] = -1 * data.get("weight", 1)

        return digraph_r

    def _get_central_nodes(self, digraph_r: nx.DiGraph) -> list[str]:
        """Returns central nodes of graph"""
        central_nodes = [n for n, data in digraph_r.nodes(data=True) if data.get("nodeType") == am.CENTRAL_CLAIM]
        if not central_nodes:
            self.logger.warning("No central claims found, will use root nodes instead")
            central_nodes = [
                n for n in digraph_r.nodes if digraph_r.in_degree(n) == 0
            ]  # using in_degree as graph has been reversed
        return central_nodes

    def _get_marginal_root_support(
        self, digraph_r: nx.DiGraph, central_nodes: list, default: float | None = None
    ) -> dict[str, dict[str, float | None]]:
        """Calculates MRS and stores values in data

        Args:
            digraph_r (nx.DiGraph): reversed argument digraph
            default (Optional[float], optional): default value for MRS. Defaults to None.

        Returns:
            dict[str, dict[str, float | None]]: dict of MRS values mrs[root][node]
        """
        mrs: dict[str, dict[str, float | None]] = {}

        for t in central_nodes:
            mrs[t] = {}
            nodes = [n for n in digraph_r.nodes if n not in central_nodes]
            paths = list(nx.all_simple_paths(digraph_r, t, nodes))
            for n in nodes:
                paths_n = [p for p in paths if p[-1] == n]
                weights = [np.prod([digraph_r[u][v]["weight"] for u, v in zip(p[:-1], p[1:])]) for p in paths_n]
                mrs[t][n] = np.mean(weights) if weights else default

        return mrs


class MeanRootSupportScorer(AbstractBalanceScorer):
    __pdescription__ = "The mean root support in the argument map (global balance score)"
    __product__ = "mean_root_support"

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[str | float, str, dict | None]:
        """Calculate mean root support"""
        digraph_r = self._preprocess_graph(digraph)

        central_nodes = self._get_central_nodes(digraph_r)
        if not central_nodes:
            self.logger.warning("No central claims or root nodes found, cannot calculate mean root support")
            return 0, "No central claims or root nodes found, cannot calculate mean root support", None

        mrs = self._get_marginal_root_support(digraph_r, central_nodes)

        root_supports = []
        for t in central_nodes:
            mrss = [v for v in mrs[t].values() if v is not None]
            if mrss:
                root_supports.append(np.mean(mrss))

        mean_root_support = np.mean(root_supports) if root_supports else 0

        return float(mean_root_support), "", None


class MeanAbsRootSupportScorer(AbstractBalanceScorer):
    __pdescription__ = "The mean absolute root support in the argument map (local balance score)"
    __product__ = "mean_absolute_root_support"

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[str | float, str, dict | None]:
        """Calculate mean absolute root support"""
        digraph_r = self._preprocess_graph(digraph)

        central_nodes = self._get_central_nodes(digraph_r)
        if not central_nodes:
            self.logger.warning("No central claims or root nodes found, cannot calculate mean absolute root support")
            return 0, "No central claims or root nodes found, cannot calculate mean root support", None

        mrs = self._get_marginal_root_support(digraph_r, central_nodes)

        root_supports = []
        for t in central_nodes:
            mrss = [v for v in mrs[t].values() if v is not None]
            if mrss:
                root_supports.append(np.mean(mrss))

        mean_absolute_root_support = np.mean([abs(v) for v in root_supports]) if root_supports else 0

        return float(mean_absolute_root_support), "", None


class GlobalBalanceScorer(AbstractBalanceScorer):
    __pdescription__ = (
        "The argument map's global balance (assumes mutually exclusive and collectively exhaustive root claims)"
    )
    __product__ = "global_balance"

    def _get_mrs_star(self, mrs: dict[str, dict[str, float | None]]) -> dict[str, dict[str, float]]:
        """Calculates MRS' from MRS"""
        mrs_star: dict[str, dict[str, float]] = {}
        nodes = list(next(iter(mrs.values())).keys())
        mrs_node = {n: [mrs[t][n] for t in mrs if mrs[t][n] is not None] for n in nodes}
        for t in mrs:
            mrs_star[t] = {}
            for n in mrs[t]:
                if mrs[t][n] is None:
                    if mrs_node[n]:
                        mrs_star[t][n] = -np.mean(mrs_node[n]) / len(mrs_node[n])  # type: ignore
                    else:
                        mrs_star[t][n] = 0
                else:
                    mrs_star[t][n] = mrs[t][n]  # type: ignore

        return mrs_star

    def _calculate_score(self, digraph: nx.DiGraph) -> tuple[str | float, str, dict | None]:
        """Calculate global_balance"""
        digraph_r = self._preprocess_graph(digraph)

        central_nodes = self._get_central_nodes(digraph_r)
        if not central_nodes:
            self.logger.warning("No central claims or root nodes found, cannot calculate global_balance")
            return 0, "No central claims or root nodes found, cannot calculate global_balance", None

        mrs = self._get_marginal_root_support(digraph_r, central_nodes)
        mrss = self._get_mrs_star(mrs)

        global_balance = np.mean([abs(np.mean(list(mrss[t].values()))) for t in central_nodes])

        return float(global_balance), "", None
