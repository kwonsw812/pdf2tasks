"""Prompt builder for LLM Planner."""

from typing import List, Tuple, Optional
from ...types.models import Section, FunctionalGroup, ImageAnalysis
from ...utils.logger import get_logger
from ..exceptions import PromptTooLongError
from .prompts import (
    SYSTEM_PROMPT,
    build_task_identification_prompt,
    build_task_identification_prompt_from_groups,
)

logger = get_logger(__name__)


class PromptBuilder:
    """
    Builder for constructing prompts from preprocessed sections.

    Handles token limits and chunking if necessary.
    """

    # Conservative estimate: ~4 chars per token
    CHARS_PER_TOKEN = 4

    # Maximum tokens for Claude (200k context, but we use conservative limit)
    MAX_CONTEXT_TOKENS = 150_000

    # Reserve tokens for system prompt and response
    RESERVED_TOKENS = 10_000

    def __init__(self, max_context_tokens: int = MAX_CONTEXT_TOKENS):
        """
        Initialize PromptBuilder.

        Args:
            max_context_tokens: Maximum context tokens allowed
        """
        self.max_context_tokens = max_context_tokens
        self.max_prompt_tokens = max_context_tokens - self.RESERVED_TOKENS
        logger.info(
            f"PromptBuilder initialized with max {self.max_prompt_tokens} prompt tokens"
        )

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // self.CHARS_PER_TOKEN

    def build_from_sections(
        self,
        sections: List[Section],
        image_analyses: Optional[List[ImageAnalysis]] = None
    ) -> Tuple[str, str]:
        """
        Build prompt from sections.

        Args:
            sections: List of document sections
            image_analyses: Optional list of image analysis results

        Returns:
            Tuple of (system_prompt, user_prompt)

        Raises:
            PromptTooLongError: If sections are too long even after truncation
        """
        if image_analyses:
            logger.info(
                f"Building prompt from {len(sections)} sections "
                f"with {len(image_analyses)} image analyses"
            )
        else:
            logger.info(f"Building prompt from {len(sections)} sections")

        user_prompt = build_task_identification_prompt(sections, image_analyses)

        # Check token limits
        system_tokens = self.estimate_tokens(SYSTEM_PROMPT)
        user_tokens = self.estimate_tokens(user_prompt)
        total_tokens = system_tokens + user_tokens

        logger.debug(
            f"Estimated tokens - System: {system_tokens}, User: {user_tokens}, "
            f"Total: {total_tokens}"
        )

        if total_tokens > self.max_prompt_tokens:
            logger.warning(
                f"Prompt too long ({total_tokens} tokens). "
                f"Max allowed: {self.max_prompt_tokens}"
            )

            # Try to truncate sections
            user_prompt = self._build_truncated_prompt(sections)
            user_tokens = self.estimate_tokens(user_prompt)
            total_tokens = system_tokens + user_tokens

            if total_tokens > self.max_prompt_tokens:
                raise PromptTooLongError(
                    f"Prompt exceeds token limit even after truncation. "
                    f"Tokens: {total_tokens}, Max: {self.max_prompt_tokens}. "
                    f"Consider splitting into multiple requests."
                )

            logger.info(f"Prompt truncated to {user_tokens} tokens")

        return SYSTEM_PROMPT, user_prompt

    def build_from_functional_groups(
        self, functional_groups: List[FunctionalGroup]
    ) -> Tuple[str, str]:
        """
        Build prompt from functional groups.

        Args:
            functional_groups: List of functional groups

        Returns:
            Tuple of (system_prompt, user_prompt)

        Raises:
            PromptTooLongError: If groups are too long even after truncation
        """
        logger.info(f"Building prompt from {len(functional_groups)} functional groups")

        user_prompt = build_task_identification_prompt_from_groups(functional_groups)

        # Check token limits
        system_tokens = self.estimate_tokens(SYSTEM_PROMPT)
        user_tokens = self.estimate_tokens(user_prompt)
        total_tokens = system_tokens + user_tokens

        logger.debug(
            f"Estimated tokens - System: {system_tokens}, User: {user_tokens}, "
            f"Total: {total_tokens}"
        )

        if total_tokens > self.max_prompt_tokens:
            logger.warning(
                f"Prompt too long ({total_tokens} tokens). "
                f"Max allowed: {self.max_prompt_tokens}"
            )
            raise PromptTooLongError(
                f"Prompt exceeds token limit. "
                f"Tokens: {total_tokens}, Max: {self.max_prompt_tokens}. "
                f"Consider splitting into multiple requests or reducing content."
            )

        return SYSTEM_PROMPT, user_prompt

    def _build_truncated_prompt(self, sections: List[Section]) -> str:
        """
        Build a truncated version of the prompt.

        Reduces content length per section to fit within token limits.

        Args:
            sections: List of sections

        Returns:
            Truncated prompt
        """
        logger.info("Building truncated prompt")

        # Calculate max chars per section
        max_total_chars = self.max_prompt_tokens * self.CHARS_PER_TOKEN
        overhead_chars = 200 * len(sections)  # Overhead for formatting
        available_chars = max_total_chars - overhead_chars

        max_chars_per_section = max(100, available_chars // len(sections))

        logger.debug(f"Max chars per section: {max_chars_per_section}")

        prompt = "다음은 기획서에서 추출한 섹션들입니다 (일부 내용 생략):\n\n"

        for idx, section in enumerate(sections, start=1):
            # Truncate content
            content = section.content
            if len(content) > max_chars_per_section:
                content = content[:max_chars_per_section] + "..."

            prompt += f"[섹션 {idx}] {section.title}\n"
            prompt += f"레벨: {section.level}\n"
            prompt += f"내용: {content}\n"
            prompt += f"페이지: {section.page_range.start}-{section.page_range.end}\n"
            prompt += "\n"

        prompt += "\n위 섹션들을 분석하여 백엔드 상위 태스크들을 식별하고 JSON 형식으로 출력하세요."

        return prompt

    def split_sections_into_chunks(
        self, sections: List[Section], max_sections_per_chunk: int = 50
    ) -> List[List[Section]]:
        """
        Split sections into multiple chunks for processing.

        Useful when dealing with very large documents.

        Args:
            sections: List of sections
            max_sections_per_chunk: Maximum sections per chunk

        Returns:
            List of section chunks
        """
        logger.info(
            f"Splitting {len(sections)} sections into chunks "
            f"(max {max_sections_per_chunk} per chunk)"
        )

        chunks = []
        for i in range(0, len(sections), max_sections_per_chunk):
            chunk = sections[i : i + max_sections_per_chunk]
            chunks.append(chunk)

        logger.info(f"Created {len(chunks)} chunks")
        return chunks
