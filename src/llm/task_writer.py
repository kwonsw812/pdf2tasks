"""LLM TaskWriter for generating detailed sub-tasks."""

import os
import asyncio
from typing import List, Optional
from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message

from src.types.models import (
    IdentifiedTask,
    Section,
    SubTask,
    TaskWriterResult,
    TokenUsage,
    ValidationResult,
    ImageAnalysis,
)
from src.llm.prompts import build_task_writer_prompt, estimate_token_count
from src.llm.parser import parse_sub_tasks, validate_markdown_structure
from src.llm.validator import validate_sub_tasks, get_validation_summary
from src.llm.exceptions import (
    APIKeyError,
    LLMCallError,
    MarkdownParseError,
    SubTaskValidationError,
)
from src.utils.logger import get_logger


logger = get_logger(__name__)


class LLMTaskWriter:
    """
    LLM-powered TaskWriter for generating detailed sub-tasks.

    This class takes a high-level task and breaks it down into detailed
    sub-tasks suitable for implementation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ):
        """
        Initialize LLMTaskWriter.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens for response
            temperature: Temperature for generation (0.0 = deterministic)

        Raises:
            APIKeyError: If API key is not provided or found
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise APIKeyError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
            )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = Anthropic(api_key=self.api_key)
        self.async_client = AsyncAnthropic(api_key=self.api_key)

        logger.info(f"Initialized LLMTaskWriter with model: {model}")

    def write_task(
        self,
        task: IdentifiedTask,
        sections: List[Section],
        image_analyses: Optional[List[ImageAnalysis]] = None,
        validate: bool = True,
        retry_on_failure: bool = True,
    ) -> TaskWriterResult:
        """
        Generate detailed sub-tasks for a high-level task.

        Args:
            task: Identified high-level task
            sections: List of all document sections
            image_analyses: Optional list of image analysis results
            validate: Whether to validate generated sub-tasks
            retry_on_failure: Whether to retry on validation failure

        Returns:
            TaskWriterResult with sub-tasks and metadata

        Raises:
            LLMCallError: If LLM API call fails
            MarkdownParseError: If parsing fails
            SubTaskValidationError: If validation fails and retry is disabled
        """
        logger.info(f"Writing sub-tasks for task {task.index}: {task.name}")
        if image_analyses:
            logger.info(f"  With {len(image_analyses)} image analyses available")

        # Build prompt
        prompt = build_task_writer_prompt(task, sections, image_analyses)
        logger.debug(
            f"Prompt length: {len(prompt)} chars, ~{estimate_token_count(prompt)} tokens"
        )

        # Call LLM
        markdown, token_usage = self._call_llm(prompt)
        logger.info(
            f"Received response: {len(markdown)} chars, {token_usage.total_tokens} tokens"
        )

        # Validate markdown structure
        if not validate_markdown_structure(markdown, task.index):
            if retry_on_failure:
                logger.warning(
                    "Markdown structure validation failed, retrying with modified prompt"
                )
                return self._retry_with_feedback(
                    task, sections, markdown, "Invalid markdown structure", image_analyses
                )
            else:
                raise MarkdownParseError(
                    "Generated markdown does not have expected structure"
                )

        # Parse sub-tasks
        try:
            sub_tasks = parse_sub_tasks(markdown, task.index)
            logger.info(f"Parsed {len(sub_tasks)} sub-tasks")
        except MarkdownParseError as e:
            if retry_on_failure:
                logger.warning(f"Parsing failed: {str(e)}, retrying")
                return self._retry_with_feedback(
                    task, sections, markdown, str(e), image_analyses
                )
            else:
                raise

        # Validate sub-tasks
        if validate:
            validation = validate_sub_tasks(sub_tasks, task.index)
            logger.info(f"Validation: {get_validation_summary(validation)}")

            if not validation.is_valid:
                if retry_on_failure:
                    logger.warning("Validation failed, retrying with feedback")
                    return self._retry_with_feedback(
                        task, sections, markdown, validation.errors[0], image_analyses
                    )
                else:
                    raise SubTaskValidationError(
                        f"Sub-task validation failed: {validation.errors}"
                    )

        # Generate final markdown document
        final_markdown = self._generate_markdown_document(task, sub_tasks, sections)

        return TaskWriterResult(
            task=task,
            sub_tasks=sub_tasks,
            markdown=final_markdown,
            token_usage=token_usage,
        )

    def _call_llm(self, prompt: str) -> tuple[str, TokenUsage]:
        """
        Call Claude API with prompt.

        Args:
            prompt: Prompt text

        Returns:
            Tuple of (response text, token usage)

        Raises:
            LLMCallError: If API call fails
        """
        try:
            message: Message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from response
            response_text = ""
            for content in message.content:
                if hasattr(content, "text"):
                    response_text += content.text

            # Extract token usage
            token_usage = TokenUsage(
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                total_tokens=message.usage.input_tokens + message.usage.output_tokens,
            )

            return response_text, token_usage

        except Exception as e:
            raise LLMCallError(f"Failed to call Claude API: {str(e)}") from e

    def _retry_with_feedback(
        self,
        task: IdentifiedTask,
        sections: List[Section],
        previous_response: str,
        error_message: str,
        image_analyses: Optional[List[ImageAnalysis]] = None,
    ) -> TaskWriterResult:
        """
        Retry generation with feedback from previous attempt.

        Args:
            task: High-level task
            sections: Document sections
            previous_response: Previous LLM response
            error_message: Error from previous attempt
            image_analyses: Optional list of image analyses

        Returns:
            TaskWriterResult from retry
        """
        logger.info(f"Retrying with feedback: {error_message}")

        # Build prompt with feedback
        prompt = build_task_writer_prompt(task, sections, image_analyses)
        prompt += f"\n\n**이전 시도에서 발생한 오류:**\n{error_message}\n\n"
        prompt += "**이전 응답:**\n```\n"
        prompt += previous_response[:500]  # Include snippet
        prompt += "\n...\n```\n\n"
        prompt += "위 오류를 수정하여 다시 생성해주세요.\n"

        # Call LLM again (without retry to prevent infinite loop)
        markdown, token_usage = self._call_llm(prompt)
        sub_tasks = parse_sub_tasks(markdown, task.index)

        # Generate final markdown
        final_markdown = self._generate_markdown_document(task, sub_tasks, sections)

        return TaskWriterResult(
            task=task,
            sub_tasks=sub_tasks,
            markdown=final_markdown,
            token_usage=token_usage,
        )

    def _generate_markdown_document(
        self, task: IdentifiedTask, sub_tasks: List[SubTask], sections: List[Section]
    ) -> str:
        """
        Generate final markdown document in standard format.

        Args:
            task: High-level task
            sub_tasks: Generated sub-tasks
            sections: Document sections (for page references)

        Returns:
            Formatted markdown document
        """
        lines = []

        # Title
        lines.append(f"# {task.name} — 상위 태스크 {task.index}")
        lines.append("")

        # Task overview
        lines.append("## 상위 태스크 개요")
        lines.append(f"- **설명:** {task.description}")
        lines.append(f"- **모듈/영역:** {task.module}")

        if task.entities:
            lines.append(f"- **관련 엔티티:** {', '.join(task.entities)}")

        if task.prerequisites:
            lines.append(f"- **선행 조건:** {', '.join(task.prerequisites)}")

        # Add page references
        if task.related_sections:
            page_ranges = []
            for section_idx in task.related_sections:
                if 0 <= section_idx < len(sections):
                    section = sections[section_idx]
                    page_ranges.append(
                        f"p.{section.page_range.start}–{section.page_range.end}"
                    )
            if page_ranges:
                lines.append(f"- **참고:** PDF 원문 {', '.join(page_ranges)}")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Sub-tasks
        lines.append("## 하위 태스크 목록")
        lines.append("")

        for sub_task in sub_tasks:
            lines.append(f"### {sub_task.index} {sub_task.title}")
            lines.append(f"- **목적:** {sub_task.purpose}")

            if sub_task.endpoint:
                lines.append(f"- **엔드포인트:** `{sub_task.endpoint}`")

            if sub_task.data_model:
                lines.append(f"- **데이터 모델:**")
                lines.append(f"  {sub_task.data_model}")

            lines.append(f"- **로직 요약:** {sub_task.logic}")

            if sub_task.security:
                lines.append(f"- **권한/보안:** {sub_task.security}")

            if sub_task.exceptions:
                lines.append(f"- **예외:** {sub_task.exceptions}")

            if sub_task.test_points:
                lines.append(f"- **테스트 포인트:** {sub_task.test_points}")

            lines.append("")

        return "\n".join(lines)

    def estimate_cost(self, token_usage: TokenUsage) -> float:
        """
        Estimate cost in USD for token usage.

        Based on Claude 3.5 Sonnet pricing (as of 2024):
        - Input: $3 per million tokens
        - Output: $15 per million tokens

        Args:
            token_usage: Token usage information

        Returns:
            Estimated cost in USD
        """
        input_cost = (token_usage.input_tokens / 1_000_000) * 3.0
        output_cost = (token_usage.output_tokens / 1_000_000) * 15.0
        return input_cost + output_cost

    # ========== Async Methods for Parallel Processing ==========

    async def write_task_async(
        self,
        task: IdentifiedTask,
        sections: List[Section],
        image_analyses: Optional[List[ImageAnalysis]] = None,
        validate: bool = True,
        retry_on_failure: bool = True,
    ) -> TaskWriterResult:
        """
        Generate detailed sub-tasks for a high-level task (async version).

        This async version allows parallel processing of multiple tasks.

        Args:
            task: Identified high-level task
            sections: List of all document sections
            image_analyses: Optional list of image analysis results
            validate: Whether to validate generated sub-tasks
            retry_on_failure: Whether to retry on validation failure

        Returns:
            TaskWriterResult with sub-tasks and metadata

        Raises:
            LLMCallError: If LLM API call fails
            MarkdownParseError: If parsing fails
            SubTaskValidationError: If validation fails and retry is disabled
        """
        logger.info(f"[Async] Writing sub-tasks for task {task.index}: {task.name}")
        if image_analyses:
            logger.info(f"  With {len(image_analyses)} image analyses available")

        # Build prompt
        prompt = build_task_writer_prompt(task, sections, image_analyses)
        logger.debug(
            f"Prompt length: {len(prompt)} chars, ~{estimate_token_count(prompt)} tokens"
        )

        # Call LLM (async)
        markdown, token_usage = await self._call_llm_async(prompt)
        logger.info(
            f"Received response: {len(markdown)} chars, {token_usage.total_tokens} tokens"
        )

        # Validate markdown structure
        if not validate_markdown_structure(markdown, task.index):
            if retry_on_failure:
                logger.warning(
                    "Markdown structure validation failed, retrying with modified prompt"
                )
                return await self._retry_with_feedback_async(
                    task, sections, markdown, "Invalid markdown structure", image_analyses
                )
            else:
                raise MarkdownParseError(
                    "Generated markdown does not have expected structure"
                )

        # Parse sub-tasks
        try:
            sub_tasks = parse_sub_tasks(markdown, task.index)
            logger.info(f"Parsed {len(sub_tasks)} sub-tasks")
        except MarkdownParseError as e:
            if retry_on_failure:
                logger.warning(f"Parsing failed: {str(e)}, retrying")
                return await self._retry_with_feedback_async(
                    task, sections, markdown, str(e), image_analyses
                )
            else:
                raise

        # Validate sub-tasks
        if validate:
            validation = validate_sub_tasks(sub_tasks, task.index)
            logger.info(f"Validation: {get_validation_summary(validation)}")

            if not validation.is_valid:
                if retry_on_failure:
                    logger.warning("Validation failed, retrying with feedback")
                    return await self._retry_with_feedback_async(
                        task, sections, markdown, validation.errors[0], image_analyses
                    )
                else:
                    raise SubTaskValidationError(
                        f"Sub-task validation failed: {validation.errors}"
                    )

        # Generate final markdown document
        final_markdown = self._generate_markdown_document(task, sub_tasks, sections)

        return TaskWriterResult(
            task=task,
            sub_tasks=sub_tasks,
            markdown=final_markdown,
            token_usage=token_usage,
        )

    async def _call_llm_async(self, prompt: str, max_retries: int = 3) -> tuple[str, TokenUsage]:
        """
        Call Claude API with prompt (async version with retry logic).

        Args:
            prompt: Prompt text
            max_retries: Maximum number of retries for rate limit errors

        Returns:
            Tuple of (response text, token usage)

        Raises:
            LLMCallError: If API call fails after all retries
        """
        for attempt in range(max_retries):
            try:
                message: Message = await self.async_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract text from response
                response_text = ""
                for content in message.content:
                    if hasattr(content, "text"):
                        response_text += content.text

                # Extract token usage
                token_usage = TokenUsage(
                    input_tokens=message.usage.input_tokens,
                    output_tokens=message.usage.output_tokens,
                    total_tokens=message.usage.input_tokens + message.usage.output_tokens,
                )

                return response_text, token_usage

            except Exception as e:
                error_str = str(e)

                # Check if it's a rate limit error (429)
                if "429" in error_str or "rate_limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Exponential backoff: 2^attempt seconds
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Rate limit hit (429), retrying in {wait_time}s... "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise LLMCallError(
                            f"Rate limit exceeded after {max_retries} retries. "
                            f"Please try again later or reduce concurrent requests."
                        ) from e
                else:
                    # Non-rate-limit error, raise immediately
                    raise LLMCallError(f"Failed to call Claude API: {error_str}") from e

        # Should never reach here, but just in case
        raise LLMCallError("Unexpected error in API call retry logic")

    async def _retry_with_feedback_async(
        self,
        task: IdentifiedTask,
        sections: List[Section],
        previous_response: str,
        error_message: str,
        image_analyses: Optional[List[ImageAnalysis]] = None,
    ) -> TaskWriterResult:
        """
        Retry generation with feedback from previous attempt (async version).

        Args:
            task: High-level task
            sections: Document sections
            previous_response: Previous LLM response
            error_message: Error from previous attempt
            image_analyses: Optional list of image analyses

        Returns:
            TaskWriterResult from retry
        """
        logger.info(f"[Async] Retrying with feedback: {error_message}")

        # Build prompt with feedback
        prompt = build_task_writer_prompt(task, sections, image_analyses)
        prompt += f"\n\n**이전 시도에서 발생한 오류:**\n{error_message}\n\n"
        prompt += "**이전 응답:**\n```\n"
        prompt += previous_response[:500]  # Include snippet
        prompt += "\n...\n```\n\n"
        prompt += "위 오류를 수정하여 다시 생성해주세요.\n"

        # Call LLM again (without retry to prevent infinite loop)
        markdown, token_usage = await self._call_llm_async(prompt)
        sub_tasks = parse_sub_tasks(markdown, task.index)

        # Generate final markdown
        final_markdown = self._generate_markdown_document(task, sub_tasks, sections)

        return TaskWriterResult(
            task=task,
            sub_tasks=sub_tasks,
            markdown=final_markdown,
            token_usage=token_usage,
        )
