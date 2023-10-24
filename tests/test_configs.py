# test score function

from logikon.schemas.configs import ScoreConfig


def test_configs():
    config = ScoreConfig()
    assert "proscons" in config.artifacts

    config = ScoreConfig(
        global_kwargs=dict(
            expert_model="text-ada-002",
            llm_framework="VLLM",
        )
    )
    assert config.global_kwargs["expert_model"] == "text-ada-002"
