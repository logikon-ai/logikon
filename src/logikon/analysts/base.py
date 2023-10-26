import logging
from abc import abstractmethod
from typing import List, Optional, Union, Type

from logikon.schemas.results import AnalysisState
from logikon.analysts.interface import Analyst, AnalystConfig

ARTIFACT = "ARTIFACT"
SCORE = "SCORE"


class AbstractAnalyst(Analyst):
    """
    Base analyst class with default __call__ implementation.
    """

    __product__: Optional[str] = None
    __requirements__: list[Union[str, set]] = []
    __pdescription__: Optional[str] = None
    __configclass__: Optional[Type] = None

    def __init__(self, config: AnalystConfig):
        self._config = config

    @abstractmethod
    def _analyze(self, analysis_state: AnalysisState):
        """Analysis given state."""
        pass

    def __call__(self, analysis_state: AnalysisState) -> AnalysisState:
        """Carries out analysis associated with this analyst for given analysis_state."""

        self._analyze(analysis_state=analysis_state)

        return analysis_state

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

    @classmethod
    def get_config_class(cls) -> Type:
        if cls.__configclass__ is None:
            raise ValueError(f"Config class not defined for {cls.__name__}.")
        # check if configclass is subclass of AnalystConfig
        if not issubclass(cls.__configclass__, AnalystConfig):
            raise ValueError(f"Config class {cls.__name__} not derived from AnalystConfig.")
        return cls.__configclass__

    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)


class ArtifcatAnalystConfig(AnalystConfig):
    pass


class AbstractArtifactAnalyst(AbstractAnalyst):
    """
    Base analyst class for creating artifacts.
    """

    __configclass__ = ArtifcatAnalystConfig

    @property
    def product_type(self) -> str:
        return ARTIFACT


class ScoreAnalystConfig(AnalystConfig):
    pass


class AbstractScoreAnalyst(AbstractAnalyst):
    """
    Base analyst class for creating scores.
    """

    __configclass__ = ScoreAnalystConfig

    @property
    def product_type(self) -> str:
        return SCORE
