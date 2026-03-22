"""
Enhanced FastAPI backend optimized for Railway + Vercel + R2 + OpenAI
Full production deployment
"""
import os
import json
import hashlib
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
import logging

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from pydantic import BaseModel
import asyncio

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Import local modules
from models import (
    init_db, Base,
    Document, Product, ProductChunk, UserInteraction, ChatMessage, SearchCache
)
from pdf_parser import PDFParser
from embeddings import create_embedding_service, ChunkingService
from rag_engine import RAGEngine
from recommendations import RecommendationEngine
from r2_storage import get_r2_client

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback for local development
    DATABASE_URL = "postgresql://user:password@localhost:5432/product_picker"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Initialize FastAPI
app = FastAPI(
    title="Product Picker API",
    description="Industrial product catalog with AI recommendations",
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
)

# CORS with production settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# GZIP compression
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Database
try:
    engine = init_db(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    logger.info("✅ Database initialized")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    engine = None

# Services
embedding_service = create_embedding_service()
rag_engine = RAGEngine(
    embedding_service=embedding_service,
    llm_provider=LLM_PROVIDER,
    model_name=LLM_MODEL
) if embedding_service else None
recommendation_engine = RecommendationEngine(embedding_model=embedding_service)
r2_client = get_r2_client()

logger.info(f"🚀 Starting in {ENVIRONMENT} mode")
logger.info(f"📡 LLM Provider: {LLM_PROVIDER} ({LLM_MODEL})")
logger.info(f"💾 Embeddings: {'Enabled' if embedding_service else 'Disabled'}")


# ==================== Pydantic Models ====================

class ProductResponse(BaseModel):
    id: UUID
    title: str
    sku: Optional[str]
    description: Optional[str]
    specs: Dict[str, str]
    category: str
    pressure_bar: Optional[float] = None
    diameter_mm: Optional[float] = None
    material: Optional[str] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 20
    skip: int = 0


class SearchResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    query: str
    execution_time: float


class FilterRequest(BaseModel):
    category: Optional[str] = None
    pressure_min: Optional[float] = None
    pressure_max: Optional[float] = None
    diameter_min: Optional[float] = None
    diameter_max: Optional[float] = None
    material: Optional[str] = None
    limit: int = 20


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    assistant_response: str
    retrieved_products: List[ProductResponse] = []


class DocumentUploadResponse(BaseModel):
    filename: str
    status: str
    products_count: int


# ==================== Routes ====================

@app.get("/health")
async def health():
    """Health check for deployment monitoring"""
    return {
        "status": "ok",
        "environment": ENVIRONMENT,
        "database": "connected" if engine else "disconnected",
        "embeddings": "enabled" if embedding_service else "disabled",
        "rag": "enabled" if rag_engine else "disabled",
        "r2": "connected" if r2_client else "disconnected",
    }


@app.get("/stats")
async def get_stats():
    """Get indexing statistics"""
    try:
        db = SessionLocal()

        total_docs = db.query(Document).count()
        total_products = db.query(Product).count()
        categories = db.query(Product.category).distinct().count()

        db.close()

        return {
            "total_documents": total_docs,
            "total_products": total_products,
            "categories": categories,
            "embeddings_enabled": embedding_service is not None,
            "rag_enabled": rag_engine is not None,
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": str(e)}


@app.get("/categories")
async def get_categories():
    """Get all product categories"""
    try:
        db = SessionLocal()
        categories = db.query(Product.category).distinct().order_by(Product.category).all()
        db.close()
        return [cat[0] for cat in categories if cat[0]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    """Semantic search for products"""
    import time
    start = time.time()

    try:
        db = SessionLocal()

        # Check cache first
        query_hash = hashlib.md5(f"{req.query}_{req.category}".encode()).hexdigest()
        cache = db.query(SearchCache).filter_by(query_hash=query_hash).first()

        if cache:
            cache.hit_count += 1
            cache.last_accessed = datetime.utcnow()
            db.commit()
            results = cache.results
        else:
            # Perform search
            q = db.query(Product)

            if req.category:
                q = q.filter(Product.category == req.category)

            search_term = f"%{req.query}%"
            q = q.filter(
                (Product.title.ilike(search_term)) |
                (Product.description.ilike(search_term)) |
                (Product.sku.ilike(search_term))
            )

            products = q.limit(req.limit).offset(req.skip).all()
            results = [ProductResponse.from_orm(p).__dict__ for p in products]

            # Cache the results
            cache_entry = SearchCache(
                query_hash=query_hash,
                query=req.query,
                category=req.category,
                results=results,
                hit_count=1
            )
            db.add(cache_entry)
            db.commit()

        db.close()

        execution_time = time.time() - start

        return SearchResponse(
            items=results,
            total=len(results),
            query=req.query,
            execution_time=execution_time
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/filter", response_model=SearchResponse)
async def filter_products(req: FilterRequest):
    """Advanced filtering by specs"""
    try:
        db = SessionLocal()

        q = db.query(Product)

        if req.category:
            q = q.filter(Product.category == req.category)

        if req.pressure_min:
            q = q.filter(Product.pressure_bar >= req.pressure_min)
        if req.pressure_max:
            q = q.filter(Product.pressure_bar <= req.pressure_max)

        if req.diameter_min:
            q = q.filter(Product.diameter_mm >= req.diameter_min)
        if req.diameter_max:
            q = q.filter(Product.diameter_mm <= req.diameter_max)

        if req.material:
            q = q.filter(Product.material.ilike(f"%{req.material}%"))

        products = q.limit(req.limit).all()
        db.close()

        items = [ProductResponse.from_orm(p) for p in products]

        return SearchResponse(
            items=items,
            total=len(items),
            query="advanced_filter",
            execution_time=0
        )

    except Exception as e:
        logger.error(f"Filter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """RAG-powered Q&A"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not available")

    try:
        db = SessionLocal()

        # Get products with embeddings for RAG
        products = db.query(Product).limit(100).all()
        embeddings = []

        for product in products:
            if product.embedding:
                try:
                    emb = embedding_service.string_to_embedding(product.embedding)
                    embeddings.append(emb)
                except:
                    embeddings.append(None)
            else:
                embeddings.append(None)

        # Get RAG answer
        rag_result = rag_engine.answer(
            req.message,
            [p.__dict__ for p in products],
            embeddings,
            top_k=3
        )

        # Save chat history
        msg = ChatMessage(
            session_id=req.session_id,
            role="user",
            content=req.message
        )
        db.add(msg)

        response_msg = ChatMessage(
            session_id=req.session_id,
            role="assistant",
            content=rag_result["answer"],
            retrieved_products=rag_result["retrieved_products"]
        )
        db.add(response_msg)

        interaction = UserInteraction(
            user_id=req.session_id,
            action="chat",
            query=req.message
        )
        db.add(interaction)
        db.commit()
        db.close()

        return ChatResponse(
            session_id=req.session_id,
            user_message=req.message,
            assistant_response=rag_result["answer"],
            retrieved_products=[]
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID):
    """Get product details"""
    try:
        db = SessionLocal()
        product = db.query(Product).filter(Product.id == product_id).first()
        db.close()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return ProductResponse.from_orm(product)

    except Exception as e:
        logger.error(f"Product get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommendations/{product_id}")
async def get_recommendations(product_id: UUID, limit: int = 5):
    """Get similar products"""
    try:
        db = SessionLocal()
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        similar = db.query(Product).filter(
            (Product.category == product.category) &
            (Product.id != product_id)
        ).limit(limit).all()

        db.close()

        return [ProductResponse.from_orm(p) for p in similar]

    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pdf/index-from-r2")
async def index_pdfs_from_r2(background_tasks: BackgroundTasks):
    """Download and index PDFs from R2 storage"""
    if not r2_client:
        raise HTTPException(status_code=503, detail="R2 storage not configured")

    # Schedule background task
    background_tasks.add_task(process_r2_pdfs)

    return {"status": "indexing", "message": "PDF indexing started"}


async def process_r2_pdfs():
    """Background task to process PDFs from R2"""
    try:
        logger.info("Starting R2 PDF indexing...")

        # Import here to avoid circular imports
        from scripts.download_pdfs_from_r2 import download_and_parse_pdfs

        download_and_parse_pdfs(limit=20)
        logger.info("✅ R2 PDF indexing completed")
    except Exception as e:
        logger.error(f"Error indexing R2 PDFs: {e}")


if __name__ == "__main__":
    import uvicorn

    # Use gunicorn for production, uvicorn for development
    if ENVIRONMENT == "production":
        # Gunicorn will be used (see railway.json)
        pass
    else:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
