# test score function

import pytest
from dotenv import load_dotenv

from logikon.schemas.configs import DebugConfig
from logikon.score import score


load_dotenv()  # load environment variables from .env file

def test_score1():
    config = DebugConfig(
        llm_framework="VLLM",
        expert_model="circulus/Llama-2-7b-orca-v1",
        expert_model_kwargs=dict(temperature=0.9, max_new_tokens=256, trust_remote_code=True),
    )

    prompt = "Vim or emacs? reason carefully!"
    completion = "Vim is lighter, emacs is stronger. Vim."
    result = score(prompt=prompt, completion=completion, config=config)
    print(result.artifacts)
    assert len(result.artifacts) == 2
    print(result.scores)
    assert len(result.scores) == 0