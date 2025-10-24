"""Formatters for report output."""

from typing import List
from ..types.models import (
    ReportResult,
    ExtractionMetrics,
    OCRMetrics,
    PreprocessingMetrics,
    LLMMetrics,
    ErrorEntry,
    FileInfo,
)


def format_time(seconds: float) -> str:
    """
    Format time in seconds to human-readable string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string (e.g., "1분 23초", "2시간 15분")

    Examples:
        >>> format_time(45.5)
        '45.50초'
        >>> format_time(125.0)
        '2분 5초'
        >>> format_time(7325.0)
        '2시간 2분'
    """
    if seconds < 60:
        return f"{seconds:.2f}초"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}분 {secs:.0f}초"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}시간 {minutes}분"


def format_size(bytes_size: int) -> str:
    """
    Format file size to human-readable string.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string (e.g., "12.5 KB", "1.2 MB")

    Examples:
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1536)
        '1.5 KB'
        >>> format_size(1048576)
        '1.0 MB'
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.1f} MB"


def format_summary_section(report: ReportResult) -> List[str]:
    """Format summary section of report."""
    lines = []
    lines.append("=" * 80)
    lines.append("PDF2Tasks 처리 리포트")
    lines.append("=" * 80)
    lines.append("")

    lines.append(f"입력 파일: {report.summary.pdf_file}")
    lines.append(f"처리 페이지: {report.summary.total_pages} 페이지")
    lines.append(f"생성 파일: {report.summary.generated_files}개")
    lines.append(f"총 처리 시간: {format_time(report.summary.total_processing_time)}")
    lines.append(f"생성 시각: {report.summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    return lines


def format_extraction_section(extraction: ExtractionMetrics) -> List[str]:
    """Format extraction metrics section."""
    lines = []
    lines.append("--- 추출 ---")
    lines.append(f"텍스트 페이지: {extraction.text_pages}개")
    lines.append(f"이미지 추출: {extraction.images_extracted}개")
    lines.append(f"표 인식: {extraction.tables_found}개")
    lines.append(f"처리 시간: {format_time(extraction.processing_time)}")
    lines.append("")
    return lines


def format_ocr_section(ocr: OCRMetrics) -> List[str]:
    """Format OCR metrics section."""
    lines = []
    lines.append("--- OCR ---")
    lines.append(f"처리 이미지: {ocr.images_processed}개")
    lines.append(f"평균 신뢰도: {ocr.average_confidence:.1f}%")
    lines.append(f"처리 시간: {format_time(ocr.total_ocr_time)}")
    lines.append("")
    return lines


def format_preprocessing_section(preprocessing: PreprocessingMetrics) -> List[str]:
    """Format preprocessing metrics section."""
    lines = []
    lines.append("--- 전처리 ---")
    lines.append(f"섹션 인식: {preprocessing.sections_identified}개")
    lines.append(f"기능 그룹: {preprocessing.functional_groups}개")
    lines.append(f"처리 시간: {format_time(preprocessing.processing_time)}")
    lines.append("")
    return lines


def format_llm_section(llm: LLMMetrics) -> List[str]:
    """Format LLM metrics section."""
    lines = []
    lines.append("--- LLM 사용 ---")
    lines.append(f"Planner 호출: {llm.planner_calls}회")
    lines.append(f"TaskWriter 호출: {llm.task_writer_calls}회")
    lines.append(f"총 토큰: {llm.total_tokens_used:,}개")
    lines.append(f"총 비용: ${llm.total_cost:.6f}")
    lines.append(f"처리 시간: {format_time(llm.processing_time)}")
    lines.append("")
    return lines


def format_output_files_section(files: List[FileInfo]) -> List[str]:
    """Format output files section."""
    lines = []
    lines.append("--- 생성 파일 ---")
    for idx, file_info in enumerate(files, 1):
        lines.append(
            f"{idx}. {file_info.file_name} ({format_size(file_info.size_bytes)}) "
            f"- Task {file_info.task_index}: {file_info.task_name}"
        )
    lines.append("")
    return lines


def format_errors_section(errors: List[ErrorEntry]) -> List[str]:
    """Format errors section."""
    lines = []
    if errors:
        lines.append(f"--- 에러 ({len(errors)}개) ---")
        for error in errors:
            severity_symbol = {
                "warning": "[WARNING]",
                "error": "[ERROR]",
                "critical": "[CRITICAL]",
            }.get(error.severity.lower(), "[?]")
            timestamp = error.timestamp.strftime("%H:%M:%S")
            lines.append(f"{severity_symbol} [{timestamp}] {error.stage}: {error.message}")
        lines.append("")
    else:
        lines.append("에러: 없음")
        lines.append("")
    return lines


def format_text_report(report: ReportResult) -> str:
    """
    Format complete report as text.

    Args:
        report: ReportResult object

    Returns:
        Formatted text report
    """
    lines = []

    # Summary
    lines.extend(format_summary_section(report))

    # Extraction
    if report.extraction:
        lines.extend(format_extraction_section(report.extraction))

    # OCR
    if report.ocr:
        lines.extend(format_ocr_section(report.ocr))

    # Preprocessing
    if report.preprocessing:
        lines.extend(format_preprocessing_section(report.preprocessing))

    # LLM
    if report.llm:
        lines.extend(format_llm_section(report.llm))

    # Output files
    if report.output_files:
        lines.extend(format_output_files_section(report.output_files))

    # Errors
    lines.extend(format_errors_section(report.errors))

    lines.append("=" * 80)

    return "\n".join(lines)
