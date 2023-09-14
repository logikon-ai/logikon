# test score function

import pytest

from dotenv import load_dotenv

from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugResults
from logikon.debuggers.reconstruction.claim_extractor import ClaimExtractor

load_dotenv()  # load environment variables from .env file

def test_claim_extractor01():
    config = DebugConfig(
        #llm_framework="LlamaCpp",
        #expert_model="/Users/gregorbetz/git/lmql-tests/llama.cpp/models/7B/Llama-2-7b-orca-v1/ggml-model-q4_0.bin",
        #expert_model="text-ada-001",
        llm_framework="VLLM",
        expert_model="OpenAssistant/codellama-13b-oasst-sft-v10",
        expert_model_kwargs=dict(temperature=0.9, max_new_tokens=256, trust_remote_code=True),
    )
    print(config)
    debugger = ClaimExtractor(config)
    
    prompt = "Vim or emacs? reason carefully!"
    completion = "Vim is lighter, emacs is stronger. Therefore: Vim."
    results = DebugResults()

    debugger._debug(prompt=prompt, completion=completion, debug_results=results)

    print(results.artifacts)

    assert results.artifacts[0].id == "claims"

