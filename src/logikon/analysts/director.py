from __future__ import annotations

import copy
import functools as ft
import logging
from typing import Callable, Iterable, Mapping

from logikon.analysts.interface import Analyst
from logikon.analysts.registry import get_analyst_registry
from logikon.schemas.configs import ScoreConfig
from logikon.schemas.results import AnalysisState, Artifact


class Director:
    """Factory for creating a analyst pipeline based on a config."""

    @staticmethod
    def run_pipeline(
        chain: Iterable[Analyst], inputs: list[Artifact] | None = None, analysis_state: AnalysisState | None = None
    ):
        """runs analysts pipeline"""

        if inputs is None:
            inputs = []

        if analysis_state is None:
            # if not provided, initialize empty analysis_state
            state = AnalysisState()
        else:
            state = copy.deepcopy(analysis_state)

        # check whether input ids are unique
        for input_artifact in inputs:
            if [a.id for a in inputs].count(input_artifact.id) > 1:
                msg = f"Found several input artifacts with id {input_artifact.id}. Input ids are required to be unique."
                raise ValueError(msg)

        # add inputs to analysis_state
        for input_artifact in inputs:
            if input_artifact.id in state.inputs:
                msg = f"Duplicate input artifact id {input_artifact.id} found in analysis_state. Ids must be unique."
                raise ValueError(msg)
            state.inputs.append(input_artifact)

        # iterate over analysts
        for analyst in chain:
            state = analyst(analysis_state=state)

        return state

    def _run_consistency_checks(self, config: ScoreConfig, input_ids: list[str], registry: Mapping):
        """consistency check for current configuration

        Args:
            config (ScoreConfig): configuration
            input_ids (List[str]): input ids provided in config
            registry (Mapping): current analyst registry
        """
        # Check if all metrics and artifacts keys in config are registered
        for key in config.metrics + config.artifacts:
            if not isinstance(key, str) and not issubclass(key, Analyst):
                msg = f"Found metrics / artifact key '{key}' of type '{type(key)}'. Must be string or Analyst."
                raise ValueError(msg)
            if isinstance(key, str):
                if key not in registry:
                    msg = f"Metrics / artifact keyword '{key}' does not correspond to a registered analyst."
                    raise ValueError(msg)
            elif issubclass(key, Analyst):
                if key.get_product() not in registry:
                    msg = f"Analyst '{key}' not properly registered: Product {key.get_product()} not in registry."
                    raise ValueError(msg)

        # Check if any of the metrics / artifacts keys in config are already provided as inputs
        for key in config.metrics + config.artifacts:
            if isinstance(key, str):
                if key in input_ids:
                    msg = f"Inconsistent configuration. {key} provided as input but also as metric / artifact."
                    raise ValueError(msg)
            elif issubclass(key, Analyst):
                if key.get_product() in input_ids:
                    msg = (
                        "Inconsistent configuration. "
                        f"{key.get_product()} provided as input but also as metric / artifact."
                    )
                    raise ValueError(msg)

    def _collect_analysts(
        self, config: ScoreConfig, input_ids: list[str], registry: Mapping[str, list[type[Analyst]]]
    ) -> list[type[Analyst]]:
        """collect all analysts required for running current configuration

        Args:
            config (ScoreConfig): configuration
            input_ids (List[str]): inputs
            registry (Mapping[str, List[type): available analysts
        """

        # Create list of analysts classes from config and registry
        analyst_classes: list[type[Analyst]] = []
        for key in config.metrics + config.artifacts:
            if isinstance(key, str):
                analyst_cls = registry[key][0]  # first analyst class in registry list is default
            else:
                analyst_cls = key
            analyst_classes.append(analyst_cls)

        # Check if all requirements are met and add further analysts as necessary
        requirements_satisfied = False

        while not requirements_satisfied:
            products = {analyst_cls.get_product() for analyst_cls in analyst_classes}
            missing_products = set()
            for analyst_cls in analyst_classes:
                requirements = analyst_cls.get_requirements()
                if requirements and isinstance(requirements[0], set):
                    if not any(set(rs).issubset(products | set(input_ids)) for rs in requirements):
                        requirements_satisfied = False
                        # use first requirement set to add additional analysts
                        missing_products = requirements[0] - products
                        break
                    if len([rs for rs in requirements if set(rs).issubset(products | set(input_ids))]) > 1:
                        self.logger.warning(
                            f"Analyst {analyst_cls} has multiple requirement sets that are satisfied; "
                            "this may lead to unexpected analyst chaining and final results. "
                            "Please consider defining a more comprehensive and unambiguous score config."
                        )
                elif not set(requirements).issubset(products):
                    requirements_satisfied = False
                    missing_products = set(requirements) - products
                    break

            requirements_satisfied = not missing_products

            for missing_product_kw in missing_products:
                if missing_product_kw not in registry:
                    msg = f"Analyst requirement '{missing_product_kw}' does not correspond to a registered analyst."
                    raise ValueError(msg)
                new_analyst_cls = registry[missing_product_kw][0]
                analyst_classes.append(new_analyst_cls)

        return analyst_classes

    def _initialize_analysts(self, config: ScoreConfig, analyst_classes: list[type[Analyst]]) -> list[Analyst]:
        """initialize all analysts with config

        Args:
            config (ScoreConfig): configuration
            analyst_classes: List[Type[Analyst]]: analyst classes to initialize
        """

        # Initialize analysts
        analysts = []
        for analyst_cls in analyst_classes:
            analyst_config = config.get_analyst_config(analyst_cls)
            analysts.append(analyst_cls(config=analyst_config))

        return analysts

    def _build_chain(self, analysts: list[Analyst], input_ids: list[str]) -> list[Analyst]:
        """builds analyst chain respecting requirements

        Args:
            analysts (List[Analyst]): analysts to be chained
            input_ids (List[str]): available inputs

        Returns:
            List[Analyst]: chained analysts (pipeline chain)
        """
        chain: list[Analyst] = []
        while analysts:
            added_any = False
            products_available = {analyst.get_product() for analyst in chain} | set(input_ids)
            for analyst in analysts:
                requirements = analyst.get_requirements()
                if requirements:
                    # use first requirement set to determine when to insert analyst
                    requirements = list(requirements[0]) if isinstance(requirements[0], set) else requirements
                if set(requirements).issubset(products_available):
                    chain.append(analyst)
                    analysts.remove(analyst)
                    added_any = True
            if not added_any:
                analysts_left = [analyst.get_product() for analyst in analysts]
                msg = (
                    "Could not create analyst chain. Failed to satisfy any of "
                    f"the following analysts' requirements: {analysts_left}"
                )
                raise ValueError(msg)

        return chain

    def create(self, config: ScoreConfig) -> tuple[Callable | None, list[Analyst] | None]:
        """Create a analyst pipeline based on a config."""

        registry = get_analyst_registry()
        input_ids = [inpt.id for inpt in config.inputs]

        config = config.cast(registry)

        self._run_consistency_checks(config, input_ids, registry)

        analyst_classes = self._collect_analysts(config, input_ids, registry)

        analysts = self._initialize_analysts(config, analyst_classes)

        chain = self._build_chain(analysts, input_ids)

        if not chain:
            return None, None

        self.logger.info("Built analyst pipeline:" + " -> ".join([str(type(analyst)) for analyst in chain]))

        pipeline = ft.partial(self.run_pipeline, chain=iter(chain))

        return pipeline, chain

    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)
