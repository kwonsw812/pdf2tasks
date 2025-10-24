"""LLM-based task matcher with context awareness (roles and environments)."""

import json
import logging
from typing import List, Dict, Any, Optional
from anthropic import Anthropic

from src.types.models import (
    IdentifiedTask,
    OpenAPISpec,
    OpenAPIEndpoint,
    TaskMatchResult,
)
from src.llm.exceptions import LLMCallError

logger = logging.getLogger(__name__)


class LLMTaskMatcher:
    """
    LLM-based task matcher that considers context (user roles and deployment environments).
    Falls back to rule-based matcher if LLM is unavailable.
    """

    def __init__(
        self,
        specs: List[OpenAPISpec],
        api_key: Optional[str] = None,
        use_llm: bool = True,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        fallback: bool = True,
    ):
        """
        Initialize the task matcher.

        Args:
            specs: List of OpenAPI specifications
            api_key: Anthropic API key (required if use_llm=True)
            use_llm: Whether to use LLM-based matching
            model: Claude model name
            max_tokens: Maximum tokens for response
            temperature: LLM temperature
            fallback: Whether to fall back to rule-based matching on error
        """
        self.specs = specs
        self.api_key = api_key
        self.use_llm = use_llm
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.fallback = fallback

        # Initialize LLM client if needed
        if use_llm and api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None

        # Initialize rule-based matcher for fallback
        if fallback:
            try:
                from src.openapi.matcher import TaskMatcher
                self.rule_based_matcher = TaskMatcher(specs)
            except Exception as e:
                logger.warning(f"Failed to initialize rule-based matcher: {e}")
                self.rule_based_matcher = None

    def match_task(self, task: IdentifiedTask) -> TaskMatchResult:
        """
        Match a task against OpenAPI endpoints with context awareness.

        Args:
            task: The task to match

        Returns:
            TaskMatchResult with context_match_matrix
        """
        # Check if LLM should be used
        if not self.use_llm or not self.client:
            logger.info(f"Using rule-based matching for task {task.name}")
            return self._fallback_match(task)

        try:
            # LLM-based matching
            logger.info(f"Using LLM-based matching for task {task.name}")
            return self._llm_match(task)

        except Exception as e:
            logger.error(f"LLM matching failed for task {task.name}: {e}")
            if self.fallback and self.rule_based_matcher:
                logger.info("Falling back to rule-based matching")
                return self._fallback_match(task)
            else:
                # Return empty result
                return TaskMatchResult(
                    task=task,
                    match_status="new",
                    matched_endpoints=[],
                    confidence_score=0.0,
                    missing_features=[f"LLM matching failed: {str(e)}"],
                    context_match_matrix={},
                    llm_based=False,
                    explanation=f"Matching failed: {str(e)}"
                )

    def _llm_match(self, task: IdentifiedTask) -> TaskMatchResult:
        """
        Perform LLM-based matching with context awareness.

        Args:
            task: The task to match

        Returns:
            TaskMatchResult
        """
        # Build prompt
        prompt = self._build_matching_prompt(task)

        # Call LLM
        response_text = self._call_llm(prompt)

        # Parse response
        result = self._parse_matching_response(response_text, task)

        return result

    def _fallback_match(self, task: IdentifiedTask) -> TaskMatchResult:
        """
        Fall back to rule-based matching.

        Args:
            task: The task to match

        Returns:
            TaskMatchResult (without context_match_matrix)
        """
        if self.rule_based_matcher:
            result = self.rule_based_matcher.match_task(task)
            # Ensure llm_based is False
            result.llm_based = False
            return result
        else:
            # Return empty result
            return TaskMatchResult(
                task=task,
                match_status="new",
                matched_endpoints=[],
                confidence_score=0.0,
                missing_features=["Rule-based matcher not available"],
                context_match_matrix={},
                llm_based=False
            )

    def _build_matching_prompt(self, task: IdentifiedTask) -> str:
        """
        Build prompt for context-aware matching.

        Args:
            task: The task to match

        Returns:
            Prompt string
        """
        # Format task context
        context_text = f"""- 역할: {', '.join(task.context.actor_roles)}
- 환경: {', '.join(task.context.deployment_envs)}"""

        if task.context.role_based_features:
            context_text += "\n- 역할별 기능:\n"
            for role, feature in task.context.role_based_features.items():
                context_text += f"  - {role}: {feature}\n"

        if task.context.env_based_features:
            context_text += "- 환경별 기능:\n"
            for env, feature in task.context.env_based_features.items():
                context_text += f"  - {env}: {feature}\n"

        # Format endpoints with context
        endpoints_text = self._format_endpoints_with_context()

        prompt = f"""당신은 API 설계 분석 전문가입니다. 태스크와 OpenAPI 엔드포인트를 비교하여 구현 상태를 판단하세요.

## 분석 대상 태스크
- 이름: {task.name}
- 설명: {task.description}
- 모듈: {task.module}
- 엔티티: {', '.join(task.entities) if task.entities else 'N/A'}

## 태스크 컨텍스트
{context_text}

## 기존 OpenAPI 엔드포인트
{endpoints_text}

## 매칭 기준

### 1. 역할별 매칭
태스크의 각 역할별 기능이 엔드포인트에 구현되어 있는지 확인:
- user 기능 → required_roles에 "user" 또는 "all" 포함된 엔드포인트
- admin 기능 → required_roles에 "admin" 또는 "all" 포함된 엔드포인트
- 기타 역할 유사

### 2. 환경별 매칭
태스크가 특정 환경을 명시했다면:
- development → deployment_env="development" 또는 "all"인 엔드포인트만 확인
- production → deployment_env="production" 또는 "all"인 엔드포인트만 확인
- all → 모든 환경 확인

### 3. 구현 상태
각 역할+환경 조합에 대해:
- "fully_implemented": 해당 역할+환경 조합의 모든 기능이 구현됨
- "partially_implemented": 일부만 구현됨
- "new": 구현 안 됨

### 4. 전체 상태
- match_status: "fully_implemented" (모든 역할/환경에서 완전 구현)
- match_status: "partially_implemented" (일부만 구현)
- match_status: "new" (전혀 구현 안 됨)

## 출력 (JSON)
{{
  "match_status": "partially_implemented",
  "confidence_score": 0.75,
  "context_match_matrix": {{
    "user": {{
      "development": "fully_implemented",
      "staging": "fully_implemented",
      "production": "fully_implemented"
    }},
    "admin": {{
      "development": "fully_implemented",
      "staging": "partially_implemented",
      "production": "new"
    }}
  }},
  "matched_endpoints": [
    {{
      "path": "/api/products",
      "method": "GET",
      "required_roles": ["user", "admin"],
      "deployment_env": "all",
      "reason": "user/admin 조회 기능과 일치"
    }}
  ],
  "missing_features": [
    "파트너 관리자용 상품 관리 API 없음",
    "관리자 등록 기능이 production 환경에 없음"
  ],
  "explanation": "조회 기능은 모든 환경에 구현되어 있으나, 등록/수정/삭제는 개발환경에만 존재."
}}

**주의사항**:
- 반드시 유효한 JSON만 출력
- context_match_matrix는 task.context의 모든 역할 x 환경 조합을 포함
- matched_endpoints는 실제로 매칭된 엔드포인트만 포함 (최대 10개)
"""
        return prompt

    def _format_endpoints_with_context(self) -> str:
        """
        Format all endpoints with their context information.

        Returns:
            Formatted endpoints string
        """
        lines = []
        for spec in self.specs:
            lines.append(f"\n### {spec.title} (v{spec.version}) - 환경: {spec.deployment_env}")
            for endpoint in spec.endpoints[:20]:  # Limit to 20 endpoints
                lines.append(
                    f"- {endpoint.method} {endpoint.path} "
                    f"[roles: {', '.join(endpoint.required_roles)}] "
                    f"[env: {endpoint.deployment_env}]"
                )
                if endpoint.summary:
                    lines.append(f"  Summary: {endpoint.summary}")

        return "\n".join(lines)

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

    def _parse_matching_response(self, response: str, task: IdentifiedTask) -> TaskMatchResult:
        """
        Parse LLM response into TaskMatchResult.

        Args:
            response: LLM response text (expected to be JSON)
            task: The original task

        Returns:
            TaskMatchResult

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

            # Extract matched endpoints
            matched_endpoints = []
            for ep_data in data.get("matched_endpoints", [])[:10]:  # Max 10
                # Find the actual endpoint object
                endpoint = self._find_endpoint(
                    ep_data.get("path"),
                    ep_data.get("method")
                )
                if endpoint:
                    matched_endpoints.append(endpoint)

            # Build result
            result = TaskMatchResult(
                task=task,
                match_status=data.get("match_status", "new"),
                matched_endpoints=matched_endpoints,
                confidence_score=float(data.get("confidence_score", 0.0)),
                missing_features=data.get("missing_features", []),
                context_match_matrix=data.get("context_match_matrix", {}),
                llm_based=True,
                explanation=data.get("explanation", "")
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise LLMCallError(f"JSON parsing error: {str(e)}")
        except Exception as e:
            raise LLMCallError(f"Failed to parse matching response: {str(e)}")

    def _find_endpoint(self, path: str, method: str) -> Optional[OpenAPIEndpoint]:
        """
        Find an endpoint by path and method.

        Args:
            path: Endpoint path
            method: HTTP method

        Returns:
            OpenAPIEndpoint or None
        """
        for spec in self.specs:
            for endpoint in spec.endpoints:
                if endpoint.path == path and endpoint.method.upper() == method.upper():
                    return endpoint
        return None
