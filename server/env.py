import random
import time
import copy
from typing import Tuple, List, Dict
from server.models import Action, Observation, Reward

# Expanded Scenarios with SLA metadata
SCENARIOS = [
    {
        "ticket_text": "I bought a premium subscription but it's not working. I want my money back right now!",
        "sentiment": "angry",
        "expected_classification": "refund",
        "expected_priority": "high",
        "sla_steps": 5,
    },
    {
        "ticket_text": "How do I change my profile picture? I tried looking in the settings but couldn't find it.",
        "sentiment": "neutral",
        "expected_classification": "general_inquiry",
        "expected_priority": "low",
        "sla_steps": 8,
    },
    {
        "ticket_text": "I can't log into my account, and I have a huge presentation in 10 minutes that needs the data!",
        "sentiment": "panicked",
        "expected_classification": "login_issue",
        "expected_priority": "high",
        "sla_steps": 3,
    },
    {
        "ticket_text": "The latest update keeps crashing on my Android phone. Please fix it ASAP.",
        "sentiment": "angry",
        "expected_classification": "technical_issue",
        "expected_priority": "medium",
        "sla_steps": 6,
    },
    {
        "ticket_text": "Do you offer any discounts for students or non-profits?",
        "sentiment": "curious",
        "expected_classification": "general_inquiry",
        "expected_priority": "low",
        "sla_steps": 10,
    },
    {
        "ticket_text": "I just wanted to say that your support team is amazing! Thank you for the quick help.",
        "sentiment": "happy",
        "expected_classification": "feedback",
        "expected_priority": "low",
        "sla_steps": 12,
    },
    {
        "ticket_text": "I'm worried about my data privacy after the recent news. Can you explain your encryption?",
        "sentiment": "concerned",
        "expected_classification": "security",
        "expected_priority": "medium",
        "sla_steps": 7,
    }
]

class CustomerSupportEnv:
    def __init__(self):
        """Initialize the Enterprise AI Customer Support environment."""
        self.queue: List[Dict] = []
        self.resolved_count = 0
        self.total_reward = 0.0
        self.max_steps_per_ticket = 10
        self.current_step = 0
        self.actions_taken = set()
        self.history = []

    def reset(self) -> Observation:
        """Initialize a new enterprise session with a queue of tickets."""
        # Pick 3 random unique scenarios for the queue
        self.queue = [copy.deepcopy(s) for s in random.sample(SCENARIOS, 3)]
        self.resolved_count = 0
        self.total_reward = 0.0
        self.current_step = 0
        self.actions_taken = set()
        self.history = []
        
        return self.state()

    def state(self) -> Observation:
        """Standard OpenEnv API: Retrieve the current observation state."""
        # Shared info for both state and info fields to satisfy frontend expectations
        current_info = {
            "queue": [t["ticket_text"][:30] + "..." for t in self.queue],
            "resolved": self.resolved_count,
            "total_reward": self.total_reward,
            "queue_size": len(self.queue)
        }

        if not self.queue:
            return Observation(
                state={
                    "status": "session_complete", 
                    "message": "All tickets in queue processed.",
                    "total_reward": self.total_reward,
                    "resolved": self.resolved_count,
                    "info": current_info
                },
                info=current_info
            )
        
        ticket = self.queue[0]
        obs_state = {
            "ticket_text": ticket["ticket_text"],
            "sentiment": ticket["sentiment"],
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
            "info": current_info # Redundant but fixes frontend lookups
        }
        
        return Observation(state=obs_state, info=current_info)

    @property
    def current_state(self):
        """Helper for the grader to access the current ticket state dictionary."""
        obs = self.state()
        return obs.state

    @property
    def ground_truth(self):
        """Helper for the grader to access the expected values of the current ticket."""
        if not self.queue:
            return None
        return self.queue[0]

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

        # Action Logic
        if a_type == "classify_ticket":
            cat = payload.get("classification")
            current_ticket["classification"] = cat
            reward_val += 0.3 if cat == current_ticket["expected_classification"] else -0.2
            message = "Classified. "
            
        elif a_type == "assign_priority":
            pri = payload.get("priority")
            current_ticket["priority"] = pri
            reward_val += 0.2 if pri == current_ticket["expected_priority"] else -0.2
            message = "Priority set. "
            
        elif a_type == "generate_response":
            resp = payload.get("response", "")
            current_ticket["response"] = resp
            has_empathy = any(w in resp.lower() for w in ["sorry", "apologize", "understand", "help"])
            if current_ticket["sentiment"] == "angry" and not has_empathy:
                reward_val -= 0.1
            reward_val += 0.2 if resp.strip() else -0.2
            message = "Response drafted. "
            
        elif a_type == "resolve":
            # Check completion
            if current_ticket.get("classification") and current_ticket.get("priority") and current_ticket.get("response"):
                reward_val += 0.4
                message = "Ticket Resolved!"
                current_ticket["status"] = "closed"
                self.resolved_count += 1
                # SLA Check
                if self.current_step > current_ticket["sla_steps"]:
                    reward_val -= 0.3
                    message += " (SLA Breached)"
            else:
                reward_val -= 0.2
                message = "Resolution attempted without full data."
            
            # Move to next ticket
            self.queue.pop(0)
            self.current_step = 0
            self.actions_taken = set()
            if not self.queue:
                is_terminal = True
            
        elif a_type == "escalate":
            reward_val += 0.2 if current_ticket["sentiment"] == "angry" else -0.2
            message = "Escalated to Manager."
            # Escalation closes current and moves on
            self.queue.pop(0)
            self.current_step = 0
            if not self.queue:
                is_terminal = True

        # Penalize repeated or excessive steps
        if a_type in self.actions_taken:
            reward_val -= 0.1
        self.actions_taken.add(a_type)
        reward_val -= 0.05 # Smaller per-step cost

        self.total_reward += reward_val

        # Step-level Status Logic
        status = "success" if reward_val > 0 else "failed" if reward_val < 0 else "neutral"
        
        # Update History with detailed metadata
        self.history.append({
            "step_count": len(self.history) + 1,
            "action": a_type,
            "reward": reward_val,
            "status": status,
            "message": message
        })
        
        step_info = {
            "message": message,
            "status": status,
            "reward": reward_val
        }
        
        return self.state(), Reward(value=reward_val, is_terminal=is_terminal), is_terminal, step_info
