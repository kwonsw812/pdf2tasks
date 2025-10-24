#!/usr/bin/env python3
"""Test script for image analysis integration with LLM Planner and TaskWriter."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.types.models import (
    Section,
    PageRange,
    ImageAnalysis,
    UIComponent,
    TokenUsage,
    IdentifiedTask,
)
from src.llm.image_utils import (
    find_related_images,
    map_images_to_sections,
    format_ui_component,
    format_image_analysis_for_prompt,
    format_section_with_images,
    format_task_related_images,
    get_image_summary,
)


def create_mock_sections():
    """Create mock sections for testing."""
    sections = [
        Section(
            title="로그인 화면",
            level=2,
            content="사용자 인증을 위한 로그인 화면입니다. 이메일과 비밀번호를 입력하여 로그인할 수 있습니다.",
            page_range=PageRange(start=5, end=7),
            subsections=[],
        ),
        Section(
            title="대시보드",
            level=2,
            content="메인 대시보드 화면입니다. 통계 카드와 차트가 표시됩니다.",
            page_range=PageRange(start=10, end=12),
            subsections=[],
        ),
        Section(
            title="상품 목록",
            level=2,
            content="상품 목록을 표시하는 화면입니다. 검색과 필터 기능이 있습니다.",
            page_range=PageRange(start=15, end=18),
            subsections=[],
        ),
    ]
    return sections


def create_mock_image_analyses():
    """Create mock image analysis results."""
    analyses = [
        ImageAnalysis(
            image_path="./images/page_5_img_1.png",
            page_number=5,
            screen_title="로그인 화면",
            screen_type="login",
            ui_components=[
                UIComponent(
                    type="input",
                    label="이메일",
                    position="center",
                    description="이메일 입력 필드 (type=email, required, placeholder='이메일을 입력하세요')",
                ),
                UIComponent(
                    type="input",
                    label="비밀번호",
                    position="center",
                    description="비밀번호 입력 필드 (type=password, required)",
                ),
                UIComponent(
                    type="button",
                    label="로그인",
                    position="center",
                    description="로그인 제출 버튼 (primary button)",
                ),
                UIComponent(
                    type="button",
                    label="Google로 로그인",
                    position="center",
                    description="소셜 로그인 버튼 (OAuth)",
                ),
                UIComponent(
                    type="button",
                    label="Kakao로 로그인",
                    position="center",
                    description="소셜 로그인 버튼 (OAuth)",
                ),
                UIComponent(
                    type="link",
                    label="비밀번호 찾기",
                    position="bottom",
                    description="비밀번호 찾기 링크",
                ),
            ],
            layout_structure="중앙 정렬 카드, 최대 너비 400px, 그림자 효과",
            user_flow="이메일/비밀번호 입력 → 로그인 버튼 클릭 → 성공 시 대시보드로 리다이렉트, 실패 시 에러 메시지 표시",
            confidence=92.5,
            processing_time=2.3,
            token_usage=TokenUsage(input_tokens=1500, output_tokens=800, total_tokens=2300),
        ),
        ImageAnalysis(
            image_path="./images/page_10_img_1.png",
            page_number=10,
            screen_title="대시보드",
            screen_type="dashboard",
            ui_components=[
                UIComponent(
                    type="navigation",
                    label="사이드바 메뉴",
                    position="left",
                    description="왼쪽 고정 사이드바 네비게이션 (홈, 상품, 주문, 설정)",
                ),
                UIComponent(
                    type="card",
                    label="총 매출",
                    position="top-left",
                    description="통계 카드 - 총 매출 금액 표시",
                ),
                UIComponent(
                    type="card",
                    label="주문 수",
                    position="top-center",
                    description="통계 카드 - 총 주문 수 표시",
                ),
                UIComponent(
                    type="card",
                    label="방문자 수",
                    position="top-right",
                    description="통계 카드 - 총 방문자 수 표시",
                ),
                UIComponent(
                    type="chart",
                    label="매출 차트",
                    position="center",
                    description="라인 차트 - 일별 매출 추이 표시",
                ),
            ],
            layout_structure="그리드 레이아웃 (3열 카드 + 전체 너비 차트)",
            user_flow="대시보드 진입 → 실시간 데이터 로딩 → 차트 인터랙션 (날짜 범위 선택)",
            confidence=88.0,
            processing_time=2.1,
            token_usage=TokenUsage(input_tokens=1400, output_tokens=750, total_tokens=2150),
        ),
        ImageAnalysis(
            image_path="./images/page_16_img_1.png",
            page_number=16,
            screen_title="상품 목록",
            screen_type="list",
            ui_components=[
                UIComponent(
                    type="input",
                    label="검색",
                    position="top",
                    description="검색 입력 필드 (placeholder='상품명 또는 카테고리 검색')",
                ),
                UIComponent(
                    type="dropdown",
                    label="카테고리 필터",
                    position="top",
                    description="카테고리 선택 드롭다운 (전체, 전자제품, 의류 등)",
                ),
                UIComponent(
                    type="card",
                    label="상품 카드",
                    position="grid",
                    description="상품 카드 (이미지, 이름, 가격, 재고 표시)",
                ),
                UIComponent(
                    type="pagination",
                    label="페이지네이션",
                    position="bottom",
                    description="페이지 네비게이션 (1, 2, 3, ... 10)",
                ),
            ],
            layout_structure="검색/필터 영역 + 그리드 상품 카드 (4열) + 페이지네이션",
            user_flow="검색어 입력 → 필터 선택 → 상품 카드 클릭 → 상세 페이지 이동",
            confidence=90.0,
            processing_time=2.5,
            token_usage=TokenUsage(input_tokens=1600, output_tokens=900, total_tokens=2500),
        ),
    ]
    return analyses


def test_find_related_images():
    """Test finding images related to a page range."""
    print("=" * 80)
    print("TEST 1: find_related_images")
    print("=" * 80)

    page_range = PageRange(start=5, end=7)
    images = create_mock_image_analyses()

    related = find_related_images(page_range, images)

    print(f"Page range: {page_range.start}-{page_range.end}")
    print(f"Found {len(related)} related image(s):")
    for img in related:
        print(f"  - Page {img.page_number}: {img.screen_title} ({img.screen_type})")

    assert len(related) == 1
    assert related[0].page_number == 5
    print("✓ PASSED\n")


def test_map_images_to_sections():
    """Test mapping images to sections."""
    print("=" * 80)
    print("TEST 2: map_images_to_sections")
    print("=" * 80)

    sections = create_mock_sections()
    images = create_mock_image_analyses()

    section_images = map_images_to_sections(sections, images)

    print(f"Mapped {len(section_images)} section(s) with images:")
    for idx, imgs in section_images.items():
        print(f"  Section {idx} ({sections[idx].title}): {len(imgs)} image(s)")
        for img in imgs:
            print(f"    - Page {img.page_number}: {img.screen_title}")

    assert 0 in section_images  # Login screen
    assert 1 in section_images  # Dashboard
    assert 2 in section_images  # Product list
    print("✓ PASSED\n")


def test_format_ui_component():
    """Test UI component formatting."""
    print("=" * 80)
    print("TEST 3: format_ui_component")
    print("=" * 80)

    component = UIComponent(
        type="button",
        label="로그인",
        position="center",
        description="로그인 제출 버튼",
    )

    formatted = format_ui_component(component)
    print(f"Formatted component:\n{formatted}")

    assert "button" in formatted
    assert "로그인" in formatted
    assert "center" in formatted
    print("✓ PASSED\n")


def test_format_image_analysis():
    """Test image analysis formatting for prompt."""
    print("=" * 80)
    print("TEST 4: format_image_analysis_for_prompt")
    print("=" * 80)

    images = create_mock_image_analyses()
    analysis = images[0]  # Login screen

    formatted = format_image_analysis_for_prompt(analysis, include_components=True, max_components=5)
    print(formatted)
    print()

    assert "로그인 화면" in formatted
    assert "login" in formatted
    assert "UI 컴포넌트" in formatted
    assert "레이아웃" in formatted
    assert "사용자 흐름" in formatted
    print("✓ PASSED\n")


def test_format_section_with_images():
    """Test section formatting with images."""
    print("=" * 80)
    print("TEST 5: format_section_with_images")
    print("=" * 80)

    sections = create_mock_sections()
    images = create_mock_image_analyses()

    section = sections[0]  # Login screen
    related_images = [images[0]]

    formatted = format_section_with_images(section, 0, related_images, max_components=10)
    print(formatted)
    print()

    assert "섹션 1" in formatted
    assert "로그인 화면" in formatted
    assert "관련 화면 설계" in formatted
    assert "UI 컴포넌트" in formatted
    print("✓ PASSED\n")


def test_format_task_related_images():
    """Test formatting task-related images."""
    print("=" * 80)
    print("TEST 6: format_task_related_images")
    print("=" * 80)

    sections = create_mock_sections()
    images = create_mock_image_analyses()

    # Task related to sections 0 and 1 (Login and Dashboard)
    task_related_sections = [0, 1]

    formatted = format_task_related_images(
        task_related_sections,
        sections,
        images,
        max_images=3
    )
    print(formatted)
    print()

    assert "관련 화면 설계" in formatted
    assert "로그인 화면" in formatted
    assert "대시보드" in formatted
    print("✓ PASSED\n")


def test_get_image_summary():
    """Test image summary generation."""
    print("=" * 80)
    print("TEST 7: get_image_summary")
    print("=" * 80)

    images = create_mock_image_analyses()
    summary = get_image_summary(images)

    print(f"Image summary: {summary}")

    assert "3개 화면" in summary
    assert "login" in summary
    assert "dashboard" in summary
    assert "list" in summary
    print("✓ PASSED\n")


def test_integration_with_planner_prompt():
    """Test integration with LLM Planner prompt building."""
    print("=" * 80)
    print("TEST 8: Integration with LLM Planner prompt")
    print("=" * 80)

    from src.llm.planner.prompts import build_task_identification_prompt

    sections = create_mock_sections()
    images = create_mock_image_analyses()

    # Without images
    prompt_without = build_task_identification_prompt(sections)
    print("Prompt length without images:", len(prompt_without))

    # With images
    prompt_with = build_task_identification_prompt(sections, images)
    print("Prompt length with images:", len(prompt_with))

    print(f"\nSample of prompt with images:\n{'-' * 80}")
    print(prompt_with[:2000])
    print(f"{'-' * 80}\n")

    assert len(prompt_with) > len(prompt_without)
    assert "화면 설계 이미지 포함" in prompt_with
    assert "UI 컴포넌트" in prompt_with
    print("✓ PASSED\n")


def test_integration_with_taskwriter_prompt():
    """Test integration with TaskWriter prompt building."""
    print("=" * 80)
    print("TEST 9: Integration with TaskWriter prompt")
    print("=" * 80)

    from src.llm.prompts import build_task_writer_prompt

    sections = create_mock_sections()
    images = create_mock_image_analyses()

    task = IdentifiedTask(
        index=1,
        name="로그인 및 인증 시스템",
        description="사용자 로그인 및 인증 기능 구현",
        module="auth",
        entities=["User", "Session"],
        prerequisites=[],
        related_sections=[0],  # Login screen section
    )

    # Without images
    prompt_without = build_task_writer_prompt(task, sections)
    print("Prompt length without images:", len(prompt_without))

    # With images
    prompt_with = build_task_writer_prompt(task, sections, images)
    print("Prompt length with images:", len(prompt_with))

    print(f"\nSample of prompt with images:\n{'-' * 80}")
    print(prompt_with[-1500:])  # Show end of prompt
    print(f"{'-' * 80}\n")

    assert len(prompt_with) > len(prompt_without)
    assert "관련 화면 설계" in prompt_with
    assert "로그인 화면" in prompt_with
    assert "UI 컴포넌트" in prompt_with
    print("✓ PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("IMAGE INTEGRATION TESTS")
    print("=" * 80 + "\n")

    tests = [
        test_find_related_images,
        test_map_images_to_sections,
        test_format_ui_component,
        test_format_image_analysis,
        test_format_section_with_images,
        test_format_task_related_images,
        test_get_image_summary,
        test_integration_with_planner_prompt,
        test_integration_with_taskwriter_prompt,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 80)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
