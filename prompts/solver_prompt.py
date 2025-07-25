# prompts/solver_prompt.py

def get_solver_prompt(question: str) -> str:
    return (
        "You are a math expert assistant.\n"
        "Given a math question, follow these steps:\n"
        "1. Identify the math domain (e.g., algebra, calculus, geometry, arithmetic, statistics, etc).\n"
        "2. Solve it step-by-step in plain English.\n"
        "Assume integration is with respect to x unless specified otherwise.\n"
        "If multiple variables exist, treat non-target variables as constants.\n"
        "Always return a JSON object like this:\n"
        "{\n"
        '  "math_type": "<math domain>",\n'
        '  "solution": "<step-by-step explanation>"\n'
        "}\n\n"
        f"Question: {question}"
    )
