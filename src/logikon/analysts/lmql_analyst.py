# lmql_analyst.py

from __future__ import annotations

from typing import Optional, Type

import lmql

from logikon.utils.model_registry import get_registry_model, register_model
from logikon.analysts.base import AbstractArtifactAnalyst, ArtifcatAnalystConfig


class LMQLAnalystConfig(ArtifcatAnalystConfig):
    """LMQLAnalystConfig

    Configuration for LMQLAnalyst.

    """

    expert_model: str
    llm_framework: str
    expert_model_kwargs: Optional[dict] = None
    generation_kwargs: Optional[dict] = None


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
            if config.llm_framework == "transformers":
                if "tokenizer" not in model_kwargs:
                    model_kwargs["tokenizer"] = model_id
                model = lmql.model(f"local:{model_id}", **model_kwargs)

            if config.llm_framework == "llama.cpp":
                model = lmql.model(f"local:llama.cpp:{model_id}", **model_kwargs)

            if config.llm_framework == "OpenAI":
                model = lmql.model(model_id, **model_kwargs)

            if model is None:
                msg = f"Model framework unknown or incompatible with lmql: {config.llm_framework}"
                raise ValueError(msg)

            register_model(model_id, model)

        if not isinstance(model, lmql.LLM):
            raise ValueError(f"Model {model_id} is not an lmql model.")

        model_kwargs.pop("tokenizer", None)
        self._model: lmql.LLM = model
        self._model_kwargs = model_kwargs
        self._generation_kwargs = config.generation_kwargs if config.generation_kwargs is not None else {}
