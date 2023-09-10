from __future__ import annotations

from typing import List, Optional, Union, Any, Dict

from logikon.debuggers.factory import DebuggerFactory
from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugResults


def score(
    prompt: str,
    completion: str,
    config: Optional[DebugConfig] = None,
) -> DebugResults:
    """Score the completion."""
    
    if config is None:
        config = DebugConfig()

    debug_results = DebugResults()

    # Dynamically construct debugger chain based on config
    debugger = DebuggerFactory().create(config)

    # Debug the completion
    debugger.handle(prompt, completion, debug_results)

    return debug_results