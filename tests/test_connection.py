import pytest
import os
from src.database.connection import create_database_engine, verify_connection

def test_sqlite_connection():
    # Path to the Olist database relative to the project root
    db_path = "data/olist.db"
    database_url = f"sqlite:///{db_path}"

    # Ensure the database file exists before testing
    assert os.path.exists(db_path), f"Database file not found at {db_path}"

    try:
        engine = create_database_engine(database_url)
        assert engine is not None
        assert verify_connection(engine) is True
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

def test_invalid_connection():
    # Use an invalid URL to test error handling
    invalid_url = "postgresql://nonexistent_user:wrong_pass@localhost:5432/nonexistent_db"

    with pytest.raises(Exception):
        create_database_engine(invalid_url)
