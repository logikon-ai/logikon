# test score function
import asyncio
from typing import ClassVar, Type

from logikon.analysts.base import (
    AbstractArtifactAnalyst,
    AbstractScoreAnalyst,
    ArtifcatAnalystConfig,
    ScoreAnalystConfig,
)
from logikon.schemas.results import INPUT_KWS, AnalysisState, Artifact, Score


class DummyAnalystConfig(ArtifcatAnalystConfig):
    pass


class DummyAnalystConfig2(ScoreAnalystConfig):
    pass


class DummyAnalyst1(AbstractArtifactAnalyst):
    """Dummy Analyst"""

    __pdescription__ = "dummy_analyst1"
    __product__ = "dummy_artifact1"
    __configclass__: Type[ArtifcatAnalystConfig] = DummyAnalystConfig

    async def _analyze(self, analysis_state: AnalysisState):
        prompt, completion = analysis_state.get_prompt_completion()
        """Concat prompt and completion."""
        data = prompt + completion if prompt and completion else "None"
        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=data,
        )
        analysis_state.artifacts.append(artifact)


class DummyAnalyst2(AbstractScoreAnalyst):
    """Dummy Analyst"""

    __pdescription__ = "dummy_analyst2"
    __product__ = "dummy_metric2"
    __requirements__: ClassVar[list[str | set]] = ["dummy_artifact1"]
    __configclass__: Type[ScoreAnalystConfig] = DummyAnalystConfig2

    async def _analyze(self, analysis_state: AnalysisState):
        """Length of prompt."""
        prompt, _ = analysis_state.get_prompt_completion()
        value = len(prompt) if prompt else 0
        score = Score(
            id=self.get_product(),
            description=self.get_description(),
            value=value,
        )
        analysis_state.scores.append(score)


def test_analyst_pipeline():
    config = DummyAnalystConfig()
    config2 = DummyAnalystConfig2()

    analyst1 = DummyAnalyst1(config)
    analyst2 = DummyAnalyst2(config2)

    prompt = "01234"
    completion = "56789"

    inputs = []
    inputs.append(Artifact(id=INPUT_KWS.prompt, description="Prompt", data=prompt, dtype="str"))
    inputs.append(Artifact(id=INPUT_KWS.completion, description="Completion", data=completion, dtype="str"))

    # manual pipeline
    async def pipeline(inputs):
        results = AnalysisState(inputs=inputs)
        results = await analyst1(analysis_state=results)
        results = await analyst2(analysis_state=results)
        return results

    results = asyncio.run(pipeline(inputs))

    assert len(results.artifacts) == 1
    assert len(results.scores) == 1

    assert results.artifacts[0].data == prompt + completion
    assert results.scores[0].value == len(prompt)
