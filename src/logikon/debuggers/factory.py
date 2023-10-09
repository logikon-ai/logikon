from __future__ import annotations

import logging
from typing import List, Optional, Callable

import copy
import functools as ft

from logikon.debuggers.interface import Debugger
from logikon.debuggers.registry import get_debugger_registry
from logikon.schemas.configs import DebugConfig
from logikon.schemas.results import DebugState, Artifact


class DebuggerFactory:
    """Factory for creating a debugger pipeline based on a config."""

    @staticmethod
    def run_pipeline(pipeline: List[Debugger], inputs: List[Artifact] = [], debug_state: Optional[DebugState] = None):
        """runs debugger pipeline"""

        if debug_state is None:
            # if not provided, initialize empty debug_state
            state = DebugState()
        else:
            state = copy.deepcopy(debug_state)

        # check whether input ids are unique
        for input_artifact in inputs:
            if [a.id for a in inputs].count(input_artifact.id) > 1:
                raise ValueError(
                    f"Found several input artifacts with id {input_artifact.id}. Input ids are required to be unique."
                )

        # add inputs to debug_state
        for input_artifact in inputs:
            if input_artifact.id in state.inputs:
                raise ValueError(
                    f"Duplicate input artifact id {input_artifact.id} found in debug_state.inputs and inputs. Ids must be unique."
                )
            state.inputs.append(input_artifact)

        # iterate over debuggers
        for debugger in pipeline:
            state = debugger(debug_state=state)

        return state

    def create(self, config: DebugConfig) -> Optional[Callable]:
        """Create a debugger pipeline based on a config."""

        registry = get_debugger_registry()
        input_ids = [inpt.id for inpt in config.inputs]

        # Check if all metrics and artifacts keys in config are registered
        for key in config.metrics + config.artifacts:
            if not isinstance(key, str) and not issubclass(key, Debugger):
                msg = f"Found metrics / artifact key '{key}' of type '{type(key)}'. Must be string or Debugger."
                raise ValueError(msg)
            if isinstance(key, str):
                if key not in registry:
                    msg = f"Metrics / artifact keyword '{key}' does not correspond to a registered debugger."
                    raise ValueError(msg)
            elif issubclass(key, Debugger):
                if key.get_product() not in registry:
                    msg = f"Debugger '{key}' not properly registered: Product {key.get_product()} not in registry."
                    raise ValueError(msg)

        # Check if any of the metrics / artifacts keys in config are already provided as inputs
        for key in config.metrics + config.artifacts:
            if isinstance(key, str):
                if key in input_ids:
                    raise ValueError(
                        f"Inconsistent configuration. {key} provided as input but also as metric / artifact."
                    )
            elif issubclass(key, Debugger):
                if key.get_product() in input_ids:
                    raise ValueError(
                        f"Inconsistent configuration. {key.get_product()} provided as input but also as metric / artifact."
                    )

        # Create list of debuggers from config and registry
        debuggers: List[Debugger] = []
        for key in config.metrics + config.artifacts:
            if isinstance(key, str):
                new_debugger = registry[key][0](config)  # first debugger class in registry list is default
            else:
                new_debugger = key(config)
            debuggers.append(new_debugger)

        # Check if all requirements are met and add further debuggers as necessary
        requirements = set()
        requirements_satisfied = False

        while not requirements_satisfied:
            products = {debugger.get_product() for debugger in debuggers}
            for debugger in debuggers:
                requirements.update(debugger.get_requirements())

            if requirements.issubset(products | set(input_ids)):
                requirements_satisfied = True

            for requirement_kw in requirements:
                if requirement_kw not in products:
                    if requirement_kw not in registry:
                        msg = f"Debugger requirement '{requirement_kw}' does not correspond to a registered debugger."
                        raise ValueError(msg)
                    new_debugger = registry[requirement_kw][0](config)
                    debuggers.append(new_debugger)

        # Create debugger pipeline respecting the dependencies (iteratively add and remove debuggers)
        pipeline: list[Debugger] = []
        while debuggers:
            added_any = False
            products_available = {debugger.get_product() for debugger in pipeline} | set(input_ids)
            for debugger in debuggers:
                requirements = set(debugger.get_requirements())
                if requirements.issubset(products_available):
                    pipeline.append(debugger)
                    debuggers.remove(debugger)
                    added_any = True
            if not added_any:
                debuggers_left = [debugger.get_product() for debugger in debuggers]
                msg = f"Could not create debugger chain. Failed to satisfy any of the following debuggers' requirements: {debuggers_left}"
                raise ValueError(msg)

        if not pipeline:
            return None

        # chain the debuggers via set_next()
        # for i in range(len(pipeline) - 1):
        #    pipeline[i].set_next(pipeline[i + 1])

        pipeline_callable = ft.partial(self.run_pipeline, pipeline=pipeline)

        return pipeline_callable

    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)
