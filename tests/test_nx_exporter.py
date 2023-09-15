import pytest

import networkx as nx

from logikon.debuggers.exporters.networkx_exporter import NetworkXExporter
from logikon.schemas.argument_mapping import InformalArgMap, ArgMapNode, ArgMapEdge, AnnotationSpan
from logikon.schemas.configs import DebugConfig


@pytest.fixture(name="argmap1")
def argmap1() -> InformalArgMap:
    nodelist = [
        ArgMapNode(id="n0", label="claim1", text="claim 1"),
        ArgMapNode(id="n1", label="pro2", text="pro 2"),
        ArgMapNode(id="n2", label="con3", text="con 3"),
    ]
    edgelist = [
        ArgMapEdge(source="n1", target="n0", valence="pro"),
        ArgMapEdge(source="n2", target="n0", valence="con"),
    ]
    return InformalArgMap(nodelist=nodelist, edgelist=edgelist)

def test_nx_exporter(argmap1: InformalArgMap):
    nx_exporter = NetworkXExporter(DebugConfig())
    nx_map = nx_exporter.to_nx(argmap1)

    print(nx.node_link_data(nx_map))

    assert isinstance(nx_map, nx.DiGraph)

    assert len(nx_map.nodes) == len(argmap1.nodelist)
    assert len(nx_map.edges) == len(argmap1.edgelist)

    for node, nodedata in nx_map.nodes.items():
        original_node = next(n for n in argmap1.nodelist if n.id == node)
        assert nodedata["label"] == original_node.label
        assert nodedata["text"] == original_node.text

