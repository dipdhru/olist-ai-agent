import logging
from typing import Any, Dict, List, Optional, Union
import polars as pl
from sqlalchemy import Engine, text
from src.schema.models import DatabaseSchema, TableMetadata, ColumnMetadata
import json

logger = logging.getLogger(__name__)

class DatabaseProfiler:
    """
    Analyzes the data in a database to provide statistics and semantic hints.
    """
    def __init__(self, engine: Engine, schema: DatabaseSchema, sample_size: int = 1000):
        self.engine = engine
        self.schema = schema
        self.sample_size = sample_size

    def _get_column_type_category(self, col_meta: ColumnMetadata, unique_count: int, total_rows: int) -> str:
        """
        Categorizes a column based on its data type and value distribution.
        """
        dtype = col_meta.data_type.upper()

        if "INT" in dtype or "REAL" in dtype or "FLOAT" in dtype or "DECIMAL" in dtype:
            return "numeric"

        if "BOOL" in dtype:
            return "boolean"

        if "DATE" in dtype or "TIMESTAMP" in dtype or "TIME" in dtype:
            return "date/time"

        # For TEXT/VARCHAR, we distinguish between identifier, categorical, and text
        if "TEXT" in dtype or "CHAR" in dtype or "VARCHAR" in dtype:
            if unique_count == total_rows and total_rows > 0:
                return "identifier"
            if total_rows > 0 and (unique_count / total_rows) < 0.1:
                return "categorical"
            return "text"

        return "other"

    def profile_table(self, table_meta: TableMetadata) -> Dict[str, Any]:
        """
        Profiles a single table.
        """
        table_name = table_meta.name
        logger.info(f"Profiling table: {table_name}")

        # Get total row count
        with self.engine.connect() as conn:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            total_rows = res.scalar()

        if total_rows == 0:
            logger.warning(f"Table {table_name} is empty.")
            return {"table": table_name, "row_count": 0, "columns": {}}

        # Sample data for Polars analysis (median, categories)
        # SQLite doesn't have a native MEDIAN, so we sample.
        query = f"SELECT * FROM {table_name} LIMIT {self.sample_size}"
        with self.engine.connect() as conn:
            df = pl.read_database(query, conn)

        column_profiles = {}
        for col in table_meta.columns:
            col_name = col.name
            logger.info(f"  Profiling column: {col_name}")

            # Basic stats via SQL for accuracy on full dataset
            with self.engine.connect() as conn:
                # Null count
                null_res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL"))
                null_count = null_res.scalar()

                # Unique count
                unique_res = conn.execute(text(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name}"))
                unique_count = unique_res.scalar()

            null_pct = (null_count / total_rows) * 100

            # Sample values
            sample_values = df[col_name].head(5).to_list()

            # Determine Category
            category = self._get_column_type_category(col, unique_count, total_rows)

            stats = {
                "type": category,
                "null_count": null_count,
                "null_percentage": null_pct,
                "unique_count": unique_count,
                "sample_values": sample_values,
            }

            # Numeric stats
            if category == "numeric":
                col_data = df[col_name].cast(pl.Float64).drop_nulls()
                if not col_data.is_empty():
                    # Use SQL for min/max to get global values
                    with self.engine.connect() as conn:
                        min_res = conn.execute(text(f"SELECT MIN({col_name}) FROM {table_name}"))
                        max_res = conn.execute(text(f"SELECT MAX({col_name}) FROM {table_name}"))
                        stats["min"] = min_res.scalar()
                        stats["max"] = max_res.scalar()

                    # Use sample for mean/median
                    stats["mean"] = col_data.mean()
                    stats["median"] = col_data.median()

            # Date/Time stats
            elif category == "date/time":
                with self.engine.connect() as conn:
                    min_res = conn.execute(text(f"SELECT MIN({col_name}) FROM {table_name}"))
                    max_res = conn.execute(text(f"SELECT MAX({col_name}) FROM {table_name}"))
                    stats["min"] = min_res.scalar()
                    stats["max"] = max_res.scalar()

            # Categorical stats
            elif category == "categorical":
                # Get top frequencies from sample
                freqs = df[col_name].value_counts().sort("count", descending=True).head(10)
                stats["top_values"] = [
                    {"value": row[0], "count": row[1]} for row in freqs.iter_rows()
                ]

            column_profiles[col_name] = stats

        return {
            "table": table_name,
            "row_count": total_rows,
            "column_count": len(table_meta.columns),
            "columns": column_profiles
        }

    def profile_all(self) -> Dict[str, Any]:
        """
        Profiles all tables in the schema.
        """
        profile = {
            "database_type": self.schema.database_type,
            "tables": []
        }

        for table in self.schema.tables:
            profile["tables"].append(self.profile_table(table))

        return profile
