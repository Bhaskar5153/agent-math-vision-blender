# prompts/solver_prompt.py

def get_solver_prompt(question: str) -> str:
    return (
        "You are a **math expert assistant**.\n"
        "Given a student's question, follow these steps:\n"
        "+ Identify the math domain (e.g., algebra, calculus, geometry, physics).\n"
        "+ Solve the problem step-by-step in plain English.\n"
        "+ Return a valid JSON object with these keys:\n"
        '  "math_type": string,\n'
        '  "solution": string\n\n'
        "**Use standard JSON formatting. Double quotes only. No markdown or trailing commas.**\n\n"
        f"Question:\n{question}"
    )