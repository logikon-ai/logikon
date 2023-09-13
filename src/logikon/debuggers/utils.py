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
        huggingface_hub.login(os.environ["HUGGINGFACEHUB_API_TOKEN"])
        model_kwargs["max_new_tokens"] = model_kwargs.pop("max_tokens", 256)
        llm = VLLM(model="mosaicml/mpt-7b",
           trust_remote_code=True,  # mandatory for hf models
           **model_kwargs
        )

    else:
        raise ValueError(f"Unknown model framework: {debug_config.llm_framework}")

    return llm