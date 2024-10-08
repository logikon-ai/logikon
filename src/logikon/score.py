from __future__ import annotations

import asyncio
import copy
from typing import Any, Dict, Generator

from logikon.analysts.director import Director
from logikon.schemas.configs import ScoreConfig
from logikon.schemas.results import AnalysisState, Artifact, Score


class ScoreResult(Dict):
    """Result object of score function."""

    def __init__(self, config: ScoreConfig, state: AnalysisState):
        super().__init__()
        self._config = config
        self._state = state

        # reference score and artifacts objects by id in dict
        for score_r in self._state.scores:
            self[score_r.id] = score_r
        for artifact_r in self._state.artifacts:
            self[artifact_r.id] = artifact_r

    def value(self, product_id: str) -> float | (str | Any) | None:
        """Get the value/data of a score/artifact."""
        product = self.get(product_id)
        if product is None:
            return None
        if isinstance(product, Artifact):
            return product.data
        elif isinstance(product, Score):
            return product.value
        return None

    def scores(self) -> Generator[Score, None, None]:
        """Get all scores."""
        yield from self._state.scores

    def artifacts(self) -> Generator[Artifact, None, None]:
        """Get all artifacts."""
        yield from self._state.artifacts

    def get_score(self, score_id: str) -> Score | None:
        """Get score by id."""
        score_obj = self.get(score_id)
        if isinstance(score_obj, Score):
            return score_obj
        return None

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        """Get artifact by id."""
        artifact = self.get(artifact_id)
        if isinstance(artifact, Artifact):
            return artifact
        return None

    def info(self) -> str:
        """Get info string for printing or logging"""
        infos = []
        for score in self.scores():
            infos.append(f"{score.id} = {score.value}")
        return "\n".join(infos)


# TODO: Rename? score -> analyze?
async def ascore(
    prompt: str | None = None,
    completion: str | None = None,
    config: ScoreConfig | str | None = None,
) -> ScoreResult | None:
    """Async analyze and score the completion."""

    if config is None:
        if prompt is None and completion is None:
            return None
        config = ScoreConfig()
    elif isinstance(config, str):
        config = ScoreConfig.parse_file(config)
    else:
        config = copy.deepcopy(config)

    # Add prompt and completion as input artifacts to config
    config = ScoreConfig.add_prompt_completion(prompt=prompt, completion=completion, config=config)

    # Dynamically create analyst pipeline based on config
    pipeline, _ = Director().create(config)
    if not pipeline:
        return None

    # Analyze the completion
    analysis_state = await pipeline(inputs=config.inputs)

    score_result = ScoreResult(config=config, state=analysis_state)

    return score_result


def score(
    prompt: str | None = None,
    completion: str | None = None,
    config: ScoreConfig | str | None = None,
) -> ScoreResult | None:
    """Analyze and score the completion."""
    score_result = asyncio.run(ascore(prompt=prompt, completion=completion, config=config))
    return score_result
