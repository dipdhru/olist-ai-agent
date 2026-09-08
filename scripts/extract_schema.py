import json
import os
import logging
from src.database.connection import create_database_engine
from src.schema.extractor import SchemaExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Use relative path for the database
    db_path = "data/olist.db"
    database_url = f"sqlite:///{db_path}"
    output_path = "data/schema.json"

    try:
        logger.info("Initializing database connection...")
        engine = create_database_engine(database_url)

        logger.info("Extracting schema...")
        extractor = SchemaExtractor(engine)
        schema = extractor.extract()

        # Convert to dictionary for JSON serialization
        schema_dict = schema.to_dict()

        # Ensure data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        logger.info(f"Saving schema to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema_dict, f, indent=2)

        logger.info("Schema extraction successfully completed.")

    except Exception as e:
        logger.error(f"An error occurred during schema extraction: {e}")
        raise e

if __name__ == "__main__":
    main()
