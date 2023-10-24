import networkx as nx
import pytest

import os

import logikon.schemas.argument_mapping as am
from logikon.debuggers.reconstruction.fuzzy_argmap_builder import FuzzyArgMapBuilder
from logikon.debuggers.base import ArtifcatDebuggerConfig


@pytest.fixture(name="nx_map1")
def nx_map1() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"text": "claim 0", "label": "claim0", "annotations": [], "nodeType": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "claim 1", "label": "claim1", "annotations": [], "nodeType": am.CENTRAL_CLAIM, "id": "n1"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": am.REASON, "id": "n2"},
            {"text": "con 3", "label": "con3", "annotations": [], "nodeType": am.REASON, "id": "n3"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n3", "target": "n0", "weight": 0.5},
            {"valence": am.SUPPORT, "source": "n2", "target": "n0", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n3", "target": "n1", "weight": 0.4},
            {"valence": am.ATTACK, "source": "n2", "target": "n1", "weight": 0.4},
            {"valence": am.ATTACK, "source": "n3", "target": "n2", "weight": 0.3},
            {"valence": am.ATTACK, "source": "n2", "target": "n3", "weight": 0.3},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


@pytest.fixture(name="nx_map2")
def nx_map2() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {
                "text": 10 * (f"argument-{i} and "),
                "label": f"arg{i}",
                "annotations": [],
                "nodeType": "proposition",
                "id": f"n{i}",
            }
            for i in range(16)
        ],
        "links": [{"valence": "pro", "source": f"n{i+1}", "target": f"n{i // 2}"} for i in range(15)],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_preprocessor01(nx_map1: nx.DiGraph):
    config = ArtifcatDebuggerConfig()
    debugger = FuzzyArgMapBuilder(config)

    print(nx.node_link_data(nx_map1))

    rn_pp = debugger._preprocess_network(nx_map1)

    print(nx.node_link_data(rn_pp))

    assert len(rn_pp.nodes) == 1 + len(nx_map1.nodes)
    assert len(rn_pp.edges) > len(nx_map1.edges)

    assert len([u for u, _ in rn_pp.edges() if str(u).startswith("super")]) == 2

    assert all(str(u).startswith("super") for u, v, d in rn_pp.edges(data=True) if v == "n0")
    assert all(d["pseudo"] for u, v, d in rn_pp.edges(data=True) if str(u).startswith("super"))
    assert all(d["pseudo"] for n, d in rn_pp.nodes(data=True) if str(n).startswith("super"))


def test_reduction_workflow(nx_map1: nx.DiGraph):
    config = ArtifcatDebuggerConfig()
    debugger = FuzzyArgMapBuilder(config)

    print(f"Original rel network:\n{nx.node_link_data(nx_map1)}")

    relevance_network = debugger._preprocess_network(nx_map1)

    print(f"With pseudo edges:\n{nx.node_link_data(relevance_network)}")

    fuzzy_argmap = nx.maximum_branching(
        relevance_network, attr='weight', default=1, preserve_attrs=True, partition=None
    )

    print(f"Maximum branching:\n{nx.node_link_data(fuzzy_argmap)}")

    debugger._add_above_threshold_edges(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

    print(f"Expanded branching:\n{nx.node_link_data(fuzzy_argmap)}")

    fuzzy_argmap = debugger._post_process_fuzzy_argmap(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

    print(f"Postprocessed fuzzy argmap:\n{nx.node_link_data(fuzzy_argmap)}")

    assert fuzzy_argmap.nodes(data=True) == nx_map1.nodes(data=True)
    assert len(fuzzy_argmap.edges) == 2
    assert all(nx_map1.has_edge(u, v) for u, v in fuzzy_argmap.edges())
