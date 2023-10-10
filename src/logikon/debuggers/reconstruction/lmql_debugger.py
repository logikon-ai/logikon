# lmql_debugger.py

from __future__ import annotations

import lmql
from lmql.models.model import LMQLModel

from logikon.debuggers.registry import get_registry_model, register_model
from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.results import DebugState, Artifact
from logikon.schemas.configs import DebugConfig


class LMQLDebugger(AbstractArtifactDebugger):
    """LMQLDebugger

    Base class for reconstruction debuggers that use `lmql` module.

    """

    def __init__(self, debug_config: DebugConfig):
        super().__init__(debug_config)

        model_id = debug_config.expert_model
        model = get_registry_model(model_id)

        if model is None:
            model_kwargs = {}
            if debug_config.llm_framework == "transformers":

                model_kwargs = debug_config.expert_model_kwargs
                if "tokenizer" not in model_kwargs:
                    model_kwargs["tokenizer"] = model_id
                model = lmql.model(f"local:{model_id}", **model_kwargs)

            if debug_config.llm_framework == "OpenAI":
                model = lmql.model(model_id, **model_kwargs)

            if model is None:
                msg = f"Model framework unknown or incompatible with lmql: {debug_config.llm_framework}"
                raise ValueError(msg)
            
            register_model(model_id, model)

        if not isinstance(model, LMQLModel):
            raise ValueError(f"Model {model_id} is not an lmql model.")

        self._model: LMQLModel = model
        self._model_kwargs = model_kwargs
