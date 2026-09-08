import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import json

logger = logging.getLogger(__name__)

class SchemaRetriever:
    """
    Retrieves relevant schema components for a natural language question.
    """
    def __init__(self, semantic_schema_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.semantic_schema = self._load_schema(semantic_schema_path)
        self.index = None
        self.documents = []

        self._build_index()

    def _load_schema(self, path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_index(self):
        """
        Creates a vector index of all tables and columns.
        """
        logger.info("Building schema retrieval index...")
        self.documents = []
        texts = []

        for table in self.semantic_schema["tables"]:
            table_name = table["table"]
            table_desc = table["description"]

            # Table document
            self.documents.append({
                "type": "table",
                "name": table_name,
                "content": f"Table {table_name}: {table_desc}"
            })
            texts.append(f"Table {table_name}: {table_desc}")

            for col in table["columns"]:
                col_name = col["column"]
                col_desc = col["description"]

                # Column document
                self.documents.append({
                    "type": "column",
                    "table": table_name,
                    "name": col_name,
                    "content": f"Table {table_name}, Column {col_name}: {col_desc}"
                })
                texts.append(f"Table {table_name}, Column {col_name}: {col_desc}")

        # Embed texts
        embeddings = self.model.encode(texts)
        dimension = embeddings.shape[1]

        # Build FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        logger.info(f"Index built with {len(self.documents)} documents.")

    def retrieve(self, question: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieves the most relevant schema components for a question.
        """
        query_embedding = self.model.encode([question])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                results.append((self.documents[idx], float(dist)))

        return results
