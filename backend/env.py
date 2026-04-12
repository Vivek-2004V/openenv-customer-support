from __future__ import annotations
import random
import copy
import os
import json
from typing import Tuple, List, Dict, Any
from .models import Action, Observation, Reward, TicketStatus, StepStatus, Sentiment, Priority, Classification

def load_tasks_from_json():
    """Load tasks from tasks.json strictly."""
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

TASKS = load_tasks_from_json()

# ── Real-world customer support scenarios ─────────────────────────────────────
SCENARIOS = [
    {
        "ticket_text": "I was charged twice for my annual subscription this month. I have the bank statement to prove it. I want one payment refunded immediately.",
        "sentiment": Sentiment.ANGRY,
        "expected_classification": Classification.REFUND,
        "expected_priority": Priority.HIGH,
        "sla_steps": 5,
        "context": "Duplicate billing charge. Customer has proof. High urgency.",
    },
    {
        "ticket_text": "I cancelled my subscription 3 days ago but was still billed for next month. I need this refunded please.",
        "sentiment": Sentiment.NEUTRAL,
        "expected_classification": Classification.REFUND,
        "expected_priority": Priority.MEDIUM,
        "sla_steps": 8,
        "context": "Post-cancellation charge. Polite customer, standard urgency.",
    },
    {
        "ticket_text": "The app crashes every single time I open a file larger than 50MB. This has been broken since last week's update — I cannot do my work.",
        "sentiment": Sentiment.ANGRY,
        "expected_classification": Classification.TECHNICAL_ISSUE,
        "expected_priority": Priority.HIGH,
        "sla_steps": 6,
        "context": "Regression bug blocking core workflow.",
    },
    {
        "ticket_text": "Our entire development team cannot access the API since this morning. We have a production deployment in 2 hours — this is a critical emergency!",
        "sentiment": Sentiment.PANICKED,
        "expected_classification": Classification.TECHNICAL_ISSUE,
        "expected_priority": Priority.HIGH,
        "sla_steps": 3,
        "context": "P0 outage. Production deadline imminent.",
    },
    {
        "ticket_text": "The dark mode setting doesn't save when I refresh the page. It reverts to light mode every time. Minor issue but a bit annoying.",
        "sentiment": Sentiment.NEUTRAL,
        "expected_classification": Classification.TECHNICAL_ISSUE,
        "expected_priority": Priority.LOW,
        "sla_steps": 10,
        "context": "Minor UI preference bug. No business impact.",
    },
    {
        "ticket_text": "I reset my password twice but I still cannot log in. My whole team is locked out and we have a client demo starting in 15 minutes!",
        "sentiment": Sentiment.PANICKED,
        "expected_classification": Classification.LOGIN_ISSUE,
        "expected_priority": Priority.HIGH,
        "sla_steps": 4,
        "context": "Password reset loop, team locked out. Time critical.",
    },
    {
        "ticket_text": "Hi, I forgot my password. Can you help me reset it or send me a recovery link? No rush, just let me know when you can.",
        "sentiment": Sentiment.NEUTRAL,
        "expected_classification": Classification.LOGIN_ISSUE,
        "expected_priority": Priority.LOW,
        "sla_steps": 12,
        "context": "Standard password recovery. No urgency.",
    },
    {
        "ticket_text": "Do you offer a non-profit discount? We are a registered charity and your standard price is a little high for our annual budget.",
        "sentiment": Sentiment.CURIOUS,
        "expected_classification": Classification.GENERAL_INQUIRY,
        "expected_priority": Priority.LOW,
        "sla_steps": 10,
        "context": "Pricing question. Low urgency.",
    },
    {
        "ticket_text": "How do I export all my project data to CSV? I need to share it with a client in a different format.",
        "sentiment": Sentiment.NEUTRAL,
        "expected_classification": Classification.GENERAL_INQUIRY,
        "expected_priority": Priority.LOW,
        "sla_steps": 10,
        "context": "Basic how-to question. No urgency.",
    },
    {
        "ticket_text": "I received an alert that someone logged into my account from a location I don't recognize. I did not authorize this. Is my account compromised?",
        "sentiment": Sentiment.CONCERNED,
        "expected_classification": Classification.SECURITY,
        "expected_priority": Priority.HIGH,
        "sla_steps": 4,
        "context": "Potential account takeover. Must be high priority.",
    },
    {
        "ticket_text": "After reading about recent data breaches at other SaaS companies, I want to understand what encryption you use to protect my credit card details.",
        "sentiment": Sentiment.CONCERNED,
        "expected_classification": Classification.SECURITY,
        "expected_priority": Priority.MEDIUM,
        "sla_steps": 7,
        "context": "Security assurance question. No active breach.",
    },
    {
        "ticket_text": "The new dashboard redesign is fantastic! Generating a report used to take me 10 minutes — now it's instant. Your team did an amazing job!",
        "sentiment": Sentiment.HAPPY,
        "expected_classification": Classification.FEEDBACK,
        "expected_priority": Priority.LOW,
        "sla_steps": 15,
    },
]

# ── Internal Knowledge Base (Product Policies) ───────────────────────────────
KNOWLEDGE_BASE = {
    "refund_policy": {
        "text": "Full refunds are allowed within 30 days for annual plans. Monthly plans are non-refundable after 48 hours. Enterprise contracts require management approval for any deviation.",
        "keywords": ["refund", "money back", "billing", "policy"]
    },
    "security_protocol": {
        "text": "For suspected breaches, immediately lock the account and escalate to the Security Team. Do NOT share recovery links via ticket. Multi-factor authentication is mandatory for all admins.",
        "keywords": ["security", "breach", "hack", "compromised", "login"]
    },
    "technical_specs": {
        "text": "Export to CSV is limited to 500MB per file. Browser support: Chrome, Firefox, Safari (latest 2 versions). Mobile app requires iOS 15+ or Android 12+.",
        "keywords": ["export", "csv", "crash", "bug", "requirement", "specs"]
    },
    "discount_policy": {
        "text": "Registered charities (501c3) get 40% off. Academic institutions get 20% off. Volume discounts start at 50 user seats.",
        "keywords": ["discount", "charity", "non-profit", "price", "cheap"]
    }
}

class CustomerSupportEnv:
    def __init__(self):
        """Initialize the Enterprise AI Customer Support environment."""
        self.queue: List[Dict] = []
        self.resolved_count = 0
        self.total_reward = 0.0
        self.current_step = 0
        self.actions_taken: set = set()
        self.history: List[Dict] = []
        self.kb_search_result: str | None = None
        self.is_clarified: bool = False

    def reset(self) -> Observation:
        """Standard OpenEnv API: Initialize a new session with a queue of 3 tickets."""
        self.queue = [copy.deepcopy(s) for s in random.sample(SCENARIOS, 3)]
        self.resolved_count = 0
        self.total_reward = 0.0
        self.current_step = 0
        self.actions_taken = set()
        self.history = []
        self.kb_search_result = None
        self.is_clarified = False
        return self.state()

    def state(self) -> Observation:
        """Standard OpenEnv API: Retrieve the current observation state."""
        current_info = {
            "queue": [t["ticket_text"][:40] + "..." for t in self.queue],
            "resolved": self.resolved_count,
            "total_reward": self.total_reward,
            "queue_size": len(self.queue),
        }

        if not self.queue:
            return Observation(
                state={
                    "status": TicketStatus.SESSION_COMPLETE,
                    "message": "All tickets in queue processed.",
                    "total_reward": self.total_reward,
                    "resolved": self.resolved_count,
                    "info": current_info,
                },
                info=current_info,
            )

        ticket = self.queue[0]
        obs_state = {
            "ticket_text": ticket["ticket_text"],
            "sentiment": ticket["sentiment"],
            "context": ticket.get("context", ""),
            "priority": ticket.get("priority"),
            "status": ticket.get("status", TicketStatus.OPEN),
            "steps_taken": self.current_step,
            "classification": ticket.get("classification"),
            "response": ticket.get("response"),
            "queue_size": len(self.queue),
            "sla_limit": ticket["sla_steps"],
            "sla_warning": self.current_step >= ticket["sla_steps"] - 2,
            "total_reward": self.total_reward,
            "resolved": self.resolved_count,
            "last_step_status": self.history[-1]["status"] if self.history else StepStatus.NEUTRAL,
            "kb_context": self.kb_search_result,
            "is_clarified": self.is_clarified,
            "info": current_info,
        }
        return Observation(state=obs_state, info=current_info)

    @property
    def current_state(self) -> Dict:
        """Helper: current ticket state dict for grading."""
        return self.state().state

    @property
    def ground_truth(self) -> Dict | None:
        """Helper: expected values for the current ticket."""
        return self.queue[0] if self.queue else None

    tasks = TASKS

    def get_tasks(self) -> List[Dict]:
        """Expose available tasks for OpenEnv discovery."""
        return TASKS

    def grade(self, task_id: str, history: List[Dict[str, Any]], ground_truth: Dict[str, Any]) -> float:
        """Standard naming for automated graders."""
        return self.grade_task(task_id, history, ground_truth)

    def grade_task(self, task_id: str, history: List[Dict[str, Any]], ground_truth: Dict[str, Any]) -> float:
        """Grade a specific task execution. Returns float in [0.0, 1.0]."""
        from .grader import score_episode

        diff = "EASY"
        for t in TASKS:
            if t["id"] == task_id:
                diff = t["difficulty"]
                break

        return score_episode(diff, history, ground_truth, task_id=task_id)

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, dict]:
        """Standard OpenEnv API: Apply an action to the environment."""
        if not self.queue:
            return self.state(), Reward(value=0, is_terminal=True), True, {"error": "Queue empty"}

        self.current_step += 1
        reward_val = 0.0
        is_terminal = False
        message = ""

        current_ticket = self.queue[0]
        a_type = action.action_type
        payload = action.payload

        # ── Action Logic ──────────────────────────────────────────────────────
        if a_type == "classify_ticket":
            cat = payload.get("classification", "")
            current_ticket["classification"] = cat
            if cat == current_ticket["expected_classification"]:
                reward_val += 0.35
                message = f"✅ Classified correctly as '{cat}'."
            else:
                reward_val -= 0.2
                message = f"❌ Wrong classification '{cat}' (expected: {current_ticket['expected_classification']})."

        elif a_type == "assign_priority":
            pri = payload.get("priority", "")
            current_ticket["priority"] = pri
            if pri == current_ticket["expected_priority"]:
                reward_val += 0.25
                message = f"✅ Priority set to '{pri}' correctly."
            elif pri in (Priority.HIGH, Priority.MEDIUM, Priority.LOW):
                reward_val -= 0.15
                message = f"⚠️ Priority '{pri}' (expected: {current_ticket['expected_priority']})."
            else:
                reward_val -= 0.2
                message = f"❌ Invalid priority value '{pri}'."

        elif a_type == "generate_response":
            resp = payload.get("response", "")
            current_ticket["response"] = resp
            if not resp.strip():
                reward_val -= 0.2
                message = "❌ Empty response — no reward."
            else:
                reward_val += 0.2
                # Empathy check for negative sentiment
                if current_ticket["sentiment"] in (Sentiment.ANGRY, Sentiment.PANICKED, Sentiment.CONCERNED):
                    empathy_words = ["sorry", "apologize", "understand", "concern", "frustrat"]
                    if not any(w in resp.lower() for w in empathy_words):
                        reward_val -= 0.1
                        message = "⚠️ Response drafted but missing empathy for upset customer."
                    else:
                        message = "✅ Empathetic response drafted."
                else:
                    message = "✅ Response drafted."

        elif a_type == "search_kb":
            query = payload.get("query", "").lower()
            if not query:
                reward_val -= 0.1
                message = "❌ Empty KB query."
            else:
                found = False
                for key, data in KNOWLEDGE_BASE.items():
                    if any(k in query for k in data["keywords"]):
                        self.kb_search_result = f"POLICY: {data['text']}"
                        reward_val += 0.15
                        message = f"✅ KB result found for '{key}'."
                        found = True
                        break
                if not found:
                    reward_val -= 0.05
                    message = f"❓ No KB results for '{query}'."

        elif a_type == "ask_clarification":
            self.is_clarified = True
            reward_val += 0.1
            message = "✅ Clarification requested from customer."

        # ── Action: Resolve ──────────────────────────────────────────────────
        elif a_type == "resolve":
            if current_ticket["status"] == TicketStatus.CLOSED:
                reward_val += 0.0
                message = "⚠️ Ticket is already closed."
            else:
                has_classify = bool(current_ticket.get("classification"))
                has_priority = bool(current_ticket.get("priority"))
                has_response = bool(current_ticket.get("response"))
                
                # Check for vague tickets that require clarification
                needs_clarify = "vague" in current_ticket.get("context", "").lower()
                if needs_clarify and not self.is_clarified:
                    reward_val -= 0.4
                    message = "❌ Cannot resolve — ticket details are vague, you must 'ask_clarification' first."
                elif has_classify and has_priority and has_response:
                    reward_val += 0.4
                    current_ticket["status"] = TicketStatus.CLOSED
                    self.resolved_count += 1
                    message = "✅ Ticket fully resolved!"
                    # SLA penalty
                    if self.current_step > current_ticket["sla_steps"]:
                        reward_val -= 0.25
                        message += " ⚠️ SLA breached."
                else:
                    missing = []
                    if not has_classify: missing.append("classification")
                    if not has_priority: missing.append("priority")
                    if not has_response: missing.append("response")
                    reward_val -= 0.2
                    message = f"❌ Cannot resolve — missing: {', '.join(missing)}."
            
            if current_ticket["status"] == TicketStatus.CLOSED:
                self.queue.pop(0)
                self.current_step = 0
                self.actions_taken = set()
                self.kb_search_result = None
                self.is_clarified = False
                if not self.queue:
                    is_terminal = True

        elif a_type == "escalate":
            if current_ticket["sentiment"] in (Sentiment.ANGRY, Sentiment.PANICKED):
                reward_val += 0.15
                message = "✅ Escalated — appropriate for high-urgency customer."
            else:
                reward_val -= 0.15
                message = "⚠️ Escalated a non-urgent ticket — overkill."
            self.queue.pop(0)
            self.current_step = 0
            self.actions_taken = set()
            if not self.queue:
                is_terminal = True

        else:
            reward_val -= 0.1
            message = f"❌ Unknown action type '{a_type}'."

        # Penalize repeated actions on the same ticket
        if a_type in self.actions_taken:
            reward_val -= 0.1
            message += " (Repeated action penalty)"
        self.actions_taken.add(a_type)

        # ── Dynamic Sentiment Decay ──
        # Every 3 steps without resolution, sentiment worsens
        if self.current_step > 0 and self.current_step % 3 == 0:
            s_levels = [Sentiment.HAPPY, Sentiment.CURIOUS, Sentiment.NEUTRAL, Sentiment.CONCERNED, Sentiment.ANGRY, Sentiment.PANICKED]
            current_idx = s_levels.index(current_ticket["sentiment"]) if current_ticket["sentiment"] in s_levels else 2
            if current_idx < len(s_levels) - 1:
                current_ticket["sentiment"] = s_levels[current_idx + 1]
                message += f" ⚠️ Customer getting frustrated ({current_ticket['sentiment']})."
                reward_val -= 0.05

        # Update aggregate reward
        self.total_reward += float(reward_val)
        status = StepStatus.SUCCESS if reward_val > 0 else StepStatus.FAILED if reward_val < 0 else StepStatus.NEUTRAL

        self.history.append({
            "step_count": len(self.history) + 1,
            "action": a_type,
            "reward": reward_val,
            "status": status,
            "message": message,
        })

        step_info = {
            "message": message,
            "status": status,
            "reward": reward_val,
        }

        return self.state(), Reward(value=reward_val, is_terminal=is_terminal), is_terminal, step_info

    def close(self):
        """Cleanup resources if needed."""
        pass
