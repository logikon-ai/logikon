
from __future__ import annotations
from typing import List, Optional

from logikon.debuggers.base import Debugger
from logikon.schemas.results import DebugResults, Artifact

class ClaimExtractor(Debugger):
    """ClaimExtractor Debugger
    
    This debugger is responsible for extracting claims from the
    prompt and completion.    
    """
    
    _KW_DESCRIPTION = "Key claims in the deliberation"
    _KW_PRODUCT = "claims"


    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT


    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Debug completion."""
        assert debug_results is not None
        # Dummy
        claims = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=["claim1", "claim2"],
        )

        debug_results.artifacts.append(claims)