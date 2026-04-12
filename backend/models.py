from pydantic import BaseModel
from typing import Any, Optional, Dict, List
from enum import Enum

class TicketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    SESSION_COMPLETE = "session_complete"

class StepStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    NEUTRAL = "neutral"

class Sentiment(str, Enum):
    ANGRY = "angry"
    NEUTRAL = "neutral"
    PANICKED = "panicked"
    CURIOUS = "curious"
    HAPPY = "happy"
    CONCERNED = "concerned"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Classification(str, Enum):
    REFUND = "refund"
    TECHNICAL_ISSUE = "technical_issue"
    LOGIN_ISSUE = "login_issue"
    GENERAL_INQUIRY = "general_inquiry"
    FEEDBACK = "feedback"
    SECURITY = "security"

class Action(BaseModel):
    action_type: str
    payload: Dict[str, Any]

class Observation(BaseModel):
    state: Dict[str, Any]
    info: Optional[Dict[str, Any]] = None

class Reward(BaseModel):
    value: float
    is_terminal: bool

# --- AI Configuration & Prompts ---

SYSTEM_PROMPT = """
You are an Enterprise AI Customer Support agent resolving a ticket pipeline.
For each ticket, you must:
{"action_type": "<name>", "payload": {...}}

Available Actions:
- classify_ticket: {"classification": "refund" | "technical_issue" | "login_issue" | "general_inquiry" | "feedback" | "security"}
- assign_priority: {"priority": "low" | "medium" | "high"}
- generate_response: {"response": "<text>"}
- search_kb: {"query": "<search_term>"} -- Returns internal policy facts
- ask_clarification: {"question": "<text>"} -- Used if a ticket is vague
- resolve: {} -- Finalizes ticket
- escalate: {} -- For extreme cases
""".strip()

DEFAULT_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
DEFAULT_API_BASE = "https://router.huggingface.co/v1"
