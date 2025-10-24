"""Test script for FileSplitter module."""

from datetime import datetime
from src.types.models import (
    IdentifiedTask,
    TaskWithMarkdown,
    FileMetadata,
)
from src.splitter import FileSplitter
from src.utils.logger import setup_logging


def test_basic_split():
    """Test 1: Basic file splitting functionality."""
    print("\n" + "=" * 60)
    print("Test 1: Basic File Splitting")
    print("=" * 60)

    # Create sample tasks
    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="인증 및 회원관리",
                description="사용자 인증 및 회원 정보 관리",
                module="AuthModule",
                entities=["User", "Session"],
                prerequisites=[],
                related_sections=[1, 2],
            ),
            markdown="""# 인증 및 회원관리 — 상위 태스크 1

## 상위 태스크 개요
- **설명:** 사용자 인증 및 회원 정보 관리
- **모듈/영역:** AuthModule
- **관련 엔티티:** User, Session

---

## 하위 태스크 목록

### 1.1 회원가입
- **목적:** 새로운 사용자 등록
- **엔드포인트:** `POST /api/auth/register`

### 1.2 로그인
- **목적:** 사용자 인증 및 세션 생성
- **엔드포인트:** `POST /api/auth/login`
""",
        ),
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=2,
                name="결제 시스템",
                description="주문 및 결제 처리",
                module="PaymentModule",
                entities=["Payment", "Order"],
                prerequisites=["인증 및 회원관리"],
                related_sections=[3, 4],
            ),
            markdown="""# 결제 시스템 — 상위 태스크 2

## 상위 태스크 개요
- **설명:** 주문 및 결제 처리
- **모듈/영역:** PaymentModule
- **관련 엔티티:** Payment, Order

---

## 하위 태스크 목록

### 2.1 주문 생성
- **목적:** 새로운 주문 생성
- **엔드포인트:** `POST /api/orders`

### 2.2 결제 처리
- **목적:** 결제 승인 및 완료 처리
- **엔드포인트:** `POST /api/payments`
""",
        ),
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=3,
                name="알림 시스템",
                description="푸시 알림 및 이메일 발송",
                module="NotificationModule",
                entities=["Notification"],
                prerequisites=[],
                related_sections=[5],
            ),
            markdown="""# 알림 시스템 — 상위 태스크 3

## 상위 태스크 개요
- **설명:** 푸시 알림 및 이메일 발송
- **모듈/영역:** NotificationModule
- **관련 엔티티:** Notification

---

## 하위 태스크 목록

### 3.1 푸시 알림
- **목적:** 모바일 푸시 알림 발송
- **엔드포인트:** `POST /api/notifications/push`

### 3.2 이메일 발송
- **목적:** 이메일 발송
- **엔드포인트:** `POST /api/notifications/email`
""",
        ),
    ]

    # Create FileSplitter with clean option
    splitter = FileSplitter(output_dir="./test_output", clean=True)

    # Split files
    result = splitter.split(tasks)

    # Print results
    print(f"\n총 태스크: {result.total_files}")
    print(f"성공: {result.success_count}")
    print(f"실패: {result.failure_count}")
    print(f"처리 시간: {result.processing_time:.2f}초")

    # Print saved files
    print(f"\n생성된 파일:")
    for file_info in result.saved_files:
        size_kb = file_info.size_bytes / 1024
        print(
            f"  {file_info.task_index}. {file_info.file_name} "
            f"({size_kb:.1f} KB) - {file_info.task_name}"
        )

    # Save report
    report_path = splitter.save_report(result)
    print(f"\n리포트 저장: {report_path}")

    # Assertions
    assert result.success_count == 3, f"Expected 3 files, got {result.success_count}"
    assert result.failure_count == 0, f"Expected 0 failures, got {result.failure_count}"
    assert len(result.saved_files) == 3, "Expected 3 saved file records"

    print("\n✓ Test 1 passed!")


def test_filename_sanitization():
    """Test 2: Filename sanitization."""
    print("\n" + "=" * 60)
    print("Test 2: Filename Sanitization")
    print("=" * 60)

    # Tasks with special characters in names
    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="인증/회원관리",  # Contains /
                description="Test",
                module="Test",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# Test 1",
        ),
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=2,
                name="결제 | 주문 시스템",  # Contains |
                description="Test",
                module="Test",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# Test 2",
        ),
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=3,
                name='알림 "푸시"',  # Contains quotes
                description="Test",
                module="Test",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# Test 3",
        ),
    ]

    splitter = FileSplitter(output_dir="./test_output/sanitize", clean=True)
    result = splitter.split(tasks)

    print(f"\n생성된 파일명:")
    for file_info in result.saved_files:
        print(f"  - {file_info.file_name}")

    # Check that special characters are removed/replaced
    assert result.success_count == 3
    assert all("/" not in f.file_name for f in result.saved_files)
    assert all("|" not in f.file_name for f in result.saved_files)
    assert all('"' not in f.file_name for f in result.saved_files)

    print("\n✓ Test 2 passed!")


def test_long_filenames():
    """Test 3: Long filename truncation."""
    print("\n" + "=" * 60)
    print("Test 3: Long Filename Truncation")
    print("=" * 60)

    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="매우 긴 태스크 이름을 가진 태스크입니다 이것은 50자를 초과하는 이름입니다 그리고 더 길게 만들어봅니다",
                description="Test",
                module="Test",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# Long name test",
        ),
    ]

    splitter = FileSplitter(
        output_dir="./test_output/long", clean=True, max_filename_length=30
    )
    result = splitter.split(tasks)

    print(f"\n생성된 파일명: {result.saved_files[0].file_name}")
    print(f"파일명 길이 (전체): {len(result.saved_files[0].file_name)}")

    # File name should be truncated (index + underscore + 30 chars + .md)
    # Format: "1_" (2) + name (30) + ".md" (3) = 35 total
    assert result.success_count == 1
    # The task name portion should be at most 30 characters
    name_portion = result.saved_files[0].file_name[2:-3]  # Remove "1_" and ".md"
    assert len(name_portion) <= 30, f"Name portion too long: {len(name_portion)}"

    print("\n✓ Test 3 passed!")


def test_front_matter():
    """Test 4: YAML front matter generation."""
    print("\n" + "=" * 60)
    print("Test 4: YAML Front Matter")
    print("=" * 60)

    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="테스트 태스크",
                description="Front matter test",
                module="TestModule",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# 테스트 태스크\n\n테스트 내용",
            metadata=FileMetadata(
                title="테스트 태스크",
                index=1,
                generated=datetime.now(),
                source_pdf="./test.pdf",
            ),
        ),
    ]

    # With front matter
    splitter_with = FileSplitter(
        output_dir="./test_output/with_fm", clean=True, add_front_matter=True
    )
    result_with = splitter_with.split(tasks)

    # Without front matter
    splitter_without = FileSplitter(
        output_dir="./test_output/without_fm", clean=True, add_front_matter=False
    )
    result_without = splitter_without.split(tasks)

    # Check file sizes (with front matter should be larger)
    size_with = result_with.saved_files[0].size_bytes
    size_without = result_without.saved_files[0].size_bytes

    print(f"\n파일 크기 (front matter 포함): {size_with} bytes")
    print(f"파일 크기 (front matter 제외): {size_without} bytes")

    assert size_with > size_without, "Front matter should increase file size"

    # Read the file with front matter and check contents
    from pathlib import Path

    file_path = Path(result_with.saved_files[0].file_path)
    content = file_path.read_text(encoding="utf-8")

    assert content.startswith("---"), "Should start with front matter delimiter"
    assert "title: 테스트 태스크" in content, "Should contain title"
    assert "index: 1" in content, "Should contain index"
    assert "source_pdf: ./test.pdf" in content, "Should contain source_pdf"

    print("\n✓ Test 4 passed!")


def test_error_recovery():
    """Test 5: Error recovery and partial failures."""
    print("\n" + "=" * 60)
    print("Test 5: Error Recovery")
    print("=" * 60)

    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="정상 태스크 1",
                description="Valid task",
                module="Module1",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# 정상 태스크 1",
        ),
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=2,
                name="",  # Invalid: empty name
                description="Invalid task",
                module="Module2",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# 잘못된 태스크",
        ),
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=3,
                name="정상 태스크 2",
                description="Valid task",
                module="Module3",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# 정상 태스크 2",
        ),
    ]

    splitter = FileSplitter(output_dir="./test_output/error", clean=True)
    result = splitter.split(tasks)

    print(f"\n총 태스크: {result.total_files}")
    print(f"성공: {result.success_count}")
    print(f"실패: {result.failure_count}")

    # Should process remaining tasks despite one failure
    assert result.total_files == 3
    assert result.success_count == 2, f"Expected 2 successes, got {result.success_count}"
    assert result.failure_count == 1, f"Expected 1 failure, got {result.failure_count}"

    print(f"\n실패한 태스크:")
    for failed in result.failed_files:
        print(f"  - Task {failed.task_index}: {failed.error}")

    print("\n✓ Test 5 passed!")


def test_report_generation():
    """Test 6: Report generation."""
    print("\n" + "=" * 60)
    print("Test 6: Report Generation")
    print("=" * 60)

    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=i,
                name=f"태스크 {i}",
                description=f"설명 {i}",
                module=f"Module{i}",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown=f"# 태스크 {i}\n\n내용 {i}",
        )
        for i in range(1, 4)
    ]

    splitter = FileSplitter(output_dir="./test_output/report", clean=True)
    result = splitter.split(tasks)

    # Generate report
    report = splitter.generate_report(result)
    print("\n생성된 리포트:")
    print(report)

    # Check report content
    assert "[FileSplitter Report]" in report
    assert f"총 생성 파일: {result.success_count}개" in report
    assert "에러: 없음" in report

    # Save report
    report_path = splitter.save_report(result, filename="test_report.log")
    assert Path(report_path).exists(), "Report file should exist"

    print("\n✓ Test 6 passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FileSplitter Test Suite")
    print("=" * 60)

    # Setup logging
    setup_logging()

    try:
        # Run tests
        test_basic_split()
        test_filename_sanitization()
        test_long_filenames()
        test_front_matter()
        test_error_recovery()
        test_report_generation()

        # Summary
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    from pathlib import Path

    main()
