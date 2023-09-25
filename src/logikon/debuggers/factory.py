from __future__ import annotations

import logging
from typing import List, Optional

from logikon.debuggers.interface import Debugger
from logikon.debuggers.registry import get_debugger_registry
from logikon.schemas.configs import DebugConfig


class DebuggerFactory:
    """Factory for creating a debugger chain based on a config."""

    def create(self, config: DebugConfig) -> Optional[Debugger]:
        """Create a debugger chain based on a config."""

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

        # Create debugger chain respecting the dependencies (iteratively add and remove debuggers)
        chain: list[Debugger] = []
        while debuggers:
            added_any = False
            products_available = {debugger.get_product() for debugger in chain} | set(input_ids)
            for debugger in debuggers:
                requirements = set(debugger.get_requirements())
                if requirements.issubset(products_available):
                    chain.append(debugger)
                    debuggers.remove(debugger)
                    added_any = True
            if not added_any:
                debuggers_left = [debugger.get_product() for debugger in debuggers]
                msg = f"Could not create debugger chain. Failed to satisfy any of the following debuggers' requirements: {debuggers_left}"
                raise ValueError(msg)

        if not chain:
            return None

        # chain the debuggers via set_next()
        for i in range(len(chain) - 1):
            chain[i].set_next(chain[i + 1])

        return chain[0]

    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)
