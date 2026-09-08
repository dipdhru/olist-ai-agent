import json
import os
import logging
from src.database.connection import create_database_engine
from src.schema.extractor import SchemaExtractor
from src.schema.semantic_mapper import SemanticMapper
from src.agent.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    db_path = "data/olist.db"
    database_url = f"sqlite:///{db_path}"
    output_path = "data/semantic_schema.json"

    try:
        logger.info("Initializing database connection...")
        engine = create_database_engine(database_url)

        logger.info("Extracting schema...")
        extractor = SchemaExtractor(engine)
        schema = extractor.extract()

        logger.info("Starting semantic mapping (this requires an LLM)...")
        llm_client = LLMClient()
        mapper = SemanticMapper(llm_client)
        semantic_schema = mapper.map_schema(schema)

        # Ensure data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        logger.info(f"Saving semantic schema to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(semantic_schema, f, indent=2)

        logger.info("Semantic schema generation successfully completed.")

    except Exception as e:
        logger.error(f"An error occurred during semantic mapping: {e}")
        raise e

if __name__ == "__main__":
    main()
