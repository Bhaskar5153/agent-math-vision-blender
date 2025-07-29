import os
import re
import json
from datetime import datetime
from langchain_google_vertexai import VertexAI
from langchain_core.runnables import RunnableLambda
from prompts.blender_animation_prompt import get_blender_animation_prompt
from dotenv import load_dotenv
from .solver_agent import math_solver_agent
# Load environment variables from .env in the root folder
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)
def get_project_id():
    return os.getenv("PROJECT_ID")


# ====== Vertex AI Init ======

MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.2

llm = VertexAI(
    project=get_project_id(),
    model_name=MODEL_NAME,
    temperature=TEMPERATURE,
    max_output_tokens=60000,
)

# ====== Agent 2: Blender Script Generator ======

def clean_blender_code(code: str) -> str:
    lines = code.splitlines()
    return "\n".join(
        line.rstrip()
        for line in lines
        if not line.strip().startswith("```")
        and "Output:" not in line
        and "<html>" not in line
    )

def generate_smart_filename(solution_text: str) -> str:
    match = re.search(r"(y\s*=\s*[^\n,;]*)", solution_text) or re.search(r"[\w\s]+=", solution_text)
    keyword = match.group(0).strip().replace(" ", "").replace("=", "_") if match else "math_visual"
    keyword = re.sub(r"[^\w_]", "", keyword)[:30]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{keyword}_{timestamp}.py"

def generate_blender_script(concept: dict) -> str:
    solution_text = concept.get("solution", "").strip()
    if not solution_text:
        return "# ⚠️ No solution provided."

    prompt = get_blender_animation_prompt(solution_text)
    code = llm.invoke(prompt)
    code = clean_blender_code(code)

    filename = generate_smart_filename(solution_text)
    output_dir = "blender_scripts"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    final_code = code + f"\n\n# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_code)

    return f"✅ Blender script saved at: {filepath}"

blender_script_agent = RunnableLambda(generate_blender_script)

# ====== Runtime Loop ======

if __name__ == "__main__":
    while True:
        user_question = input("\n📥 Enter a math question (or 'exit' to quit): ").strip()
        if user_question.lower() in ["exit", "quit"]:
            print("👋 Exiting. See you soon!")
            break

        print("\n🔍 Detecting math type and generating solution...")
        concept = math_solver_agent.invoke(user_question)
        if not concept or not isinstance(concept, dict):
            print("⚠️ Error: Invalid response from math solver.")
            continue
        output = concept.get("solution", "").strip()
        if not output:
            print("⚠️ No solution generated. Please clarify your question.")
            continue
        print(f"\n🔎 Detected Math Type: {output.get('math_type')}\n")
        print("🧠 Step-by-Step Solution:\n")
        print(output.get("solution"))
        
        print("\n🎨 Generating Blender script for animation...")
        script_msg = blender_script_agent.invoke(output)
        print(f"\n🎬 {script_msg}")
