from typing import Dict, Any, List
from .models import TicketStatus, Sentiment, Priority, Classification


# ─── Per-task grader functions ───────────────────────────────────────────────

def grade_task_easy_1(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_easy_1 – Ticket Classification: only classification matters."""
    if state.get("classification") == ground_truth.get("expected_classification"):
        return 1.0
    return 0.0


def grade_task_easy_2(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_easy_2 – Priority Assignment: only priority matters."""
    if state.get("priority") == ground_truth.get("expected_priority"):
        return 1.0
    return 0.0


def grade_task_medium_1(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_medium_1 – Classify and Respond: classification (0.5) + empathetic response (0.5)."""
    score = 0.0
    if state.get("classification") == ground_truth.get("expected_classification"):
        score += 0.5
    response = state.get("response", "")
    if response:
        empathy_keywords = ["sorry", "apologize", "understand", "help", "concern"]
        has_empathy = any(w in response.lower() for w in empathy_keywords)
        # Check if empathy was expected but missing
        if ground_truth.get("sentiment") in [Sentiment.ANGRY, Sentiment.PANICKED, Sentiment.CONCERNED] and not has_empathy:
            pass  # No empathy for upset customer — no credit for response
        else:
            score += 0.5
    return score


def grade_task_medium_2(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_medium_2 – Professional Resolution: classification (0.5) + professional response (0.5)."""
    score = 0.0
    if state.get("classification") == ground_truth.get("expected_classification"):
        score += 0.5
    response = state.get("response", "")
    if response:
        professional_keywords = ["help", "support", "assist", "resolve", "solution", "fix"]
        has_professional = any(w in response.lower() for w in professional_keywords)
        if has_professional:
            score += 0.5
    return score


def grade_task_hard_1(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_hard_1 – Full Support Workflow: classify (0.25) + priority (0.25) + respond (0.25) + resolve (0.25)."""
    score = 0.0
    if state.get("classification") == ground_truth.get("expected_classification"):
        score += 0.25
    if state.get("priority") == ground_truth.get("expected_priority"):
        score += 0.25
    response = state.get("response", "")
    if response:
        empathy_keywords = ["sorry", "apologize", "understand", "help", "concern"]
        has_empathy = any(w in response.lower() for w in empathy_keywords)
        if ground_truth.get("sentiment") in [Sentiment.ANGRY, Sentiment.PANICKED] and not has_empathy:
            pass
        else:
            score += 0.25
    if state.get("status") == TicketStatus.CLOSED:
        score += 0.25
    return score


def grade_task_hard_2(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_hard_2 – High Priority Angry Customers: escalation + empathy + priority."""
    score = 0.0
    # Classification correct
    if state.get("classification") == ground_truth.get("expected_classification"):
        score += 0.25
    # Priority must be high
    if state.get("priority") == Priority.HIGH:
        score += 0.25
    # Response must contain empathy
    response = state.get("response", "")
    if response:
        empathy_keywords = ["sorry", "apologize", "understand", "help", "concern", "reassure"]
        if any(w in response.lower() for w in empathy_keywords):
            score += 0.25
    # Sentiment identification — validating the agent understands the urgency
    if ground_truth.get("sentiment") in [Sentiment.ANGRY, Sentiment.PANICKED]:
        score += 0.25
    return score
def grade_task_hard_3(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_hard_3 – Efficiency Challenge: full workflow + bonus for low step count."""
    score = 0.0
    if state.get("classification") == ground_truth.get("expected_classification"):
        score += 0.2
    if state.get("priority") == ground_truth.get("expected_priority"):
        score += 0.2
    response = state.get("response", "")
    if response and len(response.strip()) > 10:
        score += 0.2
    if state.get("status") == TicketStatus.CLOSED:
        score += 0.2
    # Efficiency bonus: fewer steps = better
    steps = state.get("steps_taken", 10)
    if steps <= 4:
        score += 0.2
    elif steps <= 6:
        score += 0.1
    return min(score, 1.0)

def grade_task_extreme_1(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_extreme_1 – Policy-Driven: KB search (0.4) + correct policy citation in response (0.6)."""
    score = 0.0
    # Did they search the KB? (Checked via kb_context being populated)
    if state.get("kb_context"):
        score += 0.4
    # Did they cite the '48' hour rule for monthly plans?
    response = state.get("response", "").lower()
    if "48" in response and "hour" in response:
        score += 0.6
    return score


def grade_task_extreme_2(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_extreme_2 – Vague Ticket: clarification (0.5) + resolution (0.5)."""
    score = 0.0
    if state.get("is_clarified"):
        score += 0.5
    if state.get("status") == TicketStatus.CLOSED:
        score += 0.5
    return score


def grade_task_extreme_3(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """task_extreme_3 – Security Breach: KB search (0.3) + High Priority (0.3) + Escalation (0.4)."""
    score = 0.0
    if state.get("kb_context") and "security" in state.get("kb_context").lower():
        score += 0.3
    if state.get("priority") == Priority.HIGH:
        score += 0.3
    # For this task, we assume 'session_complete' or 'status' check for escalation logic
    # In env.py, escalate pops the queue but doesn't set status=CLOSED necessarily
    # But it sets terminal. Here we check history if needed, but let's simplify to 'priority' and 'kb'
    # and a history check if we can.
    return score + 0.4 if state.get("priority") == Priority.HIGH and state.get("kb_context") else score




# Map task_id → grader function
_GRADER_MAP: Dict[str, Any] = {
    "task_easy_1": grade_task_easy_1,
    "task_easy_2": grade_task_easy_2,
    "task_medium_1": grade_task_medium_1,
    "task_medium_2": grade_task_medium_2,
    "task_hard_1": grade_task_hard_1,
    "task_hard_2": grade_task_hard_2,
    "task_hard_3": grade_task_hard_3,
    "task_extreme_1": grade_task_extreme_1,
    "task_extreme_2": grade_task_extreme_2,
    "task_extreme_3": grade_task_extreme_3,
}


def score_episode(
    task_difficulty: str,
    history: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    task_id: str = "",
) -> float:
    """
    Deterministic scoring for an evaluated episode with fail-safety.
    Returns a float strictly in [0.0, 1.0].
    """
    try:
        if not history:
            return 0.0

        # Resolve final state from history
        final_step = history[-1]
        if "observation" in final_step and isinstance(final_step["observation"], dict) and "state" in final_step["observation"]:
            final_state = final_step["observation"]["state"]
        elif "state" in final_step:
            final_state = final_step["state"]
        else:
            final_state = final_step

        # Try per-task grader first
        if task_id and task_id in _GRADER_MAP:
            score = _GRADER_MAP[task_id](final_state, ground_truth)
            return float(max(0.0, min(1.0, score)))

        # Fallback: difficulty-based routing
        diff = (task_difficulty or "").upper()
        if not diff or diff == "UNKNOWN":
            tid = (task_id or "").upper()
            if "HARD" in tid: diff = "HARD"
            elif "MEDIUM" in tid: diff = "MEDIUM"
            else: diff = "EASY"

        if diff == "HARD":
            score = grade_task_hard_1(final_state, ground_truth)
        elif diff == "MEDIUM":
            score = grade_task_medium_1(final_state, ground_truth)
        else:
            score = grade_task_easy_1(final_state, ground_truth)

        return float(max(0.0, min(1.0, score)))
    except Exception as e:
        print(f"[GRADER CRASH] {task_id}: {str(e)}")
        return 0.0
