# test score function

from logikon.analysts.reconstruction.pros_cons_builder_lmql import ProsConsBuilderLMQL
from logikon.analysts.registry import get_analyst_registry
from logikon.schemas.configs import ScoreConfig


def test_configs():
    config = ScoreConfig()
    assert "argmap_size" in config.metrics
    assert len(config.artifacts) == 0

    config = ScoreConfig(
        global_kwargs={
            "expert_model": "text-ada-002",
            "llm_framework": "OpenAI",
        }
    )
    assert config.global_kwargs["expert_model"] == "text-ada-002"


def test_config_overwrite_global():
    config = ScoreConfig(
        global_kwargs={
            "expert_model": "text-ada-002",
            "llm_framework": "OpenAI",
        },
        analyst_configs={
            "ProsConsBuilderLMQL": {"llm_framework": "transformers"},
        },
    )
    config = config.cast(get_analyst_registry())

    assert config.get_analyst_config(ProsConsBuilderLMQL).llm_framework == "transformers"
