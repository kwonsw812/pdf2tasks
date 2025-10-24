"""Main LLM Planner interface - unified task identification system."""

from typing import List, Optional
from ...types.models import (
    Section,
    FunctionalGroup,
    IdentifiedTask,
    LLMPlannerResult,
    ImageAnalysis,
)
from ...utils.logger import get_logger
from ..claude_client import ClaudeClient
from .prompt_builder import PromptBuilder
from .llm_caller import LLMCaller
from .task_deduplicator import TaskDeduplicator
from .dependency_analyzer import DependencyAnalyzer
from .token_tracker import TokenTracker

logger = get_logger(__name__)


class LLMPlanner:
    """
    Main LLM Planner interface.

    Orchestrates the entire task identification pipeline:
    1. Build prompts from sections
    2. Call LLM for task identification
    3. Parse and validate response
    4. Deduplicate similar tasks
    5. Analyze dependencies
    6. Track token usage and cost
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        similarity_threshold: float = 0.8,
        enable_dependency_analysis: bool = True,
    ):
        """
        Initialize LLM Planner.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            similarity_threshold: Threshold for task deduplication
            enable_dependency_analysis: Whether to analyze dependencies
        """
        logger.info("Initializing LLM Planner")

        # Initialize Claude client
        self.client = ClaudeClient(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Initialize components
        self.prompt_builder = PromptBuilder()
        self.llm_caller = LLMCaller(self.client)
        self.deduplicator = TaskDeduplicator(similarity_threshold=similarity_threshold)
        self.dependency_analyzer = DependencyAnalyzer()
        self.token_tracker = TokenTracker(model=model)

        self.enable_dependency_analysis = enable_dependency_analysis

        logger.info(
            f"LLM Planner initialized (model={model}, "
            f"dependency_analysis={enable_dependency_analysis})"
        )

    def identify_tasks_from_sections(
        self,
        sections: List[Section],
        image_analyses: Optional[List[ImageAnalysis]] = None
    ) -> LLMPlannerResult:
        """
        Identify high-level tasks from document sections.

        Args:
            sections: List of document sections
            image_analyses: Optional list of image analysis results

        Returns:
            LLMPlannerResult containing identified tasks and usage statistics
        """
        logger.info("=" * 80)
        logger.info("STARTING TASK IDENTIFICATION FROM SECTIONS")
        logger.info(f"Input: {len(sections)} sections")
        if image_analyses:
            logger.info(f"Image analyses: {len(image_analyses)} screens")
        logger.info("=" * 80)

        # Step 1: Build prompts
        logger.info("Step 1/5: Building prompts...")
        system_prompt, user_prompt = self.prompt_builder.build_from_sections(
            sections, image_analyses
        )

        # Step 2: Call LLM
        logger.info("Step 2/5: Calling LLM for task identification...")
        tasks, token_usage = self.llm_caller.call_for_task_identification(
            system_prompt, user_prompt
        )

        # Track tokens
        cost = self.token_tracker.track(token_usage)
        logger.info(f"Identified {len(tasks)} tasks (cost: ${cost:.6f})")

        # Step 3: Deduplicate tasks
        logger.info("Step 3/5: Deduplicating tasks...")
        tasks = self.deduplicator.deduplicate(tasks)
        tasks = self.deduplicator.remove_empty_tasks(tasks)

        # Step 4: Analyze dependencies
        if self.enable_dependency_analysis:
            logger.info("Step 4/5: Analyzing dependencies...")
            tasks = self.dependency_analyzer.analyze(tasks)
        else:
            logger.info("Step 4/5: Skipping dependency analysis")

        # Step 5: Create result
        logger.info("Step 5/5: Creating result...")
        result = LLMPlannerResult(
            tasks=tasks,
            token_usage=token_usage,
            estimated_cost_usd=self.token_tracker.get_total_cost(),
            model=self.client.model,
        )

        # Log summary
        logger.info("=" * 80)
        logger.info("TASK IDENTIFICATION COMPLETE")
        logger.info(f"Total tasks identified: {len(result.tasks)}")
        logger.info(f"Total tokens used: {token_usage.total_tokens}")
        logger.info(f"Total cost: ${result.estimated_cost_usd:.6f}")
        logger.info("=" * 80)

        self._log_task_summary(result.tasks)

        return result

    def identify_tasks_from_functional_groups(
        self, functional_groups: List[FunctionalGroup]
    ) -> LLMPlannerResult:
        """
        Identify high-level tasks from functional groups.

        Args:
            functional_groups: List of functional groups

        Returns:
            LLMPlannerResult containing identified tasks and usage statistics
        """
        logger.info("=" * 80)
        logger.info("STARTING TASK IDENTIFICATION FROM FUNCTIONAL GROUPS")
        logger.info(f"Input: {len(functional_groups)} functional groups")
        logger.info("=" * 80)

        # Step 1: Build prompts
        logger.info("Step 1/5: Building prompts...")
        system_prompt, user_prompt = (
            self.prompt_builder.build_from_functional_groups(functional_groups)
        )

        # Step 2: Call LLM
        logger.info("Step 2/5: Calling LLM for task identification...")
        tasks, token_usage = self.llm_caller.call_for_task_identification(
            system_prompt, user_prompt
        )

        # Track tokens
        cost = self.token_tracker.track(token_usage)
        logger.info(f"Identified {len(tasks)} tasks (cost: ${cost:.6f})")

        # Step 3: Deduplicate tasks
        logger.info("Step 3/5: Deduplicating tasks...")
        tasks = self.deduplicator.deduplicate(tasks)
        tasks = self.deduplicator.remove_empty_tasks(tasks)

        # Step 4: Analyze dependencies
        if self.enable_dependency_analysis:
            logger.info("Step 4/5: Analyzing dependencies...")
            tasks = self.dependency_analyzer.analyze(tasks)
        else:
            logger.info("Step 4/5: Skipping dependency analysis")

        # Step 5: Create result
        logger.info("Step 5/5: Creating result...")
        result = LLMPlannerResult(
            tasks=tasks,
            token_usage=token_usage,
            estimated_cost_usd=self.token_tracker.get_total_cost(),
            model=self.client.model,
        )

        # Log summary
        logger.info("=" * 80)
        logger.info("TASK IDENTIFICATION COMPLETE")
        logger.info(f"Total tasks identified: {len(result.tasks)}")
        logger.info(f"Total tokens used: {token_usage.total_tokens}")
        logger.info(f"Total cost: ${result.estimated_cost_usd:.6f}")
        logger.info("=" * 80)

        self._log_task_summary(result.tasks)

        return result

    def _log_task_summary(self, tasks: List[IdentifiedTask]) -> None:
        """
        Log a summary of identified tasks.

        Args:
            tasks: List of tasks
        """
        logger.info("")
        logger.info("IDENTIFIED TASKS:")
        logger.info("-" * 80)

        for task in tasks:
            logger.info(f"{task.index}. {task.name} (module: {task.module})")
            logger.info(f"   Description: {task.description}")

            if task.entities:
                logger.info(f"   Entities: {', '.join(task.entities)}")

            if task.prerequisites:
                logger.info(f"   Prerequisites: {len(task.prerequisites)} items")

            if task.related_sections:
                logger.info(f"   Related sections: {task.related_sections}")

            logger.info("")

    def get_token_summary(self) -> dict:
        """
        Get token usage summary.

        Returns:
            Dictionary with usage statistics
        """
        return self.token_tracker.get_summary()

    def log_token_summary(self) -> None:
        """
        Log token usage summary.
        """
        self.token_tracker.log_summary()

    def reset_token_tracker(self) -> None:
        """
        Reset token usage tracking.
        """
        self.token_tracker.reset()

    def get_dependency_graph(self, tasks: List[IdentifiedTask]) -> dict:
        """
        Get dependency graph for tasks.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary mapping task names to dependencies
        """
        return self.dependency_analyzer.get_dependency_graph(tasks)
