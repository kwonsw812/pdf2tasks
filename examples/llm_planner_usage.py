"""
LLM Planner Usage Examples

This script demonstrates various ways to use the LLM Planner for task identification.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm.planner.llm_planner import LLMPlanner
from src.types.models import Section, FunctionalGroup, PageRange
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Load environment variables
load_dotenv()


def example_1_basic_task_identification():
    """
    Example 1: Basic task identification from sections.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Task Identification from Sections")
    print("=" * 80)

    # Create sample sections
    sections = [
        Section(
            title="사용자 인증",
            level=1,
            content="로그인, 회원가입, 비밀번호 재설정 등의 사용자 인증 기능을 제공합니다. "
            "JWT 토큰 기반 인증을 사용하며, 소셜 로그인(구글, 카카오)도 지원합니다.",
            page_range=PageRange(start=1, end=2),
        ),
        Section(
            title="상품 관리",
            level=1,
            content="상품 등록, 수정, 삭제, 조회 기능을 제공합니다. "
            "카테고리별 상품 분류 및 검색 기능도 포함됩니다.",
            page_range=PageRange(start=3, end=4),
        ),
        Section(
            title="주문 처리",
            level=1,
            content="주문 생성, 조회, 취소 기능을 제공합니다. "
            "결제 시스템과 연동되어 주문 상태를 관리합니다.",
            page_range=PageRange(start=5, end=6),
        ),
    ]

    # Initialize planner
    planner = LLMPlanner()

    try:
        # Identify tasks
        result = planner.identify_tasks_from_sections(sections)

        # Print results
        print("\nIdentified Tasks:")
        for task in result.tasks:
            print(f"\n{task.index}. {task.name}")
            print(f"   Module: {task.module}")
            print(f"   Description: {task.description}")
            print(f"   Entities: {task.entities}")
            print(f"   Prerequisites: {task.prerequisites}")

        # Print usage statistics
        print("\nToken Usage:")
        print(f"   Input tokens: {result.token_usage.input_tokens}")
        print(f"   Output tokens: {result.token_usage.output_tokens}")
        print(f"   Total cost: ${result.estimated_cost_usd:.6f}")

    except Exception as e:
        logger.error(f"Error in example 1: {e}")
        raise


def example_2_functional_groups():
    """
    Example 2: Task identification from functional groups.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Task Identification from Functional Groups")
    print("=" * 80)

    # Create functional groups
    auth_sections = [
        Section(
            title="로그인",
            level=2,
            content="이메일/비밀번호 기반 로그인",
            page_range=PageRange(start=1, end=1),
        ),
        Section(
            title="회원가입",
            level=2,
            content="이메일 인증을 통한 회원가입",
            page_range=PageRange(start=2, end=2),
        ),
    ]

    product_sections = [
        Section(
            title="상품 등록",
            level=2,
            content="관리자의 상품 등록 기능",
            page_range=PageRange(start=3, end=3),
        ),
    ]

    functional_groups = [
        FunctionalGroup(
            name="인증",
            sections=auth_sections,
            keywords=["인증", "로그인", "회원가입"],
        ),
        FunctionalGroup(
            name="상품",
            sections=product_sections,
            keywords=["상품", "제품"],
        ),
    ]

    # Initialize planner
    planner = LLMPlanner()

    try:
        # Identify tasks
        result = planner.identify_tasks_from_functional_groups(functional_groups)

        # Print results
        print("\nIdentified Tasks:")
        for task in result.tasks:
            print(f"\n{task.index}. {task.name}")
            print(f"   Module: {task.module}")
            print(f"   Related sections: {task.related_sections}")

        # Get dependency graph
        dep_graph = planner.get_dependency_graph(result.tasks)
        print("\nDependency Graph:")
        for task_name, deps in dep_graph.items():
            print(f"   {task_name}: {deps if deps else 'No dependencies'}")

    except Exception as e:
        logger.error(f"Error in example 2: {e}")
        raise


def example_3_custom_configuration():
    """
    Example 3: Task identification with custom configuration.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Custom Configuration")
    print("=" * 80)

    sections = [
        Section(
            title="결제 시스템",
            level=1,
            content="PG사 연동을 통한 결제 처리",
            page_range=PageRange(start=1, end=1),
        ),
        Section(
            title="결제 내역",
            level=2,
            content="사용자별 결제 내역 조회",
            page_range=PageRange(start=2, end=2),
        ),
    ]

    # Initialize with custom settings
    planner = LLMPlanner(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        temperature=0.7,
        similarity_threshold=0.9,  # Higher threshold for stricter deduplication
        enable_dependency_analysis=False,  # Disable dependency analysis
    )

    try:
        result = planner.identify_tasks_from_sections(sections)

        print(f"\nIdentified {len(result.tasks)} tasks")
        print(f"Cost: ${result.estimated_cost_usd:.6f}")

        # Log token summary
        planner.log_token_summary()

    except Exception as e:
        logger.error(f"Error in example 3: {e}")
        raise


def example_4_error_handling():
    """
    Example 4: Error handling and recovery.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Error Handling")
    print("=" * 80)

    sections = [
        Section(
            title="테스트",
            level=1,
            content="테스트 섹션",
            page_range=PageRange(start=1, end=1),
        ),
    ]

    try:
        # Try with invalid API key (for demonstration)
        planner = LLMPlanner(api_key="invalid_key")
        result = planner.identify_tasks_from_sections(sections)

    except Exception as e:
        logger.error(f"Expected error occurred: {type(e).__name__}: {e}")
        print(f"\nError handled gracefully: {type(e).__name__}")


def example_5_multiple_calls():
    """
    Example 5: Multiple calls with token tracking.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Multiple Calls with Token Tracking")
    print("=" * 80)

    planner = LLMPlanner()

    # First call
    sections1 = [
        Section(
            title="인증",
            level=1,
            content="사용자 인증 시스템",
            page_range=PageRange(start=1, end=1),
        ),
    ]

    # Second call
    sections2 = [
        Section(
            title="알림",
            level=1,
            content="푸시 알림 시스템",
            page_range=PageRange(start=2, end=2),
        ),
    ]

    try:
        # First identification
        result1 = planner.identify_tasks_from_sections(sections1)
        print(f"\nCall 1: {len(result1.tasks)} tasks identified")

        # Second identification
        result2 = planner.identify_tasks_from_sections(sections2)
        print(f"Call 2: {len(result2.tasks)} tasks identified")

        # Print cumulative usage
        print("\nCumulative Token Usage:")
        summary = planner.get_token_summary()
        print(f"   Total calls: {summary['total_calls']}")
        print(f"   Total tokens: {summary['total_tokens']:,}")
        print(f"   Total cost: ${summary['total_cost_usd']:.6f}")

    except Exception as e:
        logger.error(f"Error in example 5: {e}")
        raise


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("LLM PLANNER USAGE EXAMPLES")
    print("=" * 80)

    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\nERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set it in your .env file or export it:")
        print("  export ANTHROPIC_API_KEY=your_api_key_here")
        sys.exit(1)

    try:
        # Run examples
        example_1_basic_task_identification()
        # example_2_functional_groups()  # Uncomment to run
        # example_3_custom_configuration()  # Uncomment to run
        # example_4_error_handling()  # Uncomment to run
        # example_5_multiple_calls()  # Uncomment to run

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Example failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
