# test score function

import pytest

from dotenv import load_dotenv

from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugResults, Artifact
from logikon.debuggers.reconstruction.informal_arg_map import InformalArgMap

load_dotenv()  # load environment variables from .env file

def test_informal_argmap01():
    config = DebugConfig(
        #llm_framework="LlamaCpp",
        #expert_model="/Users/gregorbetz/git/lmql-tests/llama.cpp/models/7B/Llama-2-7b-orca-v1/ggml-model-q4_0.bin",
        #expert_model="text-ada-001",
        llm_framework="VLLM",
        expert_model="circulus/Llama-2-7b-orca-v1",
    )
    print(config)
    debugger = InformalArgMap(config)
    
    prompt = "Vim or emacs? reason carefully!"
    completion = "Vim is lighter, emacs is stronger. Therefore: Vim."
    claims = ["Vim is better than emacs."]

    results = DebugResults(artifacts=[Artifact(id="claims", description="mece claims", data=claims)])

    debugger._debug(prompt=prompt, completion=completion, debug_results=results)

    print(results.artifacts)

    assert results.artifacts[-1].id == "informal_argmap"

