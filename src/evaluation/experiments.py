import logging
from typing import List, Dict, Any
from src.agent.orchestrator import AIAnalystAgent
from src.evaluation.benchmark import get_olist_eval_set
from src.evaluation.runner import EvalRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExperimentRunner:
    """
    Runs comparison experiments between different system configurations.
    """
    def __init__(self, database_url: str, semantic_schema_path: str):
        self.database_url = database_url
        self.semantic_schema_path = semantic_schema_path

    def run_baseline_1(self, eval_set: List[Any]) -> float:
        """
        Baseline 1: Question -> LLM -> SQL (No schema context)
        """
        logger.info("Running Baseline 1...")
        # We simulate this by creating an agent and overriding the retriever
        agent = AIAnalystAgent(self.database_url, self.semantic_schema_path)
        # Mock retriever to return nothing
        agent.retriever.retrieve = lambda q: []

        runner = EvalRunner(agent)
        res = runner.run(eval_set)
        return res["summary"]["execution_accuracy"]

    def run_baseline_2(self, eval_set: List[Any]) -> float:
        """
        Baseline 2: Question -> LLM + Full Schema -> SQL
        """
        logger.info("Running Baseline 2...")
        agent = AIAnalystAgent(self.database_url, self.semantic_schema_path)
        # Mock retriever to return everything
        def retrieve_all(q):
            return [(doc, 0.0) for doc in agent.retriever.documents]
        agent.retriever.retrieve = retrieve_all

        runner = EvalRunner(agent)
        res = runner.run(eval_set)
        return res["summary"]["execution_accuracy"]

    def run_system_full(self, eval_set: List[Any]) -> float:
        """
        Full System: Question -> RAG -> LLM -> SQL -> Validation -> Repair
        """
        logger.info("Running Full System...")
        agent = AIAnalystAgent(self.database_url, self.semantic_schema_path)
        runner = EvalRunner(agent)
        res = runner.run(eval_set)
        return res["summary"]["execution_accuracy"]

    def run_all_experiments(self):
        eval_set = get_olist_eval_set()

        b1 = self.run_baseline_1(eval_set)
        b2 = self.run_baseline_2(eval_set)
        full = self.run_system_full(eval_set)

        print("\n=== Experiment Results ===")
        print(f"Baseline 1 (No Schema): {b1:.2%}")
        print(f"Baseline 2 (Full Schema): {b2:.2%}")
        print(f"Full System (RAG):       {full:.2%}")
        print("==========================\n")

if __name__ == "__main__":
    runner = ExperimentRunner("sqlite:///data/olist.db", "data/semantic_schema.json")
    runner.run_all_experiments()
