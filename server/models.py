from pydantic import BaseModel
from typing import Any, Optional, Dict

class Action(BaseModel):
    action_type: str
    payload: Dict[str, Any]

class Observation(BaseModel):
    state: Dict[str, Any]
    info: Optional[Dict[str, Any]] = None

class Reward(BaseModel):
    value: float
    is_terminal: bool
