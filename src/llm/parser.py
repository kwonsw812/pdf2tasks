"""Markdown parsing utilities for TaskWriter."""

import re
from typing import List, Optional, Dict
from src.types.models import SubTask
from src.llm.exceptions import MarkdownParseError
from src.utils.logger import get_logger


logger = get_logger(__name__)


def parse_sub_tasks(markdown: str, task_index: int) -> List[SubTask]:
    """
    Parse sub-tasks from LLM-generated Markdown.

    Args:
        markdown: Markdown text from LLM
        task_index: Index of parent task

    Returns:
        List of parsed SubTask objects

    Raises:
        MarkdownParseError: If parsing fails
    """
    try:
        sub_tasks = []

        # Pattern to match sub-task headers: ## 1.1 Task Name
        header_pattern = r"##\s+(\d+\.\d+)\s+(.+?)(?:\n|$)"
        headers = re.finditer(header_pattern, markdown)

        # Split markdown into sections by sub-task headers
        sections = []
        last_end = 0

        for match in re.finditer(header_pattern, markdown):
            if sections:
                # Store previous section content
                sections[-1]["content"] = markdown[last_end : match.start()].strip()
            sections.append(
                {
                    "index": match.group(1),
                    "title": match.group(2).strip(),
                    "start": match.end(),
                }
            )
            last_end = match.end()

        # Add content for last section
        if sections:
            sections[-1]["content"] = markdown[last_end:].strip()

        logger.info(f"Found {len(sections)} sub-task sections")

        # Parse each section
        for section in sections:
            try:
                sub_task = _parse_sub_task_section(
                    section["index"], section["title"], section["content"]
                )

                # Validate index format
                expected_prefix = f"{task_index}."
                if not sub_task.index.startswith(expected_prefix):
                    logger.warning(
                        f"Sub-task index {sub_task.index} does not match expected prefix {expected_prefix}"
                    )

                sub_tasks.append(sub_task)
            except Exception as e:
                logger.warning(
                    f"Failed to parse sub-task {section['index']}: {str(e)}"
                )
                # Continue parsing other sub-tasks
                continue

        if not sub_tasks:
            raise MarkdownParseError("No valid sub-tasks found in markdown")

        return sub_tasks

    except Exception as e:
        raise MarkdownParseError(f"Failed to parse sub-tasks: {str(e)}") from e


def _parse_sub_task_section(index: str, title: str, content: str) -> SubTask:
    """
    Parse a single sub-task section.

    Args:
        index: Sub-task index (e.g., "1.1")
        title: Sub-task title
        content: Section content

    Returns:
        Parsed SubTask object
    """
    fields = _extract_fields(content)

    return SubTask(
        index=index,
        title=title,
        purpose=fields.get("목적", fields.get("purpose", "")),
        endpoint=fields.get("엔드포인트", fields.get("endpoint")),
        data_model=fields.get("데이터 모델", fields.get("data_model")),
        logic=fields.get("로직 요약", fields.get("로직", fields.get("logic", ""))),
        security=fields.get("권한/보안", fields.get("보안", fields.get("security"))),
        exceptions=fields.get("예외", fields.get("예외 처리", fields.get("exceptions"))),
        test_points=fields.get(
            "테스트 포인트", fields.get("테스트", fields.get("test_points"))
        ),
    )


def _extract_fields(content: str) -> Dict[str, Optional[str]]:
    """
    Extract field values from sub-task content.

    Args:
        content: Sub-task section content

    Returns:
        Dictionary of field names to values
    """
    fields = {}

    # Pattern to match field entries: - **Field Name:** Value
    # Support both single-line and multi-line values
    lines = content.split("\n")
    current_field = None
    current_value = []

    for line in lines:
        # Check if line starts a new field
        field_match = re.match(r"-?\s*\*\*(.+?)[:：]\*\*\s*(.*)", line)
        if field_match:
            # Save previous field
            if current_field:
                fields[current_field] = "\n".join(current_value).strip() or None
            # Start new field
            current_field = field_match.group(1).strip()
            field_value = field_match.group(2).strip()
            current_value = [field_value] if field_value else []
        elif current_field and line.strip():
            # Continue current field value (multi-line)
            current_value.append(line.strip())

    # Save last field
    if current_field:
        fields[current_field] = "\n".join(current_value).strip() or None

    return fields


def extract_code_blocks(text: str) -> List[str]:
    """
    Extract code blocks from markdown text.

    Args:
        text: Markdown text

    Returns:
        List of code block contents
    """
    code_pattern = r"```(?:\w+)?\n(.*?)```"
    matches = re.findall(code_pattern, text, re.DOTALL)
    return [match.strip() for match in matches]


def clean_markdown_formatting(text: str) -> str:
    """
    Remove markdown formatting characters.

    Args:
        text: Markdown text

    Returns:
        Plain text
    """
    # Remove bold/italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # Remove inline code
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text.strip()


def validate_markdown_structure(markdown: str, task_index: int) -> bool:
    """
    Validate that markdown has expected structure.

    Args:
        markdown: Markdown text
        task_index: Expected parent task index

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check for at least one sub-task header
        header_pattern = r"##\s+\d+\.\d+\s+.+"
        if not re.search(header_pattern, markdown):
            logger.warning("No sub-task headers found in markdown")
            return False

        # Check that sub-task indices match parent task
        index_pattern = rf"##\s+({task_index}\.\d+)"
        matches = re.findall(index_pattern, markdown)
        if not matches:
            logger.warning(
                f"No sub-task indices matching task {task_index} found"
            )
            return False

        return True

    except Exception as e:
        logger.error(f"Markdown validation error: {str(e)}")
        return False
