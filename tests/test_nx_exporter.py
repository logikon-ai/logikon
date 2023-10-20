import networkx as nx
import pytest

from logikon.debuggers.exporters.networkx_exporter import NetworkXExporter, RelevanceNetworkNXExporter
from logikon.schemas.argument_mapping import (
    AnnotationSpan,
    ArgMapEdge,
    ArgMapNode,
    InformalArgMap,
    FuzzyArgMapEdge,
    FuzzyArgMap,
)
from logikon.schemas.configs import DebugConfig
import logikon.schemas.argument_mapping as am


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


@pytest.fixture(name="reln1")
def reln1() -> FuzzyArgMap:
    nodelist = [
        ArgMapNode(id="n0", label="claim1", text="claim 1"),
        ArgMapNode(id="n1", label="pro2", text="pro 2"),
        ArgMapNode(id="n2", label="con3", text="con 3"),
    ]
    edgelist = [
        FuzzyArgMapEdge(source="n1", target="n0", valence=am.SUPPORT, weight=0.5),
        FuzzyArgMapEdge(source="n2", target="n0", valence=am.ATTACK, weight=0.4),
    ]
    return FuzzyArgMap(nodelist=nodelist, edgelist=edgelist)


def test_nx_exporter(argmap1: InformalArgMap):
    nx_exporter = NetworkXExporter(DebugConfig())
    nx_map = nx_exporter._to_nx(argmap1.dict())

    print(nx.node_link_data(nx_map))

    assert isinstance(nx_map, nx.DiGraph)

    assert len(nx_map.nodes) == len(argmap1.nodelist)
    assert len(nx_map.edges) == len(argmap1.edgelist)

    for node, nodedata in nx_map.nodes.items():
        original_node = next(n for n in argmap1.nodelist if n.id == node)
        assert nodedata["label"] == original_node.label
        assert nodedata["text"] == original_node.text


def test_nx_exporter2(reln1: FuzzyArgMap):
    nx_exporter = RelevanceNetworkNXExporter(DebugConfig())
    nx_map = nx_exporter._to_nx(reln1.dict())

    print(nx.node_link_data(nx_map))

    assert isinstance(nx_map, nx.DiGraph)

    assert len(nx_map.nodes) == len(reln1.nodelist)
    assert len(nx_map.edges) == len(reln1.edgelist)

    for node, nodedata in nx_map.nodes.items():
        original_node = next(n for n in reln1.nodelist if n.id == node)
        assert nodedata["label"] == original_node.label
        assert nodedata["text"] == original_node.text

    for u, v, d in nx_map.edges(data=True):
        assert d["valence"] in [am.SUPPORT, am.ATTACK]
        assert d["weight"] in [0.4, 0.5]
