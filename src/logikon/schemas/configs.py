from __future__ import annotations

from typing import Any, Optional, Union, Type, List, Mapping, Dict

import copy
import logging
from pydantic import BaseModel
import yaml

from logikon.schemas.results import Artifact, Score
from logikon.debuggers.interface import Debugger, DebuggerConfig


# class DebugConfig(BaseModel):
#     """
#     Configuration for scoring reasoning traces.
# 
#     Args:
#         expert_model: The name of the expert model to use.
#         expert_model_kwargs: Keyword arguments to pass to the expert model.
#         llm_framework: The name of the language model framework to use (e.g., OpenAI, VLLM).
#         inputs: The inputs to the expert model (Artifacts or Scores).
#         metrics: The metrics to use for scoring (keyword or debugger class).
#         artifacts: The artifacts to generate (keyword or debugger class).
#         report_to: Integrations.
#     """
# 
#     expert_model: str = "gpt-3.5-turbo-instruct"
#     expert_model_kwargs: dict[str, Any] = {"temperature": 0.7}
#     llm_framework: str = "OpenAI"
#     generation_kwargs: Optional[dict] = None
#     inputs: list[Union[Artifact, Score]] = []
#     metrics: list[Union[str, Type[Debugger]]] = []
#     artifacts: list[Union[str, Type[Debugger]]] = ["informal_argmap"]
#     report_to: list[str] = []
# 
#     def __init__(self, **data: Any):
#         super().__init__(**data)
#         self._check_unique_ids()
# 
#     def _check_unique_ids(self):
#         """Check if all inputs, metrics and artifacts have unique ids."""
#         ids = [inpt.id for inpt in self.inputs]
#         if len(set(ids)) != len(ids):
#             raise ValueError("Inconsistent configuration. All inputs must have unique ids.")
#         ids = [metric if isinstance(metric, str) else metric.get_product() for metric in self.metrics]
#         if len(set(ids)) != len(ids):
#             raise ValueError("Inconsistent configuration. All metrics must have unique ids.")
#         ids = [artifact if isinstance(artifact, str) else artifact.get_product() for artifact in self.artifacts]
#         if len(set(ids)) != len(ids):
#             raise ValueError("Inconsistent configuration. All artifacts must have unique ids.")





class ScoreConfig(BaseModel):
    """
    Configuration for scoring reasoning traces.

    Args:
        inputs: The inputs to the expert model (Artifacts or Scores).
        metrics: The metrics to use for scoring (keyword or debugger class).
        artifacts: The artifacts to generate (keyword or debugger class).
        report_to: Integrations.
        global_kwargs: Global keyword arguments to pass to all debuggers.
        debugger_configs: Keyword arguments to pass to specific debuggers, overwrite global kwargs.
    """

    inputs: list[Union[Artifact, Score]] = []
    metrics: list[Union[str, Type[Debugger]]] = []
    artifacts: list[Union[str, Type[Debugger]]] = ["proscons"]
    report_to: list[str] = []
    global_kwargs: dict[str, Any] = {}
    debugger_configs: dict[Union[str, Type[Debugger]], Union[dict[str, Any], DebuggerConfig]] = {}

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._check_unique_ids()

    def _check_unique_ids(self):
        """Check if all inputs, metrics and artifacts have unique ids."""
        ids = [inpt.id for inpt in self.inputs]
        if len(set(ids)) != len(ids):
            raise ValueError("Inconsistent configuration. All inputs must have unique ids.")
        ids = [metric if isinstance(metric, str) else metric.get_product() for metric in self.metrics]
        if len(set(ids)) != len(ids):
            raise ValueError("Inconsistent configuration. All metrics must have unique ids.")
        ids = [artifact if isinstance(artifact, str) else artifact.get_product() for artifact in self.artifacts]
        if len(set(ids)) != len(ids):
            raise ValueError("Inconsistent configuration. All artifacts must have unique ids.")

    def cast(self, registry: Mapping[str, List[type[Debugger]]]) -> ScoreConfig:
        """Casts debugger class names and config classes to actual classes.

        Args:
            registry (Mapping[str, List[type[Debugger]]]): debugger registry

        Raises:
            ValueError: if debugger class name or config class name is not registered
        
        Returns:
            ScoreConfig: casted configuration
        """

        score_config = copy.deepcopy(self)

        debuggers: Dict[str,Type[Debugger]] = {}
        for ds in registry.values():
            for d in ds:
                debuggers[d.__name__] = d

        # cast debugger class names to actual classes
        for i, metric in enumerate(score_config.metrics):
            if isinstance(metric, str):
                score_config.metrics[i] = debuggers.get(metric,metric)
        for i, artifact in enumerate(score_config.artifacts):
            if isinstance(artifact, str):
                score_config.artifacts[i] = debuggers.get(artifact,artifact)
        debugger_configs: dict[Union[str,Type[Debugger]], Union[dict[str, Any], DebuggerConfig]] = {}
        for k,v in score_config.debugger_configs.items():
            if isinstance(k, str):
                if k in debuggers:
                    debugger_configs[debuggers[k]] = v
                else:
                    raise ValueError(f"Invalid configuration. Debugger class {k} not registered.")
            else:
                debugger_configs[k] = v
        score_config.debugger_configs = debugger_configs

        return score_config

    def get_debugger_config(self, debugger: type[Debugger]) -> Optional[DebuggerConfig]:
        """Get specific config info for debugger type using global kwargs and debugger specific kwargs.

        Args:
            debugger (type[Debugger]): debugger type

        Returns:
            Optional[DebuggerConfig]: config info for debugger type
        """

        if any(isinstance(key, str) for key in self.debugger_configs):
            self.logger.warning("Found string keys in debugger_configs. These will be ignored by get_debugger_config(). Consider calling cast() first.")

        config_data = copy.deepcopy(self.global_kwargs)

        if debugger in self.debugger_configs:
            if isinstance(self.debugger_configs[debugger], dict):
                config_data.update(self.debugger_configs[debugger])
            elif isinstance(self.debugger_configs[debugger], DebuggerConfig):
                config_data.update(self.debugger_configs[debugger].dict())  # type: ignore
            else:
                raise ValueError(f"Invalid configuration. Debugger config {self.debugger_configs[debugger]} not of type dict or DebuggerConfig.")

        try:
            debugger_config = debugger.get_config_class()(**config_data)
        except Exception as e:
            raise ValueError(f"Invalid configuration. Debugger debugger type {debugger} cannot be initialized from config data {config_data}.") from e

        return debugger_config


    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)
