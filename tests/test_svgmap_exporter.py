import networkx as nx
import pytest

import os

from logikon.analysts.export.svgmap_exporter import SVGMapExporter
from logikon.analysts.base import ArtifcatAnalystConfig
import logikon.schemas.argument_mapping as am


@pytest.fixture(name="nx_map1")
def nx_map1() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"text": "claim 1\n", "label": "claim1", "annotations": [], "nodeType": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": am.REASON, "id": "n1"},
            {"text": "con 3", "label": "con3", "annotations": [], "nodeType": am.REASON, "id": "n2"},
        ],
        "links": [
            {"valence": "pro", "source": "n1", "target": "n0", "weight": 0.5, am.IN_FOREST: True},
            {"valence": "con", "source": "n2", "target": "n0", "weight": 0.5, am.IN_FOREST: True},
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
            {"text": "claim 1\n", "label": "claim1", "annotations": [], "nodeType": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "claim 2\n", "label": "claim2", "annotations": [], "nodeType": am.CENTRAL_CLAIM, "id": "n1"},
        ]
        + [
            {
                "text": 10 * (f"argument-{i} and "),
                "label": f"arg{i}",
                "annotations": [],
                "nodeType": am.REASON,
                "id": f"n{2+i}",
            }
            for i in range(16)
        ],
        "links": [{"valence": "pro", "source": f"n{i+1}", "target": f"n{i // 2}"} for i in range(15)],
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
            {"text": "claim 1", "label": "claim1", "annotations": [], "nodeType": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": am.REASON, "id": "n1"},
            {"text": "con 3", "label": "con3", "annotations": [], "nodeType": am.REASON, "id": "n2"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n1", "target": "n0", "weight": 0.25},
            {"valence": am.ATTACK, "source": "n2", "target": "n0", "weight": 0.95},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_preprocessor01(nx_map1):
    config = ArtifcatAnalystConfig()
    svgmap_exporter = SVGMapExporter(config)
    nx_map_pp = svgmap_exporter._preprocess_graph(nx_map1)

    assert len(nx_map_pp.nodes) == len(nx_map1.nodes)
    assert nx_map_pp.nodes.keys() == nx_map1.nodes.keys()
    assert nx_map_pp.edges.keys() == nx_map1.edges.keys()

    for _, linkdata in nx_map_pp.edges.items():
        "color" in linkdata


def test_svg_exporter(nx_map1):
    config = ArtifcatAnalystConfig()
    svgmap_exporter = SVGMapExporter(config)
    svgmap = svgmap_exporter._to_svg(nx_map1)
    assert isinstance(svgmap, str)

    # svgmap = svgmap.decode("utf-8")
    assert svgmap.startswith('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')

    for _, nodedata in nx_map1.nodes.items():
        assert nodedata["label"] in svgmap


def test_svg_exporter_save(nx_map2):
    config = ArtifcatAnalystConfig()
    svgmap_exporter = SVGMapExporter(config)
    svgmap = svgmap_exporter._to_svg(nx_map2)
    assert isinstance(svgmap, str)

    with open("test_graph1.svg", 'w') as f:
        f.write(svgmap)

    assert os.path.isfile("test_graph1.svg")


def test_svg_exporter_weighted(nx_map3):
    config = ArtifcatAnalystConfig()
    svgmap_exporter = SVGMapExporter(config)
    svgmap = svgmap_exporter._to_svg(nx_map3)
    assert isinstance(svgmap, str)

    with open("test_graph2.svg", 'w') as f:
        f.write(svgmap)

    assert os.path.isfile("test_graph2.svg")
