"""
Test script for LLM Planner functionality.

This script tests the LLM Planner without making actual API calls.
For real API testing, see examples/llm_planner_usage.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.types.models import Section, FunctionalGroup, PageRange, IdentifiedTask
from src.llm.planner.task_deduplicator import TaskDeduplicator
from src.llm.planner.dependency_analyzer import DependencyAnalyzer
from src.llm.planner.token_tracker import TokenTracker, create_token_usage
from src.llm.planner.prompt_builder import PromptBuilder
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_task_deduplicator():
    """Test task deduplication functionality."""
    print("\n" + "=" * 80)
    print("TEST 1: Task Deduplicator")
    print("=" * 80)

    # Create sample tasks with duplicates
    tasks = [
        IdentifiedTask(
            index=1,
            name="사용자 인증",
            description="로그인 및 회원가입",
            module="auth",
            entities=["User", "Session"],
            prerequisites=[],
            related_sections=[1, 2],
        ),
        IdentifiedTask(
            index=2,
            name="사용자 인증 시스템",  # Similar to task 1
            description="인증 및 권한 관리",
            module="auth",
            entities=["User", "Token"],
            prerequisites=[],
            related_sections=[3],
        ),
        IdentifiedTask(
            index=3,
            name="상품 관리",
            description="상품 CRUD",
            module="product",
            entities=["Product"],
            prerequisites=[],
            related_sections=[4],
        ),
    ]

    deduplicator = TaskDeduplicator(similarity_threshold=0.7)
    deduplicated = deduplicator.deduplicate(tasks)

    print(f"\nOriginal tasks: {len(tasks)}")
    print(f"After deduplication: {len(deduplicated)}")

    for task in deduplicated:
        print(f"\n{task.index}. {task.name}")
        print(f"   Entities: {task.entities}")
        print(f"   Related sections: {task.related_sections}")

    assert len(deduplicated) == 2, "Expected 2 tasks after deduplication"
    print("\nTest passed!")


def test_dependency_analyzer():
    """Test dependency analysis functionality."""
    print("\n" + "=" * 80)
    print("TEST 2: Dependency Analyzer")
    print("=" * 80)

    tasks = [
        IdentifiedTask(
            index=1,
            name="인증",
            description="사용자 인증",
            module="auth",
            entities=["User"],
            prerequisites=[],
            related_sections=[1],
        ),
        IdentifiedTask(
            index=2,
            name="결제",
            description="결제 처리",
            module="payment",
            entities=["Payment"],
            prerequisites=[],
            related_sections=[2],
        ),
        IdentifiedTask(
            index=3,
            name="주문",
            description="주문 관리",
            module="order",
            entities=["Order"],
            prerequisites=[],
            related_sections=[3],
        ),
    ]

    analyzer = DependencyAnalyzer()
    analyzed = analyzer.analyze(tasks)

    print("\nTasks with dependencies:")
    for task in analyzed:
        print(f"\n{task.index}. {task.name}")
        print(f"   Prerequisites: {task.prerequisites}")

    # Get dependency graph
    dep_graph = analyzer.get_dependency_graph(analyzed)
    print("\nDependency Graph:")
    for task_name, deps in dep_graph.items():
        print(f"   {task_name}: {deps if deps else 'No dependencies'}")

    print("\nTest passed!")


def test_token_tracker():
    """Test token tracking functionality."""
    print("\n" + "=" * 80)
    print("TEST 3: Token Tracker")
    print("=" * 80)

    tracker = TokenTracker(model="claude-3-5-sonnet-20241022")

    # Simulate API calls
    usage1 = create_token_usage(input_tokens=1000, output_tokens=500)
    cost1 = tracker.track(usage1)
    print(f"\nCall 1: {usage1.total_tokens} tokens, ${cost1:.6f}")

    usage2 = create_token_usage(input_tokens=2000, output_tokens=1000)
    cost2 = tracker.track(usage2)
    print(f"Call 2: {usage2.total_tokens} tokens, ${cost2:.6f}")

    # Get summary
    summary = tracker.get_summary()
    print("\nSummary:")
    print(f"   Total calls: {summary['total_calls']}")
    print(f"   Total tokens: {summary['total_tokens']}")
    print(f"   Total cost: ${summary['total_cost_usd']:.6f}")

    # Verify calculations
    assert summary['total_calls'] == 2
    assert summary['total_tokens'] == 4500
    assert summary['total_cost_usd'] > 0

    print("\nTest passed!")


def test_prompt_builder():
    """Test prompt building functionality."""
    print("\n" + "=" * 80)
    print("TEST 4: Prompt Builder")
    print("=" * 80)

    sections = [
        Section(
            title="사용자 인증",
            level=1,
            content="로그인 및 회원가입 기능을 제공합니다.",
            page_range=PageRange(start=1, end=2),
        ),
        Section(
            title="상품 관리",
            level=1,
            content="상품 등록, 수정, 삭제 기능을 제공합니다.",
            page_range=PageRange(start=3, end=4),
        ),
    ]

    builder = PromptBuilder()

    # Build prompt
    system_prompt, user_prompt = builder.build_from_sections(sections)

    print(f"\nSystem prompt length: {len(system_prompt)} chars")
    print(f"User prompt length: {len(user_prompt)} chars")

    # Estimate tokens
    estimated_tokens = builder.estimate_tokens(system_prompt + user_prompt)
    print(f"Estimated tokens: {estimated_tokens}")

    assert len(system_prompt) > 0
    assert len(user_prompt) > 0
    assert "섹션 1" in user_prompt
    assert "섹션 2" in user_prompt

    print("\nTest passed!")


def test_functional_group_prompt():
    """Test prompt building from functional groups."""
    print("\n" + "=" * 80)
    print("TEST 5: Functional Group Prompt")
    print("=" * 80)

    sections = [
        Section(
            title="로그인",
            level=2,
            content="이메일/비밀번호 로그인",
            page_range=PageRange(start=1, end=1),
        ),
    ]

    groups = [
        FunctionalGroup(
            name="인증",
            sections=sections,
            keywords=["인증", "로그인"],
        ),
    ]

    builder = PromptBuilder()
    system_prompt, user_prompt = builder.build_from_functional_groups(groups)

    print(f"\nPrompt length: {len(user_prompt)} chars")
    assert "기능 그룹: 인증" in user_prompt
    assert "키워드:" in user_prompt

    print("\nTest passed!")


def test_section_splitting():
    """Test section splitting for large documents."""
    print("\n" + "=" * 80)
    print("TEST 6: Section Splitting")
    print("=" * 80)

    # Create 100 sections
    sections = [
        Section(
            title=f"섹션 {i}",
            level=1,
            content=f"내용 {i}",
            page_range=PageRange(start=i, end=i),
        )
        for i in range(1, 101)
    ]

    builder = PromptBuilder()
    chunks = builder.split_sections_into_chunks(sections, max_sections_per_chunk=25)

    print(f"\nTotal sections: {len(sections)}")
    print(f"Number of chunks: {len(chunks)}")
    print(f"Sections per chunk: {[len(chunk) for chunk in chunks]}")

    assert len(chunks) == 4  # 100 / 25 = 4
    assert all(len(chunk) <= 25 for chunk in chunks)

    print("\nTest passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("LLM PLANNER TEST SUITE")
    print("=" * 80)

    tests = [
        test_task_deduplicator,
        test_dependency_analyzer,
        test_token_tracker,
        test_prompt_builder,
        test_functional_group_prompt,
        test_section_splitting,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            logger.error(f"Test failed: {test_func.__name__}")
            logger.error(f"Error: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\nAll tests passed!")
        return 0
    else:
        print("\nSome tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
