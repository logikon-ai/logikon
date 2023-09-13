
from __future__ import annotations
from typing import List, Optional

from logikon.debuggers.base import AbstractDebugger
from logikon.debuggers.utils import init_llm_from_config
from logikon.schemas.results import DebugResults, Artifact

class InformalArgMap(AbstractDebugger):
    """InformalArgMap Debugger
    
    This debugger is responsible for extracting informal argument maps from the
    deliberation in the completion. It uses plain and non-technical successive LLM
    calls to gradually sum,m,arize reasons and build an argmap.
    
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
        """Reconstruct reasoning as argmap."""

        assert debug_results is not None

        llm = init_llm_from_config(self._debug_config)
        llmchain = InformalArgMapChain(llm=llm, max_words_claim=25)
        argmap = llmchain.run(prompt=prompt, completion=completion)

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=argmap,
        )

        debug_results.artifacts.append(artifact)
