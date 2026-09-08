from dataclasses import dataclass, asdict
from typing import List, Optional, Any

@dataclass
class ColumnMetadata:
    name: str
    data_type: str
    nullable: bool
    primary_key: bool
    default: Optional[Any] = None
    comment: Optional[str] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class ForeignKeyMetadata:
    constrained_column: str
    referred_table: str
    referred_column: str

    def to_dict(self):
        return asdict(self)

@dataclass
class TableMetadata:
    name: str
    columns: List[ColumnMetadata]
    primary_keys: List[str]
    foreign_keys: List[ForeignKeyMetadata]
    indexes: List[dict]

    def to_dict(self):
        return {
            "name": self.name,
            "columns": [c.to_dict() for c in self.columns],
            "primary_keys": self.primary_keys,
            "foreign_keys": [fk.to_dict() for fk in self.foreign_keys],
            "indexes": self.indexes
        }

@dataclass
class DatabaseSchema:
    database_type: str
    tables: List[TableMetadata]

    def to_dict(self):
        return {
            "database_type": self.database_type,
            "tables": [t.to_dict() for t in self.tables]
        }
