from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from src.agent.orchestrator import AIAnalystAgent

app = FastAPI(title="AI Database Analyst API")

# Initialize agent
# In production, these would come from environment variables
AGENT = AIAnalystAgent(
    database_url="sqlite:///data/olist.db",
    semantic_schema_path="data/semantic_schema.json"
)

class QuestionRequest(BaseModel):
    question: str

class AgentResponse(BaseModel):
    question: str
    answer: str
    sql: Optional[str] = None
    data: Optional[List[Any]] = None
    chart: Optional[Dict[str, Any]] = None

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/ask", response_model=AgentResponse)
def ask_question(request: QuestionRequest):
    try:
        result = AGENT.ask(request.question)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
def get_schema():
    import json
    import os
    path = "data/semantic_schema.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Semantic schema not found")
    with open(path, 'r') as f:
        return json.load(f)
