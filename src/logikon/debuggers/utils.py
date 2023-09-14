from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple

import copy
import os

import huggingface_hub
from langchain.llms import BaseLLM
from langchain.llms import (
    HuggingFaceHub,
    LlamaCpp,
    OpenAI,
    VLLM,
)

from logikon.schemas.configs import DebugConfig

_VLLM: Optional[VLLM] = None


def init_llm_from_config(debug_config: DebugConfig, **kwargs) -> BaseLLM:

    if debug_config.llm_framework == "HuggingFaceHub":
        llm = HuggingFaceHub(repo_id=debug_config.expert_model, model_kwargs=debug_config.expert_model_kwargs)

    elif debug_config.llm_framework == "LlamaCpp":
        llm = LlamaCpp(
            model_path=debug_config.expert_model,
            verbose=True,
            **debug_config.expert_model_kwargs
        )

    elif debug_config.llm_framework == "OpenAI":
        llm = OpenAI(model_name=debug_config.expert_model, **debug_config.expert_model_kwargs)

    elif debug_config.llm_framework == "VLLM":
        global _VLLM
        if _VLLM is not None and isinstance(_VLLM, VLLM):
            return _VLLM
        huggingface_hub.login(os.environ["HUGGINGFACEHUB_API_TOKEN"])
        llm = VLLM(
            model=debug_config.expert_model,
            **debug_config.expert_model_kwargs
        )
        _VLLM = llm

    else:
        raise ValueError(f"Unknown model framework: {debug_config.llm_framework}")

    return llm