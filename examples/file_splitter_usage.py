"""Usage examples for FileSplitter module."""

from datetime import datetime
from src.types.models import (
    IdentifiedTask,
    TaskWithMarkdown,
    FileMetadata,
)
from src.splitter import FileSplitter
from src.utils.logger import setup_logging


def example_1_basic_usage():
    """Example 1: Basic file splitting."""
    print("\n=== Example 1: Basic File Splitting ===\n")

    # Sample tasks with markdown
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
- **선행 조건:** 없음

---

## 하위 태스크 목록

### 1.1 회원가입
- **목적:** 새로운 사용자 등록
- **엔드포인트:** `POST /api/auth/register`
- **데이터 모델:** `User { email, password, name }`
- **로직 요약:** 이메일 중복 체크 → 비밀번호 해싱 → DB 저장
- **권한/보안:** 공개 엔드포인트
- **예외:** 이메일 중복 시 409 에러
- **테스트 포인트:** 정상 가입, 중복 이메일 처리

### 1.2 로그인
- **목적:** 사용자 인증 및 세션 생성
- **엔드포인트:** `POST /api/auth/login`
- **데이터 모델:** `LoginDto { email, password }`
- **로직 요약:** 인증 확인 → JWT 토큰 발급
- **권한/보안:** 공개 엔드포인트
- **예외:** 인증 실패 시 401 에러
- **테스트 포인트:** 정상 로그인, 잘못된 비밀번호 처리
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
- **선행 조건:** 인증 및 회원관리

---

## 하위 태스크 목록

### 2.1 주문 생성
- **목적:** 새로운 주문 생성
- **엔드포인트:** `POST /api/orders`
- **데이터 모델:** `Order { userId, items, totalAmount }`
- **로직 요약:** 재고 확인 → 주문 생성 → 결제 대기 상태
- **권한/보안:** JWT 인증 필수
- **예외:** 재고 부족 시 400 에러
- **테스트 포인트:** 정상 주문, 재고 부족 처리

### 2.2 결제 처리
- **목적:** 결제 승인 및 완료 처리
- **엔드포인트:** `POST /api/payments`
- **데이터 모델:** `Payment { orderId, method, amount }`
- **로직 요약:** PG사 연동 → 결제 승인 → 주문 상태 업데이트
- **권한/보안:** JWT 인증 필수
- **예외:** 결제 실패 시 402 에러
- **테스트 포인트:** 정상 결제, 결제 실패 처리
""",
        ),
    ]

    # Create splitter and split files
    splitter = FileSplitter(output_dir="./examples/output/basic")
    result = splitter.split(tasks)

    # Print results
    print(f"총 파일: {result.total_files}")
    print(f"성공: {result.success_count}")
    print(f"실패: {result.failure_count}")
    print(f"처리 시간: {result.processing_time:.2f}초")
    print(f"\n생성된 파일:")
    for file_info in result.saved_files:
        print(f"  - {file_info.file_name} ({file_info.size_bytes} bytes)")

    # Save report
    report_path = splitter.save_report(result)
    print(f"\n리포트 저장: {report_path}")


def example_2_with_metadata():
    """Example 2: File splitting with custom metadata."""
    print("\n=== Example 2: With Custom Metadata ===\n")

    # Task with custom metadata
    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="알림 시스템",
                description="푸시 알림 및 이메일 발송",
                module="NotificationModule",
                entities=["Notification"],
                prerequisites=[],
                related_sections=[5],
            ),
            markdown="# 알림 시스템\n\n푸시 알림 및 이메일 발송 기능",
            metadata=FileMetadata(
                title="알림 시스템",
                index=1,
                generated=datetime.now(),
                source_pdf="./specs/app-requirements.pdf",
            ),
        ),
    ]

    splitter = FileSplitter(
        output_dir="./examples/output/with_metadata", add_front_matter=True
    )
    result = splitter.split(tasks)

    print(f"성공: {result.success_count}")
    print(f"생성된 파일:")
    for file_info in result.saved_files:
        print(f"  - {file_info.file_path}")


def example_3_without_front_matter():
    """Example 3: File splitting without YAML front matter."""
    print("\n=== Example 3: Without Front Matter ===\n")

    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="게시판",
                description="게시판 CRUD",
                module="BoardModule",
                entities=["Post", "Comment"],
                prerequisites=[],
                related_sections=[6],
            ),
            markdown="# 게시판\n\n게시판 생성, 조회, 수정, 삭제 기능",
        ),
    ]

    splitter = FileSplitter(
        output_dir="./examples/output/no_front_matter", add_front_matter=False
    )
    result = splitter.split(tasks)

    print(f"성공: {result.success_count}")


def example_4_clean_directory():
    """Example 4: Clean directory before splitting."""
    print("\n=== Example 4: Clean Directory ===\n")

    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="검색",
                description="전체 텍스트 검색",
                module="SearchModule",
                entities=["SearchIndex"],
                prerequisites=[],
                related_sections=[7],
            ),
            markdown="# 검색\n\n전체 텍스트 검색 기능",
        ),
    ]

    # Clean=True will delete all files in output directory
    splitter = FileSplitter(output_dir="./examples/output/clean", clean=True)
    result = splitter.split(tasks)

    print(f"성공: {result.success_count}")
    print(f"출력 디렉토리: {result.output_directory}")


def example_5_error_handling():
    """Example 5: Error handling with partial failures."""
    print("\n=== Example 5: Error Handling ===\n")

    # Include one task with invalid data
    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="정상 태스크",
                description="정상적인 태스크",
                module="NormalModule",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# 정상 태스크\n\n정상적으로 처리됩니다.",
        ),
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=2,
                name="",  # Invalid: empty name
                description="잘못된 태스크",
                module="InvalidModule",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# 잘못된 태스크",
        ),
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=3,
                name="또 다른 정상 태스크",
                description="정상적인 태스크 2",
                module="NormalModule2",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# 또 다른 정상 태스크\n\n정상적으로 처리됩니다.",
        ),
    ]

    splitter = FileSplitter(output_dir="./examples/output/error_handling")
    result = splitter.split(tasks)

    print(f"총 파일: {result.total_files}")
    print(f"성공: {result.success_count}")
    print(f"실패: {result.failure_count}")

    if result.failed_files:
        print("\n실패한 파일:")
        for failed in result.failed_files:
            print(f"  - Task {failed.task_index}: {failed.error}")


def example_6_generate_report():
    """Example 6: Generate detailed report."""
    print("\n=== Example 6: Generate Report ===\n")

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
        for i in range(1, 6)
    ]

    splitter = FileSplitter(output_dir="./examples/output/report")
    result = splitter.split(tasks)

    # Generate and print report
    report = splitter.generate_report(result)
    print(report)

    # Save report
    splitter.save_report(result, filename="summary.log")


def example_7_custom_filename_length():
    """Example 7: Custom maximum filename length."""
    print("\n=== Example 7: Custom Filename Length ===\n")

    tasks = [
        TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="매우 긴 태스크 이름을 가진 태스크입니다 이것은 50자를 초과하는 이름입니다",
                description="긴 이름 테스트",
                module="LongNameModule",
                entities=[],
                prerequisites=[],
                related_sections=[],
            ),
            markdown="# 긴 이름 태스크\n\n파일명이 잘릴 것입니다.",
        ),
    ]

    # Set max filename length to 30 characters
    splitter = FileSplitter(
        output_dir="./examples/output/custom_length", max_filename_length=30
    )
    result = splitter.split(tasks)

    print(f"생성된 파일명:")
    for file_info in result.saved_files:
        print(f"  - {file_info.file_name} (길이: {len(file_info.file_name)})")


def main():
    """Run all examples."""
    # Setup logging
    setup_logging()

    # Run examples
    example_1_basic_usage()
    example_2_with_metadata()
    example_3_without_front_matter()
    example_4_clean_directory()
    example_5_error_handling()
    example_6_generate_report()
    example_7_custom_filename_length()

    print("\n모든 예제 실행 완료!")


if __name__ == "__main__":
    main()
