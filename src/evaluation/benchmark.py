import json
from typing import List
from src.evaluation.eval_datasets import EvalCase

def get_olist_eval_set() -> List[EvalCase]:
    return [
        EvalCase(
            question="How many products are in the database?",
            gold_sql="SELECT COUNT(*) FROM products",
            gold_answer=None, # Calculated at runtime
            required_tables=["products"],
            required_columns=["product_id"],
            difficulty="easy",
            category="simple"
        ),
        EvalCase(
            question="What is the total revenue from all orders?",
            gold_sql="SELECT SUM(payment_value) FROM order_payments",
            gold_answer=None,
            required_tables=["order_payments"],
            required_columns=["payment_value"],
            difficulty="easy",
            category="aggregation"
        ),
        EvalCase(
            question="Which product category generated the most revenue?",
            gold_sql="""
                SELECT p.product_category_name
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                GROUP BY p.product_category_name
                ORDER BY SUM(oi.price) DESC
                LIMIT 1
            """,
            gold_answer=None,
            required_tables=["order_items", "products"],
            required_columns=["price", "product_category_name"],
            difficulty="medium",
            category="join"
        ),
        EvalCase(
            question="How many orders were placed in 2017?",
            gold_sql="SELECT COUNT(*) FROM orders WHERE order_purchase_timestamp LIKE '2017%'",
            gold_answer=None,
            required_tables=["orders"],
            required_columns=["order_purchase_timestamp"],
            difficulty="medium",
            category="temporal"
        ),
        EvalCase(
            question="What is the average age of the customers?",
            gold_sql="SELECT 'NOT_POSSIBLE'",
            gold_answer="The database does not contain customer age information.",
            required_tables=[],
            required_columns=[],
            difficulty="easy",
            category="impossible"
        )
    ]
