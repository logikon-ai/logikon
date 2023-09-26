# test score function

from logikon.schemas.configs import DebugConfig


def test_configs():
    config = DebugConfig()
    assert config.expert_model == "gpt-3.5-turbo-instruct"

    config = DebugConfig(
        expert_model="text-ada-002",
        llm_framework="VLLM",
    )
    assert config.expert_model == "text-ada-002"
