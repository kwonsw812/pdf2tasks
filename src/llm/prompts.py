"""Prompt templates for LLM TaskWriter."""

from typing import List, Optional
from src.types.models import IdentifiedTask, Section, ImageAnalysis
from src.llm.exceptions import PromptBuildError
from src.llm.image_utils import format_task_related_images


SYSTEM_PROMPT = """당신은 시니어 풀스택 아키텍트입니다.

주어진 상위 기능(태스크)을 실제 구현 가능한 하위 개발 작업으로 세분화하는 것이 당신의 역할입니다.

**핵심 원칙:**
1. "어떻게" 구현할지가 아닌 "무엇을" 구현해야 하는지에 집중하세요.
2. 특정 프레임워크나 라이브러리를 강제하지 마세요.
3. 구현 AI가 최선의 기술 선택을 할 수 있도록 요구사항만 명확히 하세요.
4. 코드나 스키마를 직접 작성하지 말고, 필요한 데이터와 로직을 자연어로 설명하세요.

**지시사항:**
각 하위 태스크는 다음 항목을 포함해야 합니다:

- **목적:** 이 기능이 해결하는 문제 또는 제공하는 가치
- **API 스펙:** (백엔드 기능인 경우)
  - 엔드포인트 경로 (예: POST /api/auth/login)
  - 요청 데이터 (어떤 정보를 받아야 하는지)
  - 응답 데이터 (어떤 정보를 반환해야 하는지)
- **필요한 데이터:**
  - 저장해야 할 정보 (예: 사용자 이메일, 비밀번호)
  - 데이터 제약 조건 (예: 이메일 중복 불가, 비밀번호 최소 8자)
  - 관계 (예: 주문은 사용자에 속함)
- **로직 요약:**
  - 어떤 처리를 해야 하는지 (예: 이메일 중복 체크 → 비밀번호 해싱 → 사용자 생성)
  - 비즈니스 규칙 (예: 미성년자는 가입 불가)
- **UI 요구사항:** (프론트엔드 기능인 경우)
  - 필요한 UI 요소 (예: 이메일 입력 필드, 로그인 버튼)
  - 사용자 인터랙션 (예: 버튼 클릭 시 로그인 API 호출)
  - 사용자 흐름 (예: 입력 → 제출 → 성공 시 대시보드 이동)
- **보안 요구사항:**
  - 인증 필요 여부 (예: 로그인한 사용자만 접근 가능)
  - 권한 체크 (예: 관리자만 접근 가능)
  - 민감 데이터 처리 (예: 비밀번호는 암호화 저장)
- **예외 상황:**
  - 어떤 경우 실패하는지 (예: 이메일 중복, 잘못된 비밀번호)
  - 사용자에게 어떤 메시지를 보여야 하는지
- **테스트 시나리오:**
  - 정상 케이스 (예: 올바른 정보로 가입 성공)
  - 예외 케이스 (예: 중복 이메일로 가입 실패)

**출력 형식 (Markdown):**

```markdown
## {index}.1 {하위 태스크명}
- **목적:** {이 기능이 해결하는 문제}
- **API 스펙:** (백엔드 기능인 경우)
  - 엔드포인트: POST /api/...
  - 요청: {필요한 입력 데이터}
  - 응답: {반환할 데이터}
- **필요한 데이터:**
  - {저장할 정보 1} (제약: {조건})
  - {저장할 정보 2} (제약: {조건})
- **로직 요약:**
  - {처리 단계 1}
  - {처리 단계 2}
  - {처리 단계 3}
- **UI 요구사항:** (프론트엔드 기능인 경우)
  - {UI 요소 1}: {역할}
  - {UI 요소 2}: {역할}
  - 사용자 흐름: {인터랙션 설명}
- **보안 요구사항:**
  - {인증/권한 요구사항}
- **예외 상황:**
  - {실패 케이스 1}: {에러 메시지}
  - {실패 케이스 2}: {에러 메시지}
- **테스트 시나리오:**
  - {정상 케이스}
  - {예외 케이스}
- **참고 이미지:** {이미지 경로} (화면 설계가 있는 경우)

## {index}.2 {하위 태스크명}
...
```

**프론트엔드 태스크 작성 시:**
- 화면 설계 이미지가 있다면 UI 요소를 모두 나열하세요.
- 사용자가 어떻게 상호작용하는지 명확히 하세요.
- 백엔드 API와의 연동 포인트를 명시하세요.

**중요 주의사항:**
- ❌ 특정 프레임워크 코드를 작성하지 마세요 (예: Prisma 스키마, NestJS 데코레이터)
- ❌ 구현 방법을 지시하지 마세요 (예: "Service 레이어에서 처리")
- ✅ 요구사항과 제약조건만 명확히 하세요
- ✅ 구현 AI가 기술 스택을 자유롭게 선택할 수 있게 하세요
- 하위 태스크 인덱스는 {상위 태스크 인덱스}.1, {상위 태스크 인덱스}.2 형식으로 작성
- 가정이 필요한 경우 명시적으로 표기
"""


def build_task_writer_prompt(
    task: IdentifiedTask,
    sections: List[Section],
    image_analyses: Optional[List[ImageAnalysis]] = None
) -> str:
    """
    Build TaskWriter prompt from identified task and related sections.

    Args:
        task: Identified high-level task
        sections: List of all sections from preprocessor
        image_analyses: Optional list of image analysis results

    Returns:
        Complete prompt string

    Raises:
        PromptBuildError: If prompt generation fails
    """
    try:
        prompt = SYSTEM_PROMPT + "\n\n"
        prompt += "=" * 80 + "\n"
        prompt += "## 분석 대상 상위 태스크\n\n"
        prompt += f"**상위 태스크 {task.index}: {task.name}**\n\n"
        prompt += f"**설명:** {task.description}\n\n"
        prompt += f"**모듈/영역:** {task.module}\n\n"

        if task.entities:
            prompt += f"**관련 엔티티:** {', '.join(task.entities)}\n\n"

        if task.prerequisites:
            prompt += f"**선행 조건:** {', '.join(task.prerequisites)}\n\n"

        prompt += "=" * 80 + "\n"
        prompt += "## 관련 섹션 내용\n\n"

        if not task.related_sections:
            prompt += "(관련 섹션 정보 없음)\n\n"
        else:
            for section_idx in task.related_sections:
                if 0 <= section_idx < len(sections):
                    section = sections[section_idx]
                    prompt += f"### [{section.title}]\n\n"
                    # Limit section content to prevent token overflow
                    content = section.content
                    if len(content) > 2000:
                        content = content[:2000] + "\n...(내용 생략)"
                    prompt += f"{content}\n\n"
                    prompt += f"**(페이지: {section.page_range.start}-{section.page_range.end})**\n\n"
                else:
                    prompt += f"(섹션 인덱스 {section_idx}는 범위를 벗어남)\n\n"

        # Add related screen design images
        if image_analyses:
            image_section = format_task_related_images(
                task.related_sections,
                sections,
                image_analyses,
                max_images=3
            )
            if image_section:
                prompt += image_section

        prompt += "=" * 80 + "\n"
        prompt += "## 요청 사항\n\n"
        prompt += f"위의 상위 태스크 '{task.name}'를 실제 구현 가능한 하위 개발 작업으로 세분화하세요.\n"
        prompt += "하위 태스크 인덱스는 반드시 {}.1, {}.2, ... 형식으로 작성하세요.\n\n".format(
            task.index, task.index
        )

        if image_analyses and any(
            0 <= idx < len(sections) for idx in task.related_sections
        ):
            prompt += "**화면 설계 이미지가 포함된 경우:**\n"
            prompt += "- UI 컴포넌트 섹션을 반드시 포함하세요.\n"
            prompt += "- 각 컴포넌트의 타입, 레이블, 위치를 명시하세요.\n"
            prompt += "- 사용자 흐름을 구체적으로 작성하세요.\n"
            prompt += "- 참고 이미지 경로를 포함하세요.\n\n"

        prompt += "**출력 (Markdown):**\n"

        return prompt

    except Exception as e:
        raise PromptBuildError(f"Failed to build TaskWriter prompt: {str(e)}") from e


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for given text.
    Uses simple approximation: ~4 characters per token.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    return len(text) // 4


def truncate_section_content(content: str, max_tokens: int = 500) -> str:
    """
    Truncate section content to fit within token limit.

    Args:
        content: Section content
        max_tokens: Maximum token count

    Returns:
        Truncated content
    """
    max_chars = max_tokens * 4  # Approximate conversion
    if len(content) <= max_chars:
        return content

    return content[:max_chars] + "\n\n...(내용이 너무 길어 생략됨)"
