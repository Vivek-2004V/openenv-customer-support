import json
import sys
import os

# Add parent directory to path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.env import CustomerSupportEnv
from backend.models import Action

def test_kb_and_sentiment():
    env = CustomerSupportEnv()
    print("--- Testing Reset ---")
    obs = env.reset()
    ticket_text = obs.state["ticket_text"]
    print(f"Initial Ticket: {ticket_text}")
    print(f"Initial Sentiment: {obs.state['sentiment']}")

    print("\n--- Testing KB Search ---")
    action = Action(action_type="search_kb", payload={"query": "refund policy"})
    obs, reward, done, info = env.step(action)
    print(f"Message: {info['message']}")
    print(f"KB Context in Obs: {obs.state.get('kb_context')}")

    print("\n--- Testing Sentiment Decay ---")
    # Take 3 more steps to trigger sentiment change
    for i in range(2):
        action = Action(action_type="generate_response", payload={"response": "Wait..."})
        obs, reward, done, info = env.step(action)
        print(f"Step {i+2} Sentiment: {obs.state['sentiment']}")
    
    # 4th step should trigger decay from initial (which was likely ANGRY/NEUTRAL etc)
    action = Action(action_type="generate_response", payload={"response": "Almost there..."})
    obs, reward, done, info = env.step(action)
    print(f"Step 4 Sentiment: {obs.state['sentiment']}")
    print(f"Message: {info['message']}")

    print("\n--- Testing Clarification ---")
    # Force a vague scenario for testing if needed, or just test the action
    action = Action(action_type="ask_clarification", payload={"question": "What is wrong?"})
    obs, reward, done, info = env.step(action)
    print(f"Is Clarified in Obs: {obs.state.get('is_clarified')}")
    print(f"Message: {info['message']}")

if __name__ == "__main__":
    test_kb_and_sentiment()
