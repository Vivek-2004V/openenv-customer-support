import os
import json
import argparse
from typing import Any
from huggingface_hub import InferenceClient
from app.env import CustomerSupportEnv
from app.models import Action

def evaluate_llm(task_id: str):
    """Deterministically evaluate a Hugging Face LLM agent against the support environment."""
    # Strict dynamic config parsing against Hugging Face requirements
    model_name = os.environ.get("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")
    hf_token = os.environ.get("HF_TOKEN", "")
    
    # Initialize Strict standard OpenEnv tracking log
    print(f"[START] task={task_id} env=customer-support-env model={model_name}")

    if not hf_token:
        print("Warning: HF_TOKEN is explicitly empty. Hugging Face Inference may fail or rate limit.")

    # Execute via Hugging Face Hub natively mapped to their architecture
    client = InferenceClient(
        model=model_name,
        token=hf_token
    )

    env = CustomerSupportEnv()
    obs = env.reset()
    
    rewards_history = []
    
    # Inject formal logic constraints prompting reliable JSON interactions
    system_prompt = """You are a highly structured AI customer support agent resolving a ticket pipeline.
Available actions list:
1. classify_ticket (payload format: {"classification": "refund" | "general_inquiry" | "login_issue" | "feedback"})
2. assign_priority (payload format: {"priority": "low" | "medium" | "high"})
3. generate_response (payload format: {"response": "<text>"})
4. escalate (payload format: {})
5. resolve (payload format: {})

You MUST return ONLY a fully valid JSON format mapping this dict schema:
{
  "action_type": "<action_name>",
  "payload": { ... }
}"""

    done = False
    step_count = 0
    conversation_messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Interaction Loop
    while not done and step_count < env.max_steps:
        step_count += 1
        
        obs_stringified = json.dumps(obs.dict()["state"])
        conversation_messages.append({"role": "user", "content": f"Current Ticket State: {obs_stringified}\nProvide your next action strictly in JSON:"})
        
        error_msg = ""
        action_type = "unknown"
        reward_val = 0.0
        
        try:
            # Deterministic, reproducible call explicitly leveraging HF formats
            response = client.chat_completion(
                messages=conversation_messages,
                temperature=0.01, # Hugging Face often crashes on explicitly 0.0 depending on the endpoint model deployed
                max_tokens=256,
                response_format={"type": "json"} if hasattr(client, "chat_completion") else None 
                # Note: Not all HF hosted models support automatic JSON constraints, but instructions prompt for it natively.
            )
            
            action_text = response.choices[0].message.content
            action_data = json.loads(action_text)
            
            action_type = action_data.get("action_type", "unknown")
            action = Action(**action_data)
            
            # Step the mathematical environment
            obs, reward, done, info = env.step(action)
            reward_val = reward.value
            
            # Provide reflection feedback to AI
            conversation_messages.append({"role": "assistant", "content": action_text})
            conversation_messages.append({"role": "system", "content": f"Action result mapping: Reward={reward_val}, Done={done}, Info={json.dumps(info)}"})
            
        except Exception as e:
            error_msg = str(e).replace("\n", " ").strip()
            reward_val = -1.0
            done = True
            
        rewards_history.append(reward_val)
        
        # Output Explicit formatted log
        done_str = "true" if done else "false"
        print(f"[STEP] step={step_count} action={action_type} reward={reward_val:.2f} done={done_str} error={error_msg}")

    # Output Explicit formatted termination log
    # True metric determined by pipeline resolution logic
    success_str = "true" if (env.current_state and env.current_state.get("status") == "closed" and rewards_history and rewards_history[-1] > 0) else "false"
    r_mapped = ",".join(f"{r:.2f}" for r in rewards_history)
    print(f"[END] success={success_str} steps={step_count} rewards={r_mapped}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="task_hard_1", help="Task ID sequence to execute logic against.")
    args = parser.parse_args()
    
    evaluate_llm(args.task)
