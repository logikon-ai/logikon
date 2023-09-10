
from __future__ import annotations

from typing import List, Optional, Any

from pydantic import BaseModel

class DebugConfig(BaseModel):
    """Configuration for scoring."""

    metrics: List[str] = []
    artifacts: List[Any] = []
    report_to: List[str] = []
    
        