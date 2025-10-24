#!/usr/bin/env python3
"""
Example: Using Image Analysis with LLM Planner and TaskWriter

This example demonstrates how to integrate image analysis results
into the LLM task identification and writing process.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.types.models import (
    Section,
    PageRange,
    ImageAnalysis,
    UIComponent,
    TokenUsage,
    IdentifiedTask,
    FunctionalGroup,
)
from src.llm.planner.llm_planner import LLMPlanner
from src.llm.task_writer import LLMTaskWriter


def create_sample_sections_and_images():
    """Create sample sections and image analyses for demonstration."""
    # Sample sections from a hypothetical e-commerce spec
    sections = [
        Section(
            title="사용자 인증",
            level=2,
            content="""
            사용자는 이메일과 비밀번호를 사용하여 로그인할 수 있습니다.
            소셜 로그인(Google, Kakao)도 지원합니다.
            로그인 실패 시 명확한 에러 메시지를 표시합니다.
            """,
            page_range=PageRange(start=5, end=7),
            subsections=[],
        ),
        Section(
            title="대시보드",
            level=2,
            content="""
            메인 대시보드는 다음 정보를 표시합니다:
            - 총 매출액 (금액, 전일 대비 증감)
            - 주문 건수
            - 방문자 수
            - 매출 추이 차트 (최근 7일)
            """,
            page_range=PageRange(start=10, end=12),
            subsections=[],
        ),
    ]

    # Sample image analyses
    images = [
        ImageAnalysis(
            image_path="./images/page_5_login.png",
            page_number=5,
            screen_title="로그인 화면",
            screen_type="login",
            ui_components=[
                UIComponent(
                    type="input",
                    label="이메일",
                    position="center",
                    description="이메일 입력 (type=email, required)",
                ),
                UIComponent(
                    type="input",
                    label="비밀번호",
                    position="center",
                    description="비밀번호 입력 (type=password, required)",
                ),
                UIComponent(
                    type="button",
                    label="로그인",
                    position="center",
                    description="로그인 제출 버튼",
                ),
                UIComponent(
                    type="button",
                    label="Google로 로그인",
                    position="center",
                    description="Google OAuth 로그인",
                ),
            ],
            layout_structure="중앙 정렬 카드",
            user_flow="로그인 → 성공 시 대시보드, 실패 시 에러 표시",
            confidence=90.0,
            processing_time=2.0,
            token_usage=TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
        ),
        ImageAnalysis(
            image_path="./images/page_10_dashboard.png",
            page_number=10,
            screen_title="대시보드",
            screen_type="dashboard",
            ui_components=[
                UIComponent(
                    type="card",
                    label="총 매출",
                    position="top-left",
                    description="매출액 통계 카드",
                ),
                UIComponent(
                    type="card",
                    label="주문 수",
                    position="top-center",
                    description="주문 건수 통계 카드",
                ),
                UIComponent(
                    type="chart",
                    label="매출 차트",
                    position="center",
                    description="일별 매출 라인 차트",
                ),
            ],
            layout_structure="그리드 레이아웃 (3열 카드 + 차트)",
            user_flow="대시보드 로딩 → 실시간 데이터 표시",
            confidence=85.0,
            processing_time=2.5,
            token_usage=TokenUsage(input_tokens=1200, output_tokens=600, total_tokens=1800),
        ),
    ]

    return sections, images


def example1_planner_with_images():
    """Example 1: Use LLM Planner with image analysis."""
    print("=" * 80)
    print("Example 1: LLM Planner with Image Analysis")
    print("=" * 80)
    print()

    sections, images = create_sample_sections_and_images()

    print("This example shows how to identify tasks using both sections and images.")
    print("The LLM will see:")
    print(f"  - {len(sections)} sections with text content")
    print(f"  - {len(images)} screen design images with UI components")
    print()

    # Note: This would require a real API key to run
    print("Code example:")
    print("""
    planner = LLMPlanner(api_key="your-api-key")

    result = planner.identify_tasks_from_sections(
        sections=sections,
        image_analyses=images  # Include image information
    )

    # The LLM will see UI components and screen flows
    # This helps identify frontend-specific tasks more accurately
    """)
    print()


def example2_taskwriter_with_images():
    """Example 2: Use TaskWriter with image analysis."""
    print("=" * 80)
    print("Example 2: TaskWriter with Image Analysis")
    print("=" * 80)
    print()

    sections, images = create_sample_sections_and_images()

    # Create a mock task
    task = IdentifiedTask(
        index=1,
        name="로그인 화면 구현",
        description="사용자 로그인 UI 및 인증 API 구현",
        module="auth",
        entities=["User", "Session"],
        prerequisites=[],
        related_sections=[0],  # References the login section
    )

    print("This example shows how TaskWriter generates sub-tasks with UI details.")
    print(f"Task: {task.name}")
    print(f"Related images: {len([img for img in images if img.page_number in range(5, 8)])} image(s)")
    print()

    print("Code example:")
    print("""
    task_writer = LLMTaskWriter(api_key="your-api-key")

    result = task_writer.write_task(
        task=task,
        sections=sections,
        image_analyses=images  # Include image information
    )

    # The generated markdown will include:
    # - UI Component sections with specific component details
    # - Layout structure information
    # - User flow descriptions
    # - Reference to design images
    """)
    print()

    print("Sample output structure:")
    print("""
    ## 1.1 로그인 폼 컴포넌트 구현
    - **목적**: 로그인 UI 구현
    - **UI 컴포넌트**:
      - input "이메일" (center): 이메일 입력 필드
      - input "비밀번호" (center): 비밀번호 입력 필드
      - button "로그인" (center): 로그인 버튼
    - **레이아웃**: 중앙 정렬 카드
    - **사용자 흐름**: 입력 → 제출 → 성공 시 대시보드로 이동
    - **참고 이미지**: ./images/page_5_login.png
    """)
    print()


def example3_prompt_structure():
    """Example 3: Show how image information is added to prompts."""
    print("=" * 80)
    print("Example 3: Prompt Structure with Images")
    print("=" * 80)
    print()

    from src.llm.planner.prompts import build_task_identification_prompt
    from src.llm.prompts import build_task_writer_prompt

    sections, images = create_sample_sections_and_images()

    print("Without images:")
    prompt_without = build_task_identification_prompt(sections)
    print(f"  Prompt length: {len(prompt_without)} characters")
    print()

    print("With images:")
    prompt_with = build_task_identification_prompt(sections, images)
    print(f"  Prompt length: {len(prompt_with)} characters")
    print(f"  Increase: +{len(prompt_with) - len(prompt_without)} characters")
    print()

    print("Additional information included:")
    print("  - Screen type (login, dashboard, etc.)")
    print("  - UI components with types, labels, and positions")
    print("  - Layout structure descriptions")
    print("  - User flow narratives")
    print("  - Image file paths for reference")
    print()


def example4_full_pipeline():
    """Example 4: Full pipeline from sections to markdown files."""
    print("=" * 80)
    print("Example 4: Complete Pipeline with Images")
    print("=" * 80)
    print()

    print("In a real application, the full pipeline would be:")
    print()

    print("1. Extract PDF:")
    print("   pdf_result = PDFExtractor().extract('spec.pdf')")
    print()

    print("2. Analyze images (if extract_images=True):")
    print("   analyzer = ImageAnalyzer(api_key)")
    print("   image_analyses = analyzer.analyze_batch(pdf_result.pages)")
    print()

    print("3. Preprocess sections:")
    print("   preprocess_result = Preprocessor().process(pdf_result)")
    print()

    print("4. Identify tasks (WITH images):")
    print("   planner = LLMPlanner(api_key)")
    print("   tasks = planner.identify_tasks_from_sections(")
    print("       sections=all_sections,")
    print("       image_analyses=image_analyses  # ← Image integration!")
    print("   )")
    print()

    print("5. Write detailed sub-tasks (WITH images):")
    print("   task_writer = LLMTaskWriter(api_key)")
    print("   for task in tasks:")
    print("       result = task_writer.write_task(")
    print("           task=task,")
    print("           sections=all_sections,")
    print("           image_analyses=image_analyses  # ← Image integration!")
    print("       )")
    print()

    print("6. Split into files:")
    print("   splitter = FileSplitter(output_dir='./output')")
    print("   split_result = splitter.split(tasks_with_markdown)")
    print()

    print("Result: Markdown files with UI component details included!")
    print()


def example5_orchestrator_usage():
    """Example 5: Using Orchestrator with image analysis."""
    print("=" * 80)
    print("Example 5: Orchestrator with Image Analysis")
    print("=" * 80)
    print()

    print("The Orchestrator automatically integrates image analysis:")
    print()

    print("Code:")
    print("""
    from src.cli.orchestrator import Orchestrator, OrchestratorConfig

    config = OrchestratorConfig(
        pdf_path="./spec.pdf",
        output_dir="./output",
        extract_images=True,     # Enable image extraction
        analyze_images=True,      # Enable image analysis ← KEY!
        api_key="your-api-key",
    )

    orchestrator = Orchestrator(config)
    report = orchestrator.run()

    # The pipeline will:
    # 1. Extract PDF
    # 2. Extract images
    # 2.5. Analyze images with Claude Vision ← NEW STEP
    # 3. Preprocess
    # 4. LLM Planner (with images) ← Enhanced
    # 5. LLM TaskWriter (with images) ← Enhanced
    # 6. Split files
    # 7. Generate report
    """)
    print()

    print("CLI usage:")
    print("  python -m src.cli.main analyze spec.pdf \\")
    print("    --out ./output \\")
    print("    --extract-images \\")
    print("    --analyze-images")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("IMAGE INTEGRATION USAGE EXAMPLES")
    print("=" * 80)
    print()

    print("These examples show how to use image analysis results")
    print("with LLM Planner and TaskWriter to generate more accurate")
    print("frontend-related tasks with UI component details.")
    print("\n")

    examples = [
        example1_planner_with_images,
        example2_taskwriter_with_images,
        example3_prompt_structure,
        example4_full_pipeline,
        example5_orchestrator_usage,
    ]

    for example in examples:
        example()
        input("Press Enter to continue...")
        print("\n")

    print("=" * 80)
    print("For more information, see:")
    print("  - test_image_integration.py (unit tests)")
    print("  - CLAUDE.md (implementation details)")
    print("=" * 80)


if __name__ == "__main__":
    main()
