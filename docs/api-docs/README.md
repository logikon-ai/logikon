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
- [`logikon.debuggers.reconstruction`](./logikon.debuggers.reconstruction.md#module-logikondebuggersreconstruction)
- [`logikon.debuggers.reconstruction.claim_extractor`](./logikon.debuggers.reconstruction.claim_extractor.md#module-logikondebuggersreconstructionclaim_extractor)
- [`logikon.debuggers.reconstruction.informal_argmap_builder`](./logikon.debuggers.reconstruction.informal_argmap_builder.md#module-logikondebuggersreconstructioninformal_argmap_builder)
- [`logikon.debuggers.reconstruction.issue_builder_lmql`](./logikon.debuggers.reconstruction.issue_builder_lmql.md#module-logikondebuggersreconstructionissue_builder_lmql)
- [`logikon.debuggers.reconstruction.lmql_debugger`](./logikon.debuggers.reconstruction.lmql_debugger.md#module-logikondebuggersreconstructionlmql_debugger)
- [`logikon.debuggers.reconstruction.lmql_queries`](./logikon.debuggers.reconstruction.lmql_queries.md#module-logikondebuggersreconstructionlmql_queries): LMQL Queries shared by Logikon Reconstruction Debuggers
- [`logikon.debuggers.reconstruction.pros_cons_builder_lmql`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#module-logikondebuggersreconstructionpros_cons_builder_lmql): Module with debugger for building a pros & cons list with LMQL
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
- [`claim_extractor.ClaimExtractionChain`](./logikon.debuggers.reconstruction.claim_extractor.md#class-claimextractionchain)
- [`claim_extractor.ClaimExtractor`](./logikon.debuggers.reconstruction.claim_extractor.md#class-claimextractor): ClaimExtractor Debugger
- [`claim_extractor.PromptRegistry`](./logikon.debuggers.reconstruction.claim_extractor.md#class-promptregistry): A registry of prompts to be used in the deliberation process.
- [`claim_extractor.PromptRegistryFactory`](./logikon.debuggers.reconstruction.claim_extractor.md#class-promptregistryfactory): Creates Prompt Registries
- [`informal_argmap_builder.InformalArgMapBuilder`](./logikon.debuggers.reconstruction.informal_argmap_builder.md#class-informalargmapbuilder): InformalArgMap Debugger
- [`informal_argmap_builder.InformalArgMapChain`](./logikon.debuggers.reconstruction.informal_argmap_builder.md#class-informalargmapchain)
- [`informal_argmap_builder.PromptRegistry`](./logikon.debuggers.reconstruction.informal_argmap_builder.md#class-promptregistry): A registry of prompts to be used in building an informal argmap.
- [`informal_argmap_builder.PromptRegistryFactory`](./logikon.debuggers.reconstruction.informal_argmap_builder.md#class-promptregistryfactory): Creates Prompt Registries
- [`issue_builder_lmql.IssueBuilderLMQL`](./logikon.debuggers.reconstruction.issue_builder_lmql.md#class-issuebuilderlmql): IssueBuilderLMQL
- [`lmql_debugger.LMQLDebugger`](./logikon.debuggers.reconstruction.lmql_debugger.md#class-lmqldebugger): LMQLDebugger
- [`pros_cons_builder_lmql.ProsConsBuilderLMQL`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#class-prosconsbuilderlmql): ProsConsBuilderLMQL
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
- [`issue_builder_lmql.key_issue`](./logikon.debuggers.reconstruction.issue_builder_lmql.md#function-key_issue):     sample(n=3, temperature=.4)
- [`issue_builder_lmql.rate_issue_drafts`](./logikon.debuggers.reconstruction.issue_builder_lmql.md#function-rate_issue_drafts): lmql
- [`issue_builder_lmql.strip_issue_tag`](./logikon.debuggers.reconstruction.issue_builder_lmql.md#function-strip_issue_tag): Strip issue tag from text.
- [`lmql_queries.attacks_q`](./logikon.debuggers.reconstruction.lmql_queries.md#function-attacks_q): lmql
- [`lmql_queries.get_distribution`](./logikon.debuggers.reconstruction.lmql_queries.md#function-get_distribution): Extracts the distribution from an LMQL result
- [`lmql_queries.label_to_claim`](./logikon.debuggers.reconstruction.lmql_queries.md#function-label_to_claim)
- [`lmql_queries.label_to_idx`](./logikon.debuggers.reconstruction.lmql_queries.md#function-label_to_idx)
- [`lmql_queries.label_to_valence`](./logikon.debuggers.reconstruction.lmql_queries.md#function-label_to_valence)
- [`lmql_queries.most_confirmed`](./logikon.debuggers.reconstruction.lmql_queries.md#function-most_confirmed): lmql
- [`lmql_queries.most_disconfirmed`](./logikon.debuggers.reconstruction.lmql_queries.md#function-most_disconfirmed): lmql
- [`lmql_queries.supports_q`](./logikon.debuggers.reconstruction.lmql_queries.md#function-supports_q): lmql
- [`lmql_queries.system_prompt`](./logikon.debuggers.reconstruction.lmql_queries.md#function-system_prompt): Returns the system prompt used in all lmql queries
- [`lmql_queries.valence`](./logikon.debuggers.reconstruction.lmql_queries.md#function-valence): lmql
- [`pros_cons_builder_lmql.add_unused_reasons`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#function-add_unused_reasons): lmql
- [`pros_cons_builder_lmql.build_pros_and_cons`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#function-build_pros_and_cons): lmql
- [`pros_cons_builder_lmql.format_examples`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#function-format_examples)
- [`pros_cons_builder_lmql.format_proscons`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#function-format_proscons)
- [`pros_cons_builder_lmql.format_reason`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#function-format_reason)
- [`pros_cons_builder_lmql.mine_reasons`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#function-mine_reasons): lmql
- [`pros_cons_builder_lmql.unpack_reason`](./logikon.debuggers.reconstruction.pros_cons_builder_lmql.md#function-unpack_reason): lmql
- [`registry.get_debugger_registry`](./logikon.debuggers.registry.md#function-get_debugger_registry): Get the debugger registry.
- [`utils.init_llm_from_config`](./logikon.debuggers.utils.md#function-init_llm_from_config)
- [`score.score`](./logikon.score.md#function-score): Score the completion.


---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
