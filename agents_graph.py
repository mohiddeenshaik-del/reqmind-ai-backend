from typing import TypedDict
from langgraph.graph import StateGraph, END
from vector_store import retrieve_context
from google import genai
import os
import json

# -----------------------------
# Gemini Client
# -----------------------------

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# -----------------------------
# State Definition
# -----------------------------

class RequirementState(TypedDict):
    requirement: str
    context: str
    similarity_score: float
    ba_output: str
    qa_output: str
    risk_output: str
    final_output: str


# -----------------------------
# Agents
# -----------------------------

def retrieve_agent(state: RequirementState):

    rag_result = retrieve_context(state["requirement"])

    return {
        "context": rag_result["context"],
        "similarity_score": rag_result["similarity_score"]
    }


def ba_agent(state: RequirementState):

    prompt = f"""
You are a Senior Business Analyst.

Requirement:
{state["requirement"]}

Relevant Knowledge:
{state["context"]}

Provide structured business analysis.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {"ba_output": response.text}


def qa_agent(state: RequirementState):

    prompt = f"""
You are a QA Expert.

Review this analysis and highlight clarity issues, ambiguities, and missing acceptance criteria.

Business Analysis:
{state["ba_output"]}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {"qa_output": response.text}


def risk_agent(state: RequirementState):

    prompt = f"""
You are a Technical Risk Analyst.

Identify architectural, scalability, compliance, and performance risks.

Requirement:
{state["requirement"]}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {"risk_output": response.text}


def refiner_agent(state: RequirementState):

    prompt = f"""
You are a Senior Product Architect.

Using the inputs below, generate a FINAL structured requirement analysis.

Business Analysis:
{state["ba_output"]}

QA Review:
{state["qa_output"]}

Risk Analysis:
{state["risk_output"]}

Return ONLY valid JSON in the exact format below:

{{
  "business_objective": "string",
  "functional_requirements": ["string"],
  "non_functional_requirements": ["string"],
  "assumptions": ["string"],
  "constraints": ["string"],
  "quality_score": 0-100,
  "ambiguity_score": 0-100,
  "risk_score": 0-100,
  "improvement_suggestions": ["string"]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    return {
        "final_output": raw_text,
        "similarity_score": state["similarity_score"]
    }


# -----------------------------
# Build Graph
# -----------------------------

def build_graph():

    graph = StateGraph(RequirementState)

    graph.add_node("retrieve", retrieve_agent)
    graph.add_node("ba", ba_agent)
    graph.add_node("qa", qa_agent)
    graph.add_node("risk", risk_agent)
    graph.add_node("refine", refiner_agent)

    graph.set_entry_point("retrieve")

    graph.add_edge("retrieve", "ba")
    graph.add_edge("ba", "qa")
    graph.add_edge("qa", "risk")
    graph.add_edge("risk", "refine")
    graph.add_edge("refine", END)

    return graph.compile()