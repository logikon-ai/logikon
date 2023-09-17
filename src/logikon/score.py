from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from logikon.debuggers.factory import DebuggerFactory
from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugResults


def score(
    prompt: str,
    completion: str,
    config: DebugConfig | None = None,
) -> DebugResults:
    """Score the completion."""

    if config is None:
        config = DebugConfig()

    # TODO: optionally load configuration from yaml config file

    # Dynamically construct debugger chain based on config
    debugger = DebuggerFactory().create(config)
    if not debugger:
        return DebugResults()

    # Debug the completion
    debug_results = debugger.handle(prompt=prompt, completion=completion)

    return debug_results
