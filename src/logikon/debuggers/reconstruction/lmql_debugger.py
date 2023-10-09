# lmql_debugger.py

from __future__ import annotations

from abc import abstractmethod
from typing import Dict, List, Optional, Tuple, Union

import functools as ft
import numpy as np
import random

import lmql

from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.schemas.results import DebugState, Artifact
from logikon.schemas.configs import DebugConfig


class LMQLDebugger(AbstractArtifactDebugger):
    """LMQLDebugger

    Base class for reconstruction debuggers that use `lmql` module.

    """

    def __init__(self, debug_config: DebugConfig):
        super().__init__(debug_config)

        model = None
        model_kwargs = {}
        if debug_config.llm_framework == "transformers":
            model = debug_config.expert_model
            model_kwargs = debug_config.expert_model_kwargs

        if debug_config.llm_framework == "OpenAI":
            model = debug_config.expert_model

        if model is None:
            msg = f"Model framework unknown or incompatible with outlines: {debug_config.llm_framework}"
            raise ValueError(msg)

        self._model = model
        self._model_kwargs = model_kwargs
