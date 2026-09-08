import json
import os
import logging
from src.database.connection import create_database_engine
from src.schema.extractor import SchemaExtractor
from src.schema.profiler import DatabaseProfiler
from src.schema.relationships import RelationshipDiscoverer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    db_path = "data/olist.db"
    database_url = f"sqlite:///{db_path}"
    output_path = "data/relationships.json"

    try:
        logger.info("Initializing database connection...")
        engine = create_database_engine(database_url)

        logger.info("Extracting schema for relationship discovery...")
        extractor = SchemaExtractor(engine)
        schema = extractor.extract()

        logger.info("Profiling database for relationship discovery...")
        profiler = DatabaseProfiler(engine, schema)
        profile = profiler.profile_all()

        logger.info("Starting relationship discovery...")
        discoverer = RelationshipDiscoverer(engine, schema, profile)
        relationships = discoverer.discover_all()

        # Convert to dictionary for JSON serialization
        relationships_list = [rel.to_dict() for rel in relationships]

        # Ensure data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        logger.info(f"Saving relationships to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(relationships_list, f, indent=2)

        logger.info(f"Relationship discovery successfully completed. Found {len(relationships_list)} relationships.")

    except Exception as e:
        logger.error(f"An error occurred during relationship discovery: {e}")
        raise e

if __name__ == "__main__":
    main()
