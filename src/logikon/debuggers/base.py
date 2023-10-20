import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugState
from logikon.debuggers.interface import Debugger

ARTIFACT = "ARTIFACT"
SCORE = "SCORE"


class AbstractDebugger(Debugger):
    """
    Base debugger class with default __call__ implementation.
    """

    __product__: Optional[str] = None
    __requirements__: list[Union[str, set]] = []
    __pdescription__: Optional[str] = None

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

    @classmethod
    def get_product(cls) -> str:
        if cls.__product__ is None:
            raise ValueError(f"Product type not defined for {cls.__name__}.")
        return cls.__product__

    @classmethod
    def get_requirements(cls) -> list[Union[str, set]]:
        return cls.__requirements__

    @classmethod
    def get_description(cls) -> str:
        if cls.__pdescription__ is None:
            raise ValueError(f"Product description not defined for {cls.__name__}.")
        return cls.__pdescription__

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
