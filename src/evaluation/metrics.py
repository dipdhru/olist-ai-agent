import logging
from typing import List, Any, Dict, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class EvalMetrics:
    """
    Computes performance metrics for the AI Analyst Agent.
    """
    @staticmethod
    def calculate_execution_accuracy(predicted_result: Any, gold_result: Any) -> bool:
        """
        Compares the results of the generated SQL vs the gold SQL.
        """
        return predicted_result == gold_result

    @staticmethod
    def calculate_retrieval_recall(retrieved_items: List[str], required_items: List[str]) -> float:
        """
        Calculates Recall@K: proportion of required items that were retrieved.
        """
        if not required_items:
            return 1.0

        intersection = set(retrieved_items).intersection(set(required_items))
        return len(intersection) / len(required_items)

    @staticmethod
    def calculate_retrieval_precision(retrieved_items: List[str], required_items: List[str]) -> float:
        """
        Calculates Precision@K: proportion of retrieved items that are required.
        """
        if not retrieved_items:
            return 0.0

        intersection = set(retrieved_items).intersection(set(required_items))
        return len(intersection) / len(retrieved_items)

    @staticmethod
    def calculate_semantic_similarity(predicted_answer: str, gold_answer: str, llm_client=None) -> float:
        """
        Uses an LLM to determine if two answers are semantically equivalent.
        """
        if not llm_client:
            return 1.0 if predicted_answer == gold_answer else 0.0

        prompt = (
            f"Predicted Answer: {predicted_answer}\n"
            f"Gold Answer: {gold_answer}\n\n"
            "Are these two answers semantically equivalent? Return 'YES' or 'NO'."
        )
        system_prompt = "You are an evaluation judge. Be strict about numerical accuracy."
        response = llm_client.complete(prompt, system_prompt).strip().upper()

        return 1.0 if "YES" in response else 0.0
