import logging
from typing import List, Dict, Any, Optional
from src.agent.llm_client import LLMClient
from src.agent.validator import SQLValidator

logger = logging.getLogger(__name__)

class SQLRepairer:
    """
    Repairs SQL queries based on database error messages.
    """
    def __init__(self, llm_client: LLMClient, validator: SQLValidator):
        self.llm_client = llm_client
        self.validator = validator

    def repair(self, original_sql: str, error: str, question: str, schema_context: str, max_attempts: int = 3) -> Optional[str]:
        """
        Attempts to repair a failing SQL query.
        """
        current_sql = original_sql

        for attempt in range(1, max_attempts + 1):
            logger.info(f"Repair attempt {attempt}/{max_attempts}...")

            prompt = (
                f"Original SQL: {current_sql}\n"
                f"Database Error: {error}\n"
                f"User Question: {question}\n"
                f"Schema Context: {schema_context}\n\n"
                "Please repair the SQL query to fix the error. Return only the corrected SQL query."
            )
            system_prompt = "You are an expert SQL debugger. Fix the provided SQL based on the error message."

            current_sql = self.llm_client.complete(prompt, system_prompt).strip()

            # Clean up LLM output (remove markdown code blocks)
            if current_sql.startswith("```sql"):
                current_sql = current_sql.split("\n", 1)[1].rsplit("\n", 1)[0]
            elif current_sql.startswith("```"):
                current_sql = current_sql.split("\n", 1)[1].rsplit("\n", 1)[0]

            # Validate the repaired SQL
            is_valid, error_msg = self.validator.validate(current_sql)
            if is_valid:
                logger.info(f"SQL repaired successfully on attempt {attempt}.")
                return current_sql

            logger.warning(f"Repaired SQL still invalid: {error_msg}")
            error = error_msg

        logger.error("Reached maximum repair attempts. Could not fix the SQL.")
        return None
