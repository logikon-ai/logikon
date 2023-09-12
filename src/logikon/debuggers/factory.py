from __future__ import annotations

from typing import Optional

from logikon.schemas.configs import DebugConfig
from logikon.debuggers.base import Debugger

class DebuggerFactory:
    """Factory for creating a debugger chain based on a config."""

    def create(self, config: DebugConfig) -> Optional[Debugger]:
        """Create a debugger chain based on a config."""

        # Check if all metrics and artifacts keywords are registered

        # Create list of debuggers from config and registry

        # Check if all requirements are met and add further debuggers as necessary
        
        # Create dependency graph of debuggers (abort if cycle is detected) 

        # Create debugger chain from dependency graph (iteratively add and remove roots)

        return None


