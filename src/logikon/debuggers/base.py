import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugState, Score, Artifact, INPUT_KWS
from logikon.debuggers.interface import Debugger

ARTIFACT = "ARTIFACT"
SCORE = "SCORE"


class AbstractDebugger(Debugger):
    """
    Base debugger class with default __call__ implementation.
    """

    def __init__(self, debug_config: DebugConfig):
        self._debug_config = debug_config

    @abstractmethod
    def _debug(self, debug_state: DebugState):
        """Debug debug_state."""
        pass

    def __call__(self, debug_state: DebugState) -> DebugState:
        """Carries out debugging process associated with this debugger for given debug_state."""

        self._debug(debug_state=debug_state)

        return debug_state

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
    Base debugger class for creating scroes.
    """

    @property
    def product_type(self) -> str:
        return SCORE
