from __future__ import annotations

from typing import Type, Mapping

from logikon.debuggers.base import Debugger
from logikon.debuggers.reconstruction.informal_argmap_builder import InformalArgMapBuilder
from logikon.debuggers.reconstruction.claim_extractor import ClaimExtractor
from logikon.debuggers.exporters.networkx_exporter import NetworkXExporter
from logikon.debuggers.exporters.svgmap_exporter import SVGMapExporter
from logikon.debuggers.scorers.argmap_graph_scores import (
    ArgMapGraphSizeScorer,
    ArgMapGraphAvgKatzCScorer,
    ArgMapGraphAttackRatioScorer,
)

_DEBUGGER_REGISTRY = {
    "informal_argmap": InformalArgMapBuilder,
    "claims": ClaimExtractor,
    "networkx_graph": NetworkXExporter,
    "svg_argmap": SVGMapExporter,
    "argmap_size": ArgMapGraphSizeScorer,
    "argmap_avg_katz_centrality": ArgMapGraphAvgKatzCScorer,
    "argmap_attack_ratio": ArgMapGraphAttackRatioScorer,
}

def get_debugger_registry() -> Mapping[str, Type[Debugger]]:
    """Get the debugger registry."""
    # sanity checks
    for keyword, debugger in _DEBUGGER_REGISTRY.items():
        assert issubclass(debugger, Debugger)
        assert debugger.get_product() == keyword

    return _DEBUGGER_REGISTRY