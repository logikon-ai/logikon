from __future__ import annotations

import os
from typing import Optional

import huggingface_hub
from langchain.llms import (
    VLLM,
    BaseLLM,
    HuggingFaceHub,
    LlamaCpp,
    OpenAI,
)

from logikon.schemas.configs import DebugConfig

_VLLM: Optional[VLLM] = None


def init_llm_from_config(debug_config: DebugConfig, **kwargs) -> BaseLLM:
    llm: Optional[BaseLLM] = None

    if debug_config.llm_framework == "HuggingFaceHub":
        llm = HuggingFaceHub(
            repo_id=debug_config.expert_model, model_kwargs=debug_config.expert_model_kwargs, client=None
        )

    if debug_config.llm_framework == "LlamaCpp":
        llm = LlamaCpp(
            model_path=debug_config.expert_model, verbose=True, client=None, **debug_config.expert_model_kwargs
        )

    if debug_config.llm_framework == "OpenAI":
        llm = OpenAI(model=debug_config.expert_model, **debug_config.expert_model_kwargs)

    if debug_config.llm_framework == "VLLM":
        global _VLLM
        if _VLLM is not None and isinstance(_VLLM, VLLM):
            return _VLLM
        huggingface_hub.login(os.environ.get("HUGGINGFACEHUB_API_TOKEN"))
        llm = VLLM(
            model=debug_config.expert_model, client=None, trust_remote_code=True, **debug_config.expert_model_kwargs
        )
        _VLLM = llm

    if llm is None:
        msg = f"Unknown model framework: {debug_config.llm_framework}"
        raise ValueError(msg)

    return llm
