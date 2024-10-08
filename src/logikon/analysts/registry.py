from __future__ import annotations

from typing import Mapping

from logikon.analysts.base import AbstractArtifactAnalyst, AbstractScoreAnalyst, Analyst
from logikon.analysts.export.htmlsunburst_exporter import HTMLSunburstExporter
from logikon.analysts.export.networkx_exporter import RelevanceNetworkNXExporter
from logikon.analysts.export.svgmap_exporter import SVGMapExporter
from logikon.analysts.reconstruction.fuzzy_argmap_builder import FuzzyArgMapBuilder
from logikon.analysts.reconstruction.issue_builder_lcel import IssueBuilderLCEL
from logikon.analysts.reconstruction.pros_cons_builder_lcel import ProsConsBuilderLCEL
from logikon.analysts.reconstruction.relevance_network_builder_lcel import RelevanceNetworkBuilderLCEL
from logikon.analysts.score.argmap_graph_scores import (
    ArgMapGraphAttackRatioScorer,
    ArgMapGraphAvgKatzCScorer,
    ArgMapGraphSizeScorer,
    ArgMapRootCountScorer,
    MeanReasonStrengthScorer,
)
from logikon.analysts.score.balance_scores import (
    GlobalBalanceScorer,
    MeanAbsRootSupportScorer,
    MeanRootSupportScorer,
)

# TODO: set up a product registry for storing product_kw/product_cls mapping


# First class is treated as default analyst
_ANALYST_REGISTRY: Mapping[str, list[type[Analyst]]] = {
    "issue": [IssueBuilderLCEL],
    "proscons": [ProsConsBuilderLCEL],
    "relevance_network": [RelevanceNetworkBuilderLCEL],
    "relevance_network_nx": [RelevanceNetworkNXExporter],
    "fuzzy_argmap_nx": [FuzzyArgMapBuilder],
    "svg_argmap": [SVGMapExporter],
    "html_sunburst": [HTMLSunburstExporter],
    "argmap_size": [ArgMapGraphSizeScorer],
    "n_root_nodes": [ArgMapRootCountScorer],
    "argmap_avg_katz_centrality": [ArgMapGraphAvgKatzCScorer],
    "argmap_attack_ratio": [ArgMapGraphAttackRatioScorer],
    "mean_root_support": [MeanRootSupportScorer],
    "mean_absolute_root_support": [MeanAbsRootSupportScorer],
    "global_balance": [GlobalBalanceScorer],
    "mean_reason_strength": [MeanReasonStrengthScorer],
}


def get_analyst_registry() -> Mapping[str, list[type[Analyst]]]:
    """Get the analyst registry."""
    # sanity checks
    for keyword, analysts in _ANALYST_REGISTRY.items():
        if not analysts:
            msg = f"No analysts registered for {keyword}."
            raise ValueError(msg)
        if not all(issubclass(d, Analyst) for d in analysts):
            msg = f"Not all analysts registered for {keyword} are subclasses of Analyst."
            raise ValueError(msg)
        if not all(d.get_product() == keyword for d in analysts):
            msg = f"Not all analysts registered for {keyword} have the correct product type."
            raise ValueError(msg)
        if issubclass(analysts[0], AbstractArtifactAnalyst):
            if not all(issubclass(d, AbstractArtifactAnalyst) for d in analysts):
                msg = f"Not all analysts registered for {keyword} are subclasses of AbstractArtifactAnalyst."
                raise ValueError(msg)
        if issubclass(analysts[0], AbstractScoreAnalyst):
            if not all(issubclass(d, AbstractScoreAnalyst) for d in analysts):
                msg = f"Not all analysts registered for {keyword} are subclasses of AbstractScoreAnalyst."
                raise ValueError(msg)

    return _ANALYST_REGISTRY
