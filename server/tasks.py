from typing import List, Dict

TASKS = [
    {
        "id": "task_easy_1",
        "name": "Ticket Classification",
        "difficulty": "EASY",
        "objective": "Only classify the issue correctly. You do not need to assign priority or resolve the ticket.",
        "description": "Accurately categorize the customer's issue into one of the predefined categories (refund, technical_issue, etc.).",
        "grader": True,
        "has_grader": True,
        "has_evaluator": True
    },
    {
        "id": "task_easy_2",
        "name": "Priority Assignment",
        "difficulty": "EASY",
        "objective": "Correctly assign the priority level (low/medium/high) to the ticket based on the customer's sentiment and urgency.",
        "description": "Determine the urgency of the ticket and set the priority level to low, medium, or high.",
        "grader": True,
        "has_grader": True,
        "has_evaluator": True
    },
    {
        "id": "task_medium_1",
        "name": "Classify and Respond",
        "difficulty": "MEDIUM",
        "objective": "Classify the ticket issue correctly and generate an appropriate response. If the customer is angry, ensure the response includes empathy (e.g., 'sorry').",
        "description": "Categorize the issue and draft a response that addresses the user's sentiment with appropriate empathy.",
        "grader": True,
        "has_grader": True,
        "has_evaluator": True
    },
    {
        "id": "task_medium_2",
        "name": "Professional Resolution",
        "difficulty": "MEDIUM",
        "objective": "Classify the issue and draft a professional response. Any response missing a helpful tone or solution keywords like 'help' or 'support' will be penalized.",
        "description": "Classify the ticket and provide a professional, keyword-rich response that guides the user toward a solution.",
        "grader": True,
        "has_grader": True,
        "has_evaluator": True
    },
    {
        "id": "task_hard_1",
        "name": "Full Support Workflow",
        "difficulty": "HARD",
        "objective": "Complete the full support workflow: 1. Correctly classify the issue, 2. Accurately assign priority, 3. Generate a correct, empathetic response, and 4. Officially resolve (close) the ticket.",
        "description": "Execute the entire lifecycle of a support ticket from initial classification to final resolution.",
        "grader": True,
        "has_grader": True,
        "has_evaluator": True
    }
]

def get_all_tasks() -> List[Dict[str, str]]:
    """Retrieve list of all registered tasks."""
    return TASKS
