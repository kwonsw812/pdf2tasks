"""FileSplitter - Split tasks into separate Markdown files."""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.types.models import (
    TaskWithMarkdown,
    SplitResult,
    FileInfo,
    FailedFile,
    FileMetadata,
)
from src.splitter.filename_generator import FilenameGenerator
from src.splitter.exceptions import (
    FileSplitterError,
    FileWriteError,
    DirectoryCreationError,
    InvalidTaskDataError,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FileSplitter:
    """
    Splits tasks into separate Markdown files.

    This class handles:
    - Output directory management
    - File naming and deduplication
    - Markdown file writing with optional front matter
    - Error handling and recovery
    - Summary report generation
    """

    def __init__(
        self,
        output_dir: str,
        clean: bool = False,
        overwrite: bool = True,
        add_front_matter: bool = True,
        max_filename_length: int = 50,
    ):
        """
        Initialize FileSplitter.

        Args:
            output_dir: Output directory path for markdown files
            clean: If True, delete all files in output_dir before starting
            overwrite: If True, overwrite existing files (default)
            add_front_matter: If True, add YAML front matter to files
            max_filename_length: Maximum length for filename (task name portion)

        Raises:
            DirectoryCreationError: If output directory cannot be created
        """
        self.output_dir = Path(output_dir)
        self.clean = clean
        self.overwrite = overwrite
        self.add_front_matter = add_front_matter
        self.filename_generator = FilenameGenerator(max_length=max_filename_length)

        # Ensure output directory exists
        self._ensure_output_directory()

    def split(self, tasks: List[TaskWithMarkdown]) -> SplitResult:
        """
        Split tasks into separate Markdown files.

        Args:
            tasks: List of tasks with markdown content

        Returns:
            SplitResult containing saved files, failed files, and statistics

        Examples:
            >>> splitter = FileSplitter(output_dir="./out")
            >>> tasks = [...]  # List of TaskWithMarkdown
            >>> result = splitter.split(tasks)
            >>> print(f"Saved {result.success_count} files")
        """
        start_time = time.time()
        saved_files: List[FileInfo] = []
        failed_files: List[FailedFile] = []

        logger.info(f"Starting file split for {len(tasks)} tasks")

        for task_with_md in tasks:
            try:
                # Validate task data
                self._validate_task(task_with_md)

                # Generate filename
                filename = self.filename_generator.generate(
                    index=task_with_md.task.index, task_name=task_with_md.task.name
                )

                # Prepare content (with or without front matter)
                content = self._prepare_content(task_with_md)

                # Write file
                file_path = self.output_dir / filename
                self._write_file(file_path, content)

                # Get file size
                file_size = os.path.getsize(file_path)

                # Record success
                file_info = FileInfo(
                    file_path=str(file_path.absolute()),
                    file_name=filename,
                    size_bytes=file_size,
                    task_index=task_with_md.task.index,
                    task_name=task_with_md.task.name,
                )
                saved_files.append(file_info)

                logger.info(
                    f"Saved task {task_with_md.task.index}: {filename} ({file_size} bytes)"
                )

            except Exception as e:
                # Record failure but continue processing
                error_msg = str(e)
                failed_file = FailedFile(
                    task_name=task_with_md.task.name,
                    task_index=task_with_md.task.index,
                    error=error_msg,
                )
                failed_files.append(failed_file)

                logger.error(
                    f"Failed to save task {task_with_md.task.index} "
                    f"({task_with_md.task.name}): {error_msg}"
                )

        # Calculate statistics
        processing_time = time.time() - start_time

        result = SplitResult(
            saved_files=saved_files,
            failed_files=failed_files,
            total_files=len(tasks),
            success_count=len(saved_files),
            failure_count=len(failed_files),
            processing_time=processing_time,
            output_directory=str(self.output_dir.absolute()),
        )

        logger.info(
            f"File split completed: {result.success_count} succeeded, "
            f"{result.failure_count} failed in {processing_time:.2f}s"
        )

        return result

    def generate_report(self, result: SplitResult) -> str:
        """
        Generate a text report from split result.

        Args:
            result: SplitResult from split operation

        Returns:
            Formatted report string
        """
        lines = ["[FileSplitter Report]", "=" * 60, ""]

        # Summary
        lines.append(f"총 생성 파일: {result.success_count}개")
        lines.append(f"총 처리 시간: {result.processing_time:.2f}초")
        lines.append(f"출력 디렉토리: {result.output_directory}")
        lines.append("")

        # Saved files
        if result.saved_files:
            lines.append("생성된 파일:")
            lines.append("-" * 60)
            for i, file_info in enumerate(result.saved_files, 1):
                size_kb = file_info.size_bytes / 1024
                lines.append(
                    f"{i}. {file_info.file_name} ({size_kb:.1f} KB) "
                    f"- Task {file_info.task_index}: {file_info.task_name}"
                )
            lines.append("")

        # Failed files
        if result.failed_files:
            lines.append(f"에러 발생: {result.failure_count}개")
            lines.append("-" * 60)
            for i, failed in enumerate(result.failed_files, 1):
                lines.append(
                    f"{i}. Task {failed.task_index} ({failed.task_name}): "
                    f"{failed.error}"
                )
            lines.append("")
        else:
            lines.append("에러: 없음")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def save_report(self, result: SplitResult, filename: str = "report.log") -> str:
        """
        Save report to a log file.

        Args:
            result: SplitResult from split operation
            filename: Report filename (default: report.log)

        Returns:
            Path to saved report file

        Raises:
            FileWriteError: If report cannot be written
        """
        report = self.generate_report(result)
        report_path = self.output_dir / filename

        try:
            self._write_file(report_path, report)
            logger.info(f"Report saved to {report_path}")
            return str(report_path.absolute())
        except Exception as e:
            raise FileWriteError(f"Failed to save report: {e}")

    def _ensure_output_directory(self) -> None:
        """
        Ensure output directory exists.

        Raises:
            DirectoryCreationError: If directory cannot be created
        """
        try:
            # Clean directory if requested
            if self.clean and self.output_dir.exists():
                logger.info(f"Cleaning output directory: {self.output_dir}")
                shutil.rmtree(self.output_dir)

            # Create directory (recursively)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory ready: {self.output_dir}")

        except PermissionError as e:
            raise DirectoryCreationError(
                f"Permission denied creating directory {self.output_dir}: {e}"
            )
        except Exception as e:
            raise DirectoryCreationError(
                f"Failed to create output directory {self.output_dir}: {e}"
            )

    def _validate_task(self, task: TaskWithMarkdown) -> None:
        """
        Validate task data.

        Args:
            task: TaskWithMarkdown to validate

        Raises:
            InvalidTaskDataError: If task data is invalid
        """
        if not task.task:
            raise InvalidTaskDataError("Task is missing")

        if not task.task.name or not task.task.name.strip():
            raise InvalidTaskDataError("Task name is empty")

        if task.task.index < 1:
            raise InvalidTaskDataError(f"Invalid task index: {task.task.index}")

        if not task.markdown or not task.markdown.strip():
            raise InvalidTaskDataError("Markdown content is empty")

    def _prepare_content(self, task: TaskWithMarkdown) -> str:
        """
        Prepare markdown content with optional front matter.

        Args:
            task: TaskWithMarkdown

        Returns:
            Complete markdown content
        """
        if not self.add_front_matter:
            return task.markdown

        # Use provided metadata or create default
        if task.metadata:
            metadata = task.metadata
        else:
            metadata = FileMetadata(
                title=task.task.name,
                index=task.task.index,
                generated=datetime.now(),
                source_pdf=None,
            )

        # Generate YAML front matter
        front_matter = self._generate_front_matter(metadata)

        # Combine front matter and markdown
        return f"{front_matter}\n\n{task.markdown}"

    def _generate_front_matter(self, metadata: FileMetadata) -> str:
        """
        Generate YAML front matter from metadata.

        Args:
            metadata: FileMetadata

        Returns:
            YAML front matter string
        """
        lines = ["---"]
        lines.append(f"title: {metadata.title}")
        lines.append(f"index: {metadata.index}")
        lines.append(f"generated: {metadata.generated.isoformat()}")

        if metadata.source_pdf:
            lines.append(f"source_pdf: {metadata.source_pdf}")

        lines.append("---")

        return "\n".join(lines)

    def _write_file(self, file_path: Path, content: str) -> None:
        """
        Write content to file.

        Args:
            file_path: Path to file
            content: Content to write

        Raises:
            FileWriteError: If file cannot be written
        """
        try:
            # Check if file exists and overwrite is disabled
            if file_path.exists() and not self.overwrite:
                raise FileWriteError(
                    f"File {file_path} already exists and overwrite is disabled"
                )

            # Write file with UTF-8 encoding
            file_path.write_text(content, encoding="utf-8")

        except PermissionError as e:
            raise FileWriteError(f"Permission denied writing to {file_path}: {e}")
        except OSError as e:
            # Handle disk space, I/O errors, etc.
            raise FileWriteError(f"OS error writing to {file_path}: {e}")
        except Exception as e:
            raise FileWriteError(f"Unexpected error writing to {file_path}: {e}")
