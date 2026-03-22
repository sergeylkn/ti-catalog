"""
Generate sample parsers.json with demo data
Run this to create mock product data for testing
"""
from parsers.auto_generated_parsers import (
    manifest_filenames,
    BASE_URL,
    generate_parsers_json
)
from pathlib import Path
import json

def generate_demo_data():
    """Generate demo product data in parsers.json"""
    output_file = Path("parsers/parsers.json")

    # Generate base parser configs
    generate_parsers_json(str(output_file))

    print(f"✅ Generated {output_file} with {len(manifest_filenames)} file entries")
    print(f"📊 Sample entries (first 3):")

    with open(output_file) as f:
        data = json.load(f)
        for item in data[:3]:
            print(f"  - {item['filename']}")

if __name__ == "__main__":
    generate_demo_data()
