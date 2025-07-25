# agents/math_solver_agent.py

import os
import json
from langchain_google_vertexai import VertexAI
from langchain_core.runnables import RunnableLambda
from prompts.solver_prompt import get_solver_prompt
from dotenv import load_dotenv

# Load environment variables from .env in the root folder
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

def get_project_id():
    return os.getenv("PROJECT_ID")

llm = VertexAI(
    project=get_project_id(),
    model_name="gemini-2.5-flash",
    temperature=0.2,
    max_output_tokens=1024,
)

def detect_math_type_and_solve(question: str) -> dict:
    prompt = get_solver_prompt(question)
    response = llm.invoke(prompt)

    try:
        result = json.loads(response)
        if not result.get("solution", "").strip():
            result["solution"] = "[⚠️ Solution was empty. Please clarify or try again.]"
    except Exception:
        result = {
            "math_type": "calculus",  # default if unsure
            "solution": response.strip() or "[⚠️ No solution generated.]"
        }

    return result

math_solver_agent = RunnableLambda(detect_math_type_and_solve)