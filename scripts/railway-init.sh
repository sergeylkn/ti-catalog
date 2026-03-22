#!/bin/bash
# Railway initialization script
# Run after deployment to set up database and seed data

set -e

echo "🚀 Initializing Railway deployment..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
for i in {1..30}; do
    if python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    echo "  Attempt $i/30..."
    sleep 2
done

# Initialize database
echo "📊 Initializing database..."
python backend/models.py

# Download sample PDFs from R2
echo "📥 Downloading PDFs from R2..."
python scripts/download_pdfs_from_r2.py

# Generate embeddings for sample products
echo "🧠 Generating embeddings..."
python scripts/generate_embeddings.py

# Run migrations if needed
echo "✅ Deployment initialization complete"
