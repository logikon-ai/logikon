# lmql_analyst.py

from __future__ import annotations

from typing import Optional, Type
import logging
from functools import wraps
import signal

import lmql

from logikon.utils.model_registry import get_registry_model, register_model
from logikon.utils.prompt_templates_registry import get_prompt_template, PromptTemplate
from logikon.analysts.base import AbstractArtifactAnalyst, ArtifcatAnalystConfig


class LMQLAnalystConfig(ArtifcatAnalystConfig):
    """LMQLAnalystConfig

    Configuration for LMQLAnalyst.

    """

    expert_model: str
    llm_framework: str
    expert_model_kwargs: Optional[dict] = None
    generation_kwargs: Optional[dict] = None
    lmql_query_timeout: int = 300


class LMQLAnalyst(AbstractArtifactAnalyst):
    """LMQLAnalyst

    Base class for reconstruction analysts that use `lmql` module.

    """

    __configclass__: Type[ArtifcatAnalystConfig] = LMQLAnalystConfig

    def __init__(self, config: LMQLAnalystConfig):
        super().__init__(config)

        model_id = config.expert_model
        model_kwargs = config.expert_model_kwargs if config.expert_model_kwargs is not None else {}
        model = get_registry_model(model_id)

        if model is None:
            model_prefix = "local:" if "endpoint" not in model_kwargs else ""
            if config.llm_framework == "transformers":
                if "tokenizer" not in model_kwargs:
                    model_kwargs["tokenizer"] = model_id
                model = lmql.model(f"{model_prefix}{model_id}", **model_kwargs)

            if config.llm_framework == "llama.cpp":
                model = lmql.model(f"{model_prefix}llama.cpp:{model_id}", **model_kwargs)

            if config.llm_framework == "OpenAI":
                model = lmql.model(model_id, **model_kwargs)

            if model is None:
                msg = f"Model framework unknown or incompatible with lmql: {config.llm_framework}"
                raise ValueError(msg)

            register_model(model_id, model)

        if not isinstance(model, lmql.LLM):
            raise ValueError(f"Model {model_id} is not an lmql model.")

        model_kwargs.pop("tokenizer", None)

        prompt_template = model_kwargs.pop("prompt_template", None)
        if prompt_template is None:
            self.logger.info(f"No prompt template provided. Will use default prompt template.")
            prompt_template = get_prompt_template()
        elif isinstance(prompt_template, dict):
            # try to parse prompt template
            try:
                prompt_template = PromptTemplate.from_dict(prompt_template)
                self.logger.warning(
                    "Found custom prompt template in config. Note that ill-designed prompt templates "
                    "may fatally disrupt processing of lmql queries. Test custom templates thoroughly. "
                    "Use at your own risk."
                )
            except Exception as e:
                self.logger.warning(f"Failed to parse prompt template: {e}. Will use defaul prompt template.")
                prompt_template = get_prompt_template()
        elif isinstance(prompt_template, str):
            prompt_template = get_prompt_template(prompt_template)
        else:
            raise ValueError(f"Invalid prompt template: {prompt_template}")

        self._model: lmql.LLM = model
        self._model_kwargs = model_kwargs
        self._generation_kwargs = config.generation_kwargs if config.generation_kwargs is not None else {}
        self._prompt_template = prompt_template
        self._lmql_query_timeout = config.lmql_query_timeout

    @staticmethod
    def timeout(func):
        """Timeout decorator for LMQLAnalyst methods."""

        def _timeout_handler(signum, frame):
            raise TimeoutError("LMQL query timed out.")

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            signal.signal(signal.SIGALRM, _timeout_handler)
            try:
                signal.alarm(self._lmql_query_timeout)
                return func(self, *args, **kwargs)
            except TimeoutError:
                logging.getLogger().warning("LMQL query %s timed out.", func.__name__)
                return None
            finally:
                signal.alarm(0)

        return wrapper
