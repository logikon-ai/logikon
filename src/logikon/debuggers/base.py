
from abc import ABC, abstractmethod

from typing import List, Optional
import logging

from logikon.schemas.results import DebugResults

class Debugger(ABC):
    """Abstract base class for all debuggers."""

    @abstractmethod
    def set_next(self, handler):
        pass

    @abstractmethod
    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Debug completion."""
        pass

    @abstractmethod
    def handle(self, **kwargs) -> DebugResults:
        pass

    @classmethod
    @abstractmethod
    def get_product(cls) -> str:
        """Get config keyword of artifact / metric produced by debugger."""
        pass

    @classmethod
    @abstractmethod
    def get_requirements(cls) -> List[str]:
        """Get config keywords of metrics / artifacts that are required for the debugger."""
        pass


class AbstractDebugger(Debugger):
    """
    Base debugger class with default chaining behavior.
    """

    _next_debugger: Optional[Debugger] = None


    def set_next(self, debugger: Debugger) -> Debugger:
        self._next_debugger = debugger
        return debugger


    def handle(self, **kwargs) -> DebugResults:
        """Handles the debug request."""

        if "debug_results" not in kwargs:
            kwargs["debug_results"] = DebugResults()
        
        self._debug(**kwargs)

        if self._next_debugger:
            self._next_debugger.handle(**kwargs)

        return kwargs["debug_results"]

    @classmethod
    def get_requirements(cls) -> List[str]:
        """Default implementation: no requirements."""
        return []

    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)