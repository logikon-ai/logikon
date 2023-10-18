from __future__ import annotations

from typing import Mapping, List

from logikon.debuggers.base import Debugger, AbstractScoreDebugger, AbstractArtifactDebugger
from logikon.debuggers.exporters.networkx_exporter import NetworkXExporter
from logikon.debuggers.exporters.svgmap_exporter import SVGMapExporter
from logikon.debuggers.reconstruction.claim_extractor import ClaimExtractor
from logikon.debuggers.reconstruction.informal_argmap_builder import InformalArgMapBuilder
from logikon.debuggers.reconstruction.issue_builder_lmql import IssueBuilderLMQL
from logikon.debuggers.reconstruction.pros_cons_builder_lmql import ProsConsBuilderLMQL
from logikon.debuggers.scorers.argmap_graph_scores import (
    ArgMapGraphAttackRatioScorer,
    ArgMapGraphAvgKatzCScorer,
    ArgMapGraphSizeScorer,
)

# First class is treated as default debugger
_DEBUGGER_REGISTRY: Mapping[str, List[type[Debugger]]] = {
    "informal_argmap": [InformalArgMapBuilder],
    "claims": [ClaimExtractor],
    "issue": [IssueBuilderLMQL],
    "proscons": [ProsConsBuilderLMQL],
    "networkx_graph": [NetworkXExporter],
    "svg_argmap": [SVGMapExporter],
    "argmap_size": [ArgMapGraphSizeScorer],
    "argmap_avg_katz_centrality": [ArgMapGraphAvgKatzCScorer],
    "argmap_attack_ratio": [ArgMapGraphAttackRatioScorer],
}


def get_debugger_registry() -> Mapping[str, List[type[Debugger]]]:
    """Get the debugger registry."""
    # sanity checks
    for keyword, debuggers in _DEBUGGER_REGISTRY.items():
        assert debuggers
        assert all(issubclass(d, Debugger) for d in debuggers)
        assert all(d.get_product() == keyword for d in debuggers)
        if issubclass(debuggers[0], AbstractArtifactDebugger):
            assert all(issubclass(d, AbstractArtifactDebugger) for d in debuggers)
        if issubclass(debuggers[0], AbstractScoreDebugger):
            assert all(issubclass(d, AbstractScoreDebugger) for d in debuggers)

    return _DEBUGGER_REGISTRY
