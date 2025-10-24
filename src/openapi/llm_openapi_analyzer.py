"""LLM-based OpenAPI specification analyzer for role and environment extraction."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List
from anthropic import Anthropic

from src.llm.exceptions import LLMCallError

logger = logging.getLogger(__name__)


class LLMOpenAPIAnalyzer:
    """
    LLM-based analyzer for extracting user roles and deployment environments
    from OpenAPI specifications.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ):
        """
        Initialize the OpenAPI analyzer.

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

    def analyze_endpoint(self, endpoint_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single endpoint to extract required user roles.

        Args:
            endpoint_spec: Endpoint specification dict with keys:
                - path: str (e.g., "/api/products")
                - method: str (e.g., "GET")
                - summary: Optional[str]
                - description: Optional[str]
                - security: Optional[List] (OpenAPI security requirements)

        Returns:
            Dict with:
                - required_roles: List[str] (e.g., ["admin"])
                - explanation: str
        """
        logger.info(f"Analyzing endpoint: {endpoint_spec.get('method', 'UNKNOWN')} {endpoint_spec.get('path', 'UNKNOWN')}")

        # Build prompt
        prompt = self._build_role_extraction_prompt(endpoint_spec)

        # Call LLM
        try:
            response_text = self._call_llm(prompt)
            result = self._parse_role_response(response_text)
            logger.info(f"Roles extracted: {result['required_roles']}")
            return result
        except Exception as e:
            logger.error(f"Failed to analyze endpoint: {e}")
            # Fallback: all roles
            return {
                "required_roles": ["all"],
                "explanation": f"LLM analysis failed: {str(e)}"
            }

    def extract_deployment_env(self, file_path: Path) -> str:
        """
        Extract deployment environment from OpenAPI file path.

        Uses pattern matching on the filename:
            - "dev", "local" → "development"
            - "staging", "qa", "test" → "staging"
            - "prod", "production" → "production"
            - Otherwise → "all"

        Args:
            file_path: Path to OpenAPI spec file

        Returns:
            Deployment environment string
        """
        filename = file_path.stem.lower()  # Get filename without extension

        if re.search(r"(dev|local)", filename):
            return "development"
        elif re.search(r"(staging|qa|test)", filename):
            return "staging"
        elif re.search(r"(prod|production)", filename):
            return "production"
        else:
            return "all"

    def _build_role_extraction_prompt(self, endpoint_spec: Dict) -> str:
        """
        Build prompt for role extraction.

        Args:
            endpoint_spec: Endpoint specification

        Returns:
            Prompt string
        """
        path = endpoint_spec.get("path", "N/A")
        method = endpoint_spec.get("method", "N/A")
        summary = endpoint_spec.get("summary", "N/A")
        description = endpoint_spec.get("description", "N/A")
        security = endpoint_spec.get("security", [])

        # Format security for readability
        security_text = "None"
        if security:
            security_text = json.dumps(security, indent=2, ensure_ascii=False)

        prompt = f"""당신은 OpenAPI 스펙 분석 전문가입니다. 다음 엔드포인트의 사용자 역할을 추출하세요.

## 엔드포인트 정보
- Path: {path}
- Method: {method}
- Summary: {summary}
- Description: {description}
- Security: {security_text}

## 역할 추출 규칙

### 1. security 스키마 분석
security:
  - bearerAuth: [admin] → admin 역할 필요
  - bearerAuth: [user, admin] → user 또는 admin
  - bearerAuth: [] → 인증만 필요 (역할 무관 → all)
  - 없음 → 인증 불필요 (public → all)

### 2. 경로 패턴 분석
- /api/admin/* → admin
- /api/partner/* → partner_admin
- /api/user/* → user
- /api/public/* → all (인증 불필요)

### 3. 설명 분석
- "관리자 전용", "admin only" → admin
- "파트너 관리자" → partner_admin
- 명시 없음 → all

### 4. HTTP 메서드 추론 (보조)
- GET (조회): 일반적으로 user 이상
- POST/PUT/DELETE (변경): 일반적으로 admin
- 단, 위 1-3 규칙이 우선

## 출력 (JSON)
{{
  "required_roles": ["admin"],
  "explanation": "security 스키마에 [admin] 명시됨"
}}

**주의사항**:
- 반드시 유효한 JSON만 출력 (설명 금지)
- 역할은 ["user", "admin", "partner_admin", "super_admin", "all"] 중 선택
- 명시되지 않았거나 모든 역할 가능하면 ["all"]
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

    def _parse_role_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into role result.

        Args:
            response: LLM response text (expected to be JSON)

        Returns:
            Dict with required_roles and explanation

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

            # Validate
            if "required_roles" not in data:
                raise LLMCallError("Missing 'required_roles' in response")

            return {
                "required_roles": data["required_roles"],
                "explanation": data.get("explanation", "")
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise LLMCallError(f"JSON parsing error: {str(e)}")
        except Exception as e:
            raise LLMCallError(f"Failed to parse role response: {str(e)}")
