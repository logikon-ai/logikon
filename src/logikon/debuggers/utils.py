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

_LLM: Optional[VLLM] = None


def init_llm_from_config(debug_config: DebugConfig, **kwargs) -> BaseLLM:

    model_kwargs = copy.deepcopy(kwargs)

    if debug_config.llm_framework == "HuggingFaceHub":
        model_kwargs["max_length"] = model_kwargs.pop("max_tokens", 256)
        llm = HuggingFaceHub(repo_id=debug_config.expert_model, model_kwargs=model_kwargs)

    elif debug_config.llm_framework == "LlamaCpp":
        llm = LlamaCpp(
            model_path=debug_config.expert_model,
            verbose=True,
            **model_kwargs
        )

    elif debug_config.llm_framework == "OpenAI":
        llm = OpenAI(model_name=debug_config.expert_model, **model_kwargs)

    elif debug_config.llm_framework == "VLLM":
        if _LLM is not None and isinstance(_LLM, VLLM):
            return _LLM
        huggingface_hub.login(os.environ["HUGGINGFACEHUB_API_TOKEN"])
        model_kwargs["max_new_tokens"] = model_kwargs.pop("max_tokens", 256)
        llm = VLLM(
            model=debug_config.expert_model,
            trust_remote_code=True,  # mandatory for hf models
            **model_kwargs
        )
        global _LLM
        _LLM = llm

    else:
        raise ValueError(f"Unknown model framework: {debug_config.llm_framework}")

    return llm