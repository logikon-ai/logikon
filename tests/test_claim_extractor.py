# test score function

import pytest

from dotenv import load_dotenv

from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugResults
from logikon.debuggers.reconstruction.claim_extractor import ClaimExtractor


load_dotenv()  # load environment variables from .env file


def test_claim_extractor01():
    config = DebugConfig()
    print(config)
    debugger = ClaimExtractor(config)
    
    prompt = "Vim or emacs? reason carefully!"
    completion = "Vim is lighter, emacs is stronger. Therefore: Vim."
    results = DebugResults()

    debugger._debug(prompt=prompt, completion=completion, debug_results=results)

    print(results.artifacts)

    assert results.artifacts[0].id == "claims"

