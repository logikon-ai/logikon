from __future__ import annotations

from typing import Any, Optional, Union, Type, List, Mapping, Dict

import copy
import logging
from pydantic import BaseModel
import yaml

from logikon.schemas.results import Artifact, Score
from logikon.analysts.interface import Analyst, AnalystConfig





class ScoreConfig(BaseModel):
    """
    Configuration for scoring reasoning traces.

    Args:
        inputs: The inputs to the expert model (Artifacts or Scores).
        metrics: The metrics to use for scoring (keyword or analyst class).
        artifacts: The artifacts to generate (keyword or analyst class).
        report_to: Integrations.
        global_kwargs: Global keyword arguments to pass to all analysts.
        analyst_configs: Keyword arguments to pass to specific analysts, overwrite global kwargs.
    """

    inputs: list[Union[Artifact, Score]] = []
    metrics: list[Union[str, Type[Analyst]]] = []
    artifacts: list[Union[str, Type[Analyst]]] = ["proscons"]
    report_to: list[str] = []
    global_kwargs: dict[str, Any] = {}
    analyst_configs: dict[Union[str, Type[Analyst]], Union[dict[str, Any], AnalystConfig]] = {}

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

    def cast(self, registry: Mapping[str, List[type[Analyst]]]) -> ScoreConfig:
        """Casts analyst class names and config classes to actual classes.

        Args:
            registry (Mapping[str, List[type[Analyst]]]): analyst registry

        Raises:
            ValueError: if analyst class name or config class name is not registered
        
        Returns:
            ScoreConfig: casted configuration
        """

        score_config = copy.deepcopy(self)

        analysts: Dict[str,Type[Analyst]] = {}
        for anas in registry.values():
            for ana in anas:
                analysts[ana.__name__] = ana

        # cast analyst class names to actual classes
        for i, metric in enumerate(score_config.metrics):
            if isinstance(metric, str):
                score_config.metrics[i] = analysts.get(metric,metric)
        for i, artifact in enumerate(score_config.artifacts):
            if isinstance(artifact, str):
                score_config.artifacts[i] = analysts.get(artifact,artifact)
        analyst_configs: dict[Union[str,Type[Analyst]], Union[dict[str, Any], AnalystConfig]] = {}
        for k,v in score_config.analyst_configs.items():
            if isinstance(k, str):
                if k in analysts:
                    analyst_configs[analysts[k]] = v
                else:
                    raise ValueError(f"Invalid configuration. Analyst class {k} not registered.")
            else:
                analyst_configs[k] = v
        score_config.analyst_configs = analyst_configs

        return score_config

    def get_analyst_config(self, analyst: type[Analyst]) -> Optional[AnalystConfig]:
        """Get specific config info for analyst type using global kwargs and analyst specific kwargs.

        Args:
            analyst (type[Analyst]): analyst type

        Returns:
            Optional[AnalystConfig]: config info for analyst type
        """

        if any(isinstance(key, str) for key in self.analyst_configs):
            self.logger.warning("Found string keys in analyst_configs. These will be ignored by get_analyst_config(). Consider calling cast() first.")

        config_data = copy.deepcopy(self.global_kwargs)

        if analyst in self.analyst_configs:
            if isinstance(self.analyst_configs[analyst], dict):
                config_data.update(self.analyst_configs[analyst])
            elif isinstance(self.analyst_configs[analyst], AnalystConfig):
                config_data.update(self.analyst_configs[analyst].dict())  # type: ignore
            else:
                raise ValueError(f"Invalid configuration. Analyst config {self.analyst_configs[analyst]} not of type dict or AnalystConfig.")

        try:
            analyst_config = analyst.get_config_class()(**config_data)
        except Exception as e:
            raise ValueError(f"Invalid configuration. Analyst analyst type {analyst} cannot be initialized from config data {config_data}.") from e

        return analyst_config


    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)
