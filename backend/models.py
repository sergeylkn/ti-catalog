"""
Optimized schema for 500MB storage limit
Uses PostgreSQL with pgvector for efficient storage
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    url = Column(String(500))
    pages = Column(Integer, default=0)
    file_hash = Column(String(64), unique=True)  # SHA256 for deduplication
    parsed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_parsed_at', 'parsed_at'),
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False, index=True)
    sku = Column(String(100), index=True, nullable=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)

    # Specs stored as JSON - allows flexible schema
    specs = Column(JSONB, default={})

    # For quick filtering
    pressure_bar = Column(Float, nullable=True, index=True)  # Pressure in bar
    diameter_mm = Column(Float, nullable=True, index=True)   # Diameter in mm
    material = Column(String(100), nullable=True, index=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)

    # Text for search and embeddings
    searchable_text = Column(Text, nullable=True)

    # Embedding vector - compact 384 dims for space efficiency
    embedding = Column(String(2048), nullable=True)  # Stored as JSON string

    page_number = Column(Integer, nullable=True)
    coordinates = Column(JSON, nullable=True)  # bbox on page

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_sku', 'sku'),
        Index('idx_title', 'title'),
        Index('idx_category', 'category'),
        Index('idx_document_id', 'document_id'),
        Index('idx_pressure', 'pressure_bar'),
        Index('idx_diameter', 'diameter_mm'),
        Index('idx_material', 'material'),
    )


class ProductChunk(Base):
    """Store text chunks for RAG"""
    __tablename__ = "product_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    # Embedding for semantic search (compact)
    embedding = Column(String(2048), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class UserInteraction(Base):
    """Track user interactions for recommendations and analytics"""
    __tablename__ = "user_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=True)

    # Action: view, search, click, favorite, compare
    action = Column(String(50), nullable=False, index=True)

    # Context
    query = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)
    metadata = Column(JSONB, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_action', 'action'),
        Index('idx_created_at', 'created_at'),
    )


class ChatMessage(Base):
    """Store chat history for RAG conversations"""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, index=True)

    # role: user, assistant
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)

    # Retrieved context
    retrieved_products = Column(JSONB, default=[])

    created_at = Column(DateTime, default=datetime.utcnow)


class SearchCache(Base):
    """Cache popular searches to save compute"""
    __tablename__ = "search_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_hash = Column(String(64), unique=True, nullable=False, index=True)
    query = Column(String(500), nullable=False)
    category = Column(String(100), nullable=True)

    # Cached result as JSON
    results = Column(JSONB, nullable=False)

    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_query_hash', 'query_hash'),
        Index('idx_hit_count', 'hit_count'),
    )


# Database initialization
def init_db(database_url: str):
    """Initialize database with all tables"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    print("✅ Database initialized")
    return engine


if __name__ == "__main__":
    # Example: initialize local database
    import os
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/product_picker")
    init_db(db_url)
