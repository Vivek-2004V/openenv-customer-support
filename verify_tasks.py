import sys
import os
from typing import Dict, List, Any

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

try:
    from server.env import CustomerSupportEnv
    from server.tasks import TASKS
    from server.grader import score_episode
except ImportError as e:
    print(f"❌ Error: Could not import environment components: {e}")
    sys.exit(1)

def test_task_enumeration():
    print("🔍 Testing Task Enumeration...")
    env = CustomerSupportEnv()
    
    # 1. Check get_tasks exists and returns correct number
    if not hasattr(env, 'get_tasks'):
        print("❌ Error: CustomerSupportEnv missing get_tasks() method.")
        return False
    
    tasks = env.get_tasks()
    print(f"✅ Found {len(tasks)} tasks via get_tasks().")
    
    # Also check static property
    if not hasattr(CustomerSupportEnv, 'tasks'):
        print("⚠️ Warning: CustomerSupportEnv missing static tasks attribute (optional but recommended).")
    
    if len(tasks) < 3:
        print(f"❌ Error: Only found {len(tasks)} tasks, expected at least 3.")
        return False
    
    # 2. Check each task has required metadata
    for task in tasks:
        task_id = task.get('id')
        print(f"  - Checking task: {task_id}")
        
        required_keys = ['has_grader', 'has_evaluator', 'grader']
        for key in required_keys:
            val = task.get(key)
            if val is not True:
                print(f"    ❌ Error: Task {task_id} {key} should be True (boolean). Found: {val}")
                return False
        print(f"    ✅ Metadata OK (Boolean grader: {task.get('grader')})")

    return True

def test_dynamic_grading():
    print("\n🔍 Testing Dynamic Grader Execution via env.grade()...")
    env = CustomerSupportEnv()
    tasks = env.get_tasks()
    
    ground_truth = {
        "expected_classification": "refund",
        "expected_priority": "high",
        "sentiment": "angry"
    }
    
    for task in tasks:
        task_id = task.get('id')
        print(f"  - Testing grade() method for: {task_id}")
        
        # Test Grader Functionality via env.grade
        mock_state = {"classification": "refund", "priority": "high", "status": "closed", "response": "sorry", "sentiment": "angry"}
        try:
            score = env.grade(task_id, [{"state": mock_state}], ground_truth)
            print(f"    Execution score: {score:.3f}")
            
            if not (0.0 <= score <= 1.0):
                print(f"    ❌ Error: Score out of range!")
                return False
        except Exception as e:
            print(f"    ❌ Error: grade() method failed for {task_id}: {e}")
            return False
            
    return True

if __name__ == "__main__":
    success = test_task_enumeration()
    if success:
        success = test_dynamic_grading()
    
    if success:
        print("\n✨ ALL TASK VALIDATION CHECKS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME CHECKS FAILED.")
        sys.exit(1)
