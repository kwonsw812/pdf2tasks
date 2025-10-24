"""Prompts for Claude Vision API to analyze UI/UX design images."""

VISION_SYSTEM_PROMPT = """당신은 UI/UX 디자인 전문가이자 시니어 프론트엔드 개발자입니다.
기획서에 포함된 화면 설계 이미지를 분석하여 구현에 필요한 정보를 추출합니다.

당신의 역할:
1. 화면의 구조와 레이아웃을 이해
2. UI 컴포넌트를 식별하고 분류
3. 사용자 인터랙션 및 플로우 파악
4. 프론트엔드 구현에 필요한 세부사항 제공

기술 스택 컨텍스트:
- React/Next.js 기반 프론트엔드
- Material-UI 또는 Ant Design 컴포넌트 라이브러리
- RESTful API 통신
- 반응형 디자인 (모바일/데스크톱)
"""


def build_vision_analysis_prompt(context: str = "") -> str:
    """
    Build prompt for analyzing screen design image.

    Args:
        context: Additional context about the image (e.g., related section content)

    Returns:
        Formatted prompt string
    """
    prompt = """이 이미지는 기획서에 포함된 화면 설계입니다. 다음 정보를 JSON 형식으로 추출해주세요:

{
  "screen_title": "화면 이름 (예: '로그인 화면', '상품 목록', '대시보드')",
  "screen_type": "화면 유형 (login, dashboard, list, detail, form, modal, settings 중 하나)",
  "ui_components": [
    {
      "type": "컴포넌트 타입 (button, input, card, navigation, table, chart, dropdown, checkbox, radio, switch, tab, breadcrumb, pagination, search, filter, upload, modal, tooltip, badge, avatar, icon, image 등)",
      "label": "컴포넌트에 표시된 텍스트나 라벨 (있을 경우)",
      "position": "위치 (header, footer, sidebar, center, top-left, top-right, bottom-left, bottom-right 등)",
      "description": "컴포넌트의 역할과 기능 설명"
    }
  ],
  "layout_structure": "전체 레이아웃 구조 설명 (예: '헤더-사이드바-메인콘텐츠 구조', '2단 그리드 레이아웃', '모바일 단일 컬럼' 등)",
  "user_flow": "사용자가 이 화면에서 수행할 수 있는 주요 액션이나 플로우 (예: '로그인 → 대시보드 이동', '상품 검색 → 상세 페이지')",
  "confidence": 분석 신뢰도 (0-100, 숫자만)
}

중요 사항:
- 모든 텍스트는 한국어로 작성
- UI 컴포넌트는 가능한 모두 나열 (최소 5개 이상)
- 위치 정보는 일관성 있게 기술
- 컴포넌트 설명은 구현 관점에서 구체적으로 작성
- JSON 형식을 정확히 준수
- 코드 블록 없이 순수 JSON만 반환"""

    if context:
        prompt += f"\n\n추가 컨텍스트:\n{context[:500]}"  # Limit context to 500 chars

    return prompt


def build_batch_analysis_summary_prompt(analyses: list) -> str:
    """
    Build prompt for summarizing multiple screen analyses.

    Args:
        analyses: List of ImageAnalysis objects

    Returns:
        Formatted prompt string
    """
    screen_titles = [a.get("screen_title", "Unknown") for a in analyses]

    prompt = f"""다음 {len(analyses)}개의 화면 분석 결과를 요약해주세요:

화면 목록:
{', '.join(screen_titles)}

다음 항목을 포함하여 요약:
1. 전체 애플리케이션의 주요 기능 영역
2. 공통적으로 사용되는 UI 컴포넌트
3. 사용자 플로우 및 화면 간 연결 관계
4. 프론트엔드 구현 시 고려사항

200-300자로 요약해주세요."""

    return prompt


def estimate_vision_tokens(image_size_kb: int) -> int:
    """
    Estimate token usage for vision API call.

    Claude Vision uses approximately:
    - Base cost: ~85 tokens per image
    - Additional: ~6 tokens per 1000 pixels

    Args:
        image_size_kb: Image file size in KB

    Returns:
        Estimated token count
    """
    # Rough estimate based on image size
    # Assume 1KB ≈ 10 tokens for images
    base_tokens = 85
    size_tokens = image_size_kb * 10

    return base_tokens + size_tokens


def validate_vision_response(response: dict) -> bool:
    """
    Validate vision API response structure.

    Args:
        response: Parsed JSON response

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["screen_type", "ui_components", "layout_structure", "confidence"]

    # Check required fields
    for field in required_fields:
        if field not in response:
            return False

    # Validate ui_components structure
    if not isinstance(response["ui_components"], list):
        return False

    for component in response["ui_components"]:
        if not isinstance(component, dict):
            return False
        if "type" not in component or "description" not in component:
            return False

    # Validate confidence range
    confidence = response.get("confidence", -1)
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 100):
        return False

    return True
