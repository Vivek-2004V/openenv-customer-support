import requests
import sys
import time
import subprocess
import os
from typing import Dict, List, Any

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

def test_internal_logic():
    print("🔍 [TEST] Internal Logic & Task Enumeration...")
    try:
        from backend.env import CustomerSupportEnv, TASKS
    except ImportError as e:
        print(f"❌ Error: Could not import environment components: {e}")
        return False

    env = CustomerSupportEnv()
    
    # 1. Check get_tasks exists and returns correct number
    tasks = env.get_tasks()
    print(f"✅ Found {len(tasks)} tasks via get_tasks().")
    
    if len(tasks) < 3:
        print(f"❌ Error: Only found {len(tasks)} tasks, expected at least 3.")
        return False
    
    # 2. Check each task has required metadata
    for task in tasks:
        task_id = task.get('id')
        required_keys = ['has_grader', 'has_evaluator', 'grader']
        for key in required_keys:
            if task.get(key) is not True:
                print(f"❌ Error: Task {task_id} {key} is NOT True.")
                return False
    
    # 3. Test Grading
    mock_state = {"classification": "refund", "priority": "high", "status": "closed", "response": "sorry", "sentiment": "angry"}
    ground_truth = {"expected_classification": "refund", "expected_priority": "high", "sentiment": "angry"}
    try:
        score = env.grade(tasks[0]['id'], [{"state": mock_state}], ground_truth)
        print(f"✅ Grading execution successful. Score: {score:.3f}")
        if not (0.0 <= score <= 1.0):
            print("❌ Error: Score out of range!")
            return False
    except Exception as e:
        print(f"❌ Error: grade() method failed: {e}")
        return False

    print("✅ Internal logic tests passed!\n")
    return True

def test_endpoints():
    print("🔍 [TEST] API Endpoints...")
    
    # Start the server
    cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7861"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    time.sleep(5) # Wait for server
    
    try:
        # Test /tasks
        r = requests.get("http://localhost:7861/tasks")
        if r.status_code != 200 or len(r.json()) < 3:
            print("❌ Error: /tasks endpoint failed.")
            return False
        
        # Test /grader
        task_id = r.json()[0]["id"]
        r_grader = requests.get(f"http://localhost:7861/grader?task_id={task_id}")
        if r_grader.status_code != 200 or "score" not in r_grader.json():
            print("❌ Error: /grader endpoint failed.")
            return False
            
        print("✅ API endpoint tests passed!")
        return True
    except Exception as e:
        print(f"❌ Error during API test: {e}")
        return False
    finally:
        process.terminate()

def main():
    print("🚀 Starting consolidated validation...")
    if test_internal_logic() and test_endpoints():
        print("\n✨ ALL VALIDATION CHECKS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
