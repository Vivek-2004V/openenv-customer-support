from typing import List, Dict

TASKS = [
    {
        "id": "task_easy_1",
        "difficulty": "EASY",
        "objective": "Only classify the issue correctly. You do not need to assign priority or resolve the ticket.",
        "grader": True,
        "has_grader": True
    },
    {
        "id": "task_easy_2",
        "difficulty": "EASY",
        "objective": "Correctly assign the priority level (low/medium/high) to the ticket based on the customer's sentiment and urgency.",
        "grader": True,
        "has_grader": True
    },
    {
        "id": "task_medium_1",
        "difficulty": "MEDIUM",
        "objective": "Classify the ticket issue correctly and generate an appropriate response. If the customer is angry, ensure the response includes empathy (e.g., 'sorry').",
        "grader": True,
        "has_grader": True
    },
    {
        "id": "task_medium_2",
        "difficulty": "MEDIUM",
        "objective": "Classify the issue and draft a professional response. Any response missing a helpful tone or solution keywords like 'help' or 'support' will be penalized.",
        "grader": True,
        "has_grader": True
    },
    {
        "id": "task_hard_1",
        "difficulty": "HARD",
        "objective": "Complete the full support workflow: 1. Correctly classify the issue, 2. Accurately assign priority, 3. Generate a correct, empathetic response, and 4. Officially resolve (close) the ticket.",
        "grader": True,
        "has_grader": True
    }
]

def get_all_tasks() -> List[Dict[str, str]]:
    """Retrieve list of all registered tasks."""
    return TASKS
