import logging
from typing import List, Dict, Any, Optional
from src.agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

class Visualizer:
    """
    Determines if a visualization is needed and generates a chart specification.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate_chart_spec(self, question: str, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Generates a Plotly-compatible chart specification if useful.
        """
        logger.info("Determining if visualization is useful...")

        prompt = (
            f"User Question: {question}\n"
            f"Data Results: {results}\n\n"
            "If this data can be visualized effectively (e.g., time series, distribution, comparison), "
            "return a JSON chart specification with 'type' (line, bar, pie, scatter), 'x', 'y', 'title', and 'labels'. "
            "If no visualization is useful, return 'NONE'."
        )
        system_prompt = "You are a data visualization expert. Return a valid JSON chart spec or 'NONE'."

        response = self.llm_client.complete(prompt, system_prompt).strip()

        if response == "NONE":
            return None

        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse chart spec JSON: {response}")
            return None
