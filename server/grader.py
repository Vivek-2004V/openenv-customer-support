from typing import Dict, Any, List

def score_easy(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """EASY: Only classify issue correctly (1.0 or 0.0)"""
    if state.get("classification") == ground_truth.get("expected_classification"):
        return 1.0
    return 0.0

def score_medium(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """MEDIUM: classify (0.5) + generate correct response (0.5)"""
    score = 0.0
    
    # 1. Classification
    if state.get("classification") == ground_truth.get("expected_classification"):
        score += 0.5
        
    # 2. Response
    response = state.get("response")
    if response:
        # Check empathy constraint for angry customers
        empathy_keywords = ["sorry", "apologize", "understand", "help", "concern"]
        has_empathy = any(word in response.lower() for word in empathy_keywords)
        if state.get("sentiment") == "angry" and not has_empathy:
            pass # Missing empathy
        else:
            score += 0.5
            
    return score

def score_hard(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """HARD: classify (0.25) -> prioritize (0.25) -> respond (0.25) -> resolve (0.25)"""
    score = 0.0
    
    # 1. Classification
    if state.get("classification") == ground_truth.get("expected_classification"):
        score += 0.25
        
    # 2. Prioritize
    if state.get("priority") == ground_truth.get("expected_priority"):
        score += 0.25
        
    # 3. Respond
    response = state.get("response")
    if response:
        empathy_keywords = ["sorry", "apologize", "understand", "help", "concern"]
        has_empathy = any(word in response.lower() for word in empathy_keywords)
        if state.get("sentiment") == "angry" and not has_empathy:
            pass # Missing empathy
        else:
            score += 0.25
            
    # 4. Resolve
    if state.get("status") == "closed":
        score += 0.25
        
    return score

def score_episode(task_difficulty: str, history: List[Dict[str, Any]], ground_truth: Dict[str, Any]) -> float:
    """
    Deterministic scoring logic for evaluated episode. Returns a float between 0.0 and 1.0.
    """
    if not history:
        return 0.0
        
    # Analyze the final step in the history
    final_step = history[-1]
    
    # Support various OpenEnv standard observation dictionary shapes
    if "observation" in final_step and isinstance(final_step["observation"], dict) and "state" in final_step["observation"]:
        final_state = final_step["observation"]["state"]
    elif "state" in final_step:
        final_state = final_step["state"]
    else:
        final_state = final_step

    diff = task_difficulty.upper()
    if diff == "EASY":
        return score_easy(final_state, ground_truth)
    elif diff == "MEDIUM":
        return score_medium(final_state, ground_truth)
    elif diff == "HARD":
        return score_hard(final_state, ground_truth)
        
    return 0.0
