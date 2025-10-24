"""Test script for PDF Extractor."""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.extractors import PDFExtractor
from src.utils.logger import setup_logging


def save_results_to_files(result, metadata, plain_text, output_dir="./test_results"):
    """Save extraction results to files."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Save JSON result
    json_path = os.path.join(output_dir, f"extraction_result_{timestamp}.json")
    json_data = {
        "metadata": {
            "title": metadata.title,
            "author": metadata.author,
            "subject": metadata.subject,
            "creator": metadata.creator,
            "producer": metadata.producer,
            "creation_date": str(metadata.creation_date) if metadata.creation_date else None,
            "modification_date": str(metadata.modification_date) if metadata.modification_date else None,
            "total_pages": metadata.total_pages,
        },
        "pages": []
    }

    for page in result.pages:
        page_data = {
            "page_number": page.page_number,
            "text_blocks": [
                {
                    "text": text.text,
                    "metadata": {
                        "font_size": text.metadata.font_size if text.metadata else None,
                        "font_name": text.metadata.font_name if text.metadata else None,
                        "position": text.metadata.position.model_dump() if text.metadata and text.metadata.position else None,
                    }
                }
                for text in page.text
            ],
            "images": [
                {
                    "image_path": img.image_path,
                    "width": img.width,
                    "height": img.height,
                }
                for img in page.images
            ],
            "tables": [
                {
                    "rows": table.rows,
                    "row_count": len(table.rows),
                    "column_count": len(table.rows[0]) if table.rows else 0,
                    "position": table.position.model_dump() if table.position else None,
                }
                for table in page.tables
            ]
        }
        json_data["pages"].append(page_data)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"✓ JSON 결과 저장: {json_path}")

    # 2. Save plain text
    text_path = os.path.join(output_dir, f"extracted_text_{timestamp}.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(plain_text)

    print(f"✓ 텍스트 저장: {text_path}")

    # 3. Save summary report
    report_path = os.path.join(output_dir, f"extraction_report_{timestamp}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("PDF 추출 결과 리포트\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("📄 메타데이터\n")
        f.write("-" * 80 + "\n")
        f.write(f"제목: {metadata.title or 'N/A'}\n")
        f.write(f"저자: {metadata.author or 'N/A'}\n")
        f.write(f"주제: {metadata.subject or 'N/A'}\n")
        f.write(f"총 페이지: {metadata.total_pages}\n")
        f.write(f"생성일: {metadata.creation_date or 'N/A'}\n\n")

        f.write("📊 추출 요약\n")
        f.write("-" * 80 + "\n")
        total_text_blocks = sum(len(page.text) for page in result.pages)
        total_images = sum(len(page.images) for page in result.pages)
        total_tables = sum(len(page.tables) for page in result.pages)

        f.write(f"총 텍스트 블록: {total_text_blocks}개\n")
        f.write(f"총 이미지: {total_images}개\n")
        f.write(f"총 표: {total_tables}개\n")
        f.write(f"총 텍스트 길이: {len(plain_text):,} 글자\n\n")

        f.write("📑 페이지별 상세 정보\n")
        f.write("-" * 80 + "\n")
        for page in result.pages:
            f.write(f"\n[Page {page.page_number}]\n")
            f.write(f"  - 텍스트 블록: {len(page.text)}개\n")
            f.write(f"  - 이미지: {len(page.images)}개\n")
            f.write(f"  - 표: {len(page.tables)}개\n")

            if page.images:
                f.write(f"  - 이미지 목록:\n")
                for img in page.images:
                    f.write(f"    · {os.path.basename(img.image_path)} ({img.width}x{img.height})\n")

            if page.tables:
                f.write(f"  - 표 정보:\n")
                for i, table in enumerate(page.tables, 1):
                    f.write(f"    · 표 {i}: {len(table.rows)}행 x {len(table.rows[0]) if table.rows else 0}열\n")

    print(f"✓ 리포트 저장: {report_path}")

    # 4. Save tables as CSV
    table_count = 0
    for page in result.pages:
        for i, table in enumerate(page.tables, 1):
            table_count += 1
            csv_path = os.path.join(output_dir, f"table_page{page.page_number}_{i}_{timestamp}.csv")

            with open(csv_path, "w", encoding="utf-8") as f:
                for row in table.rows:
                    # Escape commas in cells
                    escaped_row = [f'"{cell}"' if ',' in str(cell) else str(cell) for cell in row]
                    f.write(",".join(escaped_row) + "\n")

    if table_count > 0:
        print(f"✓ 표 CSV 저장: {table_count}개 파일")

    # 5. Copy images to output directory
    image_count = 0
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    for page in result.pages:
        for img in page.images:
            if os.path.exists(img.image_path):
                import shutil
                dest_path = os.path.join(images_dir, os.path.basename(img.image_path))
                shutil.copy2(img.image_path, dest_path)
                image_count += 1

    if image_count > 0:
        print(f"✓ 이미지 저장: {image_count}개 파일")

    print(f"\n모든 결과가 '{output_dir}' 디렉토리에 저장되었습니다.")
    return output_dir


def main():
    """Test PDF extraction functionality."""
    # Setup logging to file as well
    setup_logging()

    # Initialize extractor
    print("\n" + "=" * 80)
    print("PDF Extractor Test")
    print("=" * 80 + "\n")

    extractor = PDFExtractor(
        output_dir="./test_output",
        extract_images=True,
        extract_tables=True,
    )

    # Test PDF path
    pdf_path = "./test_pdf.pdf"

    if not os.path.exists(pdf_path):
        print(f"Error: Test PDF not found at {pdf_path}")
        print("Please place a PDF file named 'test_pdf.pdf' in the project root.")
        return

    try:
        # Test 1: Extract metadata only
        print("\n--- Test 1: Extract Metadata ---")
        metadata = extractor.get_metadata(pdf_path)
        print(f"Title: {metadata.title}")
        print(f"Author: {metadata.author}")
        print(f"Total Pages: {metadata.total_pages}")
        print(f"Creation Date: {metadata.creation_date}")

        # Test 2: Extract plain text only
        print("\n--- Test 2: Extract Plain Text ---")
        plain_text = extractor.extract_text_only(pdf_path)
        print(f"Text length: {len(plain_text)} characters")
        print(f"First 200 characters:\n{plain_text[:200]}...")

        # Test 3: Full extraction
        print("\n--- Test 3: Full Extraction ---")
        result = extractor.extract(pdf_path)

        print(f"\nExtraction Summary:")
        print(f"  Total Pages: {len(result.pages)}")

        for page in result.pages:
            print(f"  Page {page.page_number}:")
            print(f"    - Text blocks: {len(page.text)}")
            print(f"    - Images: {len(page.images)}")
            print(f"    - Tables: {len(page.tables)}")

            # Show first text block if available
            if page.text:
                first_text = page.text[0]
                print(f"    - First text: {first_text.text[:100]}...")

            # Show table info if available
            if page.tables:
                first_table = page.tables[0]
                print(f"    - First table: {len(first_table.rows)} rows")

        # Test 4: Extract specific page
        print("\n--- Test 4: Extract Specific Page (Page 1) ---")
        page_1 = extractor.extract_page(pdf_path, 1)
        print(f"Page 1 content:")
        print(f"  - Text blocks: {len(page_1.text)}")
        print(f"  - Images: {len(page_1.images)}")
        print(f"  - Tables: {len(page_1.tables)}")

        print("\n" + "=" * 80)
        print("All tests completed successfully!")
        print("=" * 80 + "\n")

        # Save results to files
        print("\n" + "=" * 80)
        print("Saving results to files...")
        print("=" * 80 + "\n")
        output_dir = save_results_to_files(result, metadata, plain_text)

        print(f"\n✅ 테스트 완료! 결과는 '{output_dir}' 디렉토리에서 확인하세요.")

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\nCleaning up temporary files...")
        extractor.cleanup()
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
