import networkx as nx
import pytest

import os

import logikon.schemas.argument_mapping as am
from logikon.analysts.reconstruction.fuzzy_argmap_builder import FuzzyArgMapBuilder
from logikon.analysts.base import ArtifcatAnalystConfig


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
            {"text": "con 4", "label": "con4", "annotations": [], "nodeType": am.REASON, "id": "n4"},
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
            {"text": "claim 0", "label": "claim0", "annotations": [], "nodeType": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "claim 1", "label": "claim1", "annotations": [], "nodeType": am.CENTRAL_CLAIM, "id": "n1"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": am.REASON, "id": "n2"},
            {"text": "con 3", "label": "con3", "annotations": [], "nodeType": am.REASON, "id": "n3"},
            {"text": "con 4", "label": "con4", "annotations": [], "nodeType": am.REASON, "id": "n4"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n3", "target": "n0", "weight": 0.5},
            {"valence": am.SUPPORT, "source": "n2", "target": "n0", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n3", "target": "n1", "weight": 0.4},
            {"valence": am.ATTACK, "source": "n2", "target": "n1", "weight": 0.4},
            {"valence": am.ATTACK, "source": "n3", "target": "n2", "weight": 0.3},
            {"valence": am.ATTACK, "source": "n2", "target": "n3", "weight": 0.3},
            {"valence": am.ATTACK, "source": "n4", "target": "n3", "weight": 0.2},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_preprocessor01(nx_map1: nx.DiGraph):
    config = ArtifcatAnalystConfig()
    analyst = FuzzyArgMapBuilder(config)

    print(nx.node_link_data(nx_map1))

    rn_pp = analyst._preprocess_network(nx_map1)

    print(nx.node_link_data(rn_pp))

    assert len(rn_pp.nodes) == 1 + len(nx_map1.nodes)
    assert len(rn_pp.edges) > len(nx_map1.edges)

    assert len([u for u, _ in rn_pp.edges() if str(u).startswith("super")]) == 2

    assert all(str(u).startswith("super") for u, v, d in rn_pp.edges(data=True) if v == "n0")
    assert all(d["pseudo"] for u, v, d in rn_pp.edges(data=True) if str(u).startswith("super"))
    assert all(d["pseudo"] for n, d in rn_pp.nodes(data=True) if str(n).startswith("super"))


def test_reduction_workflow(nx_map1: nx.DiGraph):
    config = ArtifcatAnalystConfig()
    analyst = FuzzyArgMapBuilder(config)

    print(f"Original rel network:\n{nx.node_link_data(nx_map1)}")

    relevance_network = analyst._preprocess_network(nx_map1)

    print(f"With pseudo edges:\n{nx.node_link_data(relevance_network)}")

    fuzzy_argmap = nx.maximum_branching(
        relevance_network, attr='weight', default=1, preserve_attrs=True, partition=None
    )

    print(f"Maximum branching:\n{nx.node_link_data(fuzzy_argmap)}")
    assert nx.is_forest(fuzzy_argmap.reverse())

    analyst._add_above_threshold_edges(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

    print(f"Expanded branching:\n{nx.node_link_data(fuzzy_argmap)}")
    assert nx.is_forest(fuzzy_argmap.reverse())

    assert all(am.IN_FOREST in data for _, _, data in fuzzy_argmap.edges(data=True))

    fuzzy_argmap = analyst._post_process_fuzzy_argmap(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

    print(f"Postprocessed fuzzy argmap:\n{nx.node_link_data(fuzzy_argmap)}")

    assert fuzzy_argmap.nodes(data=True) == nx_map1.nodes(data=True)
    assert len(fuzzy_argmap.edges) == 2
    assert all(nx_map1.has_edge(u, v) for u, v in fuzzy_argmap.edges())
    assert all("weight" in data for _, _, data in fuzzy_argmap.edges(data=True))


def test_reduction_workflow2(nx_map2: nx.DiGraph):
    config = ArtifcatAnalystConfig()
    analyst = FuzzyArgMapBuilder(config)

    print(f"Original rel network:\n{nx.node_link_data(nx_map2)}")

    relevance_network = analyst._preprocess_network(nx_map2)

    print(f"With pseudo edges:\n{nx.node_link_data(relevance_network)}")

    fuzzy_argmap = nx.maximum_branching(
        relevance_network, attr='weight', default=1, preserve_attrs=True, partition=None
    )

    print(f"Maximum branching:\n{nx.node_link_data(fuzzy_argmap)}")
    assert nx.is_forest(fuzzy_argmap.reverse())

    analyst._add_above_threshold_edges(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

    print(f"Expanded branching:\n{nx.node_link_data(fuzzy_argmap)}")
    assert not nx.is_forest(fuzzy_argmap.reverse())

    assert all(am.IN_FOREST in data for _, _, data in fuzzy_argmap.edges(data=True))

    fuzzy_argmap = analyst._post_process_fuzzy_argmap(fuzzy_argmap=fuzzy_argmap, relevance_network=relevance_network)

    print(f"Postprocessed fuzzy argmap:\n{nx.node_link_data(fuzzy_argmap)}")

    assert fuzzy_argmap.nodes(data=True) == nx_map2.nodes(data=True)
    assert len(fuzzy_argmap.edges) == 6
    assert all(nx_map2.has_edge(u, v) for u, v in fuzzy_argmap.edges())
    assert all("weight" in data for _, _, data in fuzzy_argmap.edges(data=True))
