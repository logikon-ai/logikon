from __future__ import annotations

from typing import Any, MutableMapping

_model_registry: MutableMapping[str, Any] = {}


def register_model(model_id: str, model: Any):
    if model_id in _model_registry:
        msg = (
            f"Duplicate model id. Model of type {type(_model_registry[model_id])} "
            f"already registered under id {model_id}."
        )
        raise ValueError(msg)
    _model_registry[model_id] = model


def get_registry_model(model_id: str):
    return _model_registry.get(model_id)
