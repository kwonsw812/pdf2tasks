"""Basic usage examples for PDF Extractor."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from extractors import PDFExtractor
from utils.logger import setup_logging


def example_1_basic_extraction():
    """Example 1: Basic full PDF extraction."""
    print("\n=== Example 1: Basic Full Extraction ===\n")

    # Setup logging
    setup_logging()

    # Initialize extractor
    extractor = PDFExtractor()

    # Extract all content
    result = extractor.extract("sample.pdf")

    # Access metadata
    print(f"Document Title: {result.metadata.title}")
    print(f"Total Pages: {result.metadata.total_pages}")

    # Access page content
    for page in result.pages:
        print(f"\nPage {page.page_number}:")
        print(f"  - {len(page.text)} text blocks")
        print(f"  - {len(page.images)} images")
        print(f"  - {len(page.tables)} tables")

    # Cleanup
    extractor.cleanup()


def example_2_text_only():
    """Example 2: Extract text only (fast mode)."""
    print("\n=== Example 2: Text-Only Extraction ===\n")

    setup_logging()
    extractor = PDFExtractor()

    # Extract plain text
    text = extractor.extract_text_only("sample.pdf")

    print(f"Extracted {len(text)} characters")
    print(f"\nFirst 500 characters:\n{text[:500]}...")


def example_3_metadata_only():
    """Example 3: Extract metadata only."""
    print("\n=== Example 3: Metadata Only ===\n")

    setup_logging()
    extractor = PDFExtractor()

    # Extract metadata
    metadata = extractor.get_metadata("sample.pdf")

    print(f"Title: {metadata.title}")
    print(f"Author: {metadata.author}")
    print(f"Subject: {metadata.subject}")
    print(f"Creator: {metadata.creator}")
    print(f"Producer: {metadata.producer}")
    print(f"Creation Date: {metadata.creation_date}")
    print(f"Total Pages: {metadata.total_pages}")


def example_4_specific_page():
    """Example 4: Extract specific page."""
    print("\n=== Example 4: Extract Specific Page ===\n")

    setup_logging()
    extractor = PDFExtractor()

    # Extract page 1
    page = extractor.extract_page("sample.pdf", page_number=1)

    print(f"Page {page.page_number}:")
    print(f"  Text blocks: {len(page.text)}")
    print(f"  Images: {len(page.images)}")
    print(f"  Tables: {len(page.tables)}")

    # Access text with metadata
    if page.text:
        first_text = page.text[0]
        print(f"\nFirst text block:")
        print(f"  Content: {first_text.text[:100]}...")
        if first_text.metadata:
            print(f"  Font size: {first_text.metadata.font_size}")
            print(f"  Font name: {first_text.metadata.font_name}")

    # Cleanup
    extractor.cleanup()


def example_5_tables():
    """Example 5: Extract and process tables."""
    print("\n=== Example 5: Table Extraction ===\n")

    setup_logging()
    extractor = PDFExtractor(extract_images=False)  # Skip images for speed

    result = extractor.extract("sample.pdf")

    # Find and process tables
    for page in result.pages:
        if page.tables:
            print(f"\nPage {page.page_number} has {len(page.tables)} table(s)")

            for idx, table in enumerate(page.tables):
                print(f"\nTable {idx + 1}:")
                print(f"  Rows: {len(table.rows)}")
                print(f"  Columns: {len(table.rows[0]) if table.rows else 0}")

                # Print first few rows
                print("\n  First 3 rows:")
                for row in table.rows[:3]:
                    print(f"    {row}")


def example_6_selective_extraction():
    """Example 6: Selective extraction (customize what to extract)."""
    print("\n=== Example 6: Selective Extraction ===\n")

    setup_logging()

    # Extract only text and tables, skip images
    extractor = PDFExtractor(
        extract_images=False,
        extract_tables=True,
        output_dir="./custom_output",
    )

    result = extractor.extract("sample.pdf")

    print(f"Extracted {len(result.pages)} pages")
    print("(Images were skipped)")


def example_7_error_handling():
    """Example 7: Error handling."""
    print("\n=== Example 7: Error Handling ===\n")

    setup_logging()

    from extractors.exceptions import (
        FileNotFoundError,
        PDFParseError,
        EncryptedPDFError,
    )

    extractor = PDFExtractor()

    try:
        result = extractor.extract("nonexistent.pdf")
    except FileNotFoundError as e:
        print(f"File not found: {e}")

    try:
        result = extractor.extract("encrypted.pdf")
    except EncryptedPDFError as e:
        print(f"PDF is encrypted: {e}")

    try:
        result = extractor.extract("corrupted.pdf")
    except PDFParseError as e:
        print(f"Failed to parse PDF: {e}")


if __name__ == "__main__":
    # Run all examples (comment out as needed)
    # example_1_basic_extraction()
    # example_2_text_only()
    # example_3_metadata_only()
    # example_4_specific_page()
    # example_5_tables()
    # example_6_selective_extraction()
    # example_7_error_handling()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("Uncomment the example functions you want to run.")
    print("=" * 80 + "\n")
