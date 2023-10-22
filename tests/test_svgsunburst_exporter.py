import networkx as nx
import pytest

import os

from logikon.debuggers.exporters.svgsunburst_exporter import SVGSunburstExporter
from logikon.schemas.configs import DebugConfig
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
                "label": f"arg #{i}",
                "annotations": [],
                "nodeType": "proposition",
                "id": f"n{i}",
            }
            for i in range(16)
        ],
        "links": [{"valence": am.SUPPORT, "source": f"n{i+1}", "target": f"n{i // 2}"} for i in range(15)],
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
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": "proposition", "id": "n1"},
            {"text": "con 3", "label": "con3", "annotations": [], "nodeType": "proposition", "id": "n2"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n1", "target": "n0", "weight": 0.25},
            {"valence": am.ATTACK, "source": "n2", "target": "n0", "weight": 0.95},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_svg_exporter_save(nx_map2):
    config = DebugConfig()
    svgsunburst_exporter = SVGSunburstExporter(config)
    tree_data, color_map = svgsunburst_exporter._to_tree_data(nx_map2, "Issue 1")
    print(tree_data)
    svgsunburst = svgsunburst_exporter._to_svg(tree_data, color_map)

    assert isinstance(svgsunburst, str)

    assert svgsunburst.startswith('<svg')

    with open("test_svgsunburst1.svg", 'w') as f:
        f.write(svgsunburst)

    assert os.path.isfile("test_svgsunburst1.svg")

    assert 1==0


def test_svg_exporter_weighted(nx_map3):
    config = DebugConfig()
    svgsunburst_exporter = SVGSunburstExporter(config)
    tree_data, color_map = svgsunburst_exporter._to_tree_data(nx_map3, "Issue 3")
    svgsunburst = svgsunburst_exporter._to_svg(tree_data, color_map)

    assert isinstance(svgsunburst, str)

    with open("test_svgsunburst2.svg", 'w') as f:
        f.write(svgsunburst)

    assert os.path.isfile("test_svgsunburst2.svg")
