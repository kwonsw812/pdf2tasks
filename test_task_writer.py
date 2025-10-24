#!/usr/bin/env python3
"""Test script for LLM TaskWriter."""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.types.models import IdentifiedTask, Section, PageRange
from src.llm.task_writer import LLMTaskWriter
from src.utils.logger import setup_logging, get_logger


def test_task_writer():
    """Test LLM TaskWriter functionality."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    logger.info("=" * 80)
    logger.info("LLM TaskWriter Test Script")
    logger.info("=" * 80)

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        logger.error("Please set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return False

    try:
        # Create sample task
        logger.info("\n[Step 1] Creating sample high-level task")
        task = IdentifiedTask(
            index=1,
            name="인증",
            description="사용자 회원가입 및 로그인 기능 구현",
            module="AuthModule",
            entities=["User", "Session"],
            prerequisites=[],
            related_sections=[0, 1],
        )
        logger.info(f"Task: {task.name} (index: {task.index})")

        # Create sample sections
        logger.info("\n[Step 2] Creating sample sections")
        sections = [
            Section(
                title="회원 관리",
                level=1,
                content="""
사용자는 이메일과 비밀번호로 회원가입할 수 있다.
비밀번호는 최소 8자 이상이어야 하며, 영문, 숫자, 특수문자를 포함해야 한다.
회원가입 시 이메일 중복 체크가 필요하다.
가입 완료 후 자동으로 로그인 상태가 된다.
                """,
                page_range=PageRange(start=1, end=3),
                subsections=[],
            ),
            Section(
                title="로그인/로그아웃",
                level=1,
                content="""
사용자는 이메일과 비밀번호로 로그인할 수 있다.
로그인 성공 시 JWT 토큰이 발급된다.
토큰의 유효기간은 7일이다.
로그아웃 시 토큰이 무효화된다.
연속 5회 로그인 실패 시 계정이 일시 잠금된다.
                """,
                page_range=PageRange(start=4, end=6),
                subsections=[],
            ),
        ]
        logger.info(f"Created {len(sections)} sections")

        # Initialize TaskWriter
        logger.info("\n[Step 3] Initializing LLM TaskWriter")
        writer = LLMTaskWriter(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            temperature=0.0,
        )
        logger.info("TaskWriter initialized successfully")

        # Generate sub-tasks
        logger.info("\n[Step 4] Generating sub-tasks")
        logger.info("This may take 10-30 seconds...")
        result = writer.write_task(
            task=task,
            sections=sections,
            validate=True,
            retry_on_failure=True,
        )

        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS")
        logger.info("=" * 80)

        logger.info(f"\n✓ Generated {len(result.sub_tasks)} sub-tasks")
        for sub_task in result.sub_tasks:
            logger.info(f"  - {sub_task.index} {sub_task.title}")

        logger.info(f"\n✓ Token usage:")
        logger.info(f"  - Input: {result.token_usage.input_tokens:,} tokens")
        logger.info(f"  - Output: {result.token_usage.output_tokens:,} tokens")
        logger.info(f"  - Total: {result.token_usage.total_tokens:,} tokens")

        cost = writer.estimate_cost(result.token_usage)
        logger.info(f"  - Estimated cost: ${cost:.4f}")

        logger.info(f"\n✓ Generated markdown length: {len(result.markdown)} chars")

        # Save markdown to file
        output_file = f"test_output_{task.index}_{task.name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.markdown)
        logger.info(f"✓ Saved markdown to: {output_file}")

        # Display markdown preview
        logger.info("\n" + "=" * 80)
        logger.info("MARKDOWN PREVIEW (first 1000 chars)")
        logger.info("=" * 80)
        logger.info(result.markdown[:1000])
        if len(result.markdown) > 1000:
            logger.info("\n...(truncated)")

        logger.info("\n" + "=" * 80)
        logger.info("✓ All tests passed!")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"\n✗ Test failed: {str(e)}", exc_info=True)
        return False


def test_validation():
    """Test validation functionality."""
    logger = get_logger(__name__)

    logger.info("\n" + "=" * 80)
    logger.info("Testing validation functions")
    logger.info("=" * 80)

    from src.types.models import SubTask
    from src.llm.validator import validate_sub_tasks, check_completeness

    # Create sample sub-tasks
    sub_tasks = [
        SubTask(
            index="1.1",
            title="회원가입 API 구현",
            purpose="사용자 회원가입 기능 제공",
            endpoint="POST /api/auth/register",
            data_model="User { email, password, name }",
            logic="이메일 중복 체크 → 비밀번호 해싱 → DB 저장 → JWT 발급",
            security="Public 엔드포인트",
            exceptions="409: 이메일 중복, 400: 유효성 검증 실패",
            test_points="정상 가입, 이메일 중복, 비밀번호 형식 오류",
        ),
        SubTask(
            index="1.2",
            title="로그인 API 구현",
            purpose="사용자 로그인 기능 제공",
            endpoint="POST /api/auth/login",
            data_model="LoginDto { email, password }",
            logic="이메일 존재 확인 → 비밀번호 검증 → JWT 발급",
            security="Public 엔드포인트",
            exceptions="401: 인증 실패, 423: 계정 잠금",
            test_points="정상 로그인, 잘못된 비밀번호, 존재하지 않는 계정",
        ),
    ]

    # Validate
    validation = validate_sub_tasks(sub_tasks, task_index=1)
    logger.info(f"✓ Validation passed: {validation.is_valid}")
    logger.info(f"  Errors: {len(validation.errors)}")
    logger.info(f"  Warnings: {len(validation.warnings)}")

    # Check completeness
    completeness = check_completeness(sub_tasks)
    logger.info(f"✓ Completeness score: {completeness:.2%}")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("LLM TaskWriter Test Suite")
    print("=" * 80 + "\n")

    results = []

    # Test 1: Validation
    print("\n[Test 1] Validation Functions")
    print("-" * 80)
    try:
        result = test_validation()
        results.append(("Validation", result))
    except Exception as e:
        print(f"✗ Validation test failed: {str(e)}")
        results.append(("Validation", False))

    # Test 2: TaskWriter (requires API key)
    print("\n[Test 2] LLM TaskWriter")
    print("-" * 80)
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠ Skipping TaskWriter test (ANTHROPIC_API_KEY not set)")
        results.append(("TaskWriter", None))
    else:
        try:
            result = test_task_writer()
            results.append(("TaskWriter", result))
        except Exception as e:
            print(f"✗ TaskWriter test failed: {str(e)}")
            results.append(("TaskWriter", False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for name, result in results:
        if result is True:
            print(f"✓ {name}: PASSED")
        elif result is False:
            print(f"✗ {name}: FAILED")
        else:
            print(f"⚠ {name}: SKIPPED")

    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
