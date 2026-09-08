import logging
from typing import List, Tuple, Optional
import sqlglot
from sqlglot import exp, parse_one

logger = logging.getLogger(__name__)

class SQLValidator:
    """
    Validates SQL queries for syntax and safety.
    """
    def __init__(self, banned_keywords: List[str] = None):
        self.banned_keywords = banned_keywords or [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"
        ]

    def validate(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validates the SQL query.

        Returns:
            (True, None) if valid.
            (False, error_message) if invalid.
        """
        try:
            # 1. Syntax Check
            parsed = parse_one(sql)

            # 2. Read-Only Check
            # We check if the root expression is a Select
            if not isinstance(parsed, exp.Select):
                return False, "Only SELECT queries are allowed."

            # 3. Banned Keyword Check (redundant with Select check but good for safety)
            sql_upper = sql.upper()
            for keyword in self.banned_keywords:
                if keyword in sql_upper:
                    # This is a simple check; a more robust one would use the AST
                    return False, f"Query contains banned keyword: {keyword}"

            return True, None

        except sqlglot.errors.ParseError as e:
            return False, f"SQL Syntax Error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
