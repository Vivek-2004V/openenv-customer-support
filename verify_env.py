import requests
import sys
import time
import subprocess
import os

def test_endpoints():
    print("🚀 Starting local validation test...")
    
    # 1. Start the server
    process = subprocess.Popen(
        ["python3", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(5)  # Wait for server to start
    
    try:
        # 2. Test /tasks
        print("🔍 Testing /tasks endpoint...")
        r_tasks = requests.get("http://localhost:7860/tasks")
        tasks = r_tasks.json()
        
        if len(tasks) < 3:
            print(f"❌ Error: Found only {len(tasks)} tasks, expected at least 3.")
            sys.exit(1)
        
        for task in tasks:
            if not task.get("has_grader") or not task.get("has_evaluator"):
                print(f"❌ Error: Task {task['id']} missing has_grader or has_evaluator metadata.")
                sys.exit(1)
        print(f"✅ /tasks validated: {len(tasks)} tasks found with proper metadata.")
        
        # 3. Test /grader
        task_id = tasks[0]["id"]
        print(f"🔍 Testing /grader endpoint for {task_id}...")
        r_grader = requests.get(f"http://localhost:7860/grader?task_id={task_id}")
        
        if r_grader.status_code != 200:
            print(f"❌ Error: Grader returned status {r_grader.status_code}")
            print(f"Response: {r_grader.text}")
            sys.exit(1)
            
        try:
            data = r_grader.json()
        except Exception as e:
            print(f"❌ Error: Failed to decode JSON. Response: {r_grader.text}")
            sys.exit(1)
        
        required_keys = ["score", "reward", "success", "task_id"]
        for key in required_keys:
            if key not in data:
                print(f"❌ Error: Grader response missing key: {key}")
                sys.exit(1)
        
        score = data["score"]
        if not (0.0 <= score <= 1.0):
            print(f"❌ Error: Score {score} out of range [0.0, 1.0].")
            sys.exit(1)
            
        print("✅ /grader validated: Response format and score range are correct.")
        print("\n✨ LOCAL VALIDATION PASSED!")
        
    finally:
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
            print("\n--- Server Stdout ---")
            print(stdout)
            print("\n--- Server Stderr ---")
            print(stderr)
        except subprocess.TimeoutExpired:
            process.kill()
            print("\n--- Server terminated (timeout) ---")

if __name__ == "__main__":
    test_endpoints()
