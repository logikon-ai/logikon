
from __future__ import annotations

from typing import List, Optional, Any

from pydantic import BaseModel

class DebugConfig(BaseModel):
    """Configuration for scoring."""

    expert_model: str = "text-ada-001"
    model_framework: str = "OpenAI"
    metrics: List[str] = []
    artifacts: List[str] = ["informal_argmap"]
    report_to: List[str] = []
    
        