from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import copy

from logikon.analysts.director import Director
from logikon.schemas.configs import ScoreConfig
from logikon.schemas.results import AnalysisState, Artifact, INPUT_KWS


def score(
    prompt: Optional[str] = None,
    completion: Optional[str] = None,
    config: Optional[Union[ScoreConfig,str]] = None,
) -> Optional[AnalysisState]:
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
        return AnalysisState()

    # Analyze the completion
    analysis_results = pipeline(inputs=config.inputs)

    return analysis_results
