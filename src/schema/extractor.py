import logging
from typing import List
from sqlalchemy import Engine, inspect
from src.schema.models import (
    ColumnMetadata,
    ForeignKeyMetadata,
    TableMetadata,
    DatabaseSchema
)

logger = logging.getLogger(__name__)

class SchemaExtractor:
    """
    Handles automatic extraction of database schema metadata using SQLAlchemy.
    """
    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)

    def extract(self) -> DatabaseSchema:
        """
        Extracts the complete schema of the connected database.

        Returns:
            DatabaseSchema: The structured metadata of the database.
        """
        logger.info("Starting schema extraction...")

        db_type = self.engine.dialect.name
        logger.info(f"Connected to database type: {db_type}")

        tables = []
        table_names = self.inspector.get_table_names()
        logger.info(f"Found {len(table_names)} tables: {table_names}")

        for table_name in table_names:
            logger.info(f"Extracting metadata for table: {table_name}")

            # Columns
            columns_info = self.inspector.get_columns(table_name)
            columns = []
            for col in columns_info:
                columns.append(ColumnMetadata(
                    name=col['name'],
                    data_type=str(col['type']),
                    nullable=col['nullable'],
                    primary_key=col.get('primary_key', False),
                    default=str(col.get('default')) if col.get('default') else None,
                    comment=col.get('comment')
                ))

            # Primary Keys
            pk = self.inspector.get_pk_constraint(table_name)
            primary_keys = pk.get('constrained_columns', [])

            # Foreign Keys
            fks_info = self.inspector.get_foreign_keys(table_name)
            foreign_keys = []
            for fk in fks_info:
                for constrained_col, referred_col in zip(fk['constrained_columns'], fk['referred_columns']):
                    foreign_keys.append(ForeignKeyMetadata(
                        constrained_column=constrained_col,
                        referred_table=fk['referred_table'],
                        referred_column=referred_col
                    ))

            # Indexes
            indexes = self.inspector.get_indexes(table_name)

            tables.append(TableMetadata(
                name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                indexes=indexes
            ))

        logger.info("Schema extraction complete.")
        return DatabaseSchema(database_type=db_type, tables=tables)
