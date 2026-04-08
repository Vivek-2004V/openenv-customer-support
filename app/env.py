import random
import copy
from typing import Tuple
from app.models import Action, Observation, Reward

# Pre-defined real-world support tickets for the workflow simulation
SCENARIOS = [
    {
        "ticket_text": "I bought a premium subscription but it's not working. I want my money back right now!",
        "sentiment": "angry",
        "expected_classification": "refund",
        "expected_priority": "high",
    },
    {
        "ticket_text": "How do I change my profile picture? I tried looking in the settings but couldn't find it.",
        "sentiment": "neutral",
        "expected_classification": "general_inquiry",
        "expected_priority": "low",
    },
    {
        "ticket_text": "I can't log into my account, and I have a huge presentation in 10 minutes that needs the data!",
        "sentiment": "angry",
        "expected_classification": "login_issue",
        "expected_priority": "high",
    },
    {
        "ticket_text": "Thank you so much for fixing the bug! Everything is running perfectly today.",
        "sentiment": "happy",
        "expected_classification": "feedback",
        "expected_priority": "low",
    }
]

class CustomerSupportEnv:
    def __init__(self):
        """Initialize the AI Customer Support environment."""
        self.current_state = None
        self.ground_truth = None
        self.max_steps = 10
        self.current_step = 0
        self.actions_taken = set()

    def reset(self) -> Observation:
        """Reset the environment to a new random customer support ticket."""
        self.ground_truth = random.choice(SCENARIOS)
        self.current_step = 0
        self.actions_taken = set()
        
        # State strictly matching requirements
        self.current_state = {
            "ticket_text": self.ground_truth["ticket_text"],
            "sentiment": self.ground_truth["sentiment"],
            "priority": None,        # AI will assign (low / medium / high)
            "status": "open",        # Track ticket lifecycle
            "steps_taken": 0,
            "classification": None,  # AI will classify
            "response": None         # AI's generated reply
        }
        
        return self.state()
        
    def state(self) -> Observation:
        """Return the current state of the environment."""
        return Observation(
            state=self.current_state,
            info={"max_steps": self.max_steps}
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, dict]:
        """Apply an action to process the ticket workflow and evaluate using dense rewards."""
        self.current_step += 1
        self.current_state["steps_taken"] += 1
        
        reward_val = 0.0
        is_terminal = False
        message = ""
        
        a_type = action.action_type
        payload = action.payload
        
        # Ensure ticket is open to take steps
        if self.current_state["status"] == "closed":
            return self.state(), Reward(value=-0.2, is_terminal=True), True, {"error": "Ticket is already closed"}

        # Penalize repeated actions (-0.1)
        if a_type in self.actions_taken:
            reward_val -= 0.1
            message += "Repeated action penalty. "
        else:
            self.actions_taken.add(a_type)
            
        # Penalize taking too many steps (-0.1 step cost)
        reward_val -= 0.1

        # Simulate the structured workflows with standard explicit dense reward triggers
        if a_type == "classify_ticket":
            category = payload.get("classification")
            self.current_state["classification"] = category
            if category == self.ground_truth["expected_classification"]:
                reward_val += 0.3 # Correct classification
                message += "Correct classification."
            else:
                reward_val -= 0.2 # Wrong action penalty
                message += "Incorrect classification."
                
        elif a_type == "assign_priority":
            level = payload.get("priority")
            self.current_state["priority"] = level
            if level == self.ground_truth["expected_priority"]:
                reward_val += 0.2 # Correct priority
                message += "Correct priority assignment."
            else:
                reward_val -= 0.2 # Wrong action penalty
                message += "Suboptimal priority assignment."
                
        elif a_type == "generate_response":
            response_text = payload.get("response")
            self.current_state["response"] = response_text
            
            if self.current_state["sentiment"] == "angry" and "sorry" not in response_text.lower():
                reward_val -= 0.2 # Wrong action penalty (lacked empathy)
                message += "Response lacked empathy for an angry customer."
            else:
                reward_val += 0.2 # Useful response
                message += "Useful response generated."
                
        elif a_type == "escalate":
            if self.current_state["sentiment"] == "angry" and self.ground_truth["expected_priority"] == "high":
                reward_val += 0.3 # Act as successful resolution of urgent cases
                message += "Successfully escalated urgent issue."
            else:
                reward_val -= 0.2 # Wrong action penalty
                message += "Wrong action: Unnecessary escalation for low-priority issue."
            self.current_state["status"] = "closed"
            is_terminal = True
            
        elif a_type == "resolve":
            if not self.current_state["classification"] or not self.current_state["priority"] or not self.current_state["response"]:
                reward_val -= 0.2 # Wrong action penalty
                message += "Wrong action: Attempted resolution without completing workflow steps."
            else:
                reward_val += 0.3 # Resolution success
                message += "Ticket resolved successfully."
            
            self.current_state["status"] = "closed"
            is_terminal = True
            
        else:
            reward_val -= 0.2 # Wrong action explicitly
            message += f"Wrong action: Unknown action '{a_type}'."
            
        # Failsafe limit checking
        if self.current_step >= self.max_steps and not is_terminal:
             is_terminal = True
             if self.current_state["status"] == "open":
                 self.current_state["status"] = "closed"
                 
        obs = self.state()
        reward = Reward(value=reward_val, is_terminal=is_terminal)
        
        info = {
            "message": message,
            "expected_classification": self.ground_truth["expected_classification"],
            "expected_priority": self.ground_truth["expected_priority"]
        }
        
        return obs, reward, is_terminal, info
