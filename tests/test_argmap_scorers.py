import networkx as nx
import pytest

import logikon.schemas.argument_mapping as am
from logikon.analysts.score.argmap_graph_scores import (
    ArgMapGraphAttackRatioScorer,
    ArgMapGraphAvgKatzCScorer,
    ArgMapGraphSizeScorer,
    MeanReasonStrengthScorer,
)
from logikon.analysts.base import ScoreAnalystConfig


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
            {"valence": am.SUPPORT, "source": "n1", "target": "n0", "weight": 0.4},
            {"valence": am.ATTACK, "source": "n2", "target": "n0", "weight": 0.8},
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
            {"text": "claim 1", "label": "claim1", "annotations": [], "nodeType": "proposition", "id": "n0"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "nodeType": "proposition", "id": "n1"},
            {"text": "con 3", "label": "con3", "annotations": [], "nodeType": "proposition", "id": "n2"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n1", "target": "n0", "weight": 0.25},
            {"valence": am.ATTACK, "source": "n2", "target": "n0", "weight": 0.75},
            {"valence": am.ATTACK, "source": "n2", "target": "n1", "weight": 0.5},
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_argmap_size_scorer01(nx_map1):
    scorer = ArgMapGraphSizeScorer(ScoreAnalystConfig())
    score, comment, meta = scorer._calculate_score(nx_map1)

    assert score == len(nx_map1.nodes)
    assert comment == ""
    assert meta is None


def test_argmap_katz_scorer01(nx_map1, nx_map2):
    scorer = ArgMapGraphAvgKatzCScorer(ScoreAnalystConfig())
    score1, _, _ = scorer._calculate_score(nx_map1)
    score2, _, _ = scorer._calculate_score(nx_map2)

    assert score1 < score2


def test_argmap_attackratio_scorer01(nx_map1, nx_map2):
    scorer = ArgMapGraphAttackRatioScorer(ScoreAnalystConfig())
    score1, _, _ = scorer._calculate_score(nx_map1)
    score2, _, _ = scorer._calculate_score(nx_map2)

    assert score1 == 1 / 2
    assert score2 == 2 / 3


def test_meanreasonstrength_scorer01(nx_map1, nx_map2):
    scorer = MeanReasonStrengthScorer(ScoreAnalystConfig())
    score1, _, _ = scorer._calculate_score(nx_map1)
    score2, _, _ = scorer._calculate_score(nx_map2)

    assert abs(score1 - 0.6) < 1e-6
    assert abs(score2 - 0.5) < 1e-6
