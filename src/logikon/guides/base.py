"AbstractGuide Class"

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncGenerator, Dict, Optional, Tuple, Type

from pydantic import BaseModel

from logikon.backends.chat_models_with_grammar import LogitsModel


class GuideOutputType(Enum):
    progress = "progress"
    response = "response"
    svg_argmap = "svg_argmap"
    nx_argmap = "nx_argmap"
    protocol = "protocol"


class AbstractGuideConfig(BaseModel):
    pass


class AbstractGuide(ABC):
    """
    Base guide class with default __call__ implementation.

    A Guide steers a Tourist-LLM through a complex reasoning process.
    """

    __configclass__: Optional[Type] = None

    def __init__(self, tourist_llm: LogitsModel, config: AbstractGuideConfig):
        self.tourist_llm = tourist_llm
        self.config = config

    @abstractmethod
    async def guide(self, problem: str, **kwargs) -> AsyncGenerator[Tuple[GuideOutputType, Any], None]:
        """Guide the user llm. Streaming results."""
        pass

    async def __call__(self, problem: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Guides the user llm. Non-streaming method."""

        outputs = [o async for o in await self.guide(problem, **kwargs)]

        response = next((v for t, v in outputs if t == GuideOutputType.response), None)
        if response is None:
            response = "I'm sorry, I failed to draft a response."
        artifacts = {}
        for otype in [GuideOutputType.svg_argmap, GuideOutputType.protocol]:
            artifact = next((o for o in outputs if o[0] == otype), None)
            if artifact:
                artifacts[otype.value] = artifact[1]

        return response, artifacts

    @classmethod
    def get_config_class(cls) -> Type:
        if cls.__configclass__ is None:
            msg = f"Config class not defined for {cls.__name__}."
            raise ValueError(msg)
        # check if configclass is subclass of AnalystConfig
        if not issubclass(cls.__configclass__, AbstractGuideConfig):
            msg = f"Config class {cls.__configclass__.__name__} not derived from AbstractGuideConfig."
            raise ValueError(msg)
        return cls.__configclass__

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "ok"}

    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)
