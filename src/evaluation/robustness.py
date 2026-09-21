import logging
from typing import List, Dict, Any
from src.agent.orchestrator import AIAnalystAgent
from src.evaluation.runner import EvalRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustnessTester:
    """
    Tests the system against adversarial or challenging scenarios.
    """
    def __init__(self, agent: AIAnalystAgent):
        self.agent = agent

    def test_ambiguous_question(self, question: str):
        logger.info(f"Testing ambiguous question: {question}")
        return self.agent.ask(question)

    def test_impossible_question(self, question: str):
        logger.info(f"Testing impossible question: {question}")
        return self.agent.ask(question)

    def test_schema_drift(self, table_name: str, col_name: str, new_name: str):
        """
        Simulates a schema change by mocking the retriever's returned content.
        """
        logger.info(f"Testing schema drift: {col_name} -> {new_name}")
        # In a real system, we'd modify the DB or the semantic schema
        # Here we can just test if the agent handles a mismatched column name in the result
        pass

def main():
    agent = AIAnalystAgent("sqlite:///data/olist.db", "data/semantic_schema.json")
    tester = RobustnessTester(agent)

    cases = [
        ("How are things doing?", "ambiguous"),
        ("What is the average height of customers?", "impossible"),
        ("Who is the best seller?", "ambiguous")
    ]

    for q, type_ in cases:
        res = agent.ask(q)
        print(f"Question: {q} ({type_})")
        print(f"Answer: {res.get('answer')}\n")

if __name__ == "__main__":
    main()
