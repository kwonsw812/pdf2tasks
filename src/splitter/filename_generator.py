"""Filename generation utilities for FileSplitter."""

import re
from typing import Set
from pathlib import Path


class FilenameGenerator:
    """Generates safe and consistent filenames for markdown files."""

    def __init__(self, max_length: int = 50):
        """
        Initialize the filename generator.

        Args:
            max_length: Maximum length for the task name portion of the filename
        """
        self.max_length = max_length
        self._used_names: Set[str] = set()

    def generate(self, index: int, task_name: str) -> str:
        """
        Generate a safe filename from task index and name.

        Args:
            index: Task index (e.g., 1, 2, 3)
            task_name: Task name (e.g., "인증 및 회원관리")

        Returns:
            Safe filename string (e.g., "1_인증_및_회원관리.md")

        Examples:
            >>> gen = FilenameGenerator()
            >>> gen.generate(1, "인증 및 회원관리")
            '1_인증_및_회원관리.md'
            >>> gen.generate(2, "결제/주문 시스템")
            '2_결제_주문_시스템.md'
        """
        # Sanitize the task name
        safe_name = self._sanitize_name(task_name)

        # Truncate if too long
        if len(safe_name) > self.max_length:
            safe_name = safe_name[: self.max_length]

        # Create the base filename
        base_filename = f"{index}_{safe_name}.md"

        # Handle duplicates
        filename = self._ensure_unique(base_filename, index)

        # Track this filename
        self._used_names.add(filename)

        return filename

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize task name for use in filenames.

        Args:
            name: Original task name

        Returns:
            Sanitized name safe for filesystems

        Rules:
            - Replace spaces with underscores
            - Remove or replace special characters: / \ ? % * : | " < >
            - Remove leading/trailing whitespace and underscores
            - Collapse multiple underscores to single underscore
        """
        # Remove leading/trailing whitespace
        name = name.strip()

        # Replace spaces with underscores
        name = name.replace(" ", "_")

        # Remove or replace filesystem-unsafe characters
        # Replace common separators with underscore
        name = name.replace("/", "_")
        name = name.replace("\\", "_")
        name = name.replace("|", "_")

        # Remove other problematic characters
        name = re.sub(r'[?%*:"<>]', "", name)

        # Collapse multiple underscores to single
        name = re.sub(r"_+", "_", name)

        # Remove leading/trailing underscores
        name = name.strip("_")

        # If name is empty after sanitization, use a default
        if not name:
            name = "task"

        return name

    def _ensure_unique(self, filename: str, index: int) -> str:
        """
        Ensure filename is unique by adding a suffix if needed.

        Args:
            filename: Base filename
            index: Task index

        Returns:
            Unique filename

        If the filename already exists, append a number suffix before .md:
            1_인증.md -> 1_인증_2.md -> 1_인증_3.md, etc.
        """
        if filename not in self._used_names:
            return filename

        # Extract name without extension
        stem = Path(filename).stem
        suffix = 2

        while True:
            new_filename = f"{stem}_{suffix}.md"
            if new_filename not in self._used_names:
                return new_filename
            suffix += 1

    def reset(self) -> None:
        """Reset the used names tracker."""
        self._used_names.clear()

    @property
    def used_names(self) -> Set[str]:
        """Get the set of used filenames."""
        return self._used_names.copy()
