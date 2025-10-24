"""Prompt templates for LLM Planner."""

from typing import List, Optional
from ...types.models import Section, FunctionalGroup, ImageAnalysis
from ..image_utils import (
    map_images_to_sections,
    format_section_with_images,
    get_image_summary,
)


SYSTEM_PROMPT = """당신은 시니어 풀스택 아키텍트입니다.

당신의 역할은 주어진 기획서 섹션들을 분석하여 백엔드와 프론트엔드 개발 관점에서 상위 기능(태스크)을 식별하고 분류하는 것입니다.

기술 스택:
- 백엔드: Python (FastAPI, Flask 등)
- 프론트엔드: React, Vue.js 등
- 데이터베이스: ORM (SQLAlchemy, Django ORM 등)
- 아키텍처: RESTful API, 마이크로서비스

지시사항:
1. 각 상위 기능은 독립적인 모듈 또는 도메인으로 구성됩니다.
2. 관련된 섹션들을 하나의 상위 기능으로 그룹화하세요.
3. **화면 설계 이미지가 포함된 경우**, 해당 화면에 대한 프론트엔드 태스크를 명확히 식별하세요.
   - UI 컴포넌트와 사용자 흐름을 기반으로 프론트엔드 기능을 정의하세요.
   - 백엔드 API와의 연동이 필요한 부분을 고려하세요.
4. 각 태스크에 대해 다음 정보를 제공하세요:
   - name: 태스크 이름 (예: "로그인 화면 구현", "인증 API", "결제 시스템")
   - description: 태스크에 대한 간단한 설명 (1-2문장), UI가 있으면 화면 정보 포함
   - module: Python 모듈/패키지 이름 또는 프론트엔드 컴포넌트 경로 (예: "auth", "components/login")
   - entities: 관련 데이터 모델 이름들 (예: ["User", "Session"])
   - prerequisites: 선행 조건 (예: ["인증 모듈이 먼저 구현되어야 함"])
   - related_sections: 관련 섹션의 인덱스 (1부터 시작)
5. 가정이 필요한 경우 description에 명시하세요.
6. 우선순위가 높은 태스크를 먼저 나열하세요 (인증, 기본 데이터 모델 등).

출력 형식:
반드시 유효한 JSON 형식으로 응답하세요. 다른 텍스트는 포함하지 마세요.

{
  "tasks": [
    {
      "index": 1,
      "name": "인증 및 회원관리",
      "description": "사용자 인증, 로그인, 회원가입 등의 기능을 제공합니다.",
      "module": "auth",
      "entities": ["User", "Session"],
      "prerequisites": [],
      "related_sections": [1, 2, 3]
    },
    {
      "index": 2,
      "name": "결제 시스템",
      "description": "결제 처리 및 결제 내역 관리 기능을 제공합니다.",
      "module": "payment",
      "entities": ["Payment", "PaymentMethod"],
      "prerequisites": ["인증 모듈이 먼저 구현되어야 함"],
      "related_sections": [4, 5]
    }
  ]
}
"""


DEPENDENCY_ANALYSIS_SYSTEM_PROMPT = """당신은 시니어 백엔드 아키텍트입니다.

주어진 태스크 목록을 분석하여 각 태스크 간의 의존성과 우선순위를 결정하세요.

지시사항:
1. 각 태스크의 선행 조건(prerequisites)을 분석하세요.
2. 일반적인 백엔드 개발 순서를 고려하세요:
   - 인증/권한 → 핵심 비즈니스 로직 → 부가 기능
   - 데이터 모델 → API 엔드포인트 → 통합
3. 순환 의존성이 없도록 주의하세요.
4. prerequisites 필드를 업데이트하여 의존성을 명확히 하세요.

출력 형식:
반드시 유효한 JSON 형식으로 응답하세요.

{
  "tasks": [
    {
      "index": 1,
      "name": "...",
      "description": "...",
      "module": "...",
      "entities": [...],
      "prerequisites": ["태스크 2가 먼저 완료되어야 함"],
      "related_sections": [...]
    }
  ]
}
"""


def build_task_identification_prompt(
    sections: List[Section],
    image_analyses: Optional[List[ImageAnalysis]] = None
) -> str:
    """
    Build a prompt for task identification from sections.

    Args:
        sections: List of document sections
        image_analyses: Optional list of image analysis results

    Returns:
        Formatted prompt string
    """
    # Map images to sections if available
    section_images = {}
    if image_analyses:
        section_images = map_images_to_sections(sections, image_analyses)

    prompt = "다음은 기획서에서 추출한 섹션들입니다"
    if image_analyses:
        image_summary = get_image_summary(image_analyses)
        prompt += f" (화면 설계 이미지 포함: {image_summary})"
    prompt += ":\n\n"

    for idx, section in enumerate(sections, start=1):
        related_images = section_images.get(idx - 1, [])

        if related_images:
            # Use enhanced formatting with images
            prompt += format_section_with_images(
                section,
                idx - 1,
                related_images,
                max_components=8
            )
        else:
            # Original format without images
            content = section.content
            if len(content) > 500:
                content = content[:500] + "..."

            prompt += f"## 섹션 {idx}: {section.title}\n"
            prompt += f"**(페이지 {section.page_range.start}-{section.page_range.end}, 레벨 {section.level})**\n\n"
            prompt += f"{content}\n"

        prompt += "\n"

    prompt += "\n" + "=" * 80 + "\n"
    prompt += "위 섹션들을 분석하여 백엔드 및 프론트엔드 상위 태스크들을 식별하고 JSON 형식으로 출력하세요.\n"

    if image_analyses:
        prompt += "\n**특히 화면 설계 이미지가 포함된 섹션의 경우:**\n"
        prompt += "- UI 컴포넌트와 사용자 흐름을 고려하여 프론트엔드 태스크를 명확히 정의하세요.\n"
        prompt += "- 백엔드 API와의 연동이 필요한 부분을 파악하세요.\n"
        prompt += "- 화면별로 독립적인 태스크로 분리할지, 관련 화면을 하나의 태스크로 묶을지 판단하세요.\n"

    return prompt


def build_task_identification_prompt_from_groups(
    functional_groups: List[FunctionalGroup],
) -> str:
    """
    Build a prompt for task identification from functional groups.

    Args:
        functional_groups: List of functional groups

    Returns:
        Formatted prompt string
    """
    prompt = "다음은 기획서에서 추출하여 그룹화한 기능 그룹들입니다:\n\n"

    section_idx = 1
    for group in functional_groups:
        prompt += f"[기능 그룹: {group.name}]\n"
        if group.keywords:
            prompt += f"키워드: {', '.join(group.keywords)}\n"
        prompt += "\n"

        for section in group.sections:
            # Truncate content if too long
            content = section.content
            if len(content) > 500:
                content = content[:500] + "..."

            prompt += f"  [섹션 {section_idx}] {section.title}\n"
            prompt += f"  레벨: {section.level}\n"
            prompt += f"  내용: {content}\n"
            prompt += f"  페이지: {section.page_range.start}-{section.page_range.end}\n"
            prompt += "\n"

            section_idx += 1

        prompt += "\n"

    prompt += "\n위 기능 그룹들을 분석하여 백엔드 상위 태스크들을 식별하고 JSON 형식으로 출력하세요."

    return prompt


def build_dependency_analysis_prompt(task_names: List[str]) -> str:
    """
    Build a prompt for dependency analysis.

    Args:
        task_names: List of task names

    Returns:
        Formatted prompt string
    """
    prompt = "다음 태스크들의 의존성을 분석하세요:\n\n"

    for idx, name in enumerate(task_names, start=1):
        prompt += f"{idx}. {name}\n"

    prompt += (
        "\n각 태스크의 선행 조건을 분석하여 prerequisites 필드를 업데이트하고 "
        "JSON 형식으로 출력하세요."
    )

    return prompt
