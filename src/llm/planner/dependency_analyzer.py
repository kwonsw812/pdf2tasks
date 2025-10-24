"""Dependency analysis for tasks."""

from typing import List, Dict, Set
from ...types.models import IdentifiedTask
from ...utils.logger import get_logger
from ..exceptions import DependencyAnalysisError

logger = get_logger(__name__)


class DependencyAnalyzer:
    """
    Analyzes dependencies between tasks.
    """

    # Common dependency keywords
    DEPENDENCY_KEYWORDS = {
        "auth": ["인증", "권한", "로그인", "회원"],
        "user": ["사용자", "유저", "회원"],
        "payment": ["결제", "구매"],
        "order": ["주문", "구매"],
        "product": ["상품", "제품"],
        "notification": ["알림", "푸시"],
    }

    # Common dependency patterns (which tasks typically depend on others)
    DEPENDENCY_PATTERNS = {
        "인증": [],  # Authentication is usually first
        "권한": ["인증"],  # Authorization depends on authentication
        "결제": ["인증", "사용자"],  # Payment depends on auth and user
        "주문": ["인증", "사용자", "상품"],  # Order depends on auth, user, product
        "알림": ["인증", "사용자"],  # Notification depends on auth and user
    }

    def __init__(self):
        """Initialize DependencyAnalyzer."""
        logger.info("DependencyAnalyzer initialized")

    def analyze(self, tasks: List[IdentifiedTask]) -> List[IdentifiedTask]:
        """
        Analyze and update task dependencies.

        Args:
            tasks: List of tasks

        Returns:
            Tasks with updated prerequisites

        Raises:
            DependencyAnalysisError: If circular dependencies detected
        """
        logger.info(f"Analyzing dependencies for {len(tasks)} tasks")

        # Create task name to task mapping
        task_map = {task.name: task for task in tasks}

        # Analyze each task
        for task in tasks:
            # Infer dependencies based on patterns
            inferred_deps = self._infer_dependencies(task, tasks)

            # Merge with existing prerequisites
            all_deps = set(task.prerequisites) | inferred_deps

            # Update prerequisites (convert to sorted list)
            task.prerequisites = sorted(list(all_deps))

        # Check for circular dependencies
        self._check_circular_dependencies(tasks)

        # Sort tasks by dependency order
        sorted_tasks = self._topological_sort(tasks)

        logger.info("Dependency analysis complete")
        return sorted_tasks

    def _infer_dependencies(
        self, task: IdentifiedTask, all_tasks: List[IdentifiedTask]
    ) -> Set[str]:
        """
        Infer dependencies for a task based on patterns.

        Args:
            task: Task to analyze
            all_tasks: All tasks

        Returns:
            Set of inferred dependency descriptions
        """
        dependencies = set()

        # Check against dependency patterns
        for pattern_key, pattern_deps in self.DEPENDENCY_PATTERNS.items():
            if pattern_key in task.name.lower():
                # This task matches a pattern
                for dep_key in pattern_deps:
                    # Find matching task
                    for other_task in all_tasks:
                        if dep_key in other_task.name.lower() and other_task != task:
                            dep_text = f"{other_task.name} 모듈이 먼저 구현되어야 함"
                            dependencies.add(dep_text)
                            logger.debug(
                                f"Inferred dependency: {task.name} -> {other_task.name}"
                            )

        return dependencies

    def _check_circular_dependencies(self, tasks: List[IdentifiedTask]) -> None:
        """
        Check for circular dependencies.

        Args:
            tasks: List of tasks

        Raises:
            DependencyAnalysisError: If circular dependencies found
        """
        logger.debug("Checking for circular dependencies")

        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        for task in tasks:
            # Extract task names from prerequisites
            deps = set()
            for prereq in task.prerequisites:
                # Extract task name from prerequisite text
                for other_task in tasks:
                    if other_task.name in prereq:
                        deps.add(other_task.name)
                        break

            graph[task.name] = deps

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            # Check all neighbors
            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        logger.error(f"Circular dependency detected: {node} -> {neighbor}")
                        return True

            rec_stack.remove(node)
            return False

        # Check each node
        for task_name in graph:
            if task_name not in visited:
                if has_cycle(task_name):
                    raise DependencyAnalysisError(
                        f"Circular dependency detected involving: {task_name}"
                    )

        logger.debug("No circular dependencies found")

    def _topological_sort(self, tasks: List[IdentifiedTask]) -> List[IdentifiedTask]:
        """
        Sort tasks by dependency order using topological sort.

        Tasks with no dependencies come first.

        Args:
            tasks: List of tasks

        Returns:
            Sorted list of tasks
        """
        logger.debug("Performing topological sort")

        # Build task name to task mapping
        task_map = {task.name: task for task in tasks}

        # Build dependency graph (task name -> set of prerequisite task names)
        graph: Dict[str, Set[str]] = {}
        in_degree: Dict[str, int] = {}

        for task in tasks:
            graph[task.name] = set()
            in_degree[task.name] = 0

        for task in tasks:
            # Extract task names from prerequisites
            for prereq in task.prerequisites:
                for other_task in tasks:
                    if other_task.name in prereq and other_task != task:
                        graph[other_task.name].add(task.name)
                        in_degree[task.name] += 1

        # Kahn's algorithm for topological sort
        queue = [name for name in in_degree if in_degree[name] == 0]
        sorted_names = []

        while queue:
            # Sort queue to ensure deterministic order
            queue.sort()
            node = queue.pop(0)
            sorted_names.append(node)

            # Reduce in-degree for neighbors
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If not all tasks are sorted, there's a cycle (shouldn't happen if check passed)
        if len(sorted_names) != len(tasks):
            logger.warning("Topological sort incomplete, using original order")
            return tasks

        # Convert back to task objects
        sorted_tasks = [task_map[name] for name in sorted_names]

        logger.debug(f"Sorted tasks: {[t.name for t in sorted_tasks]}")
        return sorted_tasks

    def get_dependency_graph(self, tasks: List[IdentifiedTask]) -> Dict[str, List[str]]:
        """
        Get dependency graph representation.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary mapping task names to their dependencies
        """
        graph = {}
        for task in tasks:
            deps = []
            for prereq in task.prerequisites:
                # Extract task names from prerequisite text
                for other_task in tasks:
                    if other_task.name in prereq:
                        deps.append(other_task.name)
                        break

            graph[task.name] = deps

        return graph
