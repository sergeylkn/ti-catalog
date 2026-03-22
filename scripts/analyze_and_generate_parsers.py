#!/usr/bin/env python3
"""
analyze_and_generate_parsers.py

Downloads manifest.txt from configured base URL, constructs PDF URLs,
downloads each PDF, runs lightweight analysis (pages, text-extractability,
number of tables, images) and generates:
 - parsers/parsers.json : parser config suggestions per file
 - parsers/<safe_name>_parser.py : a stub parser template for each PDF

Dependencies: requests, PyMuPDF (fitz), pdfplumber
Optional: pytesseract, camelot for full parsing

Usage: python scripts/analyze_and_generate_parsers.py --manifest-url <url>
"""
import os
import re
import sys
import json
import argparse
import tempfile
from pathlib import Path

import requests

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import pdfplumber
except Exception:
    pdfplumber = None

BASE_SAVE = Path("./_downloaded_pdfs")
PARSERS_DIR = Path("./parsers")
PARSERS_DIR.mkdir(exist_ok=True)
BASE_SAVE.mkdir(exist_ok=True)

GENERIC_SKU_REGEX = r"[A-Z0-9\-_/]{4,}"


def safe_name(filename: str) -> str:
    return re.sub(r"[^0-9a-zA-Z_]+", "_", filename)


def download(url: str, target: Path) -> Path:
    if target.exists():
        return target
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    with open(target, "wb") as f:
        for chunk in r.iter_content(1024 * 64):
            f.write(chunk)
    return target


def analyze_pdf(path: Path, max_pages_sample: int = 3) -> dict:
    info = {"pages": 0, "text_sample_len": 0, "tables_found": 0, "images_found": 0}
    text_sample = ""
    try:
        if fitz is None:
            info["fitz_available"] = False
            return info
        doc = fitz.open(str(path))
        info["pages"] = doc.page_count
        # sample first n pages text
        for pno in range(min(max_pages_sample, doc.page_count)):
            page = doc.load_page(pno)
            t = page.get_text("text") or ""
            text_sample += t + "\n"
            # images via PyMuPDF
            try:
                img_list = page.get_images()
                info["images_found"] += len(img_list)
            except Exception:
                pass
        info["text_sample_len"] = len(text_sample)
    except Exception as e:
        info["error_fitz"] = str(e)

    # table detection via pdfplumber (if available)
    if pdfplumber is not None:
        try:
            with pdfplumber.open(str(path)) as pdf:
                for pno in range(min(max_pages_sample, len(pdf.pages))):
                    page = pdf.pages[pno]
                    tables = page.extract_tables()
                    info["tables_found"] += len(tables or [])
        except Exception as e:
            info["error_pdfplumber"] = str(e)
    else:
        info["pdfplumber_available"] = False

    # heuristics
    info["scanned"] = info.get("text_sample_len", 0) < 200 and info.get("images_found", 0) > 0
    # classify
    if info.get("tables_found", 0) >= 3:
        info["layout_type"] = "table_heavy"  # spec sheet
    elif info.get("images_found", 0) >= 3 and info.get("text_sample_len", 0) > 0:
        info["layout_type"] = "catalog_with_images"
    elif info.get("scanned"):
        info["layout_type"] = "scanned_document"
    else:
        info["layout_type"] = "text_document"

    return info


def make_parser_stub(filename: str, cfg: dict):
    sname = safe_name(filename)
    stub_path = PARSERS_DIR / f"{sname}_parser.py"
    if stub_path.exists():
        return
    content = f'''"""
Parser stub for {filename}
Auto-generated parser guidance.
"""
from typing import List, Dict

# Recommended tools: PyMuPDF (fitz), pdfplumber, camelot (for tables), pytesseract (for OCR)

def parse_{sname}(pdf_path: str) -> List[Dict]:
    """Parse PDF and return list of product items or sections.

    Return format (example):
    [
      {{
         "id": "unique",
         "title": "...",
         "sku": "...",
         "description": "...",
         "specs": {{"diameter_mm": 25, "pressure_bar": 16}},
         "tables": [ ... ],
         "images": ["path/to/img1.png"]
      }}
    ]
    """
    # TODO: implement parsing logic for this specific PDF
    # Heuristic configuration:
    config = {json.dumps(cfg, ensure_ascii=False)}

    # Typical steps:
    # 1) Try digital text extraction (PyMuPDF or pdfplumber)
    # 2) If scanned: run OCR (pytesseract) on page images
    # 3) Detect tables (camelot/pdfplumber) and parse numeric fields
    # 4) Segment page into product cards by bbox clustering if catalog
    # 5) Extract SKU/title using regex and heuristics

    items = []
    # ... implement
    return items
'''
    with open(stub_path, "w", encoding="utf-8") as f:
        f.write(content)


def main(manifest_url: str, base_url: str = None):
    r = requests.get(manifest_url, timeout=30)
    r.raise_for_status()
    filenames = [ln.strip() for ln in r.text.splitlines() if ln.strip()]

    results = []
    for fn in filenames:
        # allow manifest lines that may contain multiple filenames per line
        parts = re.split(r"\s+", fn)
        for p in parts:
            if not p:
                continue
            fname = p
            if base_url:
                url = base_url.rstrip('/') + '/' + fname
            else:
                # derive base from manifest_url
                url = manifest_url.rsplit('/', 1)[0].rstrip('/') + '/' + fname
            safe = safe_name(fname)
            print("Processing:", fname)
            try:
                target = BASE_SAVE / fname
                target.parent.mkdir(parents=True, exist_ok=True)
                download(url, target)
            except Exception as e:
                print("  download failed:", e)
                results.append({"filename": fname, "url": url, "error": f"download failed: {e}"})
                continue

            info = analyze_pdf(target)
            cfg = {
                "filename": fname,
                "url": url,
                "pages": info.get("pages"),
                "layout_type": info.get("layout_type"),
                "scanned": info.get("scanned"),
                "tables_found": info.get("tables_found"),
                "images_found": info.get("images_found"),
                "recommended_parsers": {
                    "text_extraction": "pymupdf/pdfplumber",
                    "ocr": "pytesseract" if info.get("scanned") else None,
                    "table_parser": "camelot/tabula" if info.get("tables_found", 0) > 0 else None,
                    "image_extraction": True if info.get("images_found", 0) > 0 else False,
                    "segment_strategy": "card_segmentation" if info.get("layout_type") == "catalog_with_images" else "page_sectioning"
                },
                "sample_text_len": info.get("text_sample_len")
            }
            # add some generic regex suggestions
            cfg["regex_sku"] = GENERIC_SKU_REGEX
            cfg["regex_dimension"] = r"(\d+(?:\.\d+)?)\s*(mm|cm|m)"
            cfg["regex_pressure"] = r"(\d+(?:\.\d+)?)\s*(bar|MPa)"

            results.append(cfg)

            # create parser stub file
            make_parser_stub(fname, cfg)

    # save parsers.json
    out = PARSERS_DIR / "parsers.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Wrote:", out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest-url", help="URL to manifest.txt", default="https://pub-ada201ec5fb84401a3b36b7b21e6ed0f.r2.dev/manifest.txt")
    ap.add_argument("--base-url", help="Optional base URL for PDFs (overrides manifest folder)")
    args = ap.parse_args()
    main(args.manifest_url, args.base_url)
