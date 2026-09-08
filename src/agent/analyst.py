import logging
from typing import List, Dict, Any, Optional
from src.agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

class ResultAnalyst:
    """
    Analyzes SQL results and generates a natural language answer.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def analyze(self, question: str, sql: str, results: List[Dict[str, Any]]) -> str:
        """
        Converts the SQL result set into a natural language answer.
        """
        logger.info("Analyzing results...")

        prompt = (
            f"User Question: {question}\n"
            f"SQL Query: {sql}\n"
            f"Query Results: {results}\n\n"
            "Provide a natural language answer to the user question based on these results. "
            "Be precise, include numerical values where applicable, and mention any caveats."
        )
        system_prompt = "You are a data analyst. Provide clear, accurate, and professional answers based on the provided data."

        return self.llm_client.complete(prompt, system_prompt).strip()
