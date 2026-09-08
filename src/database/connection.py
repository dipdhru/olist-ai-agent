from typing import Optional
import logging
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_engine(database_url: str) -> Engine:
    """
    Creates a SQLAlchemy database engine from the provided URL.

    Args:
        database_url (str): The database connection URL.
                            Example: 'sqlite:///path/to/db.sqlite' or 'postgresql://user:pass@host/db'

    Returns:
        Engine: A SQLAlchemy Engine instance.

    Raises:
        SQLAlchemyError: If the engine cannot be created or the connection fails.
    """
    try:
        logger.info(f"Creating database engine for URL: {database_url}")
        engine = create_engine(database_url)

        # Test the connection immediately to ensure it's valid
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Database connection test successful.")
        return engine

    except SQLAlchemyError as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise e
    except Exception as e:
        logger.error(f"An unexpected error occurred while connecting to the database: {e}")
        raise e

def verify_connection(engine: Engine) -> bool:
    """
    Simple utility to test if the engine can still connect to the database.

    Args:
        engine (Engine): The SQLAlchemy engine to test.

    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except SQLAlchemyError as e:
        logger.error(f"Connection test failed: {e}")
        return False
