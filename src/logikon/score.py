from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Type

import copy

from logikon.analysts.director import Director
from logikon.schemas.configs import ScoreConfig
from logikon.schemas.results import AnalysisState, Artifact, INPUT_KWS
from logikon.analysts.interface import Analyst


# TODO: test and use this class
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

        # add data/value of directly requested metrics and artifacts as attributes
        for metric in self._config.metrics:
            if isinstance(metric, str):
                setattr(self, metric, self[metric])
            elif issubclass(metric, Analyst):
                setattr(self, metric.get_product(), self[metric.get_product()].value)
        for artifact in self._config.artifacts:
            if isinstance(artifact, str):
                setattr(self, artifact, self[artifact])
            elif issubclass(artifact, Analyst):
                setattr(self, artifact.get_product(), self[artifact.get_product()].data)


def score(
    prompt: Optional[str] = None,
    completion: Optional[str] = None,
    config: Optional[Union[ScoreConfig, str]] = None,
) -> Optional[ScoreResult]:
    """Score the completion."""

    if config is None:
        if prompt is None and completion is None:
            return None
        config = ScoreConfig()
    elif isinstance(config, str):
        config = ScoreConfig.parse_file(config)
    else:
        config = copy.deepcopy(config)

    # add prompt and completion as input artifacts to config
    if prompt is not None:
        if any(inpt.id == INPUT_KWS.prompt for inpt in config.inputs):
            raise ValueError(
                "Inconsistent configuration. Prompt provided as kwargs for score() but already present in config.inputs."
            )
        config.inputs.append(Artifact(id=INPUT_KWS.prompt, description="Prompt", data=prompt, dtype="str"))
    if completion is not None:
        if any(inpt.id == INPUT_KWS.completion for inpt in config.inputs):
            raise ValueError(
                "Inconsistent configuration. Completion provided as kwargs for score() but already present in config.inputs."
            )
        config.inputs.append(Artifact(id=INPUT_KWS.completion, description="Completion", data=completion, dtype="str"))

    # Dynamically create analyst pipeline based on config
    pipeline, _ = Director().create(config)
    if not pipeline:
        return None

    # Analyze the completion
    analysis_state = pipeline(inputs=config.inputs)

    score_result = ScoreResult(config=config, state=analysis_state)

    return score_result
