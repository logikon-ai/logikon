import networkx as nx
import pytest

import logikon.schemas.argument_mapping as am
from logikon.analysts.base import ArtifcatAnalystConfig
from logikon.analysts.export.networkx_exporter import RelevanceNetworkNXExporter
from logikon.schemas.argument_mapping import (
    ArgMapEdge,
    ArgMapNode,
    FuzzyArgMap,
    FuzzyArgMapEdge,
    InformalArgMap,
)


@pytest.fixture(name="argmap1")
def argmap1() -> InformalArgMap:
    nodelist = [
        ArgMapNode(id="n0", label="claim1", text="claim 1"),
        ArgMapNode(id="n1", label="pro2", text="pro 2"),
        ArgMapNode(id="n2", label="con3", text="con 3"),
    ]
    edgelist = [
        ArgMapEdge(source="n1", target="n0", valence=am.SUPPORT),
        ArgMapEdge(source="n2", target="n0", valence=am.ATTACK),
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


def test_nx_exporter2(reln1: FuzzyArgMap):
    nx_exporter = RelevanceNetworkNXExporter(ArtifcatAnalystConfig())
    nx_map = nx_exporter._to_nx(reln1.model_dump())

    print(nx.node_link_data(nx_map))  # noqa: T201

    assert isinstance(nx_map, nx.DiGraph)

    assert len(nx_map.nodes) == len(reln1.nodelist)
    assert len(nx_map.edges) == len(reln1.edgelist)

    for node, nodedata in nx_map.nodes.items():
        original_node = next(n for n in reln1.nodelist if n.id == node)
        assert nodedata["label"] == original_node.label
        assert nodedata["text"] == original_node.text

    for _, _, d in nx_map.edges(data=True):
        assert d["valence"] in [am.SUPPORT, am.ATTACK]
        assert d["weight"] in [0.4, 0.5]
