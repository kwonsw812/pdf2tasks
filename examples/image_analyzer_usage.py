"""Examples for using ImageAnalyzer module."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.image_analyzer import ImageAnalyzer
from src.types.models import ExtractedImage


def example1_basic_usage():
    """Example 1: Basic single image analysis."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Single Image Analysis")
    print("=" * 60)

    # Initialize analyzer
    analyzer = ImageAnalyzer()

    # Analyze an image
    result = analyzer.analyze_image(
        image_path="./sample_screen.png",
        page_number=5,
        context="사용자 로그인 기능 섹션",
    )

    # Display results
    print(f"\nScreen: {result.screen_title}")
    print(f"Type: {result.screen_type}")
    print(f"Confidence: {result.confidence}%")
    print(f"\nLayout: {result.layout_structure}")
    print(f"\nUI Components ({len(result.ui_components)}):")
    for i, comp in enumerate(result.ui_components, 1):
        print(f"  {i}. {comp.type} - {comp.description}")

    if result.user_flow:
        print(f"\nUser Flow: {result.user_flow}")

    print(f"\nTokens Used: {result.token_usage.total_tokens}")
    print(f"Processing Time: {result.processing_time:.2f}s")


def example2_batch_analysis():
    """Example 2: Batch image analysis with context."""
    print("\n" + "=" * 60)
    print("Example 2: Batch Image Analysis")
    print("=" * 60)

    analyzer = ImageAnalyzer()

    # Prepare images list
    images = [
        ExtractedImage(
            page_number=5,
            image_path="./screens/login.png",
            width=800,
            height=600,
        ),
        ExtractedImage(
            page_number=7,
            image_path="./screens/dashboard.png",
            width=1200,
            height=800,
        ),
        ExtractedImage(
            page_number=10,
            image_path="./screens/product_list.png",
            width=1000,
            height=700,
        ),
    ]

    # Context for each page
    context_map = {
        5: "사용자 인증 및 로그인 기능",
        7: "관리자 대시보드 및 통계 화면",
        10: "상품 목록 조회 및 필터링 기능",
    }

    # Analyze batch (max 3 concurrent)
    batch_result = analyzer.analyze_batch(
        images=images,
        context_map=context_map,
        max_concurrent=3,
    )

    # Display summary
    print(f"\nBatch Analysis Results:")
    print(f"  Total Images: {batch_result.total_images}")
    print(f"  Successful: {batch_result.success_count}")
    print(f"  Failed: {batch_result.failure_count}")
    print(f"  Total Tokens: {batch_result.total_tokens_used:,}")
    print(f"  Total Cost: ${batch_result.total_cost:.4f}")
    print(f"  Total Time: {batch_result.total_processing_time:.2f}s")

    # Display each screen
    print("\nScreens Analyzed:")
    for analysis in batch_result.analyses:
        print(f"\n  - {analysis.screen_title or 'Unknown'}")
        print(f"    Page: {analysis.page_number}")
        print(f"    Type: {analysis.screen_type}")
        print(f"    Components: {len(analysis.ui_components)}")


def example3_with_cost_estimation():
    """Example 3: Estimate cost before analysis."""
    print("\n" + "=" * 60)
    print("Example 3: Cost Estimation")
    print("=" * 60)

    analyzer = ImageAnalyzer()

    # Estimate cost for different batch sizes
    for num_images in [10, 50, 100]:
        estimated_cost = analyzer.estimate_cost(num_images=num_images)
        print(f"Estimated cost for {num_images} images: ${estimated_cost:.4f}")

    # Ask user for confirmation
    num_images = 25
    estimated_cost = analyzer.estimate_cost(num_images=num_images)
    print(f"\nYou are about to analyze {num_images} images.")
    print(f"Estimated cost: ${estimated_cost:.4f}")
    # proceed = input("Continue? (y/n): ")
    # if proceed.lower() != 'y':
    #     print("Cancelled.")
    #     return


def example4_detailed_component_extraction():
    """Example 4: Extract detailed component information."""
    print("\n" + "=" * 60)
    print("Example 4: Detailed Component Extraction")
    print("=" * 60)

    analyzer = ImageAnalyzer()

    result = analyzer.analyze_image(
        image_path="./sample_screen.png",
        page_number=1,
        context="상품 상세 페이지",
    )

    # Group components by type
    components_by_type = {}
    for comp in result.ui_components:
        if comp.type not in components_by_type:
            components_by_type[comp.type] = []
        components_by_type[comp.type].append(comp)

    print(f"\nComponents by Type:")
    for comp_type, comps in sorted(components_by_type.items()):
        print(f"\n  {comp_type.upper()} ({len(comps)}):")
        for comp in comps:
            label = f" [{comp.label}]" if comp.label else ""
            position = f" @ {comp.position}" if comp.position else ""
            print(f"    - {comp.description}{label}{position}")


def example5_error_handling():
    """Example 5: Error handling and retries."""
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)

    # With custom retry settings
    analyzer = ImageAnalyzer(max_retries=3)

    try:
        # This will fail if file doesn't exist
        result = analyzer.analyze_image(
            image_path="./nonexistent.png",
            page_number=1,
        )
    except FileNotFoundError as e:
        print(f"✓ Caught expected error: {e}")

    try:
        # This will fail if API key is invalid
        analyzer_bad_key = ImageAnalyzer(api_key="invalid-key-123")
        result = analyzer_bad_key.analyze_image(
            image_path="./sample.png",
            page_number=1,
        )
    except Exception as e:
        print(f"✓ Caught API error: {type(e).__name__}")


def example6_summary_generation():
    """Example 6: Generate analysis summary."""
    print("\n" + "=" * 60)
    print("Example 6: Summary Generation")
    print("=" * 60)

    analyzer = ImageAnalyzer()

    # Prepare dummy batch result for demonstration
    from src.types.models import (
        ImageAnalysis,
        ImageAnalysisBatchResult,
        UIComponent,
        TokenUsage,
    )

    dummy_analyses = [
        ImageAnalysis(
            image_path="./login.png",
            page_number=1,
            screen_title="로그인 화면",
            screen_type="login",
            ui_components=[
                UIComponent(type="input", description="이메일 입력"),
                UIComponent(type="button", description="로그인 버튼"),
            ],
            layout_structure="중앙 정렬",
            confidence=95.0,
            processing_time=2.5,
            token_usage=TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
        ),
        ImageAnalysis(
            image_path="./dashboard.png",
            page_number=5,
            screen_title="대시보드",
            screen_type="dashboard",
            ui_components=[
                UIComponent(type="chart", description="매출 차트"),
                UIComponent(type="card", description="통계 카드"),
            ],
            layout_structure="그리드",
            confidence=90.0,
            processing_time=3.0,
            token_usage=TokenUsage(input_tokens=1200, output_tokens=600, total_tokens=1800),
        ),
    ]

    batch_result = ImageAnalysisBatchResult(
        analyses=dummy_analyses,
        total_images=2,
        success_count=2,
        failure_count=0,
        total_processing_time=5.5,
        total_tokens_used=3300,
        total_cost=0.0495,
    )

    # Generate summary
    summary = analyzer.get_analysis_summary(batch_result)
    print(summary)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("ImageAnalyzer Usage Examples")
    print("=" * 60)

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠ Warning: ANTHROPIC_API_KEY not set")
        print("Some examples will be skipped or use dummy data.")

    try:
        # Note: Examples 1-2 require actual image files
        # Uncomment when you have test images

        # example1_basic_usage()
        # example2_batch_analysis()

        example3_with_cost_estimation()
        # example4_detailed_component_extraction()
        example5_error_handling()
        example6_summary_generation()

        print("\n" + "=" * 60)
        print("✓ Examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Example failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
