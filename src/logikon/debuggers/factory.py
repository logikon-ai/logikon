from __future__ import annotations

from typing import Optional, List
import logging

from logikon.schemas.configs import DebugConfig
from logikon.debuggers.base import Debugger
from logikon.debuggers.registry import get_debugger_registry

class DebuggerFactory:
    """Factory for creating a debugger chain based on a config."""

    def create(self, config: DebugConfig) -> Optional[Debugger]:
        """Create a debugger chain based on a config."""

        # Check if all metrics and artifacts keywords are registered
        registry = get_debugger_registry()
        for keyword in config.metrics + config.artifacts:
            if keyword not in registry:
                raise ValueError(f"Metrics / artifact keyword '{keyword}' does not correspond to a registered debugger.")

        # Create list of debuggers from config and registry
        debuggers = [
            registry[keyword](config)
            for keyword in config.metrics + config.artifacts
        ]

        # Check if all requirements are met and add further debuggers as necessary
        requirements = set()
        requirements_satisfied = False

        while not requirements_satisfied:

            products = set(debugger.get_product() for debugger in debuggers)
            for debugger in debuggers:
                requirements.update(debugger.get_requirements())

            if requirements.issubset(products):
                requirements_satisfied = True

            for requirement_kw in requirements:
                if requirement_kw not in products:
                    if requirement_kw not in registry:
                        raise ValueError(f"Debugger requirement '{requirement_kw}' does not correspond to a registered debugger.")
                    debuggers.append(registry[requirement_kw](config))


        # Create debugger chain respecting the dependencies (iteratively add and remove debuggers)
        chain: List[Debugger] = []
        while debuggers:
            added_any = False
            products_available = set(debugger.get_product() for debugger in chain)
            for debugger in debuggers:
                requirements = set(debugger.get_requirements())
                if requirements.issubset(products_available):
                    chain.append(debugger)
                    debuggers.remove(debugger)
                    added_any = True
            if not added_any:
                debuggers_left = [debugger.get_product() for debugger in debuggers]
                raise ValueError(f"Could not create debugger chain. Failed to satisfy any of the following debuggers requirements: {debuggers_left}")

        if not chain:
            return None

        # chain the debuggers via set_next()
        for i in range(len(chain) - 1):
            chain[i].set_next(chain[i+1])

        return chain[0]


    @property
    def logger(self) -> logging.Logger:
        """
        A :class:`logging.Logger` that can be used within the :meth:`run()` method.
        """
        return logging.getLogger(self.__class__.__name__)
