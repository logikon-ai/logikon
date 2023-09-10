from __future__ import annotations

from typing import Dict, Type

from logikon.debuggers.reconstruction.informal_arg_map import InformalArgMap
from logikon.debuggers.base import Debugger

_DEBUGGER_REGISTRY = {
    "informal_argmap": InformalArgMap, 
}

@staticmethod
def get_debugger_registry() -> Dict[str, Type[Debugger]]:
    """Get the debugger registry."""
    # sanity checks
    for keyword, debugger in _DEBUGGER_REGISTRY.items():
        assert issubclass(debugger, Debugger)
        assert debugger.get_product() == keyword

    return _DEBUGGER_REGISTRY