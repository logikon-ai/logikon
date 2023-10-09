from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import copy

from logikon.debuggers.factory import DebuggerFactory
from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugState, Artifact, INPUT_KWS


def score(
    prompt: Optional[str] = None,
    completion: Optional[str] = None,
    config: Optional[DebugConfig] = None,
) -> Optional[DebugState]:
    """Score the completion."""

    if config is None:
        if prompt is None and completion is None:
            return None
        config = DebugConfig()
    else:
        config = copy.deepcopy(config)

    # TODO: optionally load configuration from yaml config file

    # add prompt and completion to config
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

    # Dynamically construct debugger pipeline based on config
    debugger_pipeline = DebuggerFactory().create(config)
    if not debugger_pipeline:
        return DebugState()

    # Debug the completion
    debug_results = debugger_pipeline(inputs=config.inputs)

    return debug_results
