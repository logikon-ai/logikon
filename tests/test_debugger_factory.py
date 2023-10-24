# test score function

from logikon.debuggers.base import AbstractArtifactDebugger, AbstractDebugger, AbstractScoreDebugger
from logikon.debuggers.reconstruction.fuzzy_argmap_builder import FuzzyArgMapBuilder
from logikon.debuggers.factory import DebuggerFactory, get_debugger_registry
from logikon.schemas.configs import ScoreConfig


def test_debugger_factory():
    registry = get_debugger_registry()

    for product_kw, debugger_classes in registry.items():
        for debugger_class in debugger_classes:
            print(f"Testing: {product_kw}: {debugger_class}")
            artifacts = []
            metrics = []
            if issubclass(debugger_class, AbstractArtifactDebugger):
                artifacts.append(product_kw)
            elif issubclass(debugger_class, AbstractScoreDebugger):
                metrics.append(product_kw)
            else:
                print("Unknown debugger class type")
                raise AssertionError()

            config = ScoreConfig(
                metrics=metrics,
                artifacts=artifacts,
                global_kwargs=dict(
                    expert_model="text-ada-002",
                    llm_framework="OpenAI",
                )
            )

            debug_chain, _ = DebuggerFactory().create(config)
            assert callable(debug_chain)


def test_debugger_factory2():
    config = ScoreConfig(
        global_kwargs=dict(
            expert_model="text-ada-002",
            llm_framework="OpenAI",
        )
    )
    debug_chain, _ = DebuggerFactory().create(config)
    assert callable(debug_chain)


def test_debugger_factory3():
    config = ScoreConfig(
        artifacts=["svg_argmap", "fuzzy_argmap_nx", "relevance_network_nx"],
        global_kwargs=dict(
            expert_model="text-ada-002",
            llm_framework="OpenAI",
        )
    )
    debug_chain, _ = DebuggerFactory().create(config)
    assert callable(debug_chain)


def test_altern_requirements():
    config = ScoreConfig(
        artifacts=["svg_argmap"],
        global_kwargs=dict(
            expert_model="text-ada-002",
            llm_framework="OpenAI",
        )
    )
    debug_chain, pipeline = DebuggerFactory().create(config)

    print(pipeline)

    assert callable(debug_chain)
    assert pipeline
    assert any(isinstance(debugger, FuzzyArgMapBuilder) for debugger in pipeline)
