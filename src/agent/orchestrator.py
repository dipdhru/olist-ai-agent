import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import Engine, text
from src.database.connection import create_database_engine
from src.schema.extractor import SchemaExtractor
from src.schema.relationships import RelationshipDiscoverer
from src.schema.profiler import DatabaseProfiler
from src.retrieval.retriever import SchemaRetriever
from src.agent.llm_client import LLMClient
from src.agent.sql_generator import SQLGenerator
from src.agent.validator import SQLValidator
from src.agent.repair import SQLRepairer
from src.agent.analyst import ResultAnalyst
from src.analytics.visualization import Visualizer

logger = logging.getLogger(__name__)

class AIAnalystAgent:
    """
    The main orchestrator for the AI Database Analyst Agent.
    """
    def __init__(self, database_url: str, semantic_schema_path: str):
        self.engine = create_database_engine(database_url)
        self.llm_client = LLMClient()
        self.history = [] # Store conversation history for multi-turn support

        # Components
        self.retriever = SchemaRetriever(semantic_schema_path)
        self.generator = SQLGenerator(self.llm_client)
        self.validator = SQLValidator()
        self.repairer = SQLRepairer(self.llm_client, self.validator)
        self.analyst = ResultAnalyst(self.llm_client)
        self.visualizer = Visualizer(self.llm_client)

        # We need relationships for the generator
        self.relationships = self._load_relationships()

    def _load_relationships(self) -> List[Dict[str, Any]]:
        import json
        import os
        path = "data/relationships.json"
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return []

    def ask(self, question: str) -> Dict[str, Any]:
        """
        The full pipeline from question to answer.
        """
        # Handle multi-turn by rewriting the question based on history
        final_question = question
        if self.history:
            final_question = self._rewrite_question(question)

        logger.info(f"Processing question: {final_question}")

        # 1. Retrieve relevant schema
        retrieved_schema = self.retriever.retrieve(final_question)

        # 2. Generate SQL
        gen_result = self.generator.generate(final_question, retrieved_schema, self.relationships)
        sql = gen_result.get("sql", "")

        if not sql:
            return {"error": "Could not generate SQL query.", "details": gen_result}

        # 3. Validate SQL
        is_valid, error_msg = self.validator.validate(sql)
        if not is_valid:
            logger.warning(f"SQL validation failed: {error_msg}. Attempting repair...")
            schema_ctx = "\n".join([doc['content'] for doc, score in retrieved_schema])
            sql = self.repairer.repair(sql, error_msg, final_question, schema_ctx)
            if not sql:
                return {"error": "SQL validation failed and repair attempts were exhausted.", "details": error_msg}

        # 4. Execute SQL
        try:
            with self.engine.connect() as conn:
                result_set = conn.execute(text(sql))
                rows = [dict(row._mapping) for row in result_set]
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            schema_ctx = "\n".join([doc['content'] for doc, score in retrieved_schema])
            sql = self.repairer.repair(sql, str(e), final_question, schema_ctx)
            if not sql:
                return {"error": f"SQL execution failed: {e}"}

            try:
                with self.engine.connect() as conn:
                    result_set = conn.execute(text(sql))
                    rows = [dict(row._mapping) for row in result_set]
            except Exception as e2:
                return {"error": f"Repaired SQL also failed: {e2}"}

        # 5. Analyze results
        answer = self.analyst.analyze(final_question, sql, rows)

        # 6. Optionally generate chart
        chart_spec = self.visualizer.generate_chart_spec(final_question, rows)

        # Update history
        self.history.append({"question": final_question, "answer": answer})

        return {
            "question": final_question,
            "sql": sql,
            "answer": answer,
            "data": rows,
            "chart": chart_spec
        }

    def _rewrite_question(self, question: str) -> str:
        """
        Rewrites a follow-up question into a standalone question using history.
        """
        history_str = "\n".join([f"Q: {h['question']}\nA: {h['answer']}" for h in self.history[-3:]])
        prompt = (
            f"Conversation History:\n{history_str}\n\n"
            f"Follow-up Question: {question}\n\n"
            "Rewrite the follow-up question into a standalone, complete question that can be answered without the history."
        )
        system_prompt = "You are a query re-writer. Output only the standalone question."
        return self.llm_client.complete(prompt, system_prompt).strip()
