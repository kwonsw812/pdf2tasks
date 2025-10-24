"""
Pytest configuration and shared fixtures for PDF Agent tests.
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Directories and Paths
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """프로젝트 루트 디렉토리"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def tests_dir(project_root: Path) -> Path:
    """테스트 디렉토리"""
    return project_root / "tests"


@pytest.fixture(scope="session")
def fixtures_dir(tests_dir: Path) -> Path:
    """테스트 fixtures 디렉토리"""
    return tests_dir / "fixtures"


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """임시 출력 디렉토리 (테스트 후 자동 삭제)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_image_dir() -> Generator[Path, None, None]:
    """임시 이미지 디렉토리"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def sample_pdf_path(fixtures_dir: Path) -> Path:
    """샘플 PDF 파일 경로"""
    pdf_path = fixtures_dir / "sample.pdf"
    if not pdf_path.exists():
        # If sample PDF doesn't exist, use test_pdf.pdf from project root
        project_pdf = fixtures_dir.parent.parent / "test_pdf.pdf"
        if project_pdf.exists():
            return project_pdf
    return pdf_path


@pytest.fixture
def sample_text() -> str:
    """테스트용 샘플 텍스트"""
    return """
    # 테스트 문서

    ## 1. 인증 기능
    사용자 로그인 및 회원가입 기능을 제공합니다.

    ### 1.1 로그인
    - 이메일/비밀번호 로그인
    - JWT 토큰 발급

    ## 2. 결제 기능
    결제 처리 및 주문 관리 기능

    ### 2.1 결제 처리
    - 카드 결제
    - 계좌이체
    """


@pytest.fixture
def sample_markdown() -> str:
    """테스트용 샘플 Markdown"""
    return """# 인증 — 상위 태스크 1

## 상위 태스크 개요
- **설명:** 사용자 인증 및 권한 관리
- **모듈/영역:** AuthModule
- **관련 엔티티:** User, Session

---

## 하위 태스크 목록

### 1.1 회원가입 API
- **목적:** 신규 사용자 등록
- **엔드포인트:** `POST /api/auth/register`
- **로직 요약:** 이메일 검증 → 비밀번호 해싱 → DB 저장
"""


# ============================================================================
# Mock Objects
# ============================================================================

@pytest.fixture
def mock_api_key(monkeypatch) -> str:
    """Mock Anthropic API key"""
    api_key = "sk-ant-test-mock-key-12345"
    monkeypatch.setenv("ANTHROPIC_API_KEY", api_key)
    return api_key


@pytest.fixture
def mock_llm_response() -> dict:
    """Mock LLM API response"""
    return {
        "id": "msg_test123",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": """```json
{
  "tasks": [
    {
      "index": 1,
      "name": "인증",
      "description": "사용자 인증 및 권한 관리",
      "module": "AuthModule",
      "entities": ["User", "Session"],
      "prerequisites": [],
      "related_sections": [0, 1]
    }
  ]
}
```"""
            }
        ],
        "model": "claude-3-5-sonnet-20241022",
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 500
        }
    }


# ============================================================================
# Test Data Models
# ============================================================================

@pytest.fixture
def sample_pdf_metadata() -> dict:
    """샘플 PDF 메타데이터"""
    return {
        "title": "테스트 기획서",
        "author": "테스트",
        "total_pages": 10,
        "creation_date": datetime.now()
    }


@pytest.fixture
def sample_extracted_text() -> dict:
    """샘플 추출된 텍스트 데이터"""
    return {
        "page_number": 1,
        "text": "테스트 텍스트",
        "metadata": {
            "font_size": 12.0,
            "font_name": "Arial",
            "position": {
                "x0": 100.0,
                "y0": 200.0,
                "x1": 500.0,
                "y1": 220.0
            }
        }
    }


@pytest.fixture
def sample_section() -> dict:
    """샘플 섹션 데이터"""
    return {
        "title": "인증 기능",
        "level": 1,
        "content": "사용자 로그인 및 회원가입 기능",
        "page_range": {
            "start": 1,
            "end": 3
        },
        "subsections": []
    }


@pytest.fixture
def sample_identified_task() -> dict:
    """샘플 식별된 태스크"""
    return {
        "index": 1,
        "name": "인증",
        "description": "사용자 인증 및 권한 관리",
        "module": "AuthModule",
        "entities": ["User", "Session"],
        "prerequisites": [],
        "related_sections": [0, 1]
    }


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Pytest 설정"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests requiring API keys"
    )
    config.addinivalue_line(
        "markers", "requires_tesseract: Tests requiring Tesseract OCR"
    )
    config.addinivalue_line(
        "markers", "error_scenario: Error handling tests"
    )


def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 처리"""
    # Skip tests requiring API key if not available
    skip_api = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set")
    skip_tesseract = pytest.mark.skip(reason="Tesseract not installed")

    for item in items:
        if "requires_api" in item.keywords and not os.getenv("ANTHROPIC_API_KEY"):
            item.add_marker(skip_api)

        if "requires_tesseract" in item.keywords:
            # Check if tesseract is available
            import shutil
            if not shutil.which("tesseract"):
                item.add_marker(skip_tesseract)
