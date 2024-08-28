# lcel_analyst.py

from __future__ import annotations

import logging
import signal
import threading
from functools import wraps
from typing import Any

from logikon.analysts.base import AbstractArtifactAnalyst, ArtifcatAnalystConfig
from logikon.backends.chat_models_with_grammar import LLMBackends, LogitsModel, create_logits_model
from logikon.backends.classifier import HfClassifier


class LCELAnalystConfig(ArtifcatAnalystConfig):
    """LCELAnalystConfig

    Configuration for LCELAnalyst.

    """

    expert_model: str
    inference_server_url: str
    api_key: str = "EMPTY"
    llm_backend: str | LLMBackends = LLMBackends.VLLM
    expert_model_kwargs: dict | None = None
    generation_kwargs: dict | None = None
    classifier_kwargs: dict | None = None
    lcel_query_timeout: int = 300


class LCELAnalyst(AbstractArtifactAnalyst):
    """LCELAnalyst

    Base class for reconstruction analysts that use `langchain` module and LCEL.

    """

    __configclass__: type[ArtifcatAnalystConfig] = LCELAnalystConfig

    def __init__(self, config: LCELAnalystConfig):
        super().__init__(config)

        model_init_kwargs: dict[str, Any] = {}
        if config.expert_model_kwargs is not None:
            model_init_kwargs = {**model_init_kwargs, **config.expert_model_kwargs}
        if config.generation_kwargs is not None:
            model_init_kwargs = {**model_init_kwargs, **config.generation_kwargs}

        self._model: LogitsModel = create_logits_model(
            model_id=config.expert_model,
            inference_server_url=config.inference_server_url,
            api_key=config.api_key,
            llm_backend=config.llm_backend,
            **model_init_kwargs,
        )

        self._classifier: HfClassifier | None = (
            HfClassifier(**config.classifier_kwargs) if config.classifier_kwargs is not None else None
        )

        self._model_kwargs = config.expert_model_kwargs if config.expert_model_kwargs is not None else {}
        self._generation_kwargs = config.generation_kwargs if config.generation_kwargs is not None else {}
        self._lcel_query_timeout = config.lcel_query_timeout

    @staticmethod
    def timeout(func):
        """Timeout decorator for LCELAnalyst methods."""

        def _timeout_handler(signum, frame):  # noqa: ARG001
            msg = "LCEL query timed out."
            raise TimeoutError(msg)

        @wraps(func)
        def wrapper(self, *args, **kwargs):

            if threading.current_thread() is not threading.main_thread():
                logging.getLogger().info("Ignoring LCEL query timeout decorator as not running in main thread.")
                return func(self, *args, **kwargs)

            signal.signal(signal.SIGALRM, _timeout_handler)
            try:
                signal.alarm(self._lcel_query_timeout)
                return func(self, *args, **kwargs)
            except TimeoutError:
                logging.getLogger().warning("LCEL query %s timed out.", func.__name__)
                return None
            finally:
                signal.alarm(0)

        return wrapper
