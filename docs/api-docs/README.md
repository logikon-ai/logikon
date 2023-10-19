<!-- markdownlint-disable -->

# API Overview

## Modules

- [`logikon.debuggers`](./logikon.debuggers.md#module-logikondebuggers)
- [`logikon.debuggers.base`](./logikon.debuggers.base.md#module-logikondebuggersbase)
- [`logikon.debuggers.exporters`](./logikon.debuggers.exporters.md#module-logikondebuggersexporters)
- [`logikon.debuggers.exporters.networkx_exporter`](./logikon.debuggers.exporters.networkx_exporter.md#module-logikondebuggersexportersnetworkx_exporter)
- [`logikon.debuggers.exporters.svgmap_exporter`](./logikon.debuggers.exporters.svgmap_exporter.md#module-logikondebuggersexporterssvgmap_exporter)
- [`logikon.debuggers.factory`](./logikon.debuggers.factory.md#module-logikondebuggersfactory)
- [`logikon.debuggers.interface`](./logikon.debuggers.interface.md#module-logikondebuggersinterface)
- [`logikon.debuggers.model_registry`](./logikon.debuggers.model_registry.md#module-logikondebuggersmodel_registry)
- [`logikon.debuggers.registry`](./logikon.debuggers.registry.md#module-logikondebuggersregistry)
- [`logikon.debuggers.scorers`](./logikon.debuggers.scorers.md#module-logikondebuggersscorers)
- [`logikon.debuggers.scorers.argmap_graph_scores`](./logikon.debuggers.scorers.argmap_graph_scores.md#module-logikondebuggersscorersargmap_graph_scores)
- [`logikon.debuggers.utils`](./logikon.debuggers.utils.md#module-logikondebuggersutils)
- [`logikon.schemas`](./logikon.schemas.md#module-logikonschemas)
- [`logikon.schemas.argument_mapping`](./logikon.schemas.argument_mapping.md#module-logikonschemasargument_mapping)
- [`logikon.schemas.configs`](./logikon.schemas.configs.md#module-logikonschemasconfigs)
- [`logikon.schemas.pros_cons`](./logikon.schemas.pros_cons.md#module-logikonschemaspros_cons): Data Models for Pros & Cons Lists
- [`logikon.schemas.results`](./logikon.schemas.results.md#module-logikonschemasresults)
- [`logikon.score`](./logikon.score.md#module-logikonscore)

## Classes

- [`base.AbstractArtifactDebugger`](./logikon.debuggers.base.md#class-abstractartifactdebugger): Base debugger class for creating artifacts.
- [`base.AbstractDebugger`](./logikon.debuggers.base.md#class-abstractdebugger): Base debugger class with default __call__ implementation.
- [`base.AbstractScoreDebugger`](./logikon.debuggers.base.md#class-abstractscoredebugger): Base debugger class for creating scroes.
- [`networkx_exporter.NetworkXExporter`](./logikon.debuggers.exporters.networkx_exporter.md#class-networkxexporter): NetworkXExporter Debugger
- [`svgmap_exporter.SVGMapExporter`](./logikon.debuggers.exporters.svgmap_exporter.md#class-svgmapexporter): SVGMapExporter Debugger
- [`factory.DebuggerFactory`](./logikon.debuggers.factory.md#class-debuggerfactory): Factory for creating a debugger pipeline based on a config.
- [`interface.Debugger`](./logikon.debuggers.interface.md#class-debugger): Abstract base class for all debuggers.
- [`argmap_graph_scores.AbstractGraphScorer`](./logikon.debuggers.scorers.argmap_graph_scores.md#class-abstractgraphscorer): AbstractGraphScorer Debugger
- [`argmap_graph_scores.ArgMapGraphAttackRatioScorer`](./logikon.debuggers.scorers.argmap_graph_scores.md#class-argmapgraphattackratioscorer)
- [`argmap_graph_scores.ArgMapGraphAvgKatzCScorer`](./logikon.debuggers.scorers.argmap_graph_scores.md#class-argmapgraphavgkatzcscorer)
- [`argmap_graph_scores.ArgMapGraphSizeScorer`](./logikon.debuggers.scorers.argmap_graph_scores.md#class-argmapgraphsizescorer)
- [`argument_mapping.AnnotationSpan`](./logikon.schemas.argument_mapping.md#class-annotationspan)
- [`argument_mapping.ArgMapEdge`](./logikon.schemas.argument_mapping.md#class-argmapedge)
- [`argument_mapping.ArgMapNode`](./logikon.schemas.argument_mapping.md#class-argmapnode)
- [`argument_mapping.InformalArgMap`](./logikon.schemas.argument_mapping.md#class-informalargmap)
- [`configs.DebugConfig`](./logikon.schemas.configs.md#class-debugconfig): Configuration for scoring reasoning traces.
- [`pros_cons.Claim`](./logikon.schemas.pros_cons.md#class-claim)
- [`pros_cons.ProsConsList`](./logikon.schemas.pros_cons.md#class-prosconslist)
- [`pros_cons.RootClaim`](./logikon.schemas.pros_cons.md#class-rootclaim)
- [`results.Artifact`](./logikon.schemas.results.md#class-artifact): An artifact serving as input and/or generated through logical debugging.
- [`results.BaseCTModel`](./logikon.schemas.results.md#class-basectmodel): Base model for all entities processed or created through logical analysis.
- [`results.DebugState`](./logikon.schemas.results.md#class-debugstate): Scores for the completion.
- [`results.Score`](./logikon.schemas.results.md#class-score): A score for a completion / reasoning trace.

## Functions

- [`model_registry.get_registry_model`](./logikon.debuggers.model_registry.md#function-get_registry_model)
- [`model_registry.register_model`](./logikon.debuggers.model_registry.md#function-register_model)
- [`registry.get_debugger_registry`](./logikon.debuggers.registry.md#function-get_debugger_registry): Get the debugger registry.
- [`utils.init_llm_from_config`](./logikon.debuggers.utils.md#function-init_llm_from_config)
- [`score.score`](./logikon.score.md#function-score): Score the completion.


---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
