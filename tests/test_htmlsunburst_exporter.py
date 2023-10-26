import networkx as nx
import pytest

import os

from logikon.analysts.export.htmlsunburst_exporter import HTMLSunburstExporter
from logikon.analysts.base import ArtifcatAnalystConfig
import logikon.schemas.argument_mapping as am


@pytest.fixture(name="nx_map1")
def nx_map1() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"text": "claim 1", "label": "claim1", "annotations": [], "nodeType": "proposition", "id": "n0"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": "proposition", "id": "n1"},
            {"text": "con 3", "label": "con3", "annotations": [], "nodeType": "proposition", "id": "n2"},
        ],
        "links": [
            {"valence": "pro", "source": "n1", "target": "n0"},
            {"valence": "con", "source": "n2", "target": "n0"},
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
                "label": f"arg #{i} reason",
                "annotations": [],
                "nodeType": "proposition",
                "id": f"n{i}",
            }
            for i in range(20)
        ],
        "links": [{"valence": am.SUPPORT, "source": f"n{i+1}", "target": f"n{i // 2}"} for i in range(19)],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


@pytest.fixture(name="nx_map3")
def nx_map3() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"text": "claim 1", "label": "claim1", "annotations": [], "nodeType": "proposition", "id": "n0"},
            {"text": "claim 2", "label": "claim2", "annotations": [], "nodeType": "proposition", "id": "n00"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": "proposition", "id": "n1"},
            {
                "text": "con 3",
                "label": "con reason 3 explained",
                "annotations": [],
                "nodeType": "proposition",
                "id": "n2",
            },
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n1", "target": "n0", "weight": 0.25},
            {"valence": am.ATTACK, "source": "n2", "target": "n0", "weight": 0.95},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


@pytest.fixture(name="nx_map4")
def nx_map4() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"text": "claim 1", "label": "claim1", "annotations": [], "nodeType": "proposition", "id": "n0"},
            {"text": "claim 2", "label": "claim2", "annotations": [], "nodeType": "proposition", "id": "n00"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": "proposition", "id": "n1"},
            {
                "text": "con 3",
                "label": "con reason 3 explained",
                "annotations": [],
                "nodeType": "proposition",
                "id": "n2",
            },
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n1", "target": "n0", "weight": 0.25},
            {"valence": am.ATTACK, "source": "n1", "target": "n2", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n2", "target": "n1", "weight": 0.95},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


@pytest.fixture(name="nx_map5")
def nx_map5() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"text": "claim 1", "label": "claim1", "annotations": [], "nodeType": "proposition", "id": "n0"},
            {"text": "claim 2", "label": "claim2", "annotations": [], "nodeType": "proposition", "id": "n00"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": "proposition", "id": "n1"},
            {
                "text": "con 3",
                "label": "con reason 3 explained",
                "annotations": [],
                "nodeType": "proposition",
                "id": "n2",
            },
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n1", "target": "n0", "weight": 0.25, am.IN_FOREST: True},
            {"valence": am.ATTACK, "source": "n2", "target": "n0", "weight": 0.5, am.IN_FOREST: True},
            {"valence": am.ATTACK, "source": "n2", "target": "n1", "weight": 0.95, am.IN_FOREST: False},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_html_exporter_save(nx_map2):
    config = ArtifcatAnalystConfig()
    htmlsunburst_exporter = HTMLSunburstExporter(config)
    tree_data, color_map, legend = htmlsunburst_exporter._to_tree_data(nx_map2, "Issue 1")
    print(tree_data)
    htmlsunburst = htmlsunburst_exporter._to_html(tree_data, color_map, "Issue 2", legend)

    assert isinstance(htmlsunburst, str)

    assert htmlsunburst.startswith('<html')

    with open("test_sunburst1.html", 'w') as f:
        f.write(htmlsunburst)

    assert os.path.isfile("test_sunburst1.html")


def test_html_exporter_weighted1(nx_map3):
    config = ArtifcatAnalystConfig()
    htmlsunburst_exporter = HTMLSunburstExporter(config)
    tree_data, color_map, legend = htmlsunburst_exporter._to_tree_data(nx_map3, "Issue 3")
    htmlsunburst = htmlsunburst_exporter._to_html(tree_data, color_map, "Issue 3", legend)

    assert isinstance(htmlsunburst, str)

    with open("test_sunburst2.html", 'w') as f:
        f.write(htmlsunburst)

    assert os.path.isfile("test_sunburst2.html")


def test_html_exporter_weighted2(nx_map4):
    config = ArtifcatAnalystConfig()
    htmlsunburst_exporter = HTMLSunburstExporter(config)
    tree = htmlsunburst_exporter._trunc_to_tree(nx_map4)
    tree_data, color_map, legend = htmlsunburst_exporter._to_tree_data(tree, "Issue 3")
    htmlsunburst = htmlsunburst_exporter._to_html(tree_data, color_map, "Issue 3", legend)

    assert isinstance(htmlsunburst, str)

    with open("test_sunburst3.html", 'w') as f:
        f.write(htmlsunburst)

    assert os.path.isfile("test_sunburst3.html")


def test_html_exporter_weighted3(nx_map5):
    config = ArtifcatAnalystConfig()
    htmlsunburst_exporter = HTMLSunburstExporter(config)
    tree = htmlsunburst_exporter._trunc_to_tree(nx_map5)
    tree_data, color_map, legend = htmlsunburst_exporter._to_tree_data(tree, "Issue 5")
    htmlsunburst = htmlsunburst_exporter._to_html(tree_data, color_map, "Issue 5", legend)

    assert isinstance(htmlsunburst, str)

    with open("test_sunburst4.html", 'w') as f:
        f.write(htmlsunburst)

    assert os.path.isfile("test_sunburst4.html")
