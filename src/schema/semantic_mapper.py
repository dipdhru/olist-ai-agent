import json
import logging
from typing import List, Dict, Any
from src.schema.models import DatabaseSchema, TableMetadata, ColumnMetadata
from src.agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

class SemanticMapper:
    """
    Maps raw database metadata to semantic business meanings using an LLM.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _generate_table_description(self, table: TableMetadata) -> str:
        """
        Generates a business description for a table.
        """
        cols = [c.name for c in table.columns]
        prompt = (
            f"Given a database table named '{table.name}' with columns {cols}, "
            "provide a concise one-sentence business description of what this table represents."
        )
        system_prompt = "You are a data architect. Provide a professional, concise business description."
        return self.llm_client.complete(prompt, system_prompt).strip()

    def _generate_column_description(self, table_name: str, col: ColumnMetadata) -> str:
        """
        Generates a business description for a column.
        """
        prompt = (
            f"In the table '{table_name}', the column '{col.name}' has the data type {col.data_type}. "
            "What is the business meaning of this column? Provide a short, descriptive phrase."
        )
        system_prompt = "You are a data architect. Provide a short, precise business meaning."
        return self.llm_client.complete(prompt, system_prompt).strip()

    def map_schema(self, schema: DatabaseSchema) -> Dict[str, Any]:
        """
        Processes the entire schema and generates semantic descriptions.
        """
        logger.info("Starting semantic mapping...")
        semantic_schema = {
            "database_type": schema.database_type,
            "tables": []
        }

        for table in schema.tables:
            logger.info(f"Mapping table: {table.name}")
            table_desc = self._generate_table_description(table)

            columns_semantics = []
            for col in table.columns:
                logger.info(f"  Mapping column: {col.name}")
                col_desc = self._generate_column_description(table.name, col)
                columns_semantics.append({
                    "column": col.name,
                    "data_type": col.data_type,
                    "description": col_desc
                })

            semantic_schema["tables"].append({
                "table": table.name,
                "description": table_desc,
                "columns": columns_semantics
            })

        logger.info("Semantic mapping complete.")
        return semantic_schema
