from __future__ import annotations

from typing import Mapping, List, Type

from logikon.analysts.base import Analyst, AbstractScoreAnalyst, AbstractArtifactAnalyst
from logikon.analysts.export.networkx_exporter import RelevanceNetworkNXExporter
from logikon.analysts.export.svgmap_exporter import SVGMapExporter
from logikon.analysts.export.htmlsunburst_exporter import HTMLSunburstExporter
from logikon.analysts.reconstruction.issue_builder_lmql import IssueBuilderLMQL
from logikon.analysts.reconstruction.pros_cons_builder_lmql import ProsConsBuilderLMQL
from logikon.analysts.reconstruction.relevance_network_builder_lmql import RelevanceNetworkBuilderLMQL
from logikon.analysts.reconstruction.fuzzy_argmap_builder import FuzzyArgMapBuilder
from logikon.analysts.score.argmap_graph_scores import (
    ArgMapGraphAttackRatioScorer,
    ArgMapGraphAvgKatzCScorer,
    ArgMapGraphSizeScorer,
)

# TODO: set up a product registry for storing product_kw/product_cls mapping


# First class is treated as default analyst
_ANALYST_REGISTRY: Mapping[str, List[type[Analyst]]] = {
    "issue": [IssueBuilderLMQL],
    "proscons": [ProsConsBuilderLMQL],
    "relevance_network": [RelevanceNetworkBuilderLMQL],
    "relevance_network_nx": [RelevanceNetworkNXExporter],
    "fuzzy_argmap_nx": [FuzzyArgMapBuilder],
    "svg_argmap": [SVGMapExporter],
    "html_sunburst": [HTMLSunburstExporter],
    "argmap_size": [ArgMapGraphSizeScorer],
    "argmap_avg_katz_centrality": [ArgMapGraphAvgKatzCScorer],
    "argmap_attack_ratio": [ArgMapGraphAttackRatioScorer],
}


def get_analyst_registry() -> Mapping[str, List[type[Analyst]]]:
    """Get the analyst registry."""
    # sanity checks
    for keyword, analysts in _ANALYST_REGISTRY.items():
        assert analysts
        assert all(issubclass(d, Analyst) for d in analysts)
        assert all(d.get_product() == keyword for d in analysts)
        if issubclass(analysts[0], AbstractArtifactAnalyst):
            assert all(issubclass(d, AbstractArtifactAnalyst) for d in analysts)
        if issubclass(analysts[0], AbstractScoreAnalyst):
            assert all(issubclass(d, AbstractScoreAnalyst) for d in analysts)

    return _ANALYST_REGISTRY
