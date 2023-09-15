import pytest

import networkx as nx

from logikon.schemas.configs import DebugConfig
from logikon.debuggers.exporters.svgmap_exporter import SVGMapExporter


@pytest.fixture(name="nx_map1")
def nx_map1() -> nx.DiGraph:
    data = {
        'directed': True,
        'multigraph': False,
        'graph': {},
        'nodes': [{'text': 'claim 1', 'label': 'claim1', 'annotations': [], 'nodeType': 'proposition', 'id': 'n0'}, {'text': 'pro 2', 'label': 'pro2', 'annotations': [], 'nodeType': 'proposition', 'id': 'n1'}, {'text': 'con 3', 'label': 'con3', 'annotations': [], 'nodeType': 'proposition', 'id': 'n2'}],
        'links': [{'valence': 'pro', 'source': 'n1', 'target': 'n0'}, {'valence': 'con', 'source': 'n2', 'target': 'n0'}]
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_preprocessor01(nx_map1):
    config = DebugConfig()
    svgmap_exporter = SVGMapExporter(config)
    nx_map_pp = svgmap_exporter._preprocess_graph(nx_map1)

    assert len(nx_map_pp.nodes) == len(nx_map1.nodes)
    assert nx_map_pp.nodes.keys() == nx_map1.nodes.keys()
    assert nx_map_pp.edges.keys() == nx_map1.edges.keys()

    for _, linkdata in nx_map_pp.edges.items():
        "color" in linkdata


def test_svg_exporter(nx_map1):
    config = DebugConfig()
    svgmap_exporter = SVGMapExporter(config)
    svgmap = svgmap_exporter._to_svg(nx_map1)
    assert isinstance(svgmap, bytes)

    svgmap = svgmap.decode("utf-8")
    assert svgmap.startswith("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>")

    for _, nodedata in nx_map1.nodes.items():
        assert nodedata["label"] in svgmap
