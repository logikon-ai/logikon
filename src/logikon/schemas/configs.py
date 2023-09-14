
from __future__ import annotations

from typing import List, Optional, Any, Dict

from pydantic import BaseModel

class DebugConfig(BaseModel):
    """Configuration for scoring."""

    expert_model: str = "text-ada-001"
    expert_model_kwargs: Dict[str, Any] = {"temperature": 0.9}
    llm_framework: str = "OpenAI"
    generation_kwargs: Optional[Dict] = None
    metrics: List[str] = []
    artifacts: List[str] = ["informal_argmap"]
    report_to: List[str] = []
    
        