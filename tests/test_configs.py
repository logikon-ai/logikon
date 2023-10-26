# test score function

from logikon.schemas.configs import ScoreConfig
from logikon.analysts.registry import get_analyst_registry
from logikon.analysts.reconstruction.pros_cons_builder_lmql import ProsConsBuilderLMQL


def test_configs():
    config = ScoreConfig()
    assert "proscons" in config.artifacts

    config = ScoreConfig(
        global_kwargs=dict(
            expert_model="text-ada-002",
            llm_framework="OpenAI",
        )
    )
    assert config.global_kwargs["expert_model"] == "text-ada-002"



def test_config_overwrite_global():

    config = ScoreConfig(
        global_kwargs=dict(
            expert_model="text-ada-002",
            llm_framework="OpenAI",
        ),
        analyst_configs={
            "ProsConsBuilderLMQL": {"llm_framework": "transformers"},
        },
    )
    config = config.cast(get_analyst_registry())

    assert config.get_analyst_config(ProsConsBuilderLMQL).llm_framework == "transformers"
