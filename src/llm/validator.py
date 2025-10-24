"""Sub-task validation utilities."""

from typing import List, Set
from src.types.models import SubTask, ValidationResult
from src.utils.logger import get_logger


logger = get_logger(__name__)


def validate_sub_tasks(sub_tasks: List[SubTask], task_index: int) -> ValidationResult:
    """
    Validate generated sub-tasks for completeness and quality.

    Args:
        sub_tasks: List of sub-tasks to validate
        task_index: Parent task index

    Returns:
        ValidationResult with errors and warnings
    """
    errors = []
    warnings = []

    if not sub_tasks:
        errors.append("No sub-tasks generated")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Track seen indices to detect duplicates
    seen_indices: Set[str] = set()

    for i, task in enumerate(sub_tasks):
        task_label = f"Sub-task {task.index}"

        # Check index format
        if not _validate_index_format(task.index, task_index):
            errors.append(
                f"{task_label}: Invalid index format (expected {task_index}.X)"
            )

        # Check for duplicates
        if task.index in seen_indices:
            errors.append(f"{task_label}: Duplicate index")
        seen_indices.add(task.index)

        # Check required fields
        if not task.title or len(task.title.strip()) < 3:
            errors.append(f"{task_label}: Missing or too short title")

        if not task.purpose or len(task.purpose.strip()) < 10:
            errors.append(f"{task_label}: Missing or too short purpose")

        if not task.logic or len(task.logic.strip()) < 20:
            errors.append(f"{task_label}: Missing or too short logic summary")

        # Check for vague descriptions
        if task.logic and _is_too_vague(task.logic):
            warnings.append(
                f"{task_label}: Logic description might be too abstract"
            )

        # Check optional but recommended fields
        if not task.endpoint:
            warnings.append(f"{task_label}: Missing endpoint information")

        if not task.data_model:
            warnings.append(f"{task_label}: Missing data model information")

        if not task.test_points:
            warnings.append(f"{task_label}: Missing test points")

    # Check sequential numbering
    indices = [t.index for t in sub_tasks]
    if not _is_sequential(indices, task_index):
        warnings.append("Sub-task indices are not sequential (e.g., 1.1, 1.2, 1.3)")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def _validate_index_format(index: str, task_index: int) -> bool:
    """
    Validate sub-task index format.

    Args:
        index: Sub-task index (e.g., "1.1")
        task_index: Parent task index

    Returns:
        True if valid, False otherwise
    """
    parts = index.split(".")
    if len(parts) != 2:
        return False

    try:
        parent_idx = int(parts[0])
        sub_idx = int(parts[1])
        return parent_idx == task_index and sub_idx > 0
    except ValueError:
        return False


def _is_too_vague(text: str) -> bool:
    """
    Check if text is too vague/abstract.

    Args:
        text: Text to check

    Returns:
        True if text appears too vague
    """
    vague_phrases = [
        "구현한다",
        "처리한다",
        "관리한다",
        "수행한다",
        "진행한다",
        "작업한다",
        "기능을 만든다",
        "기능 구현",
    ]

    text_lower = text.lower()
    vague_count = sum(1 for phrase in vague_phrases if phrase in text_lower)

    # If too many vague phrases and text is short, it's probably too abstract
    return vague_count >= 2 and len(text) < 100


def _is_sequential(indices: List[str], task_index: int) -> bool:
    """
    Check if sub-task indices are sequential.

    Args:
        indices: List of sub-task indices
        task_index: Parent task index

    Returns:
        True if sequential, False otherwise
    """
    try:
        sub_numbers = []
        for idx in indices:
            parts = idx.split(".")
            if len(parts) != 2 or int(parts[0]) != task_index:
                return False
            sub_numbers.append(int(parts[1]))

        # Check if sorted and no gaps
        sorted_numbers = sorted(sub_numbers)
        expected = list(range(1, len(sub_numbers) + 1))
        return sorted_numbers == expected

    except ValueError:
        return False


def check_completeness(sub_tasks: List[SubTask]) -> float:
    """
    Calculate completeness score for sub-tasks.

    Args:
        sub_tasks: List of sub-tasks

    Returns:
        Completeness score (0.0 to 1.0)
    """
    if not sub_tasks:
        return 0.0

    total_score = 0.0
    max_score = len(sub_tasks) * 8  # 8 fields per sub-task

    for task in sub_tasks:
        if task.title:
            total_score += 1
        if task.purpose:
            total_score += 1
        if task.endpoint:
            total_score += 1
        if task.data_model:
            total_score += 1
        if task.logic:
            total_score += 1
        if task.security:
            total_score += 1
        if task.exceptions:
            total_score += 1
        if task.test_points:
            total_score += 1

    return total_score / max_score if max_score > 0 else 0.0


def get_validation_summary(result: ValidationResult) -> str:
    """
    Get human-readable validation summary.

    Args:
        result: ValidationResult object

    Returns:
        Summary string
    """
    summary = []

    if result.is_valid:
        summary.append("✓ Validation passed")
    else:
        summary.append("✗ Validation failed")

    if result.errors:
        summary.append(f"\nErrors ({len(result.errors)}):")
        for error in result.errors:
            summary.append(f"  - {error}")

    if result.warnings:
        summary.append(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings:
            summary.append(f"  - {warning}")

    return "\n".join(summary)
