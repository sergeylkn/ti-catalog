"""
Generate embeddings for all products in database
Run after parsing PDFs
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.embeddings import create_embedding_service
from backend.models import init_db, Product
from sqlalchemy.orm import sessionmaker

def generate_embeddings():
    """Generate embeddings for all products without embeddings"""

    print("🧠 Creating embedding service...")
    embedding_service = create_embedding_service()

    if not embedding_service:
        print("❌ Embedding service not available")
        return

    print("💾 Connecting to database...")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return

    engine = init_db(db_url)
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()

    # Find products without embeddings
    products = db.query(Product).filter(Product.embedding == None).all()
    print(f"📊 Found {len(products)} products without embeddings")

    # Generate embeddings in batches
    batch_size = 32
    for i in range(0, len(products), batch_size):
        batch = products[i:i+batch_size]
        texts = [
            f"{p.title} {p.description or ''} {' '.join([f'{k}:{v}' for k,v in (p.specs or {}).items()])}"
            for p in batch
        ]

        # Generate embeddings
        embeddings = embedding_service.embed_batch(texts, show_progress=False)

        # Save to database
        for product, embedding in zip(batch, embeddings):
            product.embedding = embedding_service.embedding_to_string(embedding)

        db.commit()
        print(f"  ✅ Processed batch {i//batch_size + 1}")

    db.close()
    print("✅ Embeddings generation complete")


if __name__ == "__main__":
    generate_embeddings()
