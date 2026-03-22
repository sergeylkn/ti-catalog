"""
Embedding service for semantic search
Uses sentence-transformers for space-efficient embeddings (384 dims)
"""
import json
import numpy as np
from typing import List, Optional
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class EmbeddingService:
    """
    Compact embedding service for 500MB constraint
    Uses all-MiniLM-L6-v2 (384 dims, ~10MB model)
    """

    # Compact models (~10-40MB)
    COMPACT_MODELS = {
        "all-MiniLM-L6-v2": 384,         # 10MB, fast
        "all-MiniLM-L12-v2": 384,        # 15MB
        "all-mpnet-base-v2": 768,        # 40MB, better quality
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not EMBEDDINGS_AVAILABLE:
            raise RuntimeError("sentence-transformers not installed")

        self.model_name = model_name
        self.embedding_dim = self.COMPACT_MODELS.get(model_name, 384)
        self.model = SentenceTransformer(model_name)
        print(f"✅ Loaded embedding model: {model_name} ({self.embedding_dim} dims)")

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        if not text or not isinstance(text, str):
            return np.zeros(self.embedding_dim)

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def embed_batch(self, texts: List[str], show_progress: bool = False) -> List[np.ndarray]:
        """Generate embeddings for batch of texts"""
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )
        return embeddings

    def embedding_to_string(self, embedding: np.ndarray) -> str:
        """Convert embedding array to compact JSON string"""
        # Quantize to float32 for space efficiency
        quantized = np.round(embedding.astype(np.float32), 6)
        return json.dumps(quantized.tolist())

    def string_to_embedding(self, emb_string: str) -> np.ndarray:
        """Convert JSON string back to embedding"""
        return np.array(json.loads(emb_string))

    def semantic_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Cosine similarity between embeddings"""
        # Normalize
        emb1_norm = embedding1 / (np.linalg.norm(embedding1) + 1e-8)
        emb2_norm = embedding2 / (np.linalg.norm(embedding2) + 1e-8)
        return float(np.dot(emb1_norm, emb2_norm))

    def search_similar(self, query_embedding: np.ndarray, 
                      embeddings: List[np.ndarray], 
                      top_k: int = 5) -> List[tuple]:
        """Find top-k similar embeddings"""
        similarities = [
            self.semantic_similarity(query_embedding, emb)
            for emb in embeddings
        ]
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [(idx, similarities[idx]) for idx in top_indices]


class ChunkingService:
    """Split text into chunks for embedding"""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []

        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    @staticmethod
    def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text (simple implementation)"""
        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}

        # Split into words and filter
        words = text.lower().split()
        phrases = [w for w in words if w not in stopwords and len(w) > 3]

        return phrases[:max_phrases]


def create_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> Optional[EmbeddingService]:
    """Factory function to create embedding service"""
    try:
        return EmbeddingService(model_name)
    except Exception as e:
        print(f"⚠️  Could not initialize embedding service: {e}")
        return None


if __name__ == "__main__":
    # Test embedding service
    try:
        service = EmbeddingService()

        # Test single embedding
        text1 = "Industrial rubber hose for high pressure applications"
        emb1 = service.embed(text1)
        print(f"Embedding shape: {emb1.shape}")
        print(f"Embedding (first 10): {emb1[:10]}")

        # Test batch
        texts = [
            "Stainless steel connector",
            "Rubber hose 25mm",
            "Industrial pneumatic valve"
        ]
        embeddings = service.embed_batch(texts)
        print(f"\nBatch embeddings: {len(embeddings)} x {embeddings[0].shape}")

        # Test similarity
        sim = service.semantic_similarity(embeddings[0], embeddings[1])
        print(f"Similarity (connector vs hose): {sim:.3f}")

        # Test string conversion (for DB storage)
        emb_str = service.embedding_to_string(emb1)
        print(f"\nEmbedding as JSON string: {len(emb_str)} chars")
        emb_restored = service.string_to_embedding(emb_str)
        print(f"Restored embedding matches: {np.allclose(emb1, emb_restored)}")

    except Exception as e:
        print(f"Error: {e}")
