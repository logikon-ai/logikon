# interface.py

from abc import ABC, abstractmethod
from typing import List


class Debugger(ABC):
    """Abstract base class for all debuggers."""

    @abstractmethod
    def __init__(self, debug_config):
        pass

    @abstractmethod
    def set_next(self, handler):
        pass

    @abstractmethod
    def _debug(self, prompt: str, completion: str, debug_results):
        """Debug completion."""
        pass

    @abstractmethod
    def handle(self, inputs, debug_results=None):
        pass

    @staticmethod
    @abstractmethod
    def get_product() -> str:
        """Get config keyword of artifact / metric produced by debugger."""
        pass

    @staticmethod
    @abstractmethod
    def get_requirements() -> List[str]:
        """Get config keywords of metrics / artifacts that are required for the debugger."""
        pass

    @property
    @abstractmethod
    def product_type(self) -> str:
        pass
