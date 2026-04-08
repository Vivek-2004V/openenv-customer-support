from typing import List, Dict

TASKS = [
    {
        "id": "task_easy_1",
        "difficulty": "EASY",
        "objective": "Only classify the issue correctly. You do not need to assign priority or resolve the ticket.",
    },
    {
        "id": "task_medium_1",
        "difficulty": "MEDIUM",
        "objective": "Classify the ticket issue correctly and generate an appropriate response. If the customer is angry, ensure the response includes empathy (e.g., 'sorry').",
    },
    {
        "id": "task_hard_1",
        "difficulty": "HARD",
        "objective": "Complete the full support workflow: 1. Correctly classify the issue, 2. Accurately assign priority, 3. Generate a correct, empathetic response, and 4. Officially resolve (close) the ticket.",
    }
]

def get_all_tasks() -> List[Dict[str, str]]:
    """Retrieve list of all registered tasks."""
    return TASKS
