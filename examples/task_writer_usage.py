#!/usr/bin/env python3
"""
LLM TaskWriter Usage Examples

이 파일은 LLM TaskWriter의 다양한 사용 예제를 보여줍니다.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.types.models import IdentifiedTask, Section, PageRange
from src.llm.task_writer import LLMTaskWriter
from src.utils.logger import setup_logging, get_logger


def example_1_basic_usage():
    """
    예제 1: 기본 사용법

    가장 기본적인 TaskWriter 사용 예제입니다.
    """
    logger = get_logger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("예제 1: 기본 사용법")
    logger.info("=" * 80)

    # 상위 태스크 정의
    task = IdentifiedTask(
        index=1,
        name="인증",
        description="사용자 회원가입 및 로그인 기능",
        module="AuthModule",
        entities=["User", "Session"],
        prerequisites=[],
        related_sections=[0],
    )

    # 관련 섹션 정의
    sections = [
        Section(
            title="인증 기능",
            level=1,
            content="사용자는 이메일과 비밀번호로 회원가입하고 로그인할 수 있다.",
            page_range=PageRange(start=1, end=5),
            subsections=[],
        )
    ]

    # TaskWriter 초기화
    writer = LLMTaskWriter()

    # 하위 태스크 생성
    result = writer.write_task(task, sections)

    # 결과 출력
    logger.info(f"생성된 하위 태스크: {len(result.sub_tasks)}개")
    for sub_task in result.sub_tasks:
        logger.info(f"  - {sub_task.index} {sub_task.title}")

    logger.info(f"토큰 사용량: {result.token_usage.total_tokens:,} tokens")
    logger.info(f"예상 비용: ${writer.estimate_cost(result.token_usage):.4f}")

    return result


def example_2_multiple_sections():
    """
    예제 2: 여러 섹션을 참조하는 태스크

    복잡한 태스크의 경우 여러 섹션을 참조할 수 있습니다.
    """
    logger = get_logger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("예제 2: 여러 섹션 참조")
    logger.info("=" * 80)

    task = IdentifiedTask(
        index=2,
        name="결제",
        description="상품 결제 및 결제 내역 관리",
        module="PaymentModule",
        entities=["Payment", "Order", "User"],
        prerequisites=["인증"],
        related_sections=[0, 1, 2],  # 여러 섹션 참조
    )

    sections = [
        Section(
            title="결제 프로세스",
            level=1,
            content="사용자는 장바구니에서 상품을 선택하여 결제할 수 있다.",
            page_range=PageRange(start=10, end=15),
            subsections=[],
        ),
        Section(
            title="결제 수단",
            level=2,
            content="신용카드, 계좌이체, 카카오페이를 지원한다.",
            page_range=PageRange(start=16, end=18),
            subsections=[],
        ),
        Section(
            title="결제 내역",
            level=2,
            content="사용자는 본인의 결제 내역을 조회할 수 있다.",
            page_range=PageRange(start=19, end=20),
            subsections=[],
        ),
    ]

    writer = LLMTaskWriter()
    result = writer.write_task(task, sections)

    logger.info(f"생성된 하위 태스크: {len(result.sub_tasks)}개")
    return result


def example_3_save_to_file():
    """
    예제 3: 생성된 Markdown을 파일로 저장

    TaskWriter가 생성한 Markdown을 파일로 저장합니다.
    """
    logger = get_logger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("예제 3: 파일 저장")
    logger.info("=" * 80)

    task = IdentifiedTask(
        index=3,
        name="게시판",
        description="게시글 작성, 조회, 수정, 삭제 기능",
        module="BoardModule",
        entities=["Post", "Comment", "User"],
        prerequisites=["인증"],
        related_sections=[0],
    )

    sections = [
        Section(
            title="게시판 기능",
            level=1,
            content="사용자는 게시글을 작성하고 조회할 수 있다. 본인의 게시글만 수정/삭제 가능하다.",
            page_range=PageRange(start=21, end=25),
            subsections=[],
        )
    ]

    writer = LLMTaskWriter()
    result = writer.write_task(task, sections)

    # 파일로 저장
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{result.task.index}_{result.task.name}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result.markdown)

    logger.info(f"✓ Markdown 저장 완료: {filepath}")
    logger.info(f"  파일 크기: {os.path.getsize(filepath):,} bytes")

    return result


def example_4_custom_model():
    """
    예제 4: 커스텀 모델 설정

    다른 Claude 모델이나 설정을 사용할 수 있습니다.
    """
    logger = get_logger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("예제 4: 커스텀 모델 설정")
    logger.info("=" * 80)

    task = IdentifiedTask(
        index=4,
        name="알림",
        description="이메일 및 푸시 알림 발송",
        module="NotificationModule",
        entities=["Notification", "User"],
        prerequisites=["인증"],
        related_sections=[0],
    )

    sections = [
        Section(
            title="알림 기능",
            level=1,
            content="시스템은 사용자에게 이메일 및 푸시 알림을 보낼 수 있다.",
            page_range=PageRange(start=26, end=28),
            subsections=[],
        )
    ]

    # 커스텀 설정으로 초기화
    writer = LLMTaskWriter(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,  # 더 짧은 응답
        temperature=0.2,  # 약간의 창의성
    )

    result = writer.write_task(task, sections)
    logger.info(f"생성된 하위 태스크: {len(result.sub_tasks)}개")

    return result


def example_5_validation_disabled():
    """
    예제 5: 검증 비활성화

    빠른 프로토타이핑을 위해 검증을 비활성화할 수 있습니다.
    """
    logger = get_logger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("예제 5: 검증 비활성화")
    logger.info("=" * 80)

    task = IdentifiedTask(
        index=5,
        name="검색",
        description="전체 텍스트 검색 기능",
        module="SearchModule",
        entities=["SearchIndex", "Post", "User"],
        prerequisites=["게시판"],
        related_sections=[0],
    )

    sections = [
        Section(
            title="검색 기능",
            level=1,
            content="사용자는 키워드로 게시글을 검색할 수 있다.",
            page_range=PageRange(start=29, end=30),
            subsections=[],
        )
    ]

    writer = LLMTaskWriter()

    # 검증 비활성화 (빠른 생성)
    result = writer.write_task(
        task,
        sections,
        validate=False,  # 검증 건너뛰기
    )

    logger.info(f"생성된 하위 태스크: {len(result.sub_tasks)}개")
    logger.info("⚠ 검증이 비활성화되어 품질이 보장되지 않습니다.")

    return result


def example_6_error_handling():
    """
    예제 6: 에러 핸들링

    API 호출 실패 등의 에러를 처리하는 방법입니다.
    """
    logger = get_logger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("예제 6: 에러 핸들링")
    logger.info("=" * 80)

    from src.llm.exceptions import (
        APIKeyError,
        LLMCallError,
        MarkdownParseError,
        SubTaskValidationError,
    )

    task = IdentifiedTask(
        index=6,
        name="관리자",
        description="관리자 대시보드 및 통계",
        module="AdminModule",
        entities=["Admin", "Dashboard", "Statistics"],
        prerequisites=["인증"],
        related_sections=[0],
    )

    sections = [
        Section(
            title="관리자 기능",
            level=1,
            content="관리자는 사용자 및 게시글을 관리할 수 있다.",
            page_range=PageRange(start=31, end=33),
            subsections=[],
        )
    ]

    try:
        writer = LLMTaskWriter()
        result = writer.write_task(task, sections)
        logger.info(f"✓ 성공: {len(result.sub_tasks)}개 하위 태스크 생성")
        return result

    except APIKeyError as e:
        logger.error(f"✗ API Key 오류: {str(e)}")
        logger.error("  ANTHROPIC_API_KEY 환경 변수를 설정하세요.")
    except LLMCallError as e:
        logger.error(f"✗ LLM 호출 오류: {str(e)}")
        logger.error("  네트워크 연결 또는 API 상태를 확인하세요.")
    except MarkdownParseError as e:
        logger.error(f"✗ Markdown 파싱 오류: {str(e)}")
        logger.error("  LLM 응답 형식이 예상과 다릅니다.")
    except SubTaskValidationError as e:
        logger.error(f"✗ 검증 오류: {str(e)}")
        logger.error("  생성된 하위 태스크가 품질 기준을 충족하지 못합니다.")
    except Exception as e:
        logger.error(f"✗ 예상치 못한 오류: {str(e)}")

    return None


def example_7_batch_processing():
    """
    예제 7: 배치 처리

    여러 태스크를 순차적으로 처리합니다.
    """
    logger = get_logger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("예제 7: 배치 처리")
    logger.info("=" * 80)

    # 여러 태스크 정의
    tasks = [
        IdentifiedTask(
            index=7,
            name="상품",
            description="상품 등록 및 관리",
            module="ProductModule",
            entities=["Product", "Category"],
            prerequisites=[],
            related_sections=[0],
        ),
        IdentifiedTask(
            index=8,
            name="장바구니",
            description="장바구니 추가 및 관리",
            module="CartModule",
            entities=["Cart", "CartItem", "User"],
            prerequisites=["상품", "인증"],
            related_sections=[0],
        ),
    ]

    sections = [
        Section(
            title="상품 관리",
            level=1,
            content="관리자는 상품을 등록하고 관리할 수 있다. 사용자는 상품을 조회할 수 있다.",
            page_range=PageRange(start=34, end=38),
            subsections=[],
        )
    ]

    writer = LLMTaskWriter()
    results = []

    # 배치 처리
    for i, task in enumerate(tasks, 1):
        logger.info(f"\n[{i}/{len(tasks)}] 처리 중: {task.name}")
        try:
            result = writer.write_task(task, sections)
            results.append(result)
            logger.info(f"  ✓ 완료: {len(result.sub_tasks)}개 하위 태스크")
        except Exception as e:
            logger.error(f"  ✗ 실패: {str(e)}")
            results.append(None)

    # 전체 통계
    total_sub_tasks = sum(len(r.sub_tasks) for r in results if r)
    total_tokens = sum(r.token_usage.total_tokens for r in results if r)
    total_cost = sum(writer.estimate_cost(r.token_usage) for r in results if r)

    logger.info(f"\n배치 처리 완료:")
    logger.info(f"  - 처리된 태스크: {len([r for r in results if r])}/{len(tasks)}")
    logger.info(f"  - 총 하위 태스크: {total_sub_tasks}개")
    logger.info(f"  - 총 토큰: {total_tokens:,} tokens")
    logger.info(f"  - 총 예상 비용: ${total_cost:.4f}")

    return results


def main():
    """Run all examples."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    logger.info("\n" + "=" * 80)
    logger.info("LLM TaskWriter 사용 예제")
    logger.info("=" * 80)

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("\nANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")
        logger.error("다음 명령으로 설정하세요:")
        logger.error("  export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Run examples (uncomment the ones you want to run)

    # 예제 1: 기본 사용법
    # example_1_basic_usage()

    # 예제 2: 여러 섹션 참조
    # example_2_multiple_sections()

    # 예제 3: 파일 저장
    # example_3_save_to_file()

    # 예제 4: 커스텀 모델
    # example_4_custom_model()

    # 예제 5: 검증 비활성화
    # example_5_validation_disabled()

    # 예제 6: 에러 핸들링
    example_6_error_handling()

    # 예제 7: 배치 처리
    # example_7_batch_processing()

    logger.info("\n" + "=" * 80)
    logger.info("모든 예제 완료")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
