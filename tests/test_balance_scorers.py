import networkx as nx
import pytest

import logikon.schemas.argument_mapping as am
from logikon.analysts.base import ScoreAnalystConfig
from logikon.analysts.score.balance_scores import (
    GlobalBalanceScorer,
    MeanAbsRootSupportScorer,
    MeanRootSupportScorer,
)


@pytest.fixture(name="nx_map1")
def nx_map1() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"text": "claim 1", "label": "claim1", "annotations": [], "node_type": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "node_type": am.REASON, "id": "n1"},
            {"text": "con 3", "label": "con3", "annotations": [], "node_type": am.REASON, "id": "n2"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n1", "target": "n0", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n2", "target": "n0", "weight": 0.5},
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
            {"text": "claim 1", "label": "claim1", "annotations": [], "node_type": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "claim 2", "label": "claim1", "annotations": [], "node_type": am.CENTRAL_CLAIM, "id": "n1"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "node_type": am.REASON, "id": "n2"},
            {"text": "con 3", "label": "con3", "annotations": [], "node_type": am.REASON, "id": "n3"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n2", "target": "n0", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n3", "target": "n0", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n3", "target": "n1", "weight": 0.5},
        ],
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
            {"text": "claim 0", "label": "claim0", "annotations": [], "node_type": am.CENTRAL_CLAIM, "id": "n00"},
            {"text": "claim 1", "label": "claim1", "annotations": [], "node_type": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "claim 2", "label": "claim1", "annotations": [], "node_type": am.CENTRAL_CLAIM, "id": "n1"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "node_type": am.REASON, "id": "n2"},
            {"text": "con 3", "label": "con3", "annotations": [], "node_type": am.REASON, "id": "n3"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n2", "target": "n0", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n3", "target": "n0", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n3", "target": "n1", "weight": 0.5},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_mean_scorer01(nx_map1):
    scorer = MeanRootSupportScorer(ScoreAnalystConfig())
    score, comment, meta = scorer._calculate_score(nx_map1)

    assert score == 0
    assert comment == ""
    assert meta is None


def test_mean_scorer02(nx_map2):
    scorer = MeanRootSupportScorer(ScoreAnalystConfig())
    score, comment, meta = scorer._calculate_score(nx_map2)

    assert score == -0.25
    assert comment == ""
    assert meta is None


def test_mean_scorer03(nx_map3):
    scorer = MeanRootSupportScorer(ScoreAnalystConfig())
    score, comment, meta = scorer._calculate_score(nx_map3)

    assert score == -0.25
    assert comment == ""
    assert meta is None


def test_mean_abs_scorer01(nx_map1):
    scorer = MeanAbsRootSupportScorer(ScoreAnalystConfig())
    score, comment, meta = scorer._calculate_score(nx_map1)

    assert score == 0
    assert comment == ""
    assert meta is None


def test_mean_abs_scorer02(nx_map2):
    scorer = MeanAbsRootSupportScorer(ScoreAnalystConfig())
    score, comment, meta = scorer._calculate_score(nx_map2)

    assert score == 0.25
    assert comment == ""
    assert meta is None


def test_gb_scorer01(nx_map1):
    scorer = GlobalBalanceScorer(ScoreAnalystConfig())
    score, comment, meta = scorer._calculate_score(nx_map1)

    assert score == 0
    assert comment == ""
    assert meta is None


def test_gb_scorer02(nx_map2):
    scorer = GlobalBalanceScorer(ScoreAnalystConfig())
    score, comment, meta = scorer._calculate_score(nx_map2)

    assert score == 0.25
    assert comment == ""
    assert meta is None
