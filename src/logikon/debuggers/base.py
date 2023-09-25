import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugResults, Score, Artifact
from logikon.debuggers.interface import Debugger

ARTIFACT = "ARTIFACT"
SCORE = "SCORE"


class AbstractDebugger(Debugger):
    """
    Base debugger class with default chaining behavior.
    """

    _next_debugger: Optional[Debugger] = None

    def __init__(self, debug_config: DebugConfig):
        self._debug_config = debug_config

    def set_next(self, debugger: Debugger) -> Debugger:
        self._next_debugger = debugger
        return debugger

    @abstractmethod
    def _debug(self, prompt: str, completion: str, debug_results: DebugResults):
        """Debug completion."""
        pass

    def handle(
        self, inputs: List[Union[Artifact, Score]], debug_results: Optional[DebugResults] = None
    ) -> DebugResults:
        """Handles the debug request."""

        # add artifacts and scores provided as inputs
        if debug_results is None:
            debug_results = DebugResults(
                artifacts=[a for a in inputs if isinstance(a, Artifact) and not a.id in ["prompt", "completion"]],
                scores=[s for s in inputs if isinstance(s, Score)],
            )

        prompt = next(a.data for a in inputs if isinstance(a, Artifact) and a.id == "prompt")
        completion = next(a.data for a in inputs if isinstance(a, Artifact) and a.id == "completion")

        self._debug(prompt=prompt, completion=completion, debug_results=debug_results)

        if self._next_debugger:
            self._next_debugger.handle(inputs, debug_results)

        return debug_results

    @staticmethod
    def get_requirements() -> List[str]:
        """Default implementation: no requirements."""
        return []

    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)


class AbstractArtifactDebugger(AbstractDebugger):
    """
    Base debugger class for creating artifacts.
    """

    @property
    def product_type(self) -> str:
        return ARTIFACT


class AbstractScoreDebugger(AbstractDebugger):
    """
    Base debugger class for cerating scroes.
    """

    @property
    def product_type(self) -> str:
        return SCORE
