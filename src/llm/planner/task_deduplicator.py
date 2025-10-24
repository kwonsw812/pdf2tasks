"""Task deduplication and merging logic."""

from typing import List
from difflib import SequenceMatcher
from ...types.models import IdentifiedTask
from ...utils.logger import get_logger

logger = get_logger(__name__)


class TaskDeduplicator:
    """
    Deduplicates and merges similar tasks.
    """

    DEFAULT_SIMILARITY_THRESHOLD = 0.8  # 80% similarity
    DEFAULT_NAME_SIMILARITY_THRESHOLD = 0.7  # 70% for name similarity

    def __init__(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        name_similarity_threshold: float = DEFAULT_NAME_SIMILARITY_THRESHOLD,
    ):
        """
        Initialize TaskDeduplicator.

        Args:
            similarity_threshold: Threshold for considering tasks as duplicates (0-1)
            name_similarity_threshold: Threshold for name similarity (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.name_similarity_threshold = name_similarity_threshold
        logger.info(
            f"TaskDeduplicator initialized "
            f"(similarity={similarity_threshold}, name_similarity={name_similarity_threshold})"
        )

    def deduplicate(self, tasks: List[IdentifiedTask]) -> List[IdentifiedTask]:
        """
        Remove duplicate tasks and merge similar ones.

        Args:
            tasks: List of identified tasks

        Returns:
            Deduplicated list of tasks
        """
        if not tasks:
            return []

        logger.info(f"Deduplicating {len(tasks)} tasks")

        unique_tasks: List[IdentifiedTask] = []

        for task in tasks:
            # Find similar task in unique_tasks
            similar_task = self._find_similar_task(task, unique_tasks)

            if similar_task:
                # Merge with similar task
                logger.debug(
                    f"Merging task '{task.name}' with '{similar_task.name}'"
                )
                self._merge_tasks(similar_task, task)
            else:
                # Add as new unique task
                unique_tasks.append(task)

        logger.info(
            f"Deduplication complete. "
            f"Reduced from {len(tasks)} to {len(unique_tasks)} tasks"
        )

        # Re-index tasks
        for idx, task in enumerate(unique_tasks, start=1):
            task.index = idx

        return unique_tasks

    def _find_similar_task(
        self, task: IdentifiedTask, tasks: List[IdentifiedTask]
    ) -> IdentifiedTask | None:
        """
        Find a similar task in the list.

        Args:
            task: Task to compare
            tasks: List of tasks to search

        Returns:
            Similar task if found, None otherwise
        """
        for existing_task in tasks:
            similarity = self._calculate_similarity(task, existing_task)

            if similarity >= self.similarity_threshold:
                logger.debug(
                    f"Found similar task: '{task.name}' ~ '{existing_task.name}' "
                    f"(similarity: {similarity:.2f})"
                )
                return existing_task

        return None

    def _calculate_similarity(
        self, task1: IdentifiedTask, task2: IdentifiedTask
    ) -> float:
        """
        Calculate similarity between two tasks.

        Uses multiple factors:
        - Name similarity (weighted heavily)
        - Module similarity
        - Entity overlap

        Args:
            task1: First task
            task2: Second task

        Returns:
            Similarity score (0-1)
        """
        # Name similarity (weight: 0.6)
        name_sim = self._string_similarity(task1.name, task2.name)
        name_weight = 0.6

        # Module similarity (weight: 0.2)
        module_sim = self._string_similarity(task1.module, task2.module)
        module_weight = 0.2

        # Entity overlap (weight: 0.2)
        entity_sim = self._list_similarity(task1.entities, task2.entities)
        entity_weight = 0.2

        # Weighted average
        total_similarity = (
            name_sim * name_weight
            + module_sim * module_weight
            + entity_sim * entity_weight
        )

        return total_similarity

    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score (0-1)
        """
        if not s1 or not s2:
            return 0.0

        # Normalize strings
        s1_norm = s1.lower().strip()
        s2_norm = s2.lower().strip()

        # Use SequenceMatcher for string similarity
        return SequenceMatcher(None, s1_norm, s2_norm).ratio()

    def _list_similarity(self, list1: List[str], list2: List[str]) -> float:
        """
        Calculate similarity between two lists (Jaccard similarity).

        Args:
            list1: First list
            list2: Second list

        Returns:
            Similarity score (0-1)
        """
        if not list1 and not list2:
            return 1.0

        if not list1 or not list2:
            return 0.0

        # Normalize items
        set1 = {item.lower().strip() for item in list1}
        set2 = {item.lower().strip() for item in list2}

        # Jaccard similarity: intersection / union
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def _merge_tasks(self, target: IdentifiedTask, source: IdentifiedTask) -> None:
        """
        Merge source task into target task.

        Args:
            target: Target task (will be modified)
            source: Source task (data to merge from)
        """
        # Merge related_sections (remove duplicates)
        merged_sections = list(set(target.related_sections + source.related_sections))
        target.related_sections = sorted(merged_sections)

        # Merge entities (remove duplicates)
        merged_entities = list(set(target.entities + source.entities))
        target.entities = sorted(merged_entities)

        # Merge prerequisites (remove duplicates)
        merged_prerequisites = list(set(target.prerequisites + source.prerequisites))
        target.prerequisites = sorted(merged_prerequisites)

        # Keep longer description
        if len(source.description) > len(target.description):
            target.description = source.description

        logger.debug(
            f"Merged task now has {len(target.related_sections)} sections, "
            f"{len(target.entities)} entities, {len(target.prerequisites)} prerequisites"
        )

    def remove_empty_tasks(self, tasks: List[IdentifiedTask]) -> List[IdentifiedTask]:
        """
        Remove tasks with insufficient information.

        Args:
            tasks: List of tasks

        Returns:
            Filtered list of tasks
        """
        logger.info(f"Filtering {len(tasks)} tasks for empty/invalid entries")

        filtered = []
        for task in tasks:
            # Check if task has minimum required information
            if not task.name or not task.module:
                logger.warning(
                    f"Removing task with missing name or module: {task}"
                )
                continue

            if not task.description:
                logger.warning(f"Task '{task.name}' has no description")

            filtered.append(task)

        logger.info(f"Filtered to {len(filtered)} valid tasks")
        return filtered
