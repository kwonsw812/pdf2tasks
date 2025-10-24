#!/usr/bin/env python3
"""
PDF2Tasks CLI - Main entry point.

Command-line interface for PDF processing pipeline.
"""

import sys
import os
from pathlib import Path
import click
from dotenv import load_dotenv
from .orchestrator import Orchestrator, OrchestratorConfig
from ..utils.logger import get_logger, setup_logging

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)


@click.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "--out",
    "-o",
    "output_dir",
    required=True,
    type=click.Path(),
    help="Output directory for generated files",
)
@click.option(
    "--clean",
    is_flag=True,
    help="Clean output directory before processing",
)
@click.option(
    "--extract-images/--no-extract-images",
    default=True,
    help="Extract images from PDF (default: enabled)",
)
@click.option(
    "--extract-tables/--no-extract-tables",
    default=True,
    help="Extract tables from PDF (default: enabled)",
)
@click.option(
    "--ocr",
    is_flag=True,
    help="Use OCR for image-based text extraction (not implemented yet)",
)
@click.option(
    "--analyze-images/--no-analyze-images",
    default=True,
    help="Analyze extracted images using Claude Vision API (default: enabled)",
)
@click.option(
    "--front-matter/--no-front-matter",
    default=True,
    help="Add YAML front matter to output files (default: enabled)",
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
)
@click.option(
    "--model",
    default="claude-3-5-sonnet-20241022",
    help="Claude model to use (default: claude-3-5-sonnet-20241022)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without actually processing",
)
@click.option(
    "--openapi-dir",
    default="./openapi",
    type=click.Path(),
    help="OpenAPI spec directory (default: ./openapi)",
)
@click.option(
    "--skip-implemented",
    is_flag=True,
    help="Skip tasks that are already implemented in OpenAPI",
)
@click.option(
    "--use-llm-preprocessing/--no-llm-preprocessing",
    default=True,
    help="Use LLM for preprocessing (section segmentation and functional grouping) - more accurate (default: enabled)",
)
@click.option(
    "--use-llm-context/--no-llm-context",
    default=True,
    help="Use LLM to extract task contexts (user roles and deployment environments) (default: enabled)",
)
@click.option(
    "--use-llm-matching/--no-llm-matching",
    default=True,
    help="Use LLM for context-aware OpenAPI matching (default: enabled)",
)
def analyze(
    pdf_path,
    output_dir,
    clean,
    extract_images,
    extract_tables,
    ocr,
    analyze_images,
    front_matter,
    api_key,
    model,
    verbose,
    dry_run,
    openapi_dir,
    skip_implemented,
    use_llm_preprocessing,
    use_llm_context,
    use_llm_matching,
):
    """
    Analyze PDF document and generate development tasks.

    PDF_PATH: Path to the PDF file to analyze

    Example:
        pdf2tasks analyze ./specs/app-v1.pdf --out ./out --clean
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    # Validate inputs
    if not os.path.exists(pdf_path):
        click.echo(f"Error: PDF file not found: {pdf_path}", err=True)
        sys.exit(2)

    if not api_key:
        click.echo(
            "Error: Anthropic API key not provided. "
            "Set ANTHROPIC_API_KEY environment variable or use --api-key option.",
            err=True,
        )
        sys.exit(4)

    # Create configuration
    config = OrchestratorConfig(
        pdf_path=pdf_path,
        output_dir=output_dir,
        extract_images=extract_images,
        extract_tables=extract_tables,
        use_ocr=ocr,
        analyze_images=analyze_images,
        clean_output=clean,
        add_front_matter=front_matter,
        api_key=api_key,
        model=model,
        verbose=verbose,
        openapi_dir=openapi_dir,
        skip_implemented=skip_implemented,
        use_llm_preprocessing=use_llm_preprocessing,
        use_llm_context_extraction=use_llm_context,
        use_llm_openapi_matching=use_llm_matching,
    )

    # Dry run
    if dry_run:
        click.echo("\n" + "=" * 60)
        click.echo("[DRY RUN MODE - 미리보기]")
        click.echo("=" * 60)
        click.echo(f"\n입력 PDF: {pdf_path}")
        click.echo(f"출력 디렉토리: {output_dir}")
        click.echo(f"Claude 모델: {model}")
        click.echo(f"이미지 추출: {'예' if extract_images else '아니오'}")
        click.echo(f"이미지 분석 (Vision API): {'예' if analyze_images else '아니오'}")
        click.echo(f"표 추출: {'예' if extract_tables else '아니오'}")
        click.echo(f"OCR 사용: {'예' if ocr else '아니오'}")
        click.echo(f"기존 파일 정리: {'예' if clean else '아니오'}")
        click.echo(f"Front Matter 추가: {'예' if front_matter else '아니오'}")
        click.echo(f"OpenAPI 디렉토리: {openapi_dir}")
        click.echo(f"구현된 태스크 스킵: {'예' if skip_implemented else '아니오'}")
        preprocessing_mode = "LLM 기반 (권장)" if use_llm_preprocessing else "규칙 기반"
        click.echo(f"전처리 모드: {preprocessing_mode}")
        click.echo(f"LLM 컨텍스트 추출: {'예' if use_llm_context else '아니오'}")
        click.echo(f"LLM 컨텍스트 기반 매칭: {'예' if use_llm_matching else '아니오'}")

        click.echo("\n처리 단계 미리보기:")
        click.echo("  [1/7] PDF 추출 (텍스트, 표, 이미지)")
        if ocr:
            click.echo("  [2/7] OCR 처리")
        if analyze_images:
            click.echo("  [2.5/7] 이미지 분석 (Vision API)")
        preprocessing_method = "LLM 기반" if use_llm_preprocessing else "규칙 기반"
        click.echo(f"  [3/7] 전처리 ({preprocessing_method}: 정규화, 섹션 구분)")
        click.echo("  [4/7] LLM Planner (상위 태스크 식별)")
        if os.path.exists(openapi_dir):
            click.echo("  [4.5/7] OpenAPI 스펙 비교")
        click.echo("  [5/7] LLM TaskWriter (하위 태스크 작성)")
        click.echo("  [6/7] 파일 분리")
        click.echo("  [7/7] 리포트 생성")

        click.echo("\n예상 출력:")
        click.echo(f"  - {output_dir}/1_태스크명.md")
        click.echo(f"  - {output_dir}/2_태스크명.md")
        click.echo("  - ...")
        click.echo(f"  - {output_dir}/report.json")
        click.echo(f"  - {output_dir}/report.log")

        click.echo("\n예상 비용:")
        if use_llm_preprocessing:
            base_cost = "  - 기본 처리: ~$0.02-$0.05 (LLM 전처리로 효율화)"
            if analyze_images:
                click.echo(base_cost)
                click.echo("  - 이미지 분석: +$0.01-$0.03 (이미지 개수에 따라)")
                click.echo("  - 총 예상 비용: ~$0.03-$0.08")
            else:
                click.echo(base_cost)
        else:
            base_cost = "  - 기본 처리: ~$0.03-$0.08"
            if analyze_images:
                click.echo(base_cost)
                click.echo("  - 이미지 분석: +$0.01-$0.03")
                click.echo("  - 총 예상 비용: ~$0.04-$0.11")
            else:
                click.echo(base_cost)

        click.echo("\n주의: Dry-run 모드에서는 실제로 파일이 생성되지 않습니다.")
        click.echo("실제 처리를 하려면 --dry-run 옵션을 제거하세요.")
        click.echo("=" * 60 + "\n")
        sys.exit(0)

    try:
        # Run orchestrator
        orchestrator = Orchestrator(config)
        report = orchestrator.run()

        # Success
        click.echo("\n Processing completed successfully!")
        click.echo(f"  Generated {len(report.output_files)} files in {output_dir}")

        if report.llm:
            click.echo(f"  Total cost: ${report.llm.total_cost:.6f}")

        sys.exit(0)

    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user.", err=True)
        sys.exit(130)

    except Exception as e:
        click.echo(f"\nError: {str(e)}", err=True)
        logger.error(f"Processing failed: {e}", exc_info=True)
        sys.exit(1)


@click.group()
@click.version_option(version="0.1.0", prog_name="pdf2tasks")
def cli():
    """
    PDF2Tasks - AI-powered PDF analysis and task generation.

    Convert PDF specifications into structured development tasks
    using Claude AI.
    """
    pass


cli.add_command(analyze)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
