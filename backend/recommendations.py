"""
Advanced recommendation engine with vector search
To be implemented with actual PDF parsing and vector DB
"""
from typing import List, Dict, Optional
import json
from pathlib import Path

class RecommendationEngine:
    """
    Advanced recommendation system with multiple strategies:
    - Content-based (embedding similarity)
    - Attribute-based (spec matching)
    - Popularity-based
    - Collaborative filtering (future)
    """

    def __init__(self, embedding_model=None, vector_db=None):
        """
        Initialize recommendation engine

        Args:
            embedding_model: Optional sentence-transformer model
            vector_db: Optional vector database (Qdrant, Pinecone, etc.)
        """
        self.embedding_model = embedding_model  # e.g., 'all-MiniLM-L6-v2'
        self.vector_db = vector_db
        self.products = {}
        self.interactions = {}

    def add_product(self, product_id: str, text: str, specs: Dict, category: str):
        """Add product to recommendation index"""
        self.products[product_id] = {
            "text": text,
            "specs": specs,
            "category": category,
            "embedding": None  # Will be computed if embedding_model provided
        }

    def content_based_recommendations(self, product_id: str, limit: int = 5) -> List[str]:
        """
        Get recommendations based on embedding similarity
        Requires embedding_model to be set
        """
        if product_id not in self.products or not self.embedding_model:
            return []

        # Placeholder: actual implementation would compute embeddings
        # and use vector DB for similarity search
        source_text = self.products[product_id]["text"]
        source_category = self.products[product_id]["category"]

        # Simple fallback: return same category products
        same_category = [
            pid for pid in self.products
            if self.products[pid]["category"] == source_category and pid != product_id
        ]
        return same_category[:limit]

    def attribute_based_recommendations(self, product_id: str, limit: int = 5) -> List[str]:
        """
        Get recommendations based on matching specs
        """
        if product_id not in self.products:
            return []

        source_specs = self.products[product_id]["specs"]
        source_category = self.products[product_id]["category"]

        scored = []
        for pid, prod in self.products.items():
            if pid == product_id:
                continue
            if prod["category"] != source_category:
                continue

            # Score based on matching spec keys
            matching_keys = set(source_specs.keys()) & set(prod["specs"].keys())
            score = len(matching_keys)
            if score > 0:
                scored.append((pid, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in scored[:limit]]

    def hybrid_recommendations(self, product_id: str, limit: int = 5) -> List[str]:
        """
        Hybrid recommendation: combine content-based + attribute-based
        """
        content_recs = set(self.content_based_recommendations(product_id, limit * 2))
        attr_recs = set(self.attribute_based_recommendations(product_id, limit * 2))

        # Combine and rank by frequency
        combined = content_recs | attr_recs
        scored = [(pid, 0) for pid in combined]

        # Boost if appears in both lists
        for pid, _ in scored:
            if pid in content_recs and pid in attr_recs:
                scored = [(p, s + 2) if p == pid else (p, s) for p, s in scored]
            elif pid in content_recs or pid in attr_recs:
                scored = [(p, s + 1) if p == pid else (p, s) for p, s in scored]

        scored.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in scored[:limit]]

    def log_interaction(self, user_id: str, product_id: str, action: str, metadata: Dict = None):
        """Log user interaction for future collaborative filtering"""
        if user_id not in self.interactions:
            self.interactions[user_id] = []

        self.interactions[user_id].append({
            "product_id": product_id,
            "action": action,  # view, click, add_to_cart, purchase, etc.
            "metadata": metadata or {}
        })


# Usage example
if __name__ == "__main__":
    engine = RecommendationEngine()

    # Add some sample products
    engine.add_product(
        "prod_1",
        "Industrial hose for water transfer",
        {"diameter": "25mm", "pressure": "16bar", "material": "rubber"},
        "Industrial Hoses"
    )
    engine.add_product(
        "prod_2",
        "Industrial hose for pneumatic systems",
        {"diameter": "20mm", "pressure": "10bar", "material": "rubber"},
        "Industrial Hoses"
    )
    engine.add_product(
        "prod_3",
        "High pressure connector",
        {"type": "connector", "material": "stainless"},
        "Connectors"
    )

    # Get recommendations
    recs = engine.hybrid_recommendations("prod_1", limit=2)
    print("Recommendations for prod_1:", recs)
