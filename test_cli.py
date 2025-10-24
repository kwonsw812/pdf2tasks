"""Test script for CLI and Orchestrator module."""

import os
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from src.cli.main import cli, analyze
from src.cli.orchestrator import Orchestrator, OrchestratorConfig
from src.types.models import (
    PDFExtractResult,
    PDFMetadata,
    PDFPage,
    ReportResult,
    ReportSummary,
    ExtractionMetrics,
    PreprocessingMetrics,
    LLMMetrics,
)
from src.utils.logger import setup_logging


def test_cli_help():
    """Test 1: CLI help command."""
    print("\n" + "=" * 60)
    print("Test 1: CLI Help Command")
    print("=" * 60)

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    print(f"Exit code: {result.exit_code}")
    print(f"Output:\n{result.output}")

    assert result.exit_code == 0
    assert "PDF2Tasks" in result.output
    assert "analyze" in result.output

    print("✓ Help command working correctly\n")


def test_cli_version():
    """Test 2: CLI version display."""
    print("\n" + "=" * 60)
    print("Test 2: CLI Version Display")
    print("=" * 60)

    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])

    print(f"Exit code: {result.exit_code}")
    print(f"Output:\n{result.output}")

    assert result.exit_code == 0
    assert "0.1.0" in result.output

    print("✓ Version command working correctly\n")


def test_cli_required_arguments():
    """Test 3: Missing required arguments."""
    print("\n" + "=" * 60)
    print("Test 3: Missing Required Arguments")
    print("=" * 60)

    runner = CliRunner()

    # Missing PDF path
    result = runner.invoke(analyze, ["--out", "./out"])
    print(f"Missing PDF path - Exit code: {result.exit_code}")
    assert result.exit_code != 0

    # Missing output directory
    result = runner.invoke(analyze, ["test.pdf"])
    print(f"Missing output dir - Exit code: {result.exit_code}")
    assert result.exit_code != 0

    print("✓ Required argument validation working\n")


def test_pdf_file_not_found():
    """Test 4: Non-existent PDF file."""
    print("\n" + "=" * 60)
    print("Test 4: PDF File Not Found")
    print("=" * 60)

    runner = CliRunner()
    result = runner.invoke(
        analyze, ["nonexistent.pdf", "--out", "./out", "--api-key", "test-key"]
    )

    print(f"Exit code: {result.exit_code}")
    print(f"Output:\n{result.output}")

    # Click handles file not found with exit code 2
    assert result.exit_code == 2
    assert ("not exist" in result.output.lower() or "not found" in result.output.lower())

    print("✓ File not found error handled correctly\n")


def test_api_key_missing():
    """Test 5: Missing API key."""
    print("\n" + "=" * 60)
    print("Test 5: Missing API Key")
    print("=" * 60)

    runner = CliRunner()

    # Create temp PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4\n")
        tmp_path = tmp.name

    try:
        # Ensure no API key in environment
        with runner.isolated_filesystem():
            result = runner.invoke(
                analyze, [tmp_path, "--out", "./out"], env={"ANTHROPIC_API_KEY": ""}
            )

            print(f"Exit code: {result.exit_code}")
            print(f"Output:\n{result.output}")

            assert result.exit_code == 4
            assert "API key" in result.output

        print("✓ API key validation working\n")
    finally:
        os.unlink(tmp_path)


def test_orchestrator_initialization():
    """Test 6: Orchestrator initialization."""
    print("\n" + "=" * 60)
    print("Test 6: Orchestrator Initialization")
    print("=" * 60)

    config = OrchestratorConfig(
        pdf_path="test.pdf",
        output_dir="./out",
        extract_images=False,
        extract_tables=True,
        use_ocr=False,
        clean_output=False,
        add_front_matter=True,
        api_key="test-key",
        model="claude-3-5-sonnet-20241022",
        verbose=False,
    )

    orchestrator = Orchestrator(config)

    print(f"Config PDF path: {orchestrator.config.pdf_path}")
    print(f"Config output dir: {orchestrator.config.output_dir}")
    print(f"Config model: {orchestrator.config.model}")
    print(f"Config extract tables: {orchestrator.config.extract_tables}")

    assert orchestrator.config.pdf_path == "test.pdf"
    assert orchestrator.config.output_dir == "./out"
    assert orchestrator.config.model == "claude-3-5-sonnet-20241022"
    assert orchestrator.config.extract_tables is True

    print("✓ Orchestrator initialized correctly\n")


def test_orchestrator_pipeline_mock():
    """Test 7: Orchestrator pipeline with mocks."""
    print("\n" + "=" * 60)
    print("Test 7: Orchestrator Pipeline (Mock)")
    print("=" * 60)

    # Create temp directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create temp PDF
        pdf_path = Path(temp_dir) / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        config = OrchestratorConfig(
            pdf_path=str(pdf_path),
            output_dir=temp_dir,
            extract_images=False,
            extract_tables=False,
            use_ocr=False,
            clean_output=False,
            add_front_matter=True,
            api_key="test-api-key",
            model="claude-3-5-sonnet-20241022",
            verbose=False,
        )

        # Mock all components
        with patch("src.cli.orchestrator.PDFExtractor") as mock_extractor_class, patch(
            "src.cli.orchestrator.Preprocessor"
        ) as mock_preprocessor_class, patch(
            "src.cli.orchestrator.LLMPlanner"
        ) as mock_planner_class, patch(
            "src.cli.orchestrator.LLMTaskWriter"
        ) as mock_taskwriter_class, patch(
            "src.cli.orchestrator.FileSplitter"
        ) as mock_splitter_class, patch(
            "src.cli.orchestrator.Reporter"
        ) as mock_reporter_class:

            # Mock Extractor
            mock_extractor = Mock()
            mock_extractor.extract.return_value = PDFExtractResult(
                metadata=PDFMetadata(
                    title="Test PDF",
                    author=None,
                    subject=None,
                    creator=None,
                    producer=None,
                    creation_date=None,
                    modification_date=None,
                    total_pages=1,
                ),
                pages=[
                    PDFPage(page_number=1, text=[], images=[], tables=[])
                ],
            )
            mock_extractor_class.return_value = mock_extractor

            # Mock Preprocessor
            mock_preprocessor = Mock()
            from src.types.models import PreprocessResult, FunctionalGroup, Section

            mock_preprocessor.process.return_value = PreprocessResult(
                functional_groups=[
                    FunctionalGroup(name="인증", sections=[], keywords=["로그인"])
                ],
                metadata=PDFMetadata(
                    title="Test",
                    author=None,
                    subject=None,
                    creator=None,
                    producer=None,
                    creation_date=None,
                    modification_date=None,
                    total_pages=1,
                ),
                removed_header_patterns=[],
                removed_footer_patterns=[],
            )
            mock_preprocessor_class.return_value = mock_preprocessor

            # Mock Planner
            mock_planner = Mock()
            from src.types.models import LLMPlannerResult, IdentifiedTask, TokenUsage

            mock_planner.identify_tasks_from_functional_groups.return_value = (
                LLMPlannerResult(
                    tasks=[
                        IdentifiedTask(
                            index=1,
                            name="인증",
                            description="사용자 인증",
                            module="AuthModule",
                            entities=["User"],
                            prerequisites=[],
                            related_sections=[],
                        )
                    ],
                    token_usage=TokenUsage(
                        input_tokens=100, output_tokens=200, total_tokens=300
                    ),
                    estimated_cost_usd=0.001,
                    model="claude-3-5-sonnet-20241022",
                )
            )
            mock_planner_class.return_value = mock_planner

            # Mock TaskWriter
            mock_taskwriter = Mock()
            from src.types.models import TaskWriterResult, SubTask

            mock_taskwriter.write_task.return_value = TaskWriterResult(
                task=IdentifiedTask(
                    index=1,
                    name="인증",
                    description="사용자 인증",
                    module="AuthModule",
                    entities=["User"],
                    prerequisites=[],
                    related_sections=[],
                ),
                sub_tasks=[
                    SubTask(
                        index="1.1",
                        title="로그인",
                        purpose="사용자 인증",
                        endpoint=None,
                        data_model=None,
                        logic="JWT 생성",
                        security=None,
                        exceptions=None,
                        test_points=None,
                    )
                ],
                markdown="# 인증\n\n## 1.1 로그인\n",
                token_usage=TokenUsage(
                    input_tokens=50, output_tokens=100, total_tokens=150
                ),
            )
            mock_taskwriter_class.return_value = mock_taskwriter

            # Mock FileSplitter
            mock_splitter = Mock()
            from src.types.models import SplitResult, FileInfo

            mock_splitter.split.return_value = SplitResult(
                saved_files=[
                    FileInfo(
                        file_path=str(Path(temp_dir) / "1_인증.md"),
                        file_name="1_인증.md",
                        size_bytes=100,
                        task_index=1,
                        task_name="인증",
                    )
                ],
                failed_files=[],
                total_files=1,
                success_count=1,
                failure_count=0,
                processing_time=0.5,
                output_directory=temp_dir,
            )
            mock_splitter_class.return_value = mock_splitter

            # Mock Reporter
            mock_reporter = Mock()
            mock_reporter.generate_report.return_value = ReportResult(
                summary=ReportSummary(
                    pdf_file=str(pdf_path),
                    total_pages=1,
                    generated_files=1,
                    total_processing_time=5.0,
                    timestamp=datetime.now(),
                ),
                extraction=ExtractionMetrics(
                    text_pages=1,
                    images_extracted=0,
                    tables_found=0,
                    processing_time=1.0,
                ),
                preprocessing=PreprocessingMetrics(
                    sections_identified=1,
                    functional_groups=1,
                    processing_time=1.0,
                ),
                llm=LLMMetrics(
                    planner_calls=1,
                    task_writer_calls=1,
                    total_tokens_used=450,
                    total_cost=0.002,
                    processing_time=2.0,
                ),
                output_files=[
                    FileInfo(
                        file_path=str(Path(temp_dir) / "1_인증.md"),
                        file_name="1_인증.md",
                        size_bytes=100,
                        task_index=1,
                        task_name="인증",
                    )
                ],
                errors=[],
            )
            mock_reporter_class.return_value = mock_reporter

            # Run orchestrator
            print("Running orchestrator with mocked components...")
            orchestrator = Orchestrator(config)
            report = orchestrator.run()

            print(f"PDF file: {report.summary.pdf_file}")
            print(f"Total pages: {report.summary.total_pages}")
            print(f"Generated files: {report.summary.generated_files}")
            print(f"Total cost: ${report.llm.total_cost:.6f}")

            assert report.summary.generated_files == 1
            assert report.summary.total_pages == 1
            assert report.llm.total_cost > 0

            print("✓ Orchestrator pipeline executed successfully\n")


def test_error_handling():
    """Test 8: Error handling."""
    print("\n" + "=" * 60)
    print("Test 8: Error Handling")
    print("=" * 60)

    runner = CliRunner()

    # Test with invalid options
    result = runner.invoke(analyze, ["test.pdf", "--invalid-option"])
    print(f"Invalid option - Exit code: {result.exit_code}")
    assert result.exit_code != 0

    print("✓ Error handling working correctly\n")


def run_all_tests():
    """Run all test cases."""
    setup_logging("INFO")

    print("\n" + "=" * 80)
    print("CLI AND ORCHESTRATOR TEST SUITE")
    print("=" * 80)

    try:
        test_cli_help()
        test_cli_version()
        test_cli_required_arguments()
        test_pdf_file_not_found()
        test_api_key_missing()
        test_orchestrator_initialization()
        test_orchestrator_pipeline_mock()
        test_error_handling()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80 + "\n")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
