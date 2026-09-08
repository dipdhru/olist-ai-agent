from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy import Engine, text
from src.schema.models import DatabaseSchema, TableMetadata, ColumnMetadata

logger = logging.getLogger(__name__)

@dataclass
class RelationshipMetadata:
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    relationship_type: str # "one_to_one", "many_to_one", "one_to_many"
    source: str # "explicit" or "inferred"
    confidence: float # 0.0 to 1.0

    def to_dict(self):
        return asdict(self)

class RelationshipDiscoverer:
    """
    Discovers relationships between tables using both explicit FKs and data-driven inference.
    """
    def __init__(self, engine: Engine, schema: DatabaseSchema, profile: Dict[str, Any]):
        self.engine = engine
        self.schema = schema
        self.profile = profile

    def discover_explicit(self) -> List[RelationshipMetadata]:
        """
        Extracts relationships from foreign key metadata.
        """
        logger.info("Discovering explicit relationships...")
        relationships = []
        for table in self.schema.tables:
            for fk in table.foreign_keys:
                relationships.append(RelationshipMetadata(
                    source_table=table.name,
                    source_column=fk.constrained_column,
                    target_table=fk.referred_table,
                    target_column=fk.referred_column,
                    relationship_type="many_to_one", # Default for FKs, can be refined
                    source="explicit",
                    confidence=1.0
                ))
        return relationships

    def _calculate_naming_score(self, col_a: str, table_a: str, col_b: str, table_b: str) -> float:
        """
        Scores the likelihood of a relationship based on column names.
        """
        if col_a == col_b:
            return 0.8
        if col_a == f"{table_b}_id" and col_b == "id":
            return 0.9
        if col_a.endswith(f"_{col_b}") or col_b.endswith(f"_{col_a}"):
            return 0.6
        return 0.0

    def _calculate_value_overlap(self, table_a: str, col_a: str, table_b: str, col_b: str) -> float:
        """
        Calculates the percentage of sampled values from table_a.col_a that exist in table_b.col_b.
        """
        try:
            # Sample 100 values from table A
            with self.engine.connect() as conn:
                res = conn.execute(text(f"SELECT {col_a} FROM {table_a} WHERE {col_a} IS NOT NULL LIMIT 100"))
                sample_a = [row[0] for row in res]

            if not sample_a:
                return 0.0

            # Check existence in table B
            overlap_count = 0
            for val in sample_a:
                with self.engine.connect() as conn:
                    # Simple existence check
                    count_res = conn.execute(
                        text(f"SELECT 1 FROM {table_b} WHERE {col_b} = :val LIMIT 1"),
                        {"val": val}
                    )
                    if count_res.scalar():
                        overlap_count += 1

            return overlap_count / len(sample_a)
        except Exception as e:
            logger.debug(f"Error calculating overlap for {table_a}.{col_a} -> {table_b}.{col_b}: {e}")
            return 0.0

    def discover_inferred(self) -> List[RelationshipMetadata]:
        """
        Infers relationships based on naming, types, and value overlap.
        """
        logger.info("Discovering inferred relationships...")
        relationships = []

        # Pre-calculate uniqueness for all columns from profile
        uniqueness = {}
        for table_prof in self.profile.get("tables", []):
            t_name = table_prof["table"]
            uniqueness[t_name] = {}
            for col_name, col_prof in table_prof["columns"].items():
                # Unique if unique_count == row_count
                uniqueness[t_name][col_name] = (
                    col_prof["unique_count"] == table_prof["row_count"]
                    if table_prof["row_count"] > 0 else False
                )

        # Iterate over all pairs of tables and columns
        for table_a in self.schema.tables:
            for table_b in self.schema.tables:
                if table_a.name == table_b.name:
                    continue

                for col_a in table_a.columns:
                    for col_b in table_b.columns:
                        # 1. Basic Type Check
                        if col_a.data_type != col_b.data_type:
                            # Allow some flexibility, but generally they should match
                            continue

                        # 2. Naming Score
                        name_score = self._calculate_naming_score(col_a.name, table_a.name, col_b.name, table_b.name)

                        # Only proceed if there's some naming hint or we want to be thorough
                        if name_score == 0:
                            continue

                        # 3. Value Overlap
                        overlap_score = self._calculate_value_overlap(table_a.name, col_a.name, table_b.name, col_b.name)

                        # 4. Calculate Final Confidence
                        # Weighted average: overlap is much more reliable than naming
                        confidence = (name_score * 0.3) + (overlap_score * 0.7)

                        if confidence > 0.5:
                            # Determine relationship type
                            # If col_b is unique in table_b, it's many_to_one
                            is_b_unique = uniqueness.get(table_b.name, {}).get(col_b.name, False)
                            rel_type = "many_to_one" if is_b_unique else "many_to_many"

                            # Special case: if both are unique, it's one_to_one
                            is_a_unique = uniqueness.get(table_a.name, {}).get(col_a.name, False)
                            if is_a_unique and is_b_unique:
                                rel_type = "one_to_one"

                            relationships.append(RelationshipMetadata(
                                source_table=table_a.name,
                                source_column=col_a.name,
                                target_table=table_b.name,
                                target_column=col_b.name,
                                relationship_type=rel_type,
                                source="inferred",
                                confidence=round(confidence, 3)
                            ))

        return relationships

    def discover_all(self) -> List[RelationshipMetadata]:
        """
        Runs both explicit and inferred discovery.
        """
        explicit = self.discover_explicit()
        inferred = self.discover_inferred()

        # Remove duplicates (if explicit and inferred find the same thing)
        # Explicit always wins
        seen = set()
        final = []

        for rel in explicit:
            final.append(rel)
            seen.add((rel.source_table, rel.source_column, rel.target_table, rel.target_column))

        for rel in inferred:
            if (rel.source_table, rel.source_column, rel.target_table, rel.target_column) not in seen:
                final.append(rel)

        return final
