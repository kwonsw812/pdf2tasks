"""LLM-based context extraction from PDF sections."""

import json
import logging
from typing import List, Optional
from anthropic import Anthropic

from src.types.models import IdentifiedTask, Section, TaskContext
from src.llm.exceptions import LLMCallError

logger = logging.getLogger(__name__)


class LLMContextExtractor:
    """
    LLM-based context extractor for identifying user roles and deployment environments
    from PDF specification documents.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ):
        """
        Initialize the context extractor.

        Args:
            api_key: Anthropic API key
            model: Claude model name
            max_tokens: Maximum tokens for response
            temperature: LLM temperature (0.0 for deterministic output)
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = Anthropic(api_key=api_key)

    def extract_task_context(
        self,
        task: IdentifiedTask,
        sections: List[Section]
    ) -> TaskContext:
        """
        Extract context information (roles and environments) from task and related sections.

        Args:
            task: The identified task
            sections: All sections from PDF (will filter by task.related_sections)

        Returns:
            TaskContext with deployment_envs, actor_roles, and feature descriptions
        """
        logger.info(f"Extracting context for task {task.index}: {task.name}")

        # Filter related sections
        related_sections = [s for i, s in enumerate(sections) if i in task.related_sections]

        if not related_sections:
            logger.warning(f"No related sections found for task {task.name}, using default context")
            return TaskContext()

        # Build prompt
        prompt = self._build_context_extraction_prompt(task, related_sections)

        # Call LLM
        try:
            response_text = self._call_llm(prompt)
            context = self._parse_context_response(response_text)
            logger.info(f"Context extracted: roles={context.actor_roles}, envs={context.deployment_envs}")
            return context
        except Exception as e:
            logger.error(f"Failed to extract context for task {task.name}: {e}")
            # Return default context on failure
            return TaskContext()

    def _build_context_extraction_prompt(
        self,
        task: IdentifiedTask,
        sections: List[Section]
    ) -> str:
        """
        Build prompt for context extraction.

        Args:
            task: The task to extract context for
            sections: Related sections

        Returns:
            Prompt string
        """
        # Format sections
        sections_text = "\n\n".join([
            f"### [{section.title}]\n{section.content[:1000]}"  # Limit content to 1000 chars
            for section in sections[:5]  # Max 5 sections
        ])

        prompt = f"""당신은 기획서 분석 전문가입니다. 다음 태스크의 컨텍스트를 추출하세요.

## 분석 대상 태스크
- 이름: {task.name}
- 설명: {task.description}
- 모듈: {task.module}

## 관련 섹션 내용
{sections_text}

## 추출 항목

### 1. 사용자 역할 구분
다음 키워드를 찾아 역할을 식별하세요:
- "일반 사용자", "사용자", "user", "회원" → user
- "관리자", "admin", "어드민", "운영자" → admin
- "파트너 관리자", "partner admin", "파트너" → partner_admin
- "슈퍼 관리자", "super admin", "시스템 관리자" → super_admin

역할별로 서로 다른 기능이 명시되어 있다면 role_based_features에 요약하세요.

### 2. 배포 환경 구분
다음 키워드를 찾아 환경을 식별하세요:
- "개발환경", "개발", "dev", "local", "로컬" → development
- "스테이징", "staging", "qa", "테스트 서버" → staging
- "프로덕션", "운영", "production", "prod", "실서버" → production

환경별로 다른 동작이 명시되어 있다면 env_based_features에 요약하세요.

## 출력 (JSON 형식)
{{
  "deployment_envs": ["development", "production"],
  "actor_roles": ["user", "admin"],
  "role_based_features": {{
    "user": "상품 조회만 가능",
    "admin": "상품 등록/수정/삭제 가능"
  }},
  "env_based_features": {{
    "development": "테스트 PG 사용",
    "production": "실제 PG 연동"
  }}
}}

**주의사항**:
- 명시되지 않았거나 모든 역할/환경에서 동일하면 ["all"] 반환
- role_based_features와 env_based_features는 명시된 경우만 포함
- 반드시 유효한 JSON만 출력 (설명 금지)
"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """
        Call Claude API.

        Args:
            prompt: The prompt to send

        Returns:
            Response text

        Raises:
            LLMCallError: If API call fails
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text from response
            response_text = message.content[0].text
            return response_text

        except Exception as e:
            raise LLMCallError(f"Failed to call Claude API: {str(e)}")

    def _parse_context_response(self, response: str) -> TaskContext:
        """
        Parse LLM response into TaskContext.

        Args:
            response: LLM response text (expected to be JSON)

        Returns:
            TaskContext object

        Raises:
            LLMCallError: If JSON parsing fails
        """
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # Parse JSON
            data = json.loads(cleaned)

            # Create TaskContext
            context = TaskContext(
                deployment_envs=data.get("deployment_envs", ["all"]),
                actor_roles=data.get("actor_roles", ["all"]),
                role_based_features=data.get("role_based_features", {}),
                env_based_features=data.get("env_based_features", {})
            )

            return context

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise LLMCallError(f"JSON parsing error: {str(e)}")
        except Exception as e:
            raise LLMCallError(f"Failed to parse context response: {str(e)}")
