# test score function

from logikon.analysts.reconstruction.pros_cons_builder_lcel import ProsConsBuilderLCEL
from logikon.analysts.registry import get_analyst_registry
from logikon.schemas.configs import ScoreConfig


def test_configs():
    config = ScoreConfig()
    assert "argmap_size" in config.metrics
    assert len(config.artifacts) == 0

    config = ScoreConfig(
        global_kwargs={
            "inference_server_url": "localhost",
            "expert_model": "gpt3",
        }
    )
    assert config.global_kwargs["expert_model"] == "gpt3"


def test_config_overwrite_global():
    config = ScoreConfig(
        global_kwargs={
            "inference_server_url": "localhost",
            "expert_model": "gpt2",
        },
        analyst_configs={
            "ProsConsBuilderLCEL": {"inference_server_url": "huggingface.co"},
        },
    )
    config = config.cast(get_analyst_registry())

    assert config.get_analyst_config(ProsConsBuilderLCEL).inference_server_url == "huggingface.co"
