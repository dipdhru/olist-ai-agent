from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

@dataclass
class EvalCase:
    question: str
    gold_sql: str
    gold_answer: Any
    required_tables: List[str]
    required_columns: List[str]
    difficulty: str # "easy", "medium", "hard"
    category: str # "simple", "aggregation", "join", "temporal", "nested", "ambiguous", "impossible"
    database: str = "olist.db"

    def to_dict(self):
        return asdict(self)
