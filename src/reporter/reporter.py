# -*- coding: utf-8 -*-
"""Reporter for generating processing reports."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from ..types.models import (
    ReportResult,
    ReportSummary,
    ExtractionMetrics,
    OCRMetrics,
    PreprocessingMetrics,
    LLMMetrics,
    FileInfo,
    ErrorEntry,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Reporter:
    """Reporter for generating comprehensive processing reports."""

    def __init__(self):
        """Initialize Reporter."""
        logger.info("Reporter initialized")

    def generate_report(
        self,
        pdf_file: str,
        total_pages: int,
        output_files: list[FileInfo],
        extraction_metrics: Optional[ExtractionMetrics] = None,
        ocr_metrics: Optional[OCRMetrics] = None,
        preprocessing_metrics: Optional[PreprocessingMetrics] = None,
        llm_metrics: Optional[LLMMetrics] = None,
        errors: Optional[list[ErrorEntry]] = None,
        total_processing_time: Optional[float] = None,
    ) -> ReportResult:
        """Generate a comprehensive processing report."""
        logger.info("Generating report")

        if total_processing_time is None:
            total_processing_time = 0.0
            if extraction_metrics:
                total_processing_time += extraction_metrics.processing_time
            if ocr_metrics:
                total_processing_time += ocr_metrics.total_ocr_time
            if preprocessing_metrics:
                total_processing_time += preprocessing_metrics.processing_time
            if llm_metrics:
                total_processing_time += llm_metrics.processing_time

        summary = ReportSummary(
            pdf_file=pdf_file,
            total_pages=total_pages,
            generated_files=len(output_files),
            total_processing_time=total_processing_time,
            timestamp=datetime.now(),
        )

        report = ReportResult(
            summary=summary,
            extraction=extraction_metrics,
            ocr=ocr_metrics,
            preprocessing=preprocessing_metrics,
            llm=llm_metrics,
            output_files=output_files,
            errors=errors or [],
        )

        logger.info(f"Report generated: {len(output_files)} files, {len(errors or [])} errors")
        return report

    def format_text_report(self, report: ReportResult) -> str:
        """Format report as human-readable text."""
        lines = []
        lines.append("=" * 80)
        lines.append("PDF2Tasks Processing Report")
        lines.append("=" * 80)
        lines.append("")

        lines.append(f"Input File: {report.summary.pdf_file}")
        lines.append(f"Pages Processed: {report.summary.total_pages} pages")
        lines.append(f"Files Generated: {report.summary.generated_files}")
        lines.append(f"Total Time: {self._format_time(report.summary.total_processing_time)}")
        lines.append(f"Generated At: {report.summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        if report.extraction:
            lines.append("--- Extraction ---")
            lines.append(f"Text Pages: {report.extraction.text_pages}")
            lines.append(f"Images Extracted: {report.extraction.images_extracted}")
            lines.append(f"Tables Found: {report.extraction.tables_found}")
            lines.append(f"Processing Time: {self._format_time(report.extraction.processing_time)}")
            lines.append("")

        if report.ocr:
            lines.append("--- OCR ---")
            lines.append(f"Images Processed: {report.ocr.images_processed}")
            lines.append(f"Avg Confidence: {report.ocr.average_confidence:.1f}%")
            lines.append(f"Processing Time: {self._format_time(report.ocr.total_ocr_time)}")
            lines.append("")

        if report.preprocessing:
            lines.append("--- Preprocessing ---")
            lines.append(f"Sections Identified: {report.preprocessing.sections_identified}")
            lines.append(f"Functional Groups: {report.preprocessing.functional_groups}")
            lines.append(f"Processing Time: {self._format_time(report.preprocessing.processing_time)}")
            lines.append("")

        if report.llm:
            lines.append("--- LLM Usage ---")
            lines.append(f"Planner Calls: {report.llm.planner_calls}")
            lines.append(f"TaskWriter Calls: {report.llm.task_writer_calls}")
            lines.append(f"Total Tokens: {report.llm.total_tokens_used:,}")
            lines.append(f"Total Cost: ${report.llm.total_cost:.6f}")
            lines.append(f"Processing Time: {self._format_time(report.llm.processing_time)}")
            lines.append("")

        if report.output_files:
            lines.append("--- Generated Files ---")
            for idx, file_info in enumerate(report.output_files, 1):
                size_kb = file_info.size_bytes / 1024
                lines.append(
                    f"{idx}. {file_info.file_name} ({size_kb:.1f} KB) "
                    f"- Task {file_info.task_index}: {file_info.task_name}"
                )
            lines.append("")

        if report.errors:
            lines.append(f"--- Errors ({len(report.errors)}) ---")
            for error in report.errors:
                severity_symbol = {
                    "warning": "[WARNING]",
                    "error": "[ERROR]",
                    "critical": "[CRITICAL]",
                }.get(error.severity, "[?]")
                lines.append(f"{severity_symbol} {error.stage}: {error.message}")
            lines.append("")
        else:
            lines.append("Errors: None")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def save_text_report(self, report: ReportResult, output_path: str) -> None:
        """Save text report to file."""
        text_report = self.format_text_report(report)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text_report)

        logger.info(f"Text report saved to {output_path}")

    def save_json_report(self, report: ReportResult, output_path: str) -> None:
        """Save report as JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        report_dict = report.model_dump(mode="json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON report saved to {output_path}")

    def print_to_console(self, report: ReportResult) -> None:
        """Print report to console."""
        print(self.format_text_report(report))

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def calculate_llm_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-3-5-sonnet-20241022",
    ) -> float:
        """Calculate LLM API cost."""
        pricing = {
            "claude-3-5-sonnet-20241022": {
                "input": 3.0 / 1_000_000,
                "output": 15.0 / 1_000_000,
            },
            "claude-3-sonnet-20240229": {
                "input": 3.0 / 1_000_000,
                "output": 15.0 / 1_000_000,
            },
        }

        model_pricing = pricing.get(model, pricing["claude-3-5-sonnet-20241022"])
        input_cost = input_tokens * model_pricing["input"]
        output_cost = output_tokens * model_pricing["output"]

        return input_cost + output_cost
