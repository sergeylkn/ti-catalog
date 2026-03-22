"""
Enhanced FastAPI backend with full features:
- PDF parsing and ingestion
- Vector embeddings and semantic search
- PostgreSQL storage with pgvector
- RAG-powered Q&A chat
- Advanced filtering
- Caching and optimization for 500MB limit
"""
import os
import json
import hashlib
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
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

# Environment setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/product_picker")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/pdfs")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # or "openai"

# Initialize FastAPI
app = FastAPI(
    title="Interactive Product Picker API",
    description="Full-featured PDF catalog search with recommendations and RAG",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
try:
    engine = init_db(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
except Exception as e:
    print(f"⚠️  Database initialization failed: {e}")
    engine = None

# Embedding service
embedding_service = create_embedding_service()

# RAG engine
rag_engine = RAGEngine(
    embedding_service=embedding_service,
    llm_provider=LLM_PROVIDER
) if embedding_service else None

# Recommendation engine
recommendation_engine = RecommendationEngine(embedding_model=embedding_service)


# ==================== Pydantic Models ====================

class ProductResponse(BaseModel):
    id: UUID
    title: str
    sku: Optional[str]
    description: Optional[str]
    specs: Dict[str, str]
    category: str
    pressure_bar: Optional[float]
    diameter_mm: Optional[float]
    material: Optional[str]

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
    skip: int = 0


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    assistant_response: str
    retrieved_products: List[ProductResponse]


class DocumentUploadResponse(BaseModel):
    filename: str
    status: str
    products_count: int
    file_hash: str


# ==================== Routes ====================

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "database": "connected" if engine else "disconnected",
        "embeddings": "enabled" if embedding_service else "disabled",
        "rag": "enabled" if rag_engine else "disabled"
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

            # Full-text search
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

        products = q.limit(req.limit).offset(req.skip).all()
        db.close()

        items = [ProductResponse.from_orm(p) for p in products]

        return SearchResponse(
            items=items,
            total=len(items),
            query="advanced_filter",
            execution_time=0
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """RAG-powered Q&A"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not available")

    try:
        db = SessionLocal()

        # Get all products with embeddings for RAG
        products = db.query(Product).all()
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

        # Save to chat history
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
        db.commit()

        # Log interaction
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
            retrieved_products=[
                ProductResponse.from_orm(p) 
                for p in products 
                if any(rp["id"] == str(p.id) for rp in rag_result["retrieved_products"])
            ]
        )

    except Exception as e:
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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommendations/{product_id}")
async def get_recommendations(product_id: UUID, limit: int = 5):
    """Get similar products"""
    try:
        db = SessionLocal()
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get similar products from same category
        similar = db.query(Product).filter(
            (Product.category == product.category) &
            (Product.id != product_id)
        ).limit(limit).all()

        db.close()

        return [ProductResponse.from_orm(p) for p in similar]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-pdf", response_model=DocumentUploadResponse)
async def upload_pdf(pdf_path: str, background_tasks: BackgroundTasks):
    """Upload and parse a PDF"""
    try:
        # Parse PDF
        parser = PDFParser(pdf_path)
        result = parser.parse_full(max_items=None)
        parser.close()

        # Store in database
        db = SessionLocal()

        # Check if already parsed
        existing = db.query(Document).filter_by(file_hash=result["file_hash"]).first()
        if existing:
            return DocumentUploadResponse(
                filename=result["filename"],
                status="already_exists",
                products_count=0,
                file_hash=result["file_hash"]
            )

        # Create document
        doc = Document(
            filename=result["filename"],
            category="Imported",
            file_hash=result["file_hash"],
            pages=result["pages"]
        )
        db.add(doc)
        db.flush()

        # Add products
        product_count = 0
        for prod_data in result["products"]:
            product = Product(
                document_id=doc.id,
                title=prod_data.get("title", "Unknown"),
                sku=prod_data.get("sku"),
                description=prod_data.get("description"),
                specs=prod_data.get("specs", {}),
                category="Imported",
                page_number=prod_data.get("page_number"),
            )

            # Generate embedding if service available
            if embedding_service:
                text = f"{product.title} {product.description}"
                emb = embedding_service.embed(text)
                product.embedding = embedding_service.embedding_to_string(emb)

            db.add(product)
            product_count += 1

        db.commit()
        db.close()

        return DocumentUploadResponse(
            filename=result["filename"],
            status="success",
            products_count=product_count,
            file_hash=result["file_hash"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket for live chat ====================

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket for real-time chat"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            # Process message
            req = ChatRequest(session_id=session_id, message=data)
            response = await chat(req)

            await websocket.send_json({
                "type": "response",
                "data": response.dict()
            })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
