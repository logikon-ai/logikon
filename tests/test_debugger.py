# test score function
from typing import List, Optional

import pytest

from logikon.debuggers.base import AbstractArtifactDebugger, AbstractScoreDebugger
from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import Artifact, DebugResults, Score


class DummyDebugger1(AbstractArtifactDebugger):
    """Dummy Debugger"""

    _KW_DESCRIPTION = "dummy_debugger1"
    _KW_PRODUCT = "dummy_artifact1"
    _KW_REQUIREMENTS: List[str] = []

    @staticmethod
    def get_product() -> str:
        return DummyDebugger1._KW_PRODUCT

    @staticmethod
    def get_requirements() -> List[str]:
        return DummyDebugger1._KW_REQUIREMENTS

    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Concat prompt and completion."""
        assert debug_results is not None
        data = prompt + completion
        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=data,
        )
        debug_results.artifacts.append(artifact)


class DummyDebugger2(AbstractScoreDebugger):
    """Dummy Debugger"""

    _KW_DESCRIPTION = "dummy_debugger2"
    _KW_PRODUCT = "dummy_metric2"
    _KW_REQUIREMENTS = ["dummy_artifact1"]

    @staticmethod
    def get_product() -> str:
        return DummyDebugger2._KW_PRODUCT

    @staticmethod
    def get_requirements() -> List[str]:
        return DummyDebugger2._KW_REQUIREMENTS

    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Length of prompt."""
        assert debug_results is not None
        value = len(prompt)
        score = Score(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            score=value,
        )
        debug_results.scores.append(score)


def test_debugger_chaining():
    config = DebugConfig()
    debugger1 = DummyDebugger1(config)
    debugger1.set_next(DummyDebugger2(config))

    prompt = "01234"
    completion = "56789"

    results = debugger1.handle(prompt=prompt, completion=completion)

    assert len(results.artifacts) == 1
    assert len(results.scores) == 1

    assert results.artifacts[0].data == prompt + completion
    assert results.scores[0].score == len(prompt)
