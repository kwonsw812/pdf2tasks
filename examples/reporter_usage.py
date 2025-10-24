#!/usr/bin/env python3
"""
Reporter Usage Examples

This script demonstrates various ways to use the Reporter module
to generate processing reports for PDF Agent.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporter import Reporter, calculate_cost
from src.types.models import (
    ExtractionMetrics,
    OCRMetrics,
    PreprocessingMetrics,
    LLMMetrics,
    FileInfo,
    ErrorEntry,
)


def example1_basic_report():
    """
    Example 1: Basic Report Generation

    Generate a simple report with minimal metrics.
    """
    print("\n" + "=" * 80)
    print("Example 1: Basic Report Generation")
    print("=" * 80)

    reporter = Reporter()

    # Create minimal test data
    output_files = [
        FileInfo(
            file_path="./output/1_auth.md",
            file_name="1_auth.md",
            size_bytes=12800,
            task_index=1,
            task_name="인증 시스템",
        ),
        FileInfo(
            file_path="./output/2_payment.md",
            file_name="2_payment.md",
            size_bytes=8500,
            task_index=2,
            task_name="결제 시스템",
        ),
    ]

    # Generate report
    report = reporter.generate_report(
        pdf_file="./specs/app_v1.pdf",
        total_pages=30,
        output_files=output_files,
    )

    # Print to console
    reporter.print_to_console(report)

    print("\n✓ Basic report generated successfully!")


def example2_full_metrics_report():
    """
    Example 2: Report with All Metrics

    Generate a comprehensive report including all processing stages.
    """
    print("\n" + "=" * 80)
    print("Example 2: Full Metrics Report")
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
            file_path=f"./output/{i}_feature.md",
            file_name=f"{i}_feature.md",
            size_bytes=10000 + i * 1000,
            task_index=i,
            task_name=f"Feature {i}",
        )
        for i in range(1, 6)
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
    )

    # Print to console
    reporter.print_to_console(report)

    print(f"\n✓ Full report generated!")
    print(f"  Total processing time: {report.summary.total_processing_time:.2f}s")
    print(f"  Total cost: ${llm_metrics.total_cost:.4f}")


def example3_report_with_errors():
    """
    Example 3: Report with Errors

    Generate a report that includes error tracking.
    """
    print("\n" + "=" * 80)
    print("Example 3: Report with Errors")
    print("=" * 80)

    reporter = Reporter()

    # Create test errors
    errors = [
        ErrorEntry(
            stage="PDF Extraction",
            message="Unable to extract text from page 10 - encrypted content",
            severity="error",
            timestamp=datetime.now(),
        ),
        ErrorEntry(
            stage="OCR",
            message="Low confidence on page-15.png (45.2%)",
            severity="warning",
            timestamp=datetime.now(),
        ),
        ErrorEntry(
            stage="Preprocessor",
            message="Section title missing on page 23",
            severity="warning",
            timestamp=datetime.now(),
        ),
        ErrorEntry(
            stage="LLM Planner",
            message="API rate limit reached, retrying...",
            severity="critical",
            timestamp=datetime.now(),
        ),
    ]

    output_files = [
        FileInfo(
            file_path="./output/1_partial.md",
            file_name="1_partial.md",
            size_bytes=5000,
            task_index=1,
            task_name="Partially Processed Task",
        ),
    ]

    # Generate report
    report = reporter.generate_report(
        pdf_file="./specs/problematic.pdf",
        total_pages=40,
        output_files=output_files,
        errors=errors,
    )

    # Print to console
    reporter.print_to_console(report)

    print(f"\n✓ Report with errors generated!")
    print(f"  Total errors: {len(report.errors)}")
    print(f"  - Errors: {sum(1 for e in errors if e.severity == 'error')}")
    print(f"  - Warnings: {sum(1 for e in errors if e.severity == 'warning')}")
    print(f"  - Critical: {sum(1 for e in errors if e.severity == 'critical')}")


def example4_save_reports():
    """
    Example 4: Save Reports to Files

    Generate and save reports to both JSON and text formats.
    """
    print("\n" + "=" * 80)
    print("Example 4: Save Reports to Files")
    print("=" * 80)

    reporter = Reporter()

    # Create test data
    llm_metrics = LLMMetrics(
        planner_calls=1,
        task_writer_calls=3,
        total_tokens_used=25000,
        total_cost=0.375,
        processing_time=45.0,
    )

    output_files = [
        FileInfo(
            file_path="./output/1_task.md",
            file_name="1_task.md",
            size_bytes=8000,
            task_index=1,
            task_name="Task 1",
        ),
    ]

    # Generate report
    report = reporter.generate_report(
        pdf_file="./specs/test.pdf",
        total_pages=20,
        output_files=output_files,
        llm_metrics=llm_metrics,
    )

    # Create output directory
    output_dir = Path("./example_output")
    output_dir.mkdir(exist_ok=True)

    # Save JSON report
    json_path = output_dir / "report.json"
    reporter.save_json_report(report, str(json_path))
    print(f"\n✓ JSON report saved: {json_path}")

    # Save text report
    text_path = output_dir / "report.log"
    reporter.save_text_report(report, str(text_path))
    print(f"✓ Text report saved: {text_path}")

    # Verify files
    print(f"\nFile sizes:")
    print(f"  - JSON: {json_path.stat().st_size / 1024:.2f} KB")
    print(f"  - Text: {text_path.stat().st_size / 1024:.2f} KB")

    # Cleanup
    import shutil

    shutil.rmtree(output_dir)
    print(f"\n✓ Cleanup completed")


def example5_cost_calculation():
    """
    Example 5: LLM Cost Calculation

    Calculate LLM API costs for different usage scenarios.
    """
    print("\n" + "=" * 80)
    print("Example 5: LLM Cost Calculation")
    print("=" * 80)

    reporter = Reporter()

    # Scenario 1: Small task
    print("\nScenario 1: Small Task")
    input_tokens = 5000
    output_tokens = 2000
    cost = reporter.calculate_llm_cost(input_tokens, output_tokens)
    print(f"  Input: {input_tokens:,} tokens")
    print(f"  Output: {output_tokens:,} tokens")
    print(f"  Cost: ${cost:.6f}")

    # Scenario 2: Medium task
    print("\nScenario 2: Medium Task")
    input_tokens = 20000
    output_tokens = 10000
    cost = reporter.calculate_llm_cost(input_tokens, output_tokens)
    print(f"  Input: {input_tokens:,} tokens")
    print(f"  Output: {output_tokens:,} tokens")
    print(f"  Cost: ${cost:.6f}")

    # Scenario 3: Large task
    print("\nScenario 3: Large Task")
    input_tokens = 100000
    output_tokens = 50000
    cost = reporter.calculate_llm_cost(input_tokens, output_tokens)
    print(f"  Input: {input_tokens:,} tokens")
    print(f"  Output: {output_tokens:,} tokens")
    print(f"  Cost: ${cost:.6f}")

    # Using standalone function
    print("\nUsing standalone calculate_cost():")
    cost = calculate_cost(15000, 7500)
    print(f"  Cost: ${cost:.6f}")

    print("\n✓ Cost calculations completed!")


def example6_custom_processing_time():
    """
    Example 6: Custom Total Processing Time

    Override automatic processing time calculation.
    """
    print("\n" + "=" * 80)
    print("Example 6: Custom Total Processing Time")
    print("=" * 80)

    reporter = Reporter()

    extraction_metrics = ExtractionMetrics(
        text_pages=30,
        images_extracted=5,
        tables_found=3,
        processing_time=45.0,
    )

    output_files = [
        FileInfo(
            file_path="./output/1_task.md",
            file_name="1_task.md",
            size_bytes=10000,
            task_index=1,
            task_name="Task 1",
        ),
    ]

    # Auto-calculate processing time
    report1 = reporter.generate_report(
        pdf_file="./test.pdf",
        total_pages=30,
        output_files=output_files,
        extraction_metrics=extraction_metrics,
    )
    print(f"\nAuto-calculated time: {report1.summary.total_processing_time:.2f}s")

    # Custom processing time
    custom_time = 150.0
    report2 = reporter.generate_report(
        pdf_file="./test.pdf",
        total_pages=30,
        output_files=output_files,
        extraction_metrics=extraction_metrics,
        total_processing_time=custom_time,
    )
    print(f"Custom time: {report2.summary.total_processing_time:.2f}s")

    print("\n✓ Custom processing time example completed!")


def example7_programmatic_report_analysis():
    """
    Example 7: Programmatic Report Analysis

    Access report data programmatically for further analysis.
    """
    print("\n" + "=" * 80)
    print("Example 7: Programmatic Report Analysis")
    print("=" * 80)

    reporter = Reporter()

    # Generate report
    extraction_metrics = ExtractionMetrics(
        text_pages=50,
        images_extracted=20,
        tables_found=10,
        processing_time=80.0,
    )

    llm_metrics = LLMMetrics(
        planner_calls=2,
        task_writer_calls=8,
        total_tokens_used=60000,
        total_cost=0.90,
        processing_time=120.0,
    )

    output_files = [
        FileInfo(
            file_path=f"./output/{i}_task.md",
            file_name=f"{i}_task.md",
            size_bytes=5000 * i,
            task_index=i,
            task_name=f"Task {i}",
        )
        for i in range(1, 9)
    ]

    report = reporter.generate_report(
        pdf_file="./specs/large_spec.pdf",
        total_pages=50,
        output_files=output_files,
        extraction_metrics=extraction_metrics,
        llm_metrics=llm_metrics,
    )

    # Analyze report data
    print("\nReport Analysis:")
    print(f"  - PDF File: {report.summary.pdf_file}")
    print(f"  - Total Pages: {report.summary.total_pages}")
    print(f"  - Generated Files: {report.summary.generated_files}")
    print(f"  - Total Processing Time: {report.summary.total_processing_time:.2f}s")

    if report.extraction:
        print(f"\nExtraction Metrics:")
        print(f"  - Text Pages: {report.extraction.text_pages}")
        print(f"  - Images: {report.extraction.images_extracted}")
        print(f"  - Tables: {report.extraction.tables_found}")
        print(f"  - Efficiency: {report.extraction.text_pages / report.extraction.processing_time:.2f} pages/sec")

    if report.llm:
        print(f"\nLLM Metrics:")
        print(f"  - Total Calls: {report.llm.planner_calls + report.llm.task_writer_calls}")
        print(f"  - Total Tokens: {report.llm.total_tokens_used:,}")
        print(f"  - Total Cost: ${report.llm.total_cost:.4f}")
        print(f"  - Cost per 1K tokens: ${(report.llm.total_cost / report.llm.total_tokens_used * 1000):.6f}")

    # Calculate total file size
    total_size = sum(f.size_bytes for f in report.output_files)
    print(f"\nOutput Files:")
    print(f"  - Total Size: {total_size / 1024:.2f} KB")
    print(f"  - Average Size: {total_size / len(report.output_files) / 1024:.2f} KB")

    # Export to dict for further processing
    report_dict = report.model_dump()
    print(f"\nReport exported to dictionary with {len(report_dict)} top-level keys")

    print("\n✓ Programmatic analysis completed!")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("REPORTER USAGE EXAMPLES")
    print("=" * 80)

    try:
        example1_basic_report()
        example2_full_metrics_report()
        example3_report_with_errors()
        example4_save_reports()
        example5_cost_calculation()
        example6_custom_processing_time()
        example7_programmatic_report_analysis()

        print("\n" + "=" * 80)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ EXAMPLE FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
