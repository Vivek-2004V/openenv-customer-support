import os
import json
import textwrap
import asyncio
from typing import List, Optional
from openai import OpenAI

from backend.env import CustomerSupportEnv
from backend.models import Action, SYSTEM_PROMPT, DEFAULT_MODEL, DEFAULT_API_BASE

# Mandatory Environment Configuration
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or DEFAULT_API_BASE
MODEL_NAME = os.getenv("MODEL_NAME") or DEFAULT_MODEL

# Benchmark Configuration
TASK_NAME = os.getenv("TASK_NAME", "task_hard_1")
BENCHMARK = "customer-support-enterprise"
MAX_STEPS = 15  # Total steps allowed across the queue
SUCCESS_SCORE_THRESHOLD = 0.1

# Max Total Reward: Approx 1.0 per ticket * 3 tickets in queue
MAX_TOTAL_REWARD = 3.0

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = CustomerSupportEnv()
    
    rewards = []
    total_steps = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset current enterprise session (populates queue)
        obs = env.reset()
        done = False
        
        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            current_state = obs.model_dump()["state"]
            
            # Agent decision using OpenAI
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Current State: {json.dumps(current_state)}"}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                action_text = completion.choices[0].message.content or "{}"
                action_data = json.loads(action_text)
                action = Action(**action_data)
                action_type = action.action_type
            except Exception:
                action = Action(action_type="unknown", payload={})
                action_type = "error"

            # Step the environment
            obs, reward_obj, done, info = env.step(action)
            reward = reward_obj.value
            
            rewards.append(reward)
            total_steps = step
            
            log_step(step=step, action=action_type, reward=reward, done=done, error=info.get("error"))

            if done:
                break

        # Calculate final normalized score
        final_reward_sum = sum(rewards)
        # We target a normalized score between 0 and 1
        score = final_reward_sum / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=total_steps, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
