# test argumentmapping module

import networkx as nx
import pytest

import logikon.schemas.argument_mapping as am


@pytest.fixture(name="nx_map1")
def nx_map1() -> nx.DiGraph:
    data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"text": "claim 0", "label": "claim0", "annotations": [], "node_type": am.CENTRAL_CLAIM, "id": "n0"},
            {"text": "claim 1", "label": "claim1", "annotations": [], "node_type": am.CENTRAL_CLAIM, "id": "n1"},
            {"text": "pro 2", "label": "pro2", "annotations": [], "node_type": am.REASON, "id": "n2"},
            {"text": "con 3", "label": "con3", "annotations": [], "node_type": am.REASON, "id": "n3"},
            {"text": "con 4", "label": "con4", "annotations": [], "node_type": am.REASON, "id": "n4"},
        ],
        "links": [
            {"valence": am.SUPPORT, "source": "n3", "target": "n0", "weight": 0.5},
            {"valence": am.SUPPORT, "source": "n2", "target": "n0", "weight": 0.5},
            {"valence": am.ATTACK, "source": "n3", "target": "n1", "weight": 0.4},
            {"valence": am.ATTACK, "source": "n2", "target": "n1", "weight": 0.4},
            {"valence": am.ATTACK, "source": "n3", "target": "n2", "weight": 0.3},
            {"valence": am.ATTACK, "source": "n2", "target": "n3", "weight": 0.3},
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
                "text": "Bob should buy a Mercedes for its reliability and affordability.",
                "label": "Buy Mercedes for reliability and affordability",
                "annotations": [],
                "node_type": "central_claim",
                "id": "e336b830-ed2d-4d31-8b92-fcf787e4e4a3",
            },
            {
                "text": "Mercedes is known for its high-quality engineering and durability.",
                "label": "Reliability",
                "annotations": [],
                "node_type": "reason",
                "id": "65f53a2c-2214-493d-a700-6de864a7015a",
            },
            {
                "text": "Mercedes cars tend to have a high resale value.",
                "label": "Resale value",
                "annotations": [],
                "node_type": "reason",
                "id": "c9001e2b-289e-4ae9-bc1d-22abf769397f",
            },
            {
                "text": (
                    "Bob should consider buying a used car from a different brand that "
                    "offers similar quality and features at a lower price."
                ),
                "label": "Consider alternatives",
                "annotations": [],
                "node_type": "reason",
                "id": "fc5dc7e4-06ca-46b7-b49e-fb44302de6b4",
            },
            {
                "text": "Bob should also consider leasing a car.",
                "label": "Lease a car",
                "annotations": [],
                "node_type": "reason",
                "id": "3a1cb3eb-fd63-4a2c-9b63-1f72deeea327",
            },
            {
                "text": (
                    "Mercedes offers a range of fuel-efficient models, but some of their larger, "
                    "more powerful models may have lower fuel efficiency."
                ),
                "label": "Fuel efficiency",
                "annotations": [],
                "node_type": "reason",
                "id": "24c9846b-4aa3-4450-9ca5-84ad0b5192da",
            },
            {
                "text": (
                    "Mercedes cars are generally more expensive than other brands, "
                    "both in terms of the initial purchase price and maintenance costs."
                ),
                "label": "Initial Purchase Price",
                "annotations": [],
                "node_type": "reason",
                "id": "669b09af-da38-4fdb-b1fa-d33cc33ff76a",
            },
            {
                "text": (
                    "Mercedes cars are generally more expensive than other brands, "
                    "both in terms of the initial purchase price and maintenance costs."
                ),
                "label": "Maintenance Costs",
                "annotations": [],
                "node_type": "reason",
                "id": "74f75d75-9303-45ce-8028-d083f3188d2b",
            },
        ],
        "links": [
            {
                "weight": 0.4323806289563452,
                "valence": "support",
                "in_forest": True,
                "source": "65f53a2c-2214-493d-a700-6de864a7015a",
                "target": "e336b830-ed2d-4d31-8b92-fcf787e4e4a3",
            },
            {
                "weight": 0.20880087102865005,
                "valence": "support",
                "in_forest": True,
                "source": "c9001e2b-289e-4ae9-bc1d-22abf769397f",
                "target": "65f53a2c-2214-493d-a700-6de864a7015a",
            },
            {
                "weight": 0.001998136532828182,
                "valence": "support",
                "in_forest": True,
                "source": "fc5dc7e4-06ca-46b7-b49e-fb44302de6b4",
                "target": "669b09af-da38-4fdb-b1fa-d33cc33ff76a",
            },
            {
                "weight": 0.00909152296896161,
                "valence": "support",
                "in_forest": True,
                "source": "3a1cb3eb-fd63-4a2c-9b63-1f72deeea327",
                "target": "fc5dc7e4-06ca-46b7-b49e-fb44302de6b4",
            },
            {
                "weight": 0.18145458455605762,
                "valence": "attack",
                "in_forest": True,
                "source": "24c9846b-4aa3-4450-9ca5-84ad0b5192da",
                "target": "e336b830-ed2d-4d31-8b92-fcf787e4e4a3",
            },
            {
                "weight": 0.5301199994421609,
                "valence": "attack",
                "in_forest": True,
                "source": "669b09af-da38-4fdb-b1fa-d33cc33ff76a",
                "target": "e336b830-ed2d-4d31-8b92-fcf787e4e4a3",
            },
            {
                "weight": 0.5609494295759642,
                "valence": "attack",
                "in_forest": True,
                "source": "74f75d75-9303-45ce-8028-d083f3188d2b",
                "target": "e336b830-ed2d-4d31-8b92-fcf787e4e4a3",
            },
            {
                "valence": "support",
                "weight": 0.13831632786433226,
                "in_forest": False,
                "source": "74f75d75-9303-45ce-8028-d083f3188d2b",
                "target": "669b09af-da38-4fdb-b1fa-d33cc33ff76a",
            },
        ],
    }
    nx_graph = nx.node_link_graph(data)
    return nx_graph


def test_fuzzyarggraph(nx_map1):
    arggraph = am.FuzzyArgGraph(nx_map1)
    assert len(arggraph.central_claims()) == 2
    assert set(arggraph.supporting_reasons("n0")) == {"n3", "n2"}
    assert set(arggraph.attacking_reasons("n0")) == set()
    assert set(arggraph.supporting_reasons("n1")) == set()
    assert set(arggraph.attacking_reasons("n1")) == {"n3", "n2"}
    assert set(arggraph.attacking_reasons("n2")) == {"n3"}


def test_fuzzyarggraph2(nx_map2):
    arggraph = am.FuzzyArgGraph(nx_map2)
    assert set(arggraph.attacking_reasons("e336b830-ed2d-4d31-8b92-fcf787e4e4a3")) == {
        "24c9846b-4aa3-4450-9ca5-84ad0b5192da",
        "669b09af-da38-4fdb-b1fa-d33cc33ff76a",
        "74f75d75-9303-45ce-8028-d083f3188d2b",
    }
