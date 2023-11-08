# test score function

from logikon.analysts.base import AbstractArtifactAnalyst, AbstractScoreAnalyst
from logikon.analysts.director import Director, get_analyst_registry
from logikon.analysts.reconstruction.fuzzy_argmap_builder import FuzzyArgMapBuilder
from logikon.schemas.configs import ScoreConfig


def test_analyst_factory():
    registry = get_analyst_registry()

    for product_kw, analyst_classes in registry.items():
        for analyst_class in analyst_classes:
            print(f"Testing: {product_kw}: {analyst_class}")  # noqa: T201
            artifacts = []
            metrics = []
            if issubclass(analyst_class, AbstractArtifactAnalyst):
                artifacts.append(product_kw)
            elif issubclass(analyst_class, AbstractScoreAnalyst):
                metrics.append(product_kw)
            else:
                print("Unknown analyst class type")  # noqa: T201
                raise AssertionError()

            config = ScoreConfig(
                metrics=metrics,
                artifacts=artifacts,
                global_kwargs={
                    "expert_model": "text-ada-002",
                    "llm_framework": "OpenAI",
                },
            )

            pipeline, _ = Director().create(config)
            assert callable(pipeline)


def test_analyst_factory2():
    config = ScoreConfig(
        global_kwargs={
            "expert_model": "text-ada-002",
            "llm_framework": "OpenAI",
        }
    )
    pipeline, _ = Director().create(config)
    assert callable(pipeline)


def test_analyst_factory3():
    config = ScoreConfig(
        artifacts=["svg_argmap", "fuzzy_argmap_nx", "relevance_network_nx"],
        global_kwargs={
            "expert_model": "text-ada-002",
            "llm_framework": "OpenAI",
        },
    )
    pipeline, _ = Director().create(config)
    assert callable(pipeline)


def test_altern_requirements():
    config = ScoreConfig(
        artifacts=["svg_argmap"],
        global_kwargs={
            "expert_model": "text-ada-002",
            "llm_framework": "OpenAI",
        },
    )
    pipeline, chain = Director().create(config)

    print(chain)  # noqa: T201

    assert callable(pipeline)
    assert chain
    assert any(isinstance(analyst, FuzzyArgMapBuilder) for analyst in chain)
