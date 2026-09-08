import json
import os
import logging
from src.database.connection import create_database_engine
from src.schema.extractor import SchemaExtractor
from src.schema.profiler import DatabaseProfiler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    db_path = "data/olist.db"
    database_url = f"sqlite:///{db_path}"
    output_path = "data/database_profile.json"

    try:
        logger.info("Initializing database connection...")
        engine = create_database_engine(database_url)

        logger.info("Extracting schema for profiling...")
        extractor = SchemaExtractor(engine)
        schema = extractor.extract()

        logger.info("Starting database profiling...")
        profiler = DatabaseProfiler(engine, schema)
        profile_results = profiler.profile_all()

        # Ensure data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        logger.info(f"Saving profile to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile_results, f, indent=2, default=str)

        logger.info("Database profiling successfully completed.")

    except Exception as e:
        logger.error(f"An error occurred during database profiling: {e}")
        raise e

if __name__ == "__main__":
    main()
