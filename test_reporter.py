#!/usr/bin/env python3
"""Test script for Reporter module."""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.reporter import Reporter, calculate_cost
from src.types.models import (
    ExtractionMetrics,
    OCRMetrics,
    PreprocessingMetrics,
    LLMMetrics,
    FileInfo,
    ErrorEntry,
)


def test_cost_calculator():
    """Test 1: Cost calculation function."""
    print("\n" + "=" * 80)
    print("Test 1: Cost Calculator")
    print("=" * 80)

    # Test case 1: Small usage
    input_tokens = 1000
    output_tokens = 500
    cost = calculate_cost(input_tokens, output_tokens)
    print(f"\nInput: {input_tokens:,} tokens, Output: {output_tokens:,} tokens")
    print(f"Cost: ${cost:.6f}")
    assert cost > 0, "Cost should be positive"
    print("✓ Small usage test passed")

    # Test case 2: Large usage
    input_tokens = 100_000
    output_tokens = 50_000
    cost = calculate_cost(input_tokens, output_tokens)
    print(f"\nInput: {input_tokens:,} tokens, Output: {output_tokens:,} tokens")
    print(f"Cost: ${cost:.6f}")
    assert cost > 0, "Cost should be positive"
    print("✓ Large usage test passed")

    print("\n✓ All cost calculator tests passed!")


def test_basic_report_generation():
    """Test 2: Basic report generation."""
    print("\n" + "=" * 80)
    print("Test 2: Basic Report Generation")
    print("=" * 80)

    reporter = Reporter()

    # Create test data
    extraction_metrics = ExtractionMetrics(
        text_pages=50,
        images_extracted=10,
        tables_found=5,
        processing_time=45.5,
    )

    llm_metrics = LLMMetrics(
        planner_calls=1,
        task_writer_calls=3,
        total_tokens_used=15000,
        total_cost=0.225,
        processing_time=30.0,
    )

    output_files = [
        FileInfo(
            file_path="./out/1_auth.md",
            file_name="1_auth.md",
            size_bytes=12800,
            task_index=1,
            task_name="인증 시스템",
        ),
        FileInfo(
            file_path="./out/2_payment.md",
            file_name="2_payment.md",
            size_bytes=8500,
            task_index=2,
            task_name="결제 시스템",
        ),
    ]

    # Generate report
    report = reporter.generate_report(
        pdf_file="./test.pdf",
        total_pages=50,
        output_files=output_files,
        extraction_metrics=extraction_metrics,
        llm_metrics=llm_metrics,
    )

    # Verify report
    assert report.summary.total_pages == 50, "Total pages mismatch"
    assert report.summary.generated_files == 2, "Generated files count mismatch"
    assert report.extraction is not None, "Extraction metrics missing"
    assert report.llm is not None, "LLM metrics missing"
    assert len(report.output_files) == 2, "Output files count mismatch"

    print("\n✓ Report generation successful!")
    print(f"  - Total pages: {report.summary.total_pages}")
    print(f"  - Generated files: {report.summary.generated_files}")
    print(f"  - Processing time: {report.summary.total_processing_time:.2f}s")


def test_report_with_errors():
    """Test 3: Report generation with errors."""
    print("\n" + "=" * 80)
    print("Test 3: Report with Errors")
    print("=" * 80)

    reporter = Reporter()

    errors = [
        ErrorEntry(
            stage="OCR",
            message="이미지 처리 실패: page-10.png",
            severity="error",
            timestamp=datetime.now(),
        ),
        ErrorEntry(
            stage="Preprocessor",
            message="섹션 제목 누락 (p.23)",
            severity="warning",
            timestamp=datetime.now(),
        ),
    ]

    output_files = [
        FileInfo(
            file_path="./out/1_test.md",
            file_name="1_test.md",
            size_bytes=5000,
            task_index=1,
            task_name="테스트",
        ),
    ]

    report = reporter.generate_report(
        pdf_file="./test.pdf",
        total_pages=30,
        output_files=output_files,
        errors=errors,
    )

    assert len(report.errors) == 2, "Error count mismatch"
    assert report.errors[0].severity == "error", "Error severity mismatch"
    assert report.errors[1].severity == "warning", "Warning severity mismatch"

    print(f"\n✓ Error reporting test passed!")
    print(f"  - Total errors: {len(report.errors)}")
    print(f"  - Errors: {sum(1 for e in report.errors if e.severity == 'error')}")
    print(f"  - Warnings: {sum(1 for e in report.errors if e.severity == 'warning')}")


def test_text_formatting():
    """Test 4: Text report formatting."""
    print("\n" + "=" * 80)
    print("Test 4: Text Report Formatting")
    print("=" * 80)

    reporter = Reporter()

    ocr_metrics = OCRMetrics(
        images_processed=12,
        average_confidence=87.3,
        total_ocr_time=45.0,
    )

    preprocessing_metrics = PreprocessingMetrics(
        sections_identified=15,
        functional_groups=5,
        processing_time=10.5,
    )

    output_files = [
        FileInfo(
            file_path="./out/1_auth.md",
            file_name="1_auth.md",
            size_bytes=12800,
            task_index=1,
            task_name="인증",
        ),
    ]

    report = reporter.generate_report(
        pdf_file="./specs/app.pdf",
        total_pages=25,
        output_files=output_files,
        ocr_metrics=ocr_metrics,
        preprocessing_metrics=preprocessing_metrics,
    )

    text_report = reporter.format_text_report(report)

    assert "PDF2Tasks" in text_report or "Processing Report" in text_report, "Report title missing"
    assert "OCR" in text_report, "OCR section missing"
    assert "Preprocessing" in text_report, "Preprocessing section missing"
    assert "87.3%" in text_report, "OCR confidence missing"

    print("\n✓ Text formatting test passed!")
    print(f"  - Report length: {len(text_report)} characters")
    print("\nSample output:")
    print("-" * 80)
    print(text_report[:500] + "...")


def test_file_operations():
    """Test 5: File save operations."""
    print("\n" + "=" * 80)
    print("Test 5: File Save Operations")
    print("=" * 80)

    reporter = Reporter()

    output_files = [
        FileInfo(
            file_path="./out/1_test.md",
            file_name="1_test.md",
            size_bytes=5000,
            task_index=1,
            task_name="테스트",
        ),
    ]

    report = reporter.generate_report(
        pdf_file="./test.pdf",
        total_pages=10,
        output_files=output_files,
    )

    # Test directory
    output_dir = Path("./test_output_reporter")
    output_dir.mkdir(exist_ok=True)

    try:
        # Save JSON report
        json_path = output_dir / "report.json"
        reporter.save_json_report(report, str(json_path))
        assert json_path.exists(), "JSON file not created"
        print(f"\n✓ JSON report saved: {json_path}")

        # Save text report
        text_path = output_dir / "report.log"
        reporter.save_text_report(report, str(text_path))
        assert text_path.exists(), "Text file not created"
        print(f"✓ Text report saved: {text_path}")

        # Verify files exist
        assert (output_dir / "report.json").exists(), "JSON file missing"
        assert (output_dir / "report.log").exists(), "Text file missing"
        print(f"✓ Both reports verified")

        print("\n✓ All file operations passed!")

    finally:
        # Cleanup
        import shutil

        if output_dir.exists():
            shutil.rmtree(output_dir)
            print("\n✓ Cleanup completed")


def test_complete_workflow():
    """Test 6: Complete workflow with all metrics."""
    print("\n" + "=" * 80)
    print("Test 6: Complete Workflow")
    print("=" * 80)

    reporter = Reporter()

    # All metrics
    extraction_metrics = ExtractionMetrics(
        text_pages=50,
        images_extracted=15,
        tables_found=8,
        processing_time=60.0,
    )

    ocr_metrics = OCRMetrics(
        images_processed=15,
        average_confidence=89.5,
        total_ocr_time=120.0,
    )

    preprocessing_metrics = PreprocessingMetrics(
        sections_identified=25,
        functional_groups=8,
        processing_time=15.0,
    )

    llm_metrics = LLMMetrics(
        planner_calls=1,
        task_writer_calls=5,
        total_tokens_used=45000,
        total_cost=0.675,
        processing_time=90.0,
    )

    output_files = [
        FileInfo(
            file_path=f"./out/{i}_task.md",
            file_name=f"{i}_task.md",
            size_bytes=10000 + i * 1000,
            task_index=i,
            task_name=f"Task {i}",
        )
        for i in range(1, 6)
    ]

    errors = [
        ErrorEntry(
            stage="OCR",
            message="낮은 신뢰도: page-20.png",
            severity="warning",
            timestamp=datetime.now(),
        ),
    ]

    # Generate report
    report = reporter.generate_report(
        pdf_file="./specs/complete_spec.pdf",
        total_pages=50,
        output_files=output_files,
        extraction_metrics=extraction_metrics,
        ocr_metrics=ocr_metrics,
        preprocessing_metrics=preprocessing_metrics,
        llm_metrics=llm_metrics,
        errors=errors,
    )

    # Verify all sections
    assert report.extraction is not None
    assert report.ocr is not None
    assert report.preprocessing is not None
    assert report.llm is not None
    assert len(report.output_files) == 5
    assert len(report.errors) == 1

    print("\n✓ Complete workflow test passed!")
    print(f"  - Extraction: {report.extraction.text_pages} pages")
    print(f"  - OCR: {report.ocr.images_processed} images, {report.ocr.average_confidence:.1f}% confidence")
    print(f"  - Preprocessing: {report.preprocessing.sections_identified} sections")
    print(f"  - LLM: {report.llm.total_tokens_used:,} tokens, ${report.llm.total_cost:.4f}")
    print(f"  - Output: {len(report.output_files)} files")
    print(f"  - Errors: {len(report.errors)}")
    print(f"  - Total time: {report.summary.total_processing_time:.2f}s")

    # Print console output
    print("\n" + "=" * 80)
    print("Sample Console Output:")
    print("=" * 80)
    reporter.print_to_console(report)


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("REPORTER MODULE TEST SUITE")
    print("=" * 80)

    try:
        test_cost_calculator()
        test_basic_report_generation()
        test_report_with_errors()
        test_text_formatting()
        test_file_operations()
        test_complete_workflow()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
