"""Usage examples for preprocessor module."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.extractors.pdf_extractor import PDFExtractor
from src.preprocessor.preprocessor import Preprocessor
from src.preprocessor.text_normalizer import TextNormalizer
from src.preprocessor.header_footer_remover import HeaderFooterRemover
from src.preprocessor.section_segmenter import SectionSegmenter
from src.preprocessor.functional_grouper import FunctionalGrouper
from src.utils.logger import setup_logging

# Setup logging
setup_logging()


def example_1_basic_preprocessing():
    """Example 1: Basic preprocessing with default settings."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Preprocessing")
    print("=" * 60)

    pdf_path = "sample.pdf"  # Replace with your PDF path

    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return

    # Extract PDF
    extractor = PDFExtractor()
    pdf_result = extractor.extract(pdf_path)

    # Preprocess with default settings
    preprocessor = Preprocessor()
    result = preprocessor.process(pdf_result)

    # Display results
    print(f"\nDocument: {result.metadata.title or 'Untitled'}")
    print(f"Functional groups: {len(result.functional_groups)}")

    for group in result.functional_groups:
        print(f"\n{group.name}: {len(group.sections)} sections")


def example_2_text_normalization_only():
    """Example 2: Text normalization without other preprocessing."""
    print("\n" + "=" * 60)
    print("Example 2: Text Normalization Only")
    print("=" * 60)

    # Create text normalizer
    normalizer = TextNormalizer()

    # Sample texts with various issues
    texts = [
        "여러    공백이     있는      텍스트",
        "줄바꿈이\n\n\n\n많은\n\n\n텍스트",
        "  앞뒤 공백  ",
        "ＡＢＣ１２３",  # Full-width
    ]

    for text in texts:
        normalized = normalizer.normalize(text)
        print(f"\nOriginal: {repr(text)}")
        print(f"Normalized: {repr(normalized)}")


def example_3_custom_preprocessing():
    """Example 3: Custom preprocessing with selective features."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Preprocessing")
    print("=" * 60)

    pdf_path = "sample.pdf"

    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return

    # Extract PDF
    extractor = PDFExtractor()
    pdf_result = extractor.extract(pdf_path)

    # Custom preprocessing: normalize and segment, but don't group
    preprocessor = Preprocessor(
        normalize_text=True,
        remove_headers_footers=True,
        segment_sections=True,
        group_by_function=False,  # Disable grouping
    )

    result = preprocessor.process(pdf_result)

    print(f"\nSections found: {sum(len(g.sections) for g in result.functional_groups)}")


def example_4_custom_keywords():
    """Example 4: Functional grouping with custom keywords."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Keywords for Grouping")
    print("=" * 60)

    pdf_path = "sample.pdf"

    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return

    # Define custom keywords for domain-specific grouping
    custom_keywords = {
        "배송": ["배송", "택배", "운송", "물류"],
        "재고": ["재고", "입고", "출고", "수량"],
        "마케팅": ["프로모션", "광고", "이벤트", "캠페인"],
    }

    # Extract PDF
    extractor = PDFExtractor()
    pdf_result = extractor.extract(pdf_path)

    # Preprocess with custom keywords
    preprocessor = Preprocessor(custom_keywords=custom_keywords)
    result = preprocessor.process(pdf_result)

    # Display groups
    for group in result.functional_groups:
        print(f"\n{group.name}:")
        print(f"  Keywords: {', '.join(group.keywords)}")
        print(f"  Sections: {len(group.sections)}")


def example_5_header_footer_removal():
    """Example 5: Header and footer detection."""
    print("\n" + "=" * 60)
    print("Example 5: Header/Footer Detection")
    print("=" * 60)

    pdf_path = "sample.pdf"

    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return

    # Extract PDF
    extractor = PDFExtractor()
    pdf_result = extractor.extract(pdf_path)

    # Create header/footer remover
    remover = HeaderFooterRemover(
        min_repetition=3,  # Pattern must repeat at least 3 times
        position_threshold=50.0,  # Top/bottom 50 points
    )

    # Remove headers/footers
    cleaned_result, headers, footers = remover.remove_headers_footers(pdf_result)

    print(f"\nDetected headers: {len(headers)}")
    for pattern in headers[:5]:  # Show first 5
        print(f"  - {pattern}")

    print(f"\nDetected footers: {len(footers)}")
    for pattern in footers[:5]:  # Show first 5
        print(f"  - {pattern}")


def example_6_section_analysis():
    """Example 6: Section segmentation and analysis."""
    print("\n" + "=" * 60)
    print("Example 6: Section Analysis")
    print("=" * 60)

    pdf_path = "sample.pdf"

    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return

    # Extract PDF
    extractor = PDFExtractor()
    pdf_result = extractor.extract(pdf_path)

    # Segment sections
    segmenter = SectionSegmenter(
        min_heading_font_size=12.0,  # Minimum font size for headings
        font_size_ratio_threshold=1.2,  # Font size ratio vs average
    )

    sections = segmenter.segment(pdf_result)

    # Analyze sections
    print(f"\nTotal sections: {len(sections)}")

    def print_section_tree(section, indent=0):
        """Recursively print section hierarchy."""
        prefix = "  " * indent
        print(f"{prefix}- {section.title} (Level {section.level})")
        print(f"{prefix}  Pages: {section.page_range.start}-{section.page_range.end}")
        print(f"{prefix}  Content length: {len(section.content)} chars")

        for subsection in section.subsections:
            print_section_tree(subsection, indent + 1)

    for section in sections:
        print_section_tree(section)


def example_7_export_to_markdown():
    """Example 7: Export preprocessed content to Markdown."""
    print("\n" + "=" * 60)
    print("Example 7: Export to Markdown")
    print("=" * 60)

    pdf_path = "sample.pdf"
    output_path = "output.md"

    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return

    # Extract and preprocess
    extractor = PDFExtractor()
    pdf_result = extractor.extract(pdf_path)

    preprocessor = Preprocessor()
    result = preprocessor.process(pdf_result)

    # Generate Markdown
    markdown_lines = []

    # Title
    markdown_lines.append(f"# {result.metadata.title or 'Document'}\n")

    # Metadata
    if result.metadata.author:
        markdown_lines.append(f"**Author:** {result.metadata.author}\n")
    markdown_lines.append(f"**Pages:** {result.metadata.total_pages}\n")
    markdown_lines.append("\n---\n")

    # Content by functional groups
    for group in result.functional_groups:
        markdown_lines.append(f"\n## {group.name}\n")

        if group.keywords:
            markdown_lines.append(f"*Keywords: {', '.join(group.keywords)}*\n\n")

        for section in group.sections:
            # Section title
            markdown_lines.append(f"\n### {section.title}\n")

            # Page reference
            markdown_lines.append(
                f"*참고: PDF p.{section.page_range.start}-{section.page_range.end}*\n\n"
            )

            # Content
            markdown_lines.append(f"{section.content}\n")

            # Subsections
            for subsection in section.subsections:
                markdown_lines.append(f"\n#### {subsection.title}\n")
                markdown_lines.append(f"{subsection.content}\n")

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(markdown_lines)

    print(f"\nMarkdown exported to: {output_path}")


def main():
    """Run all examples."""
    print("Preprocessor Usage Examples")
    print("=" * 60)

    # Note: Most examples require a PDF file
    print("\nNote: These examples require a PDF file named 'sample.pdf'")
    print("Replace 'sample.pdf' with your actual PDF file path.\n")

    # Uncomment the examples you want to run:

    # example_1_basic_preprocessing()
    example_2_text_normalization_only()  # This doesn't require a PDF
    # example_3_custom_preprocessing()
    # example_4_custom_keywords()
    # example_5_header_footer_removal()
    # example_6_section_analysis()
    # example_7_export_to_markdown()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
