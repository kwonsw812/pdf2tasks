"""LLM-based functional grouping using semantic understanding."""

import json
from typing import List, Optional, Dict, Set
from anthropic import Anthropic
from ..types.models import Section, FunctionalGroup
from .exceptions import GroupingError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMFunctionalGrouper:
    """Groups sections by functional categories using LLM."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        custom_categories: Optional[List[str]] = None,
    ):
        """
        Initialize LLM functional grouper.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens for response
            temperature: Temperature for generation (0.0 for deterministic)
            custom_categories: Custom category names (if None, LLM will suggest categories)
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.custom_categories = custom_categories
        self.client = None

        if api_key:
            self.client = Anthropic(api_key=api_key)

        # Default categories for backend systems
        self.default_categories = [
            "인증",
            "결제",
            "사용자관리",
            "상품관리",
            "검색",
            "알림",
            "관리자",
            "데이터관리",
            "API",
            "보안",
        ]

    def group_sections(self, sections: List[Section]) -> List[FunctionalGroup]:
        """
        Group sections by functional categories using LLM.

        Args:
            sections: List of sections to group

        Returns:
            List of functional groups

        Raises:
            GroupingError: If grouping fails
        """
        try:
            logger.info(f"Starting LLM-based functional grouping for {len(sections)} sections")

            if not self.client:
                raise GroupingError("API key not provided for LLM grouping")

            # Flatten sections for analysis
            flat_sections = self._flatten_sections(sections)

            if not flat_sections:
                logger.warning("No sections to group")
                return []

            # Build section summaries for prompt
            section_summaries = self._build_section_summaries(flat_sections)

            # Get categories to use
            categories = self.custom_categories or self.default_categories

            # Build prompt
            prompt = self._build_grouping_prompt(section_summaries, categories)

            # Call LLM
            logger.info("Calling Claude API for functional grouping...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text
            groupings = self._parse_grouping_response(response_text)

            # Create functional groups
            functional_groups = self._create_functional_groups(
                flat_sections, groupings
            )

            logger.info(f"LLM created {len(functional_groups)} functional groups")
            logger.info(
                f"Token usage: {response.usage.input_tokens} input, "
                f"{response.usage.output_tokens} output"
            )

            return functional_groups

        except Exception as e:
            logger.error(f"LLM functional grouping failed: {e}")
            raise GroupingError(f"Failed to group sections with LLM: {e}") from e

    def _flatten_sections(self, sections: List[Section]) -> List[Section]:
        """
        Flatten hierarchical sections into a flat list.

        Args:
            sections: Hierarchical sections

        Returns:
            Flattened list of sections
        """
        flat = []
        for section in sections:
            flat.append(section)
            if section.subsections:
                flat.extend(self._flatten_sections(section.subsections))
        return flat

    def _build_section_summaries(self, sections: List[Section]) -> List[Dict]:
        """
        Build section summaries for prompt.

        Args:
            sections: List of sections

        Returns:
            List of section summary dictionaries
        """
        summaries = []
        for idx, section in enumerate(sections):
            # Truncate content to max 200 chars
            content_preview = section.content[:200]
            if len(section.content) > 200:
                content_preview += "..."

            summaries.append({
                "id": idx,
                "title": section.title,
                "content_preview": content_preview,
            })

        return summaries

    def _build_grouping_prompt(
        self, section_summaries: List[Dict], categories: List[str]
    ) -> str:
        """
        Build prompt for functional grouping.

        Args:
            section_summaries: List of section summaries
            categories: List of category names

        Returns:
            Prompt string
        """
        # Format sections for prompt
        sections_text = []
        for s in section_summaries:
            sections_text.append(
                f"[ID: {s['id']}] {s['title']}\n  Preview: {s['content_preview']}"
            )

        sections_formatted = "\n\n".join(sections_text)

        # Format categories
        categories_formatted = "\n".join([f"- {cat}" for cat in categories])

        prompt = f"""You are an expert at organizing technical documentation. Your task is to classify sections into functional categories.

Given these sections from a technical specification document:
---
{sections_formatted}
---

Please classify each section into one or more of these functional categories:
{categories_formatted}

For sections that don't fit any category, suggest a new category name or use "기타" (Other).

Respond with a JSON object in this exact format:
{{
  "groups": [
    {{
      "category": "Category name",
      "section_ids": [0, 2, 5],
      "keywords": ["keyword1", "keyword2"]
    }},
    {{
      "category": "Another category",
      "section_ids": [1, 3],
      "keywords": ["keyword3"]
    }}
  ]
}}

Rules:
- Each section should belong to at least one category
- A section can belong to multiple categories if relevant
- Provide 2-5 keywords that represent each category
- Use semantic understanding, not just keyword matching
- Return valid JSON only, no additional text"""

        return prompt

    def _parse_grouping_response(self, response_text: str) -> Dict:
        """
        Parse LLM response into grouping data.

        Args:
            response_text: LLM response text

        Returns:
            Grouping data dictionary
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text.strip()
            if json_text.startswith("```"):
                # Remove markdown code block
                lines = json_text.split("\n")
                json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text

            # Parse JSON
            data = json.loads(json_text)

            if "groups" not in data:
                raise ValueError("Response does not contain 'groups' field")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise GroupingError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            logger.error(f"Failed to parse grouping: {e}")
            raise GroupingError(f"Failed to parse LLM response: {e}")

    def _create_functional_groups(
        self, all_sections: List[Section], groupings: Dict
    ) -> List[FunctionalGroup]:
        """
        Create FunctionalGroup objects from grouping data.

        Args:
            all_sections: All sections
            groupings: Grouping data from LLM

        Returns:
            List of FunctionalGroup objects
        """
        functional_groups = []

        for group_data in groupings["groups"]:
            category = group_data.get("category", "기타")
            section_ids = group_data.get("section_ids", [])
            keywords = group_data.get("keywords", [])

            # Get sections by ID
            group_sections = []
            for section_id in section_ids:
                if 0 <= section_id < len(all_sections):
                    group_sections.append(all_sections[section_id])
                else:
                    logger.warning(f"Invalid section ID: {section_id}")

            if group_sections:
                functional_group = FunctionalGroup(
                    name=category,
                    sections=group_sections,
                    keywords=keywords,
                )
                functional_groups.append(functional_group)

        # Check for ungrouped sections
        grouped_section_titles = set()
        for group in functional_groups:
            for section in group.sections:
                grouped_section_titles.add(section.title)

        ungrouped = [
            s for s in all_sections if s.title not in grouped_section_titles
        ]

        if ungrouped:
            logger.info(f"Found {len(ungrouped)} ungrouped sections")
            functional_groups.append(
                FunctionalGroup(
                    name="기타",
                    sections=ungrouped,
                    keywords=[],
                )
            )

        return functional_groups
