import networkx as nx
import pytest

import os

import logikon.schemas.argument_mapping as am
from logikon.analysts.reconstruction.relevance_network_builder_lmql import RelevanceNetworkBuilderLMQL, RelevanceNetworkBuilderConfig


@pytest.fixture(name="map1")
def map1() -> am.FuzzyArgMap:
    map1 = am.FuzzyArgMap(
        nodelist=[
            am.ArgMapNode(text="claim 0", label="claim0", annotations=[], nodeType=am.CENTRAL_CLAIM, id="n0"),
            am.ArgMapNode(text="claim 1", label="claim1", annotations=[], nodeType=am.CENTRAL_CLAIM, id="n1"),
            am.ArgMapNode(text="pro 0", label="pro2", annotations=[], nodeType=am.REASON, id="n2"),
            am.ArgMapNode(text="pro 0", label="con3", annotations=[], nodeType=am.REASON, id="n3"),
            am.ArgMapNode(text="con 1", label="con4", annotations=[], nodeType=am.REASON, id="n4"),
            am.ArgMapNode(text="pro 1", label="pro4", annotations=[], nodeType=am.REASON, id="n5"),
        ],
        edgelist=[
            am.FuzzyArgMapEdge(valence=am.SUPPORT, source="n3", target="n0", weight=0.5),
            am.FuzzyArgMapEdge(valence=am.SUPPORT, source="n2", target="n0", weight=0.5),
            am.FuzzyArgMapEdge(valence=am.ATTACK, source="n4", target="n1", weight=0.4),
            am.FuzzyArgMapEdge(valence=am.SUPPORT, source="n5", target="n1", weight=0.4),
        ],
    )
    return map1


def test_dialectic_equivalence(map1: am.FuzzyArgMap):
    config = RelevanceNetworkBuilderConfig(
        llm_framework="transformers",
        expert_model="gpt2",
    )
    analyst = RelevanceNetworkBuilderLMQL(config)

    assert analyst._dialectically_equivalent(map1, map1.nodelist[2], map1.nodelist[3])

    assert analyst._dialectically_equivalent(map1, map1.nodelist[2], map1.nodelist[4])

    assert analyst._dialectically_equivalent(map1, map1.nodelist[4], map1.nodelist[3])

    assert not analyst._dialectically_equivalent(map1, map1.nodelist[2], map1.nodelist[5])

    assert not analyst._dialectically_equivalent(map1, map1.nodelist[3], map1.nodelist[5])

    assert not analyst._dialectically_equivalent(map1, map1.nodelist[4], map1.nodelist[5])
