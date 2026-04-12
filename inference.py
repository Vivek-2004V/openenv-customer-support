import asyncio
import os
import json
import textwrap
import sys
import uuid
from typing import List, Optional
from openai import OpenAI

# Required to import backend local package
sys.path.append(os.getcwd())

from backend.env import CustomerSupportEnv
from backend.models import Action, SYSTEM_PROMPT, DEFAULT_MODEL, DEFAULT_API_BASE

# ==============================================================================
# MANDATORY PRE-SUBMISSION CONFIGURATION
# Participants MUST use these environment variables
# ==============================================================================
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or DEFAULT_API_BASE
MODEL_NAME = os.getenv("MODEL_NAME") or DEFAULT_MODEL

# Benchmark Configuration
SESSION_ID = os.getenv("SESSION_ID", str(uuid.uuid4())[:8])
TASK_NAME = os.getenv("TASK_NAME", "task_hard_1")
BENCHMARK = os.getenv("BENCHMARK", "customer-support-enterprise")
MAX_STEPS = 15
TEMPERATURE = 0.7
MAX_TOKENS = 150
SUCCESS_SCORE_THRESHOLD = 0.1

# Max possible reward: 3 tickets * (~1.2 max reward per ticket)
MAX_TOTAL_REWARD = 3.6

def log_start(task: str, env: str, model: str) -> None:
    """[START] task=<task_name> env=<benchmark> model=<model_name>"""
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>"""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """[END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>"""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def build_user_prompt(step: int, state: dict) -> str:
    return textwrap.dedent(
        f"""
        Step: {step}
        Current Observations:
        {json.dumps(state, indent=2)}
        
        Analyze the ticket and the queue, then decide on the next action.
        Return ONLY a JSON object: {{"action_type": "<type>", "payload": {{...}}}}
        Valid Types: classify_ticket, assign_priority, generate_response, search_kb, ask_clarification, resolve, escalate.
        """
    ).strip()

async def get_action_with_retry(client, user_prompt, retries=3) -> Optional[Action]:
    """Fetch action from LLM with JSON schema validation and retry logic."""
    for attempt in range(retries):
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            raw_content = completion.choices[0].message.content or "{}"
            data = json.loads(raw_content)
            
            # Strict verification of required fields
            if "action_type" in data and "payload" in data:
                return Action(**data)
            
            print(f"[DEBUG] Attempt {attempt+1}: Missing required fields in LLM response.", file=sys.stderr)
        except Exception as e:
            print(f"[DEBUG] Attempt {attempt+1}: LLM Error - {str(e)}", file=sys.stderr)
        
        if attempt < retries - 1:
            await asyncio.sleep(1) # Backoff
            
    return None

async def main() -> None:
    if not API_KEY:
        print("Error: HF_TOKEN environment variable not set.", file=sys.stderr)
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = CustomerSupportEnv() # Local instance for isolation in inference script

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Initial Reset
        obs = env.reset()
        done = False

        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            current_state = obs.state
            user_prompt = build_user_prompt(step, current_state)

            # 1. Prediction with Robustness
            action = await get_action_with_retry(client, user_prompt)
            
            if not action:
                # Fallback to no-op
                action = Action(action_type="unknown", payload={"reason": "llm_failure"})

            # 2. Environment Step
            obs, reward_obj, done, info = env.step(action)
            reward = float(reward_obj.value)
            
            rewards.append(reward)
            steps_taken = step
            error = info.get("message") if not done else None

            # 3. Step Logging
            log_step(step=step, action=action.action_type, reward=reward, done=done, error=error)

            if done:
                break

        # Calculate Results
        reward_sum = sum(rewards)
        score = reward_sum / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            env.close()
        except Exception:
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
