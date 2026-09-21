import logging
import time
import json
from typing import List, Dict, Any
from sqlalchemy import text
from src.database.connection import create_database_engine
from src.agent.orchestrator import AIAnalystAgent
from src.evaluation.benchmark import get_olist_eval_set
from src.evaluation.metrics import EvalMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvalRunner:
    """
    Runs the evaluation benchmark against the AIAnalystAgent.
    """
    def __init__(self, agent: AIAnalystAgent):
        self.agent = agent
        self.metrics = EvalMetrics()

    def run(self, eval_set: List[Any]) -> Dict[str, Any]:
        logger.info(f"Running evaluation on {len(eval_set)} cases...")

        results = []
        summary = {
            "execution_accuracy": 0,
            "retrieval_recall": 0,
            "semantic_accuracy": 0,
            "total_cases": len(eval_set)
        }

        for case in eval_set:
            logger.info(f"Evaluating: {case.question}")

            start_time = time.time()
            agent_res = self.agent.ask(case.question)
            latency = time.time() - start_time

            # 1. Execute Gold SQL for ground truth
            gold_res = None
            if case.gold_sql != "SELECT 'NOT_POSSIBLE'":
                with self.agent.engine.connect() as conn:
                    res = conn.execute(text(case.gold_sql))
                    gold_res = [dict(row._mapping) for row in res]

            # 2. Calculate Metrics
            # Execution Accuracy
            exec_acc = self.metrics.calculate_execution_accuracy(
                agent_res.get("data"), gold_res
            ) if "error" not in agent_res else 0

            # Retrieval Accuracy (we need to track what the agent retrieved)
            # Since agent.ask() doesn't return retrieved_schema, we'd need to modify it
            # For now, we'll assume we can't measure it without agent modification
            retrieval_recall = 0.0 # Placeholder

            # Semantic Accuracy
            semantic_acc = 0.0
            if case.gold_answer:
                semantic_acc = self.metrics.calculate_semantic_similarity(
                    agent_res.get("answer", ""), case.gold_answer, self.agent.llm_client
                )
            elif exec_acc:
                semantic_acc = 1.0

            results.append({
                "question": case.question,
                "exec_acc": exec_acc,
                "semantic_acc": semantic_acc,
                "latency": latency,
                "sql": agent_res.get("sql"),
                "error": agent_res.get("error")
            })

            summary["execution_accuracy"] += exec_acc
            summary["semantic_accuracy"] += semantic_acc

        summary["execution_accuracy"] /= len(eval_set)
        summary["semantic_accuracy"] /= len(eval_set)

        return {"summary": summary, "details": results}

def main():
    agent = AIAnalystAgent(
        database_url="sqlite:///data/olist.db",
        semantic_schema_path="data/semantic_schema.json"
    )
    runner = EvalRunner(agent)
    eval_set = get_olist_eval_set()
    results = runner.run(eval_set)

    print("\n=== Evaluation Summary ===")
    print(f"Execution Accuracy: {results['summary']['execution_accuracy']:.2%}")
    print(f"Semantic Accuracy:  {results['summary']['semantic_accuracy']:.2%}")
    print("==========================\n")

if __name__ == "__main__":
    main()
