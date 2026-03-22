"""
PDF Parser with full feature support
Extracts text, tables, specs, and coordinates for product items
"""
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


@dataclass
class ProductItem:
    """Extracted product item from PDF"""
    sku: Optional[str] = None
    title: str = ""
    description: str = ""
    specs: Dict[str, str] = None
    page_number: int = 0
    bbox: Optional[Tuple[float, float, float, float]] = None  # (x0, y0, x1, y1)
    images: List[str] = None

    def __post_init__(self):
        if self.specs is None:
            self.specs = {}
        if self.images is None:
            self.images = []


class PDFParser:
    """
    Comprehensive PDF parser for product catalogs
    Handles: text extraction, tables, specs, images, OCR for scanned docs
    """

    # Regex patterns for common fields
    SKU_PATTERNS = [
        r'(?:SKU|Art\.?|Article|Artikel)[\s:]+([A-Z0-9\-/_]+)',
        r'(?:Model|Modell)[\s:]+([A-Z0-9\-/_]+)',
        r'^[A-Z0-9]{3,}(?:\-[A-Z0-9]+)*$',  # Generic SKU
    ]

    PRESSURE_PATTERNS = [
        r'(\d+(?:\.\d+)?)\s*(?:bar|BAR|бар)',
        r'(\d+(?:\.\d+)?)\s*MPa',
    ]

    DIMENSION_PATTERNS = [
        r'Ø\s*(\d+(?:\.\d+)?)\s*mm',
        r'Diameter[\s:]+(\d+(?:\.\d+)?)\s*mm',
        r'(\d+(?:\.\d+)?)\s*mm',
    ]

    TEMPERATURE_PATTERN = r'(?:Temp|Temperature)[\s:]+(-?\d+)\s*(?:to|–)\s*(\+?\d+)\s*°?C'

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.filename = self.pdf_path.name
        self.doc = None
        self.page_count = 0
        self._open_pdf()

    def _open_pdf(self):
        """Open PDF with appropriate library"""
        if PYMUPDF_AVAILABLE:
            self.doc = fitz.open(str(self.pdf_path))
            self.page_count = self.doc.page_count
        elif PDFPLUMBER_AVAILABLE:
            import pdfplumber as pp
            self.doc = pp.open(str(self.pdf_path))
            self.page_count = len(self.doc.pages)
        else:
            raise RuntimeError("Neither PyMuPDF nor pdfplumber available")

    def get_file_hash(self) -> str:
        """Get SHA256 hash of PDF for deduplication"""
        sha256_hash = hashlib.sha256()
        with open(self.pdf_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def extract_text_page(self, page_num: int) -> Tuple[str, List]:
        """Extract text and blocks from page"""
        if PYMUPDF_AVAILABLE and self.doc:
            page = self.doc.load_page(page_num)
            text = page.get_text("text")
            blocks = page.get_text("blocks")  # [(x0, y0, x1, y1, text, block_no, block_type)]
            return text, blocks
        elif PDFPLUMBER_AVAILABLE and self.doc:
            page = self.doc.pages[page_num]
            text = page.extract_text() or ""
            # Get text elements with coordinates
            chars = page.chars or []
            return text, chars
        return "", []

    def extract_tables_page(self, page_num: int) -> List[List[List[str]]]:
        """Extract tables from page"""
        if PDFPLUMBER_AVAILABLE and self.doc:
            page = self.doc.pages[page_num]
            tables = page.extract_tables() or []
            return tables
        return []

    def extract_images_page(self, page_num: int, output_dir: str = None) -> List[str]:
        """Extract images from page"""
        images = []
        if PYMUPDF_AVAILABLE and self.doc:
            page = self.doc.load_page(page_num)
            image_list = page.get_images()

            for img_index, xref in enumerate(image_list):
                pix = fitz.Pixmap(self.doc, xref)

                if output_dir:
                    output_path = Path(output_dir) / f"{self.filename}_p{page_num}_img{img_index}.png"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    pix.save(str(output_path))
                    images.append(str(output_path))

        return images

    def _extract_sku(self, text: str) -> Optional[str]:
        """Extract SKU/article number from text"""
        for pattern in self.SKU_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1)
        return None

    def _extract_specs(self, text: str) -> Dict[str, str]:
        """Extract specifications from text"""
        specs = {}

        # Pressure
        for pattern in self.PRESSURE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                specs['pressure'] = f"{match.group(1)} bar"
                break

        # Diameter
        for pattern in self.DIMENSION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                specs['diameter'] = f"{match.group(1)} mm"
                break

        # Temperature range
        match = re.search(self.TEMPERATURE_PATTERN, text, re.IGNORECASE)
        if match:
            specs['temperature_range'] = f"{match.group(1)}...{match.group(2)}°C"

        # Material (simple extraction)
        materials = ['stainless', 'steel', 'rubber', 'plastic', 'nylon', 'teflon', 'brass']
        for material in materials:
            if material.lower() in text.lower():
                specs['material'] = material.capitalize()
                break

        return specs

    def segment_page_into_cards(self, page_num: int) -> List[ProductItem]:
        """Try to segment page into product cards"""
        text, blocks = self.extract_text_page(page_num)

        # Simple heuristic: split by large gaps or markers
        # In production: use ML-based layout parser (LayoutLM, Donut)
        items = []

        # Split by common separators or page breaks
        sections = re.split(r'\n\s*\n+', text)

        for section in sections:
            if len(section.strip()) < 20:  # Skip very small sections
                continue

            item = ProductItem(
                page_number=page_num,
                title=section.split('\n')[0][:100],
                description=section[:300],
                sku=self._extract_sku(section),
                specs=self._extract_specs(section),
            )
            items.append(item)

        return items

    def parse_full(self, max_items: int = None) -> Dict:
        """Parse entire PDF and extract products"""
        result = {
            'filename': self.filename,
            'file_hash': self.get_file_hash(),
            'pages': self.page_count,
            'products': [],
            'tables': [],
            'images': [],
        }

        for page_num in range(min(self.page_count, max_items or self.page_count)):
            print(f"  Parsing page {page_num + 1}/{self.page_count}...")

            # Extract text-based products
            page_products = self.segment_page_into_cards(page_num)
            result['products'].extend([asdict(p) for p in page_products])

            # Extract tables
            tables = self.extract_tables_page(page_num)
            for table_idx, table in enumerate(tables):
                result['tables'].append({
                    'page': page_num,
                    'table_index': table_idx,
                    'data': table,
                })

        return result

    def close(self):
        """Close PDF document"""
        if PYMUPDF_AVAILABLE and self.doc:
            self.doc.close()
        elif PDFPLUMBER_AVAILABLE and self.doc:
            self.doc.close()


def parse_pdf(pdf_path: str, max_items: int = None) -> Dict:
    """Convenience function to parse PDF"""
    parser = PDFParser(pdf_path)
    result = parser.parse_full(max_items)
    parser.close()
    return result


if __name__ == "__main__":
    # Test parser
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <pdf_path>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    print(f"Parsing: {pdf_file}")

    result = parse_pdf(pdf_file, max_items=3)
    print(json.dumps(result, indent=2, default=str))
