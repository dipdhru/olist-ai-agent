import logging
from typing import List, Dict, Any
from src.agent.llm_client import LLMClient
from src.schema.relationships import RelationshipMetadata

logger = logging.getLogger(__name__)

class SQLGenerator:
    """
    Generates SQL queries from natural language questions and retrieved schema.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(self, question: str, retrieved_schema: List[Dict[str, Any]], relationships: List[RelationshipMetadata], dialect: str = "sqlite") -> Dict[str, Any]:
        """
        Generates a SQL query based on the provided context.
        """
        logger.info("Generating SQL...")

        # Format schema context
        schema_context = "\n".join([
            f"- {doc['content']}" for doc, score in retrieved_schema
        ])

        # Format relationship context
        rel_context = "\n".join([
            f"- {rel.source_table}.{rel.source_column} -> {rel.target_table}.{rel.target_column} ({rel.relationship_type})"
            for rel in relationships
        ])

        prompt = (
            f"User Question: {question}\n\n"
            f"Relevant Schema:\n{schema_context}\n\n"
            f"Table Relationships:\n{rel_context}\n\n"
            f"Database Dialect: {dialect}\n\n"
            "Generate a read-only SQL query to answer the question. "
            "Return the result in JSON format with the following keys: "
            "'sql', 'tables_used', 'columns_used', 'reasoning_summary', and 'assumptions'."
        )

        system_prompt = (
            "You are an expert SQL developer. Generate accurate, efficient, and read-only SQL. "
            "Always return valid JSON."
        )

        response = self.llm_client.complete(prompt, system_prompt)

        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"LLM returned invalid JSON: {response}")
            return {
                "sql": "",
                "error": "Failed to parse LLM response as JSON",
                "raw_response": response
            }
