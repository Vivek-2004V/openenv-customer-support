import random
import copy
from typing import Tuple, List, Dict, Any
from server.models import Action, Observation, Reward
from server.tasks import TASKS

# ── Real-world customer support scenarios ─────────────────────────────────────
# Each scenario covers a distinct category with strong classification signals
# and realistic urgency cues so agents can learn correct behavior.
SCENARIOS = [
    # REFUND — angry, clear billing error
    {
        "ticket_text": "I was charged twice for my annual subscription this month. I have the bank statement to prove it. I want one payment refunded immediately.",
        "sentiment": "angry",
        "expected_classification": "refund",
        "expected_priority": "high",
        "sla_steps": 5,
        "context": "Duplicate billing charge. Customer has proof. High urgency.",
    },
    # REFUND — neutral, post-cancellation billing
    {
        "ticket_text": "I cancelled my subscription 3 days ago but was still billed for next month. I need this refunded please.",
        "sentiment": "neutral",
        "expected_classification": "refund",
        "expected_priority": "medium",
        "sla_steps": 8,
        "context": "Post-cancellation charge. Polite customer, standard urgency.",
    },
    # TECHNICAL ISSUE — angry, regression crash
    {
        "ticket_text": "The app crashes every single time I open a file larger than 50MB. This has been broken since last week's update — I cannot do my work.",
        "sentiment": "angry",
        "expected_classification": "technical_issue",
        "expected_priority": "high",
        "sla_steps": 6,
        "context": "Regression bug blocking core workflow.",
    },
    # TECHNICAL ISSUE — panicked, team outage
    {
        "ticket_text": "Our entire development team cannot access the API since this morning. We have a production deployment in 2 hours — this is a critical emergency!",
        "sentiment": "panicked",
        "expected_classification": "technical_issue",
        "expected_priority": "high",
        "sla_steps": 3,
        "context": "P0 outage. Production deadline imminent.",
    },
    # TECHNICAL ISSUE — neutral, minor UI bug
    {
        "ticket_text": "The dark mode setting doesn't save when I refresh the page. It reverts to light mode every time. Minor issue but a bit annoying.",
        "sentiment": "neutral",
        "expected_classification": "technical_issue",
        "expected_priority": "low",
        "sla_steps": 10,
        "context": "Minor UI preference bug. No business impact.",
    },
    # LOGIN ISSUE — panicked, team locked out
    {
        "ticket_text": "I reset my password twice but I still cannot log in. My whole team is locked out and we have a client demo starting in 15 minutes!",
        "sentiment": "panicked",
        "expected_classification": "login_issue",
        "expected_priority": "high",
        "sla_steps": 4,
        "context": "Password reset loop, team locked out. Time critical.",
    },
    # LOGIN ISSUE — neutral, standard password reset
    {
        "ticket_text": "Hi, I forgot my password. Can you help me reset it or send me a recovery link? No rush, just let me know when you can.",
        "sentiment": "neutral",
        "expected_classification": "login_issue",
        "expected_priority": "low",
        "sla_steps": 12,
        "context": "Standard password recovery. No urgency.",
    },
    # GENERAL INQUIRY — curious, pricing
    {
        "ticket_text": "Do you offer a non-profit discount? We are a registered charity and your standard price is a little high for our annual budget.",
        "sentiment": "curious",
        "expected_classification": "general_inquiry",
        "expected_priority": "low",
        "sla_steps": 10,
        "context": "Pricing question. Low urgency.",
    },
    # GENERAL INQUIRY — neutral, how-to
    {
        "ticket_text": "How do I export all my project data to CSV? I need to share it with a client in a different format.",
        "sentiment": "neutral",
        "expected_classification": "general_inquiry",
        "expected_priority": "low",
        "sla_steps": 10,
        "context": "Basic how-to question. No urgency.",
    },
    # SECURITY — concerned, unauthorized login
    {
        "ticket_text": "I received an alert that someone logged into my account from a location I don't recognize. I did not authorize this. Is my account compromised?",
        "sentiment": "concerned",
        "expected_classification": "security",
        "expected_priority": "high",
        "sla_steps": 4,
        "context": "Potential account takeover. Must be high priority.",
    },
    # SECURITY — concerned, encryption question
    {
        "ticket_text": "After reading about recent data breaches at other SaaS companies, I want to understand what encryption you use to protect my credit card details.",
        "sentiment": "concerned",
        "expected_classification": "security",
        "expected_priority": "medium",
        "sla_steps": 7,
        "context": "Security assurance question. No active breach.",
    },
    # FEEDBACK — happy, positive
    {
        "ticket_text": "The new dashboard redesign is fantastic! Generating a report used to take me 10 minutes — now it's instant. Your team did an amazing job!",
        "sentiment": "happy",
        "expected_classification": "feedback",
        "expected_priority": "low",
        "sla_steps": 15,
        "context": "Positive feedback. No action needed urgently.",
    },
]


class CustomerSupportEnv:
    def __init__(self):
        """Initialize the Enterprise AI Customer Support environment."""
        self.queue: List[Dict] = []
        self.resolved_count = 0
        self.total_reward = 0.0
        self.current_step = 0
        self.actions_taken: set = set()
        self.history: List[Dict] = []

    def reset(self) -> Observation:
        """Standard OpenEnv API: Initialize a new session with a queue of 3 tickets."""
        self.queue = [copy.deepcopy(s) for s in random.sample(SCENARIOS, 3)]
        self.resolved_count = 0
        self.total_reward = 0.0
        self.current_step = 0
        self.actions_taken = set()
        self.history = []
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
                    "status": "session_complete",
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
            "status": ticket.get("status", "open"),
            "steps_taken": self.current_step,
            "classification": ticket.get("classification"),
            "response": ticket.get("response"),
            "queue_size": len(self.queue),
            "sla_limit": ticket["sla_steps"],
            "sla_warning": self.current_step >= ticket["sla_steps"] - 2,
            "total_reward": self.total_reward,
            "resolved": self.resolved_count,
            "last_step_status": self.history[-1]["status"] if self.history else "neutral",
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

    # Static tasks attribute for discovery
    tasks = TASKS

    def get_tasks(self) -> List[Dict]:
        """Expose available tasks for OpenEnv discovery."""
        return TASKS

    def grade(self, task_id: str, history: List[Dict[str, Any]], ground_truth: Dict[str, Any]) -> float:
        """Standard naming for automated graders."""
        return self.grade_task(task_id, history, ground_truth)

    def grade_task(self, task_id: str, history: List[Dict[str, Any]], ground_truth: Dict[str, Any]) -> float:
        """Grade a specific task execution. Returns float in [0.0, 1.0]."""
        from server.grader import score_episode

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
            elif pri in ("high", "medium", "low"):
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
                if current_ticket["sentiment"] in ("angry", "panicked", "concerned"):
                    empathy_words = ["sorry", "apologize", "understand", "concern", "frustrat"]
                    if not any(w in resp.lower() for w in empathy_words):
                        reward_val -= 0.1
                        message = "⚠️ Response drafted but missing empathy for upset customer."
                    else:
                        message = "✅ Empathetic response drafted."
                else:
                    message = "✅ Response drafted."

        elif a_type == "resolve":
            has_classify = bool(current_ticket.get("classification"))
            has_priority = bool(current_ticket.get("priority"))
            has_response = bool(current_ticket.get("response"))

            if has_classify and has_priority and has_response:
                reward_val += 0.4
                current_ticket["status"] = "closed"
                self.resolved_count += 1
                message = "✅ Ticket fully resolved!"
                # SLA penalty
                if self.current_step > current_ticket["sla_steps"]:
                    reward_val -= 0.25
                    message += " ⚠️ SLA breached."
            else:
                missing = [k for k, v in [("classification", has_classify), ("priority", has_priority), ("response", has_response)] if not v]
                reward_val -= 0.2
                message = f"❌ Cannot resolve — missing: {', '.join(missing)}."

            self.queue.pop(0)
            self.current_step = 0
            self.actions_taken = set()
            if not self.queue:
                is_terminal = True

        elif a_type == "escalate":
            if current_ticket["sentiment"] in ("angry", "panicked"):
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

        # Small per-step cost to encourage efficiency
        reward_val -= 0.02

        self.total_reward += reward_val
        status = "success" if reward_val > 0 else "failed" if reward_val < 0 else "neutral"

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
