
from __future__ import annotations
from typing import List, Optional

from logikon.debuggers.base import Debugger
from logikon.schemas.results import DebugResults, Artifact

class InformalArgMap(Debugger):
    """InformalArgMap Debugger
    
    This debugger is responsible for extracting informal argument maps from the
    deliberation in the completion.
    
    It requires the following artifacts:
    - claims
    """
    
    _KW_DESCRIPTION = "Informal Argument Map"
    _KW_PRODUCT = "informal_argmap"
    _KW_REQUIREMENTS = ["claims"]

    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT

    @classmethod
    def get_requirements(cls) -> List[str]:
        return cls._KW_REQUIREMENTS    

    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Debug completion."""
        assert debug_results is not None
        # Dummy
        map = f">>>This is an argmap for {prompt} and {completion}<<<"
        argmap = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=map,
        )

        debug_results.artifacts.append(argmap)