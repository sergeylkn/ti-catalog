"""
Download PDFs from Cloudflare R2 and parse them
Designed to run on Railway after deployment
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.r2_storage import R2StorageClient
from backend.pdf_parser import parse_pdf
from backend.models import init_db, Document, Product
from sqlalchemy.orm import sessionmaker

def download_and_parse_pdfs(limit: int = 50):
    """Download PDFs from R2 and parse them into database"""

    print("🔗 Connecting to R2...")
    r2 = R2StorageClient()

    # Get list of PDFs
    pdf_files = r2.list_files()
    print(f"📋 Found {len(pdf_files)} PDFs in R2")

    # Initialize database
    print("💾 Connecting to database...")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return

    engine = init_db(db_url)
    SessionLocal = sessionmaker(bind=engine)

    # Download and parse
    cache_dir = Path("/tmp/pdfs")
    cache_dir.mkdir(exist_ok=True)

    parsed_count = 0
    for i, pdf_file in enumerate(pdf_files[:limit]):
        print(f"\n[{i+1}/{min(limit, len(pdf_files))}] Processing {pdf_file}...")

        try:
            # Download PDF
            local_path = cache_dir / pdf_file
            if not r2.download_file(pdf_file, str(local_path)):
                continue

            # Parse PDF
            result = parse_pdf(str(local_path), max_items=5)  # Limit items per PDF

            # Store in database
            db = SessionLocal()

            # Check if already exists
            existing = db.query(Document).filter_by(file_hash=result['file_hash']).first()
            if existing:
                print(f"  ⏭️  Already parsed (hash: {result['file_hash'][:8]}...)")
                db.close()
                continue

            # Create document
            doc = Document(
                filename=result['filename'],
                category=pdf_file.split('_')[0].replace('-', ' ').title(),
                url=r2.get_public_url(pdf_file),
                file_hash=result['file_hash'],
                pages=result['pages']
            )
            db.add(doc)
            db.flush()

            # Add products
            product_count = 0
            for prod_data in result['products'][:5]:  # Limit products
                product = Product(
                    document_id=doc.id,
                    title=prod_data.get('title', 'Unknown'),
                    sku=prod_data.get('sku'),
                    description=prod_data.get('description'),
                    specs=prod_data.get('specs', {}),
                    category=doc.category,
                    page_number=prod_data.get('page_number'),
                )
                db.add(product)
                product_count += 1

            db.commit()
            print(f"  ✅ Parsed: {product_count} products added")
            parsed_count += 1

            db.close()

            # Cleanup
            local_path.unlink()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    print(f"\n✅ Successfully parsed {parsed_count} PDFs")


if __name__ == "__main__":
    download_and_parse_pdfs(limit=50)
