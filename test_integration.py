#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration test for PDF Agent."""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.types.models import (
    IdentifiedTask,
    Section,
    FunctionalGroup,
    PageRange,
    TaskWithMarkdown,
    FileMetadata,
    ExtractionMetrics,
    PreprocessingMetrics,
    LLMMetrics,
)
from src.reporter.reporter import Reporter
from src.splitter.file_splitter import FileSplitter


def create_mock_tasks():
    """Create mock tasks for testing."""
    return [
        IdentifiedTask(
            index=1,
            name="Authentication System",
            description="User authentication and authorization",
            module="AuthModule",
            entities=["User", "Session", "Token"],
            prerequisites=["Database Setup"],
            related_sections=[0],
        ),
        IdentifiedTask(
            index=2,
            name="Payment System",
            description="Payment processing and order management",
            module="PaymentModule",
            entities=["Payment", "Order"],
            prerequisites=["Authentication System"],
            related_sections=[1],
        ),
    ]


def test_mock_mode():
    """Test the pipeline in mock mode."""
    print("=" * 80)
    print("Integration Test - Mock Mode")
    print("=" * 80)
    print()

    # Create mock tasks
    print("Step 1: Creating mock tasks...")
    mock_tasks = create_mock_tasks()
    print(f"Created {len(mock_tasks)} mock tasks")
    print()

    # Create mock markdown
    print("Step 2: Creating mock markdown documents...")
    tasks_with_markdown = []

    for task in mock_tasks:
        markdown = f"""# {task.name} - Task {task.index}

## Overview
- **Description:** {task.description}
- **Module:** {task.module}
- **Entities:** {', '.join(task.entities)}

## Sub-tasks

### {task.index}.1 Module Setup
- **Purpose:** Setup NestJS module structure
- **Logic:** Create module, controller, service
"""

        metadata = FileMetadata(
            title=task.name,
            index=task.index,
            generated=datetime.now(),
            source_pdf="mock_test.pdf",
        )

        task_with_md = TaskWithMarkdown(
            task=task,
            markdown=markdown,
            metadata=metadata,
        )
        tasks_with_markdown.append(task_with_md)

    print(f"Created markdown for {len(tasks_with_markdown)} tasks")
    print()

    # Split files
    print("Step 3: Splitting into individual files...")
    output_dir = "./test_output_integration"

    splitter = FileSplitter(
        output_dir=output_dir,
        clean=True,
        overwrite=True,
        add_front_matter=True,
    )

    split_result = splitter.split(tasks_with_markdown)
    print(f"Generated {split_result.success_count} files")
    print()

    # Generate report
    print("Step 4: Generating report...")
    reporter = Reporter()

    extraction_metrics = ExtractionMetrics(
        text_pages=10,
        images_extracted=5,
        tables_found=3,
        processing_time=2.5,
    )

    preprocessing_metrics = PreprocessingMetrics(
        sections_identified=3,
        functional_groups=2,
        processing_time=1.2,
    )

    llm_metrics = LLMMetrics(
        planner_calls=1,
        task_writer_calls=2,
        total_tokens_used=5000,
        total_cost=0.15,
        processing_time=8.3,
    )

    report = reporter.generate_report(
        pdf_file="mock_test.pdf",
        total_pages=10,
        output_files=split_result.saved_files,
        extraction_metrics=extraction_metrics,
        preprocessing_metrics=preprocessing_metrics,
        llm_metrics=llm_metrics,
        errors=[],
        total_processing_time=12.0,
    )

    print("Report generated")
    print()

    # Save reports
    print("Step 5: Saving reports...")
    reporter.save_text_report(report, f"{output_dir}/report.log")
    reporter.save_json_report(report, f"{output_dir}/report.json")
    print(f"Reports saved to {output_dir}")
    print()

    # Print summary
    print("=" * 80)
    print("Integration Test Summary")
    print("=" * 80)
    reporter.print_to_console(report)

    print("\nIntegration test completed successfully!")
    print(f"\nGenerated files in: {output_dir}/")


if __name__ == "__main__":
    test_mock_mode()
