# test score function
from typing import List, Optional

import pytest

from logikon.debuggers.base import AbstractArtifactDebugger, AbstractScoreDebugger
from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import Artifact, DebugState, Score, INPUT_KWS


class DummyDebugger1(AbstractArtifactDebugger):
    """Dummy Debugger"""

    __pdescription__ = "dummy_debugger1"
    __product__ = "dummy_artifact1"

    def _debug(self, debug_state: DebugState):
        prompt, completion = debug_state.get_prompt_completion()
        """Concat prompt and completion."""
        data = prompt + completion if prompt and completion else "None"
        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=data,
        )
        debug_state.artifacts.append(artifact)


class DummyDebugger2(AbstractScoreDebugger):
    """Dummy Debugger"""

    __pdescription__ = "dummy_debugger2"
    __product__ = "dummy_metric2"
    __requirements__ = ["dummy_artifact1"]

    def _debug(self, debug_state: DebugState):
        """Length of prompt."""
        prompt, _ = debug_state.get_prompt_completion()
        value = len(prompt) if prompt else 0
        score = Score(
            id=self.get_product(),
            description=self.get_description(),
            value=value,
        )
        debug_state.scores.append(score)


def test_debugger_pipeline():
    config = DebugConfig()

    debugger1 = DummyDebugger1(config)
    debugger2 = DummyDebugger2(config)

    prompt = "01234"
    completion = "56789"

    config.inputs.append(Artifact(id=INPUT_KWS.prompt, description="Prompt", data=prompt, dtype="str"))
    config.inputs.append(Artifact(id=INPUT_KWS.completion, description="Completion", data=completion, dtype="str"))

    # manual pipeline
    results = DebugState(inputs=config.inputs)
    results = debugger1(debug_state=results)
    results = debugger2(debug_state=results)

    assert len(results.artifacts) == 1
    assert len(results.scores) == 1

    assert results.artifacts[0].data == prompt + completion
    assert results.scores[0].value == len(prompt)
