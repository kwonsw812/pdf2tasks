"""Task matching against OpenAPI specifications."""

from typing import List
from ..types.models import (
    IdentifiedTask,
    OpenAPISpec,
    OpenAPIEndpoint,
    TaskMatchResult,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TaskMatcher:
    """
    Match identified tasks against OpenAPI endpoints.

    Uses tag-based and path-based matching to determine if a task
    is already implemented in the API.
    """

    def __init__(self, specs: List[OpenAPISpec]):
        """
        Initialize matcher with OpenAPI specs.

        Args:
            specs: List of parsed OpenAPI specifications
        """
        self.specs = specs
        self.all_endpoints = []

        # Collect all endpoints from all specs
        for spec in specs:
            self.all_endpoints.extend(spec.endpoints)

        logger.info(
            f"TaskMatcher initialized with {len(specs)} specs, "
            f"{len(self.all_endpoints)} total endpoints"
        )

    def match_task(self, task: IdentifiedTask) -> TaskMatchResult:
        """
        Match a task against OpenAPI endpoints.

        Args:
            task: Task to match

        Returns:
            TaskMatchResult with matched endpoints and confidence score
        """
        logger.debug(f"Matching task: {task.name}")

        # Find matching endpoints
        matched_endpoints = []
        confidence_scores = []

        for endpoint in self.all_endpoints:
            score = self._calculate_match_score(task, endpoint)
            if score > 0:
                matched_endpoints.append(endpoint)
                confidence_scores.append(score)

        # Calculate overall confidence
        if confidence_scores:
            confidence_score = max(confidence_scores)
        else:
            confidence_score = 0.0

        # Determine match status
        if confidence_score >= 0.8:
            match_status = "fully_implemented"
        elif confidence_score >= 0.4:
            match_status = "partially_implemented"
        else:
            match_status = "new"

        # Identify missing features (placeholder - could be enhanced)
        missing_features = self._identify_missing_features(task, matched_endpoints)

        result = TaskMatchResult(
            task=task,
            match_status=match_status,
            matched_endpoints=matched_endpoints,
            confidence_score=confidence_score,
            missing_features=missing_features,
        )

        logger.info(
            f"  Task '{task.name}': {match_status} "
            f"(confidence: {confidence_score:.2f}, "
            f"matched: {len(matched_endpoints)} endpoints)"
        )

        return result

    def _calculate_match_score(
        self, task: IdentifiedTask, endpoint: OpenAPIEndpoint
    ) -> float:
        """
        Calculate match score between a task and an endpoint.

        Args:
            task: Task to match
            endpoint: OpenAPI endpoint

        Returns:
            Match score (0.0 - 1.0)
        """
        score = 0.0

        # Normalize strings for comparison (lowercase)
        task_name_lower = task.name.lower()
        task_description_lower = task.description.lower()
        task_module_lower = task.module.lower()

        # Tag-based matching (highest weight)
        for tag in endpoint.tags:
            tag_lower = tag.lower()

            # Direct name match
            if task_name_lower in tag_lower or tag_lower in task_name_lower:
                score += 0.6
                break

            # Partial match
            task_words = task_name_lower.split()
            tag_words = tag_lower.split()
            common_words = set(task_words) & set(tag_words)
            if common_words and len(common_words) >= 1:
                score += 0.4
                break

        # Path-based matching (module name in path)
        path_lower = endpoint.path.lower()

        # Check if module name appears in path
        module_words = task_module_lower.replace("module", "").strip().split()
        for word in module_words:
            if len(word) > 3 and word in path_lower:  # Skip short words
                score += 0.3
                break

        # Summary/description matching (bonus)
        if endpoint.summary:
            summary_lower = endpoint.summary.lower()
            if (
                task_name_lower in summary_lower
                or any(word in summary_lower for word in task_name_lower.split())
            ):
                score += 0.1

        # Cap score at 1.0
        return min(score, 1.0)

    def _match_by_tags(
        self, task: IdentifiedTask, endpoints: List[OpenAPIEndpoint]
    ) -> List[OpenAPIEndpoint]:
        """
        Match task by tags.

        Args:
            task: Task to match
            endpoints: List of endpoints to search

        Returns:
            List of matching endpoints
        """
        matched = []
        task_name_lower = task.name.lower()

        for endpoint in endpoints:
            for tag in endpoint.tags:
                if task_name_lower in tag.lower() or tag.lower() in task_name_lower:
                    matched.append(endpoint)
                    break

        return matched

    def _match_by_module(
        self, task: IdentifiedTask, endpoints: List[OpenAPIEndpoint]
    ) -> List[OpenAPIEndpoint]:
        """
        Match task by module/path.

        Args:
            task: Task to match
            endpoints: List of endpoints to search

        Returns:
            List of matching endpoints
        """
        matched = []
        module_lower = task.module.lower().replace("module", "").strip()

        for endpoint in endpoints:
            path_lower = endpoint.path.lower()
            if module_lower in path_lower:
                matched.append(endpoint)

        return matched

    def _identify_missing_features(
        self, task: IdentifiedTask, matched_endpoints: List[OpenAPIEndpoint]
    ) -> List[str]:
        """
        Identify features mentioned in task but not found in endpoints.

        This is a simple implementation - could be enhanced with NLP.

        Args:
            task: Task being matched
            matched_endpoints: Endpoints that matched

        Returns:
            List of potentially missing features
        """
        if not matched_endpoints:
            return [f"All features in task '{task.name}' appear to be new"]

        # Simple keyword extraction from task description
        # In a more advanced implementation, this could use NLP to extract features
        missing = []

        # Check if task mentions specific entities that aren't in matched endpoints
        for entity in task.entities:
            entity_lower = entity.lower()
            found = False

            for endpoint in matched_endpoints:
                # Check path, summary, description
                search_text = f"{endpoint.path} {endpoint.summary or ''} {endpoint.description or ''}"
                if entity_lower in search_text.lower():
                    found = True
                    break

            if not found:
                missing.append(f"Entity '{entity}' not found in matched endpoints")

        return missing
