"""Test script for preprocessor module."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.extractors.pdf_extractor import PDFExtractor
from src.preprocessor.preprocessor import Preprocessor
from src.preprocessor.text_normalizer import TextNormalizer
from src.preprocessor.section_segmenter import SectionSegmenter
from src.preprocessor.functional_grouper import FunctionalGrouper
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_text_normalizer():
    """Test text normalization functions."""
    print("\n" + "=" * 60)
    print("Test 1: Text Normalizer")
    print("=" * 60)

    normalizer = TextNormalizer()

    # Test cases
    test_texts = [
        "여러    공백이     있는      텍스트",  # Multiple spaces
        "줄바꿈이\n\n\n\n많은\n\n\n텍스트",  # Multiple newlines
        "  앞뒤 공백이 있는 텍스트  ",  # Leading/trailing whitespace
        "ＡＢＣ１２３",  # Full-width characters
        '이것은 "특수" 따옴표입니다',  # Special quotes
    ]

    for i, text in enumerate(test_texts, 1):
        normalized = normalizer.normalize(text)
        print(f"\nTest {i}:")
        print(f"  Original: {repr(text)}")
        print(f"  Normalized: {repr(normalized)}")

    print("\n✓ Text normalization tests completed")


def test_section_segmentation():
    """Test section segmentation with sample text."""
    print("\n" + "=" * 60)
    print("Test 2: Section Segmentation")
    print("=" * 60)

    # Create sample PDF result
    from src.types.models import (
        PDFExtractResult,
        PDFMetadata,
        PDFPage,
        ExtractedText,
        TextMetadata,
        Position,
    )

    # Sample structured text
    text_items = [
        # Level 1 heading
        ("1. 회원가입 기능", 18.0, 100.0, 1),
        ("회원가입은 이메일로 진행됩니다.", 12.0, 120.0, 1),
        # Level 2 heading
        ("1.1 이메일 인증", 14.0, 140.0, 1),
        ("이메일 인증은 6자리 코드로 진행됩니다.", 12.0, 160.0, 1),
        # Level 1 heading
        ("2. 로그인 기능", 18.0, 200.0, 1),
        ("로그인은 이메일과 비밀번호로 진행됩니다.", 12.0, 220.0, 1),
        # Level 2 heading
        ("2.1 비밀번호 찾기", 14.0, 240.0, 1),
        ("비밀번호는 이메일로 재설정할 수 있습니다.", 12.0, 260.0, 1),
    ]

    # Create extracted text objects
    extracted_texts = []
    for text, font_size, y_pos, page_num in text_items:
        extracted_texts.append(
            ExtractedText(
                page_number=page_num,
                text=text,
                metadata=TextMetadata(
                    font_size=font_size,
                    font_name="Arial",
                    position=Position(x=50.0, y=y_pos, width=500.0, height=20.0),
                ),
            )
        )

    # Create PDF result
    pdf_result = PDFExtractResult(
        metadata=PDFMetadata(
            title="Test Document",
            total_pages=1,
        ),
        pages=[
            PDFPage(
                page_number=1,
                text=extracted_texts,
            )
        ],
    )

    # Test segmentation
    segmenter = SectionSegmenter()
    sections = segmenter.segment(pdf_result)

    print(f"\nFound {len(sections)} top-level sections:")
    for section in sections:
        print(f"\n  Section: {section.title} (Level {section.level})")
        print(f"  Pages: {section.page_range.start}-{section.page_range.end}")
        print(f"  Content: {section.content[:50]}...")
        if section.subsections:
            print(f"  Subsections: {len(section.subsections)}")
            for subsection in section.subsections:
                print(f"    - {subsection.title} (Level {subsection.level})")

    print("\n✓ Section segmentation tests completed")


def test_functional_grouping():
    """Test functional grouping."""
    print("\n" + "=" * 60)
    print("Test 3: Functional Grouping")
    print("=" * 60)

    from src.types.models import Section, PageRange

    # Create sample sections
    sections = [
        Section(
            title="회원가입",
            level=1,
            content="사용자는 이메일로 회원가입할 수 있습니다. 인증 절차를 거쳐야 합니다.",
            page_range=PageRange(start=1, end=1),
        ),
        Section(
            title="로그인",
            level=1,
            content="사용자는 이메일과 비밀번호로 로그인합니다. 세션이 생성됩니다.",
            page_range=PageRange(start=2, end=2),
        ),
        Section(
            title="상품 등록",
            level=1,
            content="관리자는 상품을 등록할 수 있습니다. 제품 정보를 입력합니다.",
            page_range=PageRange(start=3, end=3),
        ),
        Section(
            title="결제 처리",
            level=1,
            content="사용자는 카드로 결제할 수 있습니다. 구매 내역이 저장됩니다.",
            page_range=PageRange(start=4, end=4),
        ),
    ]

    # Test grouping
    grouper = FunctionalGrouper()
    groups = grouper.group_sections(sections)

    print(f"\nFound {len(groups)} functional groups:")
    for group in groups:
        print(f"\n  Group: {group.name}")
        print(f"  Keywords: {', '.join(group.keywords)}")
        print(f"  Sections: {len(group.sections)}")
        for section in group.sections:
            print(f"    - {section.title}")

    print("\n✓ Functional grouping tests completed")


def test_full_preprocessing_pipeline(pdf_path: str):
    """Test full preprocessing pipeline with a real PDF."""
    print("\n" + "=" * 60)
    print("Test 4: Full Preprocessing Pipeline")
    print("=" * 60)

    # Check if PDF exists
    if not Path(pdf_path).exists():
        print(f"\n⚠ PDF file not found: {pdf_path}")
        print("Skipping full pipeline test.")
        return

    try:
        # Step 1: Extract PDF
        print("\nStep 1: Extracting PDF...")
        extractor = PDFExtractor(extract_images=False, extract_tables=True)
        pdf_result = extractor.extract(pdf_path)
        print(f"  Extracted {len(pdf_result.pages)} pages")

        # Step 2: Preprocess
        print("\nStep 2: Preprocessing...")
        preprocessor = Preprocessor(
            normalize_text=True,
            remove_headers_footers=True,
            segment_sections=True,
            group_by_function=True,
        )

        result = preprocessor.process(pdf_result)

        # Display results
        print("\n" + "=" * 60)
        print("Preprocessing Results")
        print("=" * 60)

        print(f"\nDocument: {result.metadata.title or 'Untitled'}")
        print(f"Total pages: {result.metadata.total_pages}")

        if result.removed_header_patterns:
            print(f"\nRemoved header patterns: {len(result.removed_header_patterns)}")
            for pattern in result.removed_header_patterns[:3]:
                print(f"  - {pattern}")

        if result.removed_footer_patterns:
            print(f"\nRemoved footer patterns: {len(result.removed_footer_patterns)}")
            for pattern in result.removed_footer_patterns[:3]:
                print(f"  - {pattern}")

        print(f"\nFunctional groups: {len(result.functional_groups)}")
        for group in result.functional_groups:
            print(f"\n  Group: {group.name}")
            print(f"  Sections: {len(group.sections)}")
            for section in group.sections[:3]:  # Show first 3 sections
                print(f"    - {section.title} (Pages {section.page_range.start}-{section.page_range.end})")
                print(f"      Content preview: {section.content[:80]}...")

        # Show statistics
        stats = preprocessor.get_statistics()
        print("\n" + "=" * 60)
        print("Performance Statistics")
        print("=" * 60)
        print(f"Normalization time: {stats['normalization_time']:.2f}s")
        print(f"Header/footer removal: {stats['header_footer_removal_time']:.2f}s")
        print(f"Section segmentation: {stats['segmentation_time']:.2f}s")
        print(f"Functional grouping: {stats['grouping_time']:.2f}s")
        print(f"Total time: {stats['total_time']:.2f}s")

        print("\n✓ Full preprocessing pipeline completed successfully")

    except Exception as e:
        print(f"\n✗ Error during preprocessing: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Preprocessor Module Tests")
    print("=" * 60)

    # Test 1: Text normalizer
    test_text_normalizer()

    # Test 2: Section segmentation
    test_section_segmentation()

    # Test 3: Functional grouping
    test_functional_grouping()

    # Test 4: Full pipeline (if PDF is provided)
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_full_preprocessing_pipeline(pdf_path)
    else:
        print("\n" + "=" * 60)
        print("Test 4: Full Preprocessing Pipeline")
        print("=" * 60)
        print("\n⚠ No PDF file provided. Skipping full pipeline test.")
        print("Usage: python test_preprocessor.py <path_to_pdf>")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
