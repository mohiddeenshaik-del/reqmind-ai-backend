from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
# from agents_graph import build_graph
import json

app = FastAPI()
graph = build_graph()

class RequirementInput(BaseModel):
    requirement: str

@app.get("/")
def home():
    return {"message": "ReqMind AI Backend Running with RAG 🚀"}

@app.post("/analyze")
def analyze_requirement(data: RequirementInput):

    try:
        result = graph.invoke({
            "requirement": data.requirement,
            "context": "",
            "ba_output": "",
            "qa_output": "",
            "risk_output": "",
            "final_output": "",
            "similarity_score": 0.0
        })

        try:
            structured_output = json.loads(result["final_output"])
        except json.JSONDecodeError:
            return {"error": "Invalid JSON returned by model"}

        structured_output["similarity_score"] = result["similarity_score"]

        return structured_output

    except Exception as e:
        return {"error": str(e)}