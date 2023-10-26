# interface.py

from abc import ABC, abstractmethod
from typing import List, Union, Type

from pydantic import BaseModel


class Analyst(ABC):
    """Abstract base class for all analysts."""

    @abstractmethod
    def __init__(self, config):
        pass

    @abstractmethod
    def _analyze(self, analysis_state):
        """Carry out analysis given state."""
        pass

    @abstractmethod
    def __call__(self, analysis_state):
        pass

    @classmethod
    @abstractmethod
    def get_product(cls) -> str:
        """Get config keyword of artifact / metric produced by analyst."""
        pass

    @classmethod
    @abstractmethod
    def get_requirements(cls) -> List[Union[str, set]]:
        """Get config keywords of metrics / artifacts that are required for the analyst."""
        pass

    @classmethod
    @abstractmethod
    def get_config_class(cls) -> Type:
        """Get type of config class (subclass of AnalystConfig)."""
        pass

    @property
    @abstractmethod
    def product_type(self) -> str:
        pass


class AnalystConfig(BaseModel):
    pass
