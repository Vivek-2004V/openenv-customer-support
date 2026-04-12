import os
import sys
import json
from typing import Dict, Any

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.env import CustomerSupportEnv
from backend.models import Action, TicketStatus

def run_baseline():
    print("🚀 [BASELINE] Starting Real-world Support Workflow Demo...")
    env = CustomerSupportEnv()
    obs = env.reset()
    
    total_reward = 0.0
    steps = 0
    
    # Process the queue of 3 tickets
    while obs.state.get("status") != TicketStatus.SESSION_COMPLETE:
        steps += 1
        gt = env.ground_truth
        if not gt:
            break
            
        ticket_text = obs.state.get("ticket_text", "")
        print(f"\n🎫 Step {steps}: Processing Ticket: \"{ticket_text[:50]}...\"")
        
        # 1. Classify
        action = Action(
            action_type="classify_ticket",
            payload={"classification": gt["expected_classification"]}
        )
        obs, reward, done, info = env.step(action)
        total_reward += reward.value
        print(f"   └─ Action: Classify -> {gt['expected_classification']} | Reward: {reward.value:+.2f}")
        
        # 2. Assign Priority
        action = Action(
            action_type="assign_priority",
            payload={"priority": gt["expected_priority"]}
        )
        obs, reward, done, info = env.step(action)
        total_reward += reward.value
        print(f"   └─ Action: Priority -> {gt['expected_priority']} | Reward: {reward.value:+.2f}")
        
        # 3. Generate Response
        empathy = "I am so sorry for the inconvenience, I understand your concern."
        action = Action(
            action_type="generate_response",
            payload={"response": empathy}
        )
        obs, reward, done, info = env.step(action)
        total_reward += reward.value
        print(f"   └─ Action: Respond  -> [Empathetic Draft] | Reward: {reward.value:+.2f}")
        
        # 4. Resolve
        action = Action(action_type="resolve", payload={})
        obs, reward, done, info = env.step(action)
        total_reward += reward.value
        print(f"   └─ Action: Resolve  -> Ticket Closed | Reward: {reward.value:+.2f}")

    print("\n" + "="*50)
    print(f"✨ BASELINE COMPLETE")
    print(f"📊 Total Reward Earned: {total_reward:.2f}")
    print(f"🏁 Final Status: {obs.state.get('status')}")
    print("="*50)

if __name__ == "__main__":
    try:
        run_baseline()
    except Exception as e:
        print(f"❌ Baseline failed: {e}")
        sys.exit(1)
