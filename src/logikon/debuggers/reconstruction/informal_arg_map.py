
from __future__ import annotations
from typing import List

from logikon.debuggers.base import Debugger

class InformalArgMap(Debugger):
    
    _KW_PRODUCT = "informal_argmap"
    _KW_REQUIREMENTS = ["claims"]

    def get_product(self) -> str:
        return self._KW_PRODUCT

    def get_requirements(self) -> List[str]:
        return self._KW_REQUIREMENTS    
