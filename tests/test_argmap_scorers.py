import pytest

import networkx as nx

from logikon.schemas.configs import DebugConfig
from logikon.debuggers.scorers.argmap_graph_scores import (
    ArgMapGraphSizeScorer,
    ArgMapGraphAvgKatzCScorer,
    ArgMapGraphAttackRatioScorer,
)


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


@pytest.fixture(name="nx_map2")
def nx_map2() -> nx.DiGraph:
    data = {
        'directed': True,
        'multigraph': False,
        'graph': {},
        'nodes': [{'text': 'claim 1', 'label': 'claim1', 'annotations': [], 'nodeType': 'proposition', 'id': 'n0'}, {'text': 'pro 2', 'label': 'pro2', 'annotations': [], 'nodeType': 'proposition', 'id': 'n1'}, {'text': 'con 3', 'label': 'con3', 'annotations': [], 'nodeType': 'proposition', 'id': 'n2'}],
        'links': [{'valence': 'pro', 'source': 'n1', 'target': 'n0'}, {'valence': 'con', 'source': 'n2', 'target': 'n0'}, {'valence': 'con', 'source': 'n2', 'target': 'n1'}]
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_argmap_size_scorer01(nx_map1):
    scorer = ArgMapGraphSizeScorer(DebugConfig())
    score, comment, meta = scorer._calculate_score(nx_map1)

    assert score == len(nx_map1.nodes)
    assert comment == ""
    assert meta == None


def test_argmap_katz_scorer01(nx_map1, nx_map2):
    scorer = ArgMapGraphAvgKatzCScorer(DebugConfig())
    score1, _, _ = scorer._calculate_score(nx_map1)
    score2, _, _ = scorer._calculate_score(nx_map2)

    assert score1 < score2

def test_argmap_attackratio_scorer01(nx_map1, nx_map2):
    scorer = ArgMapGraphAttackRatioScorer(DebugConfig())
    score1, _, _ = scorer._calculate_score(nx_map1)
    score2, _, _ = scorer._calculate_score(nx_map2)

    assert score1 == 1/2
    assert score2 == 2/3

