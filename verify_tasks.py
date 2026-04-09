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
    print(f"✅ Found {len(tasks)} tasks.")
    
    if len(tasks) < 3:
        print(f"❌ Error: Only found {len(tasks)} tasks, expected at least 3.")
        return False
    
    # 2. Check each task has required metadata
    for task in tasks:
        task_id = task.get('id')
        print(f"  - Checking task: {task_id}")
        
        required_keys = ['has_grader', 'has_evaluator', 'grader']
        for key in required_keys:
            if not task.get(key):
                print(f"    ❌ Error: Task {task_id} missing or false for '{key}'.")
                return False
        print(f"    ✅ Metadata OK")

    return True

def test_grader_range():
    print("\n🔍 Testing Grader Range [0.0, 1.0]...")
    env = CustomerSupportEnv()
    tasks = env.get_tasks()
    
    # Mock ground truth and state for testing
    ground_truth = {
        "expected_classification": "refund",
        "expected_priority": "high",
        "sentiment": "angry"
    }
    
    for task in tasks:
        task_id = task.get('id')
        difficulty = task.get('difficulty', 'EASY')
        print(f"  - Grading task: {task_id} ({difficulty})")
        
        # Test Case 1: Empty History
        score_empty = score_episode(difficulty, [], ground_truth)
        print(f"    Empty history score: {score_empty:.3f}")
        if not (0.0 <= score_empty <= 1.0):
            print(f"    ❌ Error: Score {score_empty} out of range!")
            return False
            
        # Test Case 2: Perfect State
        mock_perfect_state = {
            "classification": "refund",
            "priority": "high",
            "response": "I am so sorry, we will help you.",
            "status": "closed",
            "sentiment": "angry"
        }
        mock_history = [{"state": mock_perfect_state}]
        score_perfect = score_episode(difficulty, mock_history, ground_truth)
        print(f"    Perfect state score: {score_perfect:.3f}")
        if not (0.0 <= score_perfect <= 1.0):
            print(f"    ❌ Error: Score {score_perfect} out of range!")
            return False
            
        # Test Case 3: Poor State
        mock_poor_state = {
            "classification": "wrong",
            "priority": "low",
            "response": "",
            "status": "open",
            "sentiment": "angry"
        }
        mock_history_poor = [{"state": mock_poor_state}]
        score_poor = score_episode(difficulty, mock_history_poor, ground_truth)
        print(f"    Poor state score: {score_poor:.3f}")
        if not (0.0 <= score_poor <= 1.0):
            print(f"    ❌ Error: Score {score_poor} out of range!")
            return False

    print("✅ Grader range validation passed for all tasks.")
    return True

if __name__ == "__main__":
    success = test_task_enumeration()
    if success:
        success = test_grader_range()
    
    if success:
        print("\n✨ ALL TASK VALIDATION CHECKS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME CHECKS FAILED.")
        sys.exit(1)
