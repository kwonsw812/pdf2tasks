# FileSplitter - Task 파일 분리 모듈

FileSplitter는 LLM TaskWriter에서 생성된 상위 태스크별 Markdown 콘텐츠를 개별 파일로 분리하여 저장하는 모듈입니다.

## 주요 기능

### 1. 파일명 자동 생성
- **형식**: `{index}_{기능명}.md`
- **특수문자 제거**: `/`, `\`, `?`, `%`, `*`, `:`, `|`, `"`, `<`, `>`
- **공백 처리**: 공백 → 언더스코어(`_`)
- **길이 제한**: 최대 50자 (설정 가능)
- **중복 방지**: 동일 이름 시 자동으로 숫자 추가

**예시**:
```python
"인증 및 회원관리" → "1_인증_및_회원관리.md"
"결제/주문 시스템" → "2_결제_주문_시스템.md"
```

### 2. 출력 디렉토리 관리
- 출력 디렉토리 자동 생성 (재귀적)
- `clean` 옵션: 기존 파일 모두 삭제 후 생성
- `overwrite` 옵션: 덮어쓰기 허용/차단
- 권한 및 디스크 공간 체크

### 3. YAML Front Matter 지원
각 파일 상단에 메타데이터 추가 (선택 사항):

```markdown
---
title: 인증 및 회원관리
index: 1
generated: 2025-10-23T16:23:42.848362
source_pdf: ./specs/app-v1.pdf
---

# 인증 및 회원관리 — 상위 태스크 1
...
```

### 4. 에러 핸들링 및 복구
- 일부 파일 저장 실패 시 나머지 계속 처리
- 상세한 에러 메시지 제공
- 실패한 파일 정보 로깅 및 리포트

### 5. 상세 리포트 생성
생성된 파일 목록, 크기, 처리 시간, 에러 정보를 포함한 리포트 자동 생성

## 설치

```bash
# 프로젝트 루트에서
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용

```python
from src.types.models import IdentifiedTask, TaskWithMarkdown
from src.splitter import FileSplitter

# 태스크 데이터 준비
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
        markdown="# 인증 및 회원관리\n\n...",
    ),
    # ... 더 많은 태스크
]

# FileSplitter 생성 및 실행
splitter = FileSplitter(output_dir="./output")
result = splitter.split(tasks)

# 리포트 저장
splitter.save_report(result, filename="report.log")

# 결과 출력
print(f"성공: {result.success_count}개")
print(f"실패: {result.failure_count}개")
```

### 고급 옵션

```python
# 모든 옵션 사용
splitter = FileSplitter(
    output_dir="./output",
    clean=True,              # 기존 파일 모두 삭제
    overwrite=True,          # 파일 덮어쓰기 허용
    add_front_matter=True,   # YAML Front Matter 추가
    max_filename_length=30,  # 파일명 최대 길이
)

result = splitter.split(tasks)
```

### 커스텀 메타데이터

```python
from datetime import datetime
from src.types.models import FileMetadata

tasks = [
    TaskWithMarkdown(
        task=IdentifiedTask(...),
        markdown="# 태스크 내용",
        metadata=FileMetadata(
            title="인증 시스템",
            index=1,
            generated=datetime.now(),
            source_pdf="./specs/app-v1.pdf",
        ),
    ),
]
```

### 리포트 생성

```python
# 텍스트 리포트 생성
report = splitter.generate_report(result)
print(report)

# 파일로 저장
splitter.save_report(result, filename="summary.log")
```

## 데이터 모델

### TaskWithMarkdown
```python
class TaskWithMarkdown(BaseModel):
    task: IdentifiedTask          # 태스크 정보
    markdown: str                  # 마크다운 콘텐츠
    metadata: Optional[FileMetadata]  # 메타데이터 (선택)
```

### SplitResult
```python
class SplitResult(BaseModel):
    saved_files: List[FileInfo]    # 성공한 파일 정보
    failed_files: List[FailedFile] # 실패한 파일 정보
    total_files: int               # 전체 파일 개수
    success_count: int             # 성공 개수
    failure_count: int             # 실패 개수
    processing_time: float         # 처리 시간 (초)
    output_directory: str          # 출력 디렉토리
```

### FileInfo
```python
class FileInfo(BaseModel):
    file_path: str        # 전체 경로
    file_name: str        # 파일명만
    size_bytes: int       # 파일 크기 (바이트)
    task_index: int       # 태스크 인덱스
    task_name: str        # 태스크 이름
```

## 예제

프로젝트에는 7가지 사용 예제가 포함되어 있습니다:

```bash
# 예제 실행
python examples/file_splitter_usage.py
```

### 예제 목록
1. **기본 파일 분리**: 3개의 태스크를 개별 파일로 저장
2. **커스텀 메타데이터**: 사용자 정의 메타데이터 사용
3. **Front Matter 제외**: YAML 헤더 없이 저장
4. **디렉토리 정리**: `clean` 옵션으로 기존 파일 삭제
5. **에러 핸들링**: 일부 실패 시에도 나머지 처리
6. **상세 리포트**: 완전한 리포트 생성
7. **커스텀 파일명 길이**: 최대 길이 설정

## 테스트

```bash
# 전체 테스트 실행
python test_file_splitter.py
```

### 테스트 항목
- ✓ 기본 파일 분리
- ✓ 파일명 특수문자 제거
- ✓ 긴 파일명 잘림 처리
- ✓ YAML Front Matter 생성
- ✓ 에러 복구 (부분 실패)
- ✓ 리포트 생성

## 에러 처리

FileSplitter는 다음과 같은 커스텀 예외를 사용합니다:

```python
from src.splitter.exceptions import (
    FileSplitterError,       # 베이스 예외
    FileWriteError,          # 파일 쓰기 실패
    PermissionError,         # 권한 문제
    DirectoryCreationError,  # 디렉토리 생성 실패
    InvalidTaskDataError,    # 잘못된 태스크 데이터
)
```

### 예외 처리 예시

```python
try:
    splitter = FileSplitter(output_dir="./output")
    result = splitter.split(tasks)
except DirectoryCreationError as e:
    print(f"디렉토리 생성 실패: {e}")
except InvalidTaskDataError as e:
    print(f"잘못된 태스크 데이터: {e}")
except FileSplitterError as e:
    print(f"FileSplitter 에러: {e}")
```

## 출력 예시

### 파일 구조
```
output/
├── 1_인증_및_회원관리.md
├── 2_결제_시스템.md
├── 3_알림_시스템.md
└── report.log
```

### 리포트 예시 (report.log)
```
[FileSplitter Report]
============================================================

총 생성 파일: 3개
총 처리 시간: 0.02초
출력 디렉토리: /path/to/output

생성된 파일:
------------------------------------------------------------
1. 1_인증_및_회원관리.md (0.5 KB) - Task 1: 인증 및 회원관리
2. 2_결제_시스템.md (0.5 KB) - Task 2: 결제 시스템
3. 3_알림_시스템.md (0.5 KB) - Task 3: 알림 시스템

에러: 없음

============================================================
```

## API 레퍼런스

### FileSplitter 클래스

#### `__init__(output_dir, clean=False, overwrite=True, add_front_matter=True, max_filename_length=50)`
FileSplitter 인스턴스를 생성합니다.

**Parameters:**
- `output_dir` (str): 출력 디렉토리 경로
- `clean` (bool): 기존 파일 모두 삭제 여부 (기본값: False)
- `overwrite` (bool): 파일 덮어쓰기 허용 여부 (기본값: True)
- `add_front_matter` (bool): YAML Front Matter 추가 여부 (기본값: True)
- `max_filename_length` (int): 파일명 최대 길이 (기본값: 50)

#### `split(tasks: List[TaskWithMarkdown]) -> SplitResult`
태스크를 개별 파일로 분리하여 저장합니다.

**Parameters:**
- `tasks`: TaskWithMarkdown 객체 리스트

**Returns:**
- `SplitResult`: 저장 결과 (성공/실패 정보)

#### `generate_report(result: SplitResult) -> str`
저장 결과로부터 텍스트 리포트를 생성합니다.

**Parameters:**
- `result`: split() 메서드의 결과

**Returns:**
- `str`: 포맷된 리포트 문자열

#### `save_report(result: SplitResult, filename: str = "report.log") -> str`
리포트를 파일로 저장합니다.

**Parameters:**
- `result`: split() 메서드의 결과
- `filename`: 리포트 파일명 (기본값: "report.log")

**Returns:**
- `str`: 저장된 리포트 파일의 전체 경로

### FilenameGenerator 클래스

#### `generate(index: int, task_name: str) -> str`
안전한 파일명을 생성합니다.

**Parameters:**
- `index`: 태스크 인덱스
- `task_name`: 태스크 이름

**Returns:**
- `str`: 생성된 파일명 (예: "1_인증_및_회원관리.md")

## 모듈 구조

```
src/splitter/
├── __init__.py              # 모듈 진입점
├── file_splitter.py         # 메인 FileSplitter 클래스
├── filename_generator.py    # 파일명 생성 유틸리티
└── exceptions.py            # 커스텀 예외
```

## 의존성

- Python 3.10+
- Pydantic 2.6.0+
- pathlib (표준 라이브러리)
- shutil (표준 라이브러리)

## 라이센스

이 프로젝트는 PDF Agent의 일부입니다.

## 기여

버그 리포트 및 기능 제안은 이슈로 등록해 주세요.

## 변경 이력

### v0.1.0 (2025-10-23)
- 초기 릴리스
- 모든 Task 7 하위 태스크 구현 완료
- 6가지 테스트 통과
- 7가지 사용 예제 포함
