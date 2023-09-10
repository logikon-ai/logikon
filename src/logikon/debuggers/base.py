

from abc import ABC, abstractmethod

from typing import List

from logikon.schemas.results import DebugResults

class Debugger(ABC):
    """Abstract base class for all debuggers."""

    @abstractmethod
    def set_next(self, handler):
        pass

    @abstractmethod
    def _debug(self, prompt: str, completion: str, debug_results: DebugResults):
        """Debug completion."""
        pass

    @abstractmethod
    def handle(self, **kwargs):
        pass

    @abstractmethod
    def get_product(self) -> str:
        """Get config keyword of artifact / metric produced by debugger."""
        pass

    @abstractmethod
    def get_requirements(self) -> List[str]:
        """Get config keywords of metrics / artifacts that are required for the debugger."""
        pass


class AbstractDebugger(Debugger):
    """
    Base debugger class with default chaining behavior.
    """

    _next_debugger: Debugger = None

    def set_next(self, debugger: Debugger) -> Debugger:
        self._next_debugger = debugger
        return debugger

    def handle(self, **kwargs):
        self._debug(**kwargs)
        if self._next_debugger:
            self._next_debugger.handle(**kwargs)

    def get_requirements(self) -> List[str]:
        """Default implementation: no requirements."""
        return []

