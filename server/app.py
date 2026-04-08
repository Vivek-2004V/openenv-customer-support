from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from server.env import CustomerSupportEnv
from server.models import Action, Observation
from server.tasks import get_all_tasks
from server.grader import score_episode
import os

app = FastAPI(title="OpenEnv Customer Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# Global singleton for the environment state lifecycle
env_instance = CustomerSupportEnv()

@app.api_route("/reset", methods=["GET", "POST"], response_model=Observation)
def reset_env():
    """Reset the environment and yield the initial observation."""
    return env_instance.reset()

@app.post("/step")
def step_env(action: Action):
    """Submit an action schema to process the environment workflow."""
    if env_instance.current_state is None:
        env_instance.reset()
        
    obs, reward, done, info = env_instance.step(action)
    return {
        "observation": obs.dict(),
        "reward": reward.dict(),
        "done": done,
        "info": info
    }

@app.get("/state", response_model=Observation)
def get_state():
    """Retrieve the current deterministic state of the environment."""
    if env_instance.current_state is None:
        env_instance.reset()
    return env_instance.state()

@app.get("/tasks")
def get_tasks():
    """Retrieve all available tasks mapped in the environment."""
    return {"tasks": get_all_tasks()}

@app.get("/grader")
def run_grader(task_id: str = Query(..., description="The matching task ID to score against (e.g. 'task_easy_1')")):
    """Grade the current state of the ticket interaction strictly using the deterministic grader."""
    if env_instance.current_state is None:
        env_instance.reset()
        
    # Map task ID to its logical difficulty tier
    tasks = get_all_tasks()
    task_diff = "EASY"
    for t in tasks:
        if t["id"] == task_id:
            task_diff = t["difficulty"]
            break
            
    # Mock history extraction mapped to grader logic expecting the final state
    mock_history = [{"state": env_instance.current_state}]
    
    score = score_episode(task_diff, mock_history, env_instance.ground_truth)
    return {"task_id": task_id, "score": score}

@app.get("/baseline")
def run_baseline():
    """Execute a hardcoded 'perfect' baseline workflow on the current scenario to trace rewards."""
    if env_instance.current_state is None:
        env_instance.reset()
        
    gt = env_instance.ground_truth
    
    baseline_sequence = [
        {"action_type": "classify_ticket", "payload": {"classification": gt["expected_classification"]}},
        {"action_type": "assign_priority", "payload": {"priority": gt["expected_priority"]}},
        {"action_type": "generate_response", "payload": {"response": "I am so sorry for the inconvenience. That is completely fixed now."}},
        {"action_type": "resolve", "payload": {}}
    ]
    
    trace_results = []
    
    for step_logic in baseline_sequence:
        action = Action(**step_logic)
        obs, reward, done, info = env_instance.step(action)
        trace_results.append({
            "action": step_logic,
            "reward_earned": reward.value,
            "done": done
        })
        if done:
            break
            
    return {
        "message": "Baseline ideal sequence successfully executed against ground truth.",
        "trace": trace_results,
        "final_state": env_instance.current_state
    }

# Mount static files for the built frontend
static_dir = os.path.join(os.getcwd(), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()
