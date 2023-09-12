# test score function

import pytest

from logikon.schemas.configs import DebugConfig
from logikon.score import score


def test_score1():
    prompt = "Vim or emacs? reason carefully!"
    completion = "Vim is lighter, emacs is stronger. Vim."
    result = score(prompt, completion)
    print(result.artifacts)
    assert len(result.artifacts) == 2
    print(result.scores)
    assert len(result.scores) == 0