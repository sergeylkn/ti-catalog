"""
RAG (Retrieval Augmented Generation) engine for Q&A over product catalogs
Supports local LLM (ollama) and OpenAI API
"""
import os
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime

from embeddings import EmbeddingService, ChunkingService


class RAGEngine:
    """
    Retrieval Augmented Generation for product Q&A
    1. Retrieve relevant products/chunks via embedding similarity
    2. Generate answer using LLM (OpenAI or Ollama)
    """

    def __init__(self, 
                 embedding_service: EmbeddingService,
                 llm_provider: str = "openai",
                 model_name: str = "gpt-3.5-turbo"):
        """
        Initialize RAG engine

        Args:
            embedding_service: EmbeddingService instance
            llm_provider: "openai" (recommended) or "ollama"
            model_name: Model to use (gpt-3.5-turbo, gpt-4, mistral, etc)
        """
        self.embedding_service = embedding_service
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.openai_client = None

        if llm_provider == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self.openai_client = OpenAI(api_key=api_key)
                print(f"✅ Connected to OpenAI (model: {model_name})")
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {e}")
                print("  Set OPENAI_API_KEY environment variable")
        elif llm_provider == "ollama":
            try:
                import requests
                self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                resp = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
                print(f"✅ Connected to Ollama at {self.ollama_base_url}")
            except Exception as e:
                print(f"⚠️  Ollama not available: {e}")

    def retrieve(self, query: str, products: List[Dict], 
                 embeddings: List, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Retrieve top-k relevant products for query

        Returns: List of (product, score) tuples
        """
        query_embedding = self.embedding_service.embed(query)

        results = []
        for product, embedding in zip(products, embeddings):
            if embedding is None:
                continue

            similarity = self.embedding_service.semantic_similarity(
                query_embedding,
                embedding
            )
            results.append((product, similarity))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def build_context(self, products: List[Dict]) -> str:
        """Build context string from retrieved products"""
        context_parts = []

        for product in products:
            part = f"""
Product: {product.get('title', 'N/A')}
SKU: {product.get('sku', 'N/A')}
Description: {product.get('description', 'N/A')}
Specs: {json.dumps(product.get('specs', {}))}
---"""
            context_parts.append(part)

        return "\n".join(context_parts)

    def generate_ollama(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate response using Ollama"""
        try:
            import requests

            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Error: {response.status_code}"

        except Exception as e:
            return f"Error connecting to Ollama: {e}"

    def generate_openai(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate response using OpenAI API"""
        if not self.openai_client:
            return "OpenAI client not initialized. Check OPENAI_API_KEY."

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful industrial product specialist. Provide concise, technical recommendations based on product catalog information. Always mention specific SKUs when available."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=500,
                timeout=30
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def answer(self, query: str, products: List[Dict], 
               embeddings: List, top_k: int = 3) -> Dict:
        """
        Answer user query based on product retrieval

        Returns:
            {
                "query": original query,
                "retrieved_products": list of relevant products,
                "context": formatted context for LLM,
                "answer": generated answer,
                "timestamp": timestamp
            }
        """
        # Retrieve relevant products
        retrieved = self.retrieve(query, products, embeddings, top_k)
        retrieved_products = [p for p, _ in retrieved]

        # Build context
        context = self.build_context(retrieved_products)

        # Build prompt
        prompt = f"""Based on the following product catalog information, answer the user's question.

Product Catalog:
{context}

User Question: {query}

Answer:"""

        # Generate answer
        if self.llm_provider == "openai":
            answer = self.generate_openai(prompt)
        else:
            answer = self.generate_ollama(prompt)

        return {
            "query": query,
            "retrieved_products": [
                {
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "sku": p.get("sku"),
                    "relevance": score
                }
                for p, score in retrieved
            ],
            "context": context,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        }


# Context for system prompt
SYSTEM_PROMPT = """You are a helpful industrial product specialist with expertise in:
- Hydraulic components
- Pneumatic systems
- Industrial hoses and fittings
- Fluid transfer systems

When answering questions:
1. Reference specific products from the catalog
2. Highlight relevant specifications (pressure, temperature, material)
3. Provide practical recommendations
4. Be concise and technical when appropriate
5. Always mention the SKU for specific products

If the product catalog doesn't contain relevant information, say so clearly."""


if __name__ == "__main__":
    # Test RAG engine
    from embeddings import create_embedding_service

    embedding_service = create_embedding_service()
    if not embedding_service:
        print("Embeddings not available")
        exit(1)

    # Test with ollama
    rag = RAGEngine(embedding_service, llm_provider="ollama")

    # Sample products
    sample_products = [
        {
            "id": "1",
            "title": "Industrial Rubber Hose 25mm",
            "sku": "HR-25-16",
            "description": "High-pressure rubber hose for industrial applications",
            "specs": {"diameter": "25mm", "pressure": "16 bar", "material": "rubber"}
        },
        {
            "id": "2",
            "title": "Stainless Steel Connector",
            "sku": "SC-316-M20",
            "description": "Food-grade stainless steel connector",
            "specs": {"material": "stainless steel 316", "type": "M20", "temperature": "-40 to 120°C"}
        }
    ]

    # Get embeddings
    embeddings = [
        embedding_service.embed(f"{p['title']} {p['description']}")
        for p in sample_products
    ]

    # Test query
    query = "What hose do you recommend for 16 bar pressure?"
    result = rag.answer(query, sample_products, embeddings)

    print("Query:", result["query"])
    print("Retrieved Products:", [p["title"] for p in result["retrieved_products"]])
    print("Answer:", result["answer"])
