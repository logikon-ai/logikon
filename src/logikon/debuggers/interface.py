# interface.py

from abc import ABC, abstractmethod
from typing import List, Union


class Debugger(ABC):
    """Abstract base class for all debuggers."""

    @abstractmethod
    def __init__(self, debug_config):
        pass

    @abstractmethod
    def _debug(self, debug_state):
        """Debug inputs in debug_state."""
        pass

    @abstractmethod
    def __call__(self, debug_state):
        pass

    @classmethod
    @abstractmethod
    def get_product(cls) -> str:
        """Get config keyword of artifact / metric produced by debugger."""
        pass

    @classmethod
    @abstractmethod
    def get_requirements(cls) -> List[Union[str,set]]:
        """Get config keywords of metrics / artifacts that are required for the debugger."""
        pass

    @property
    @abstractmethod
    def product_type(self) -> str:
        pass
