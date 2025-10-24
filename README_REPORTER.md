# Reporter Module

**Reporter** 모듈은 PDF Agent의 모든 처리 단계에서 수집된 메트릭을 종합하여 포괄적인 리포트를 생성합니다.

## 목차

1. [개요](#개요)
2. [주요 기능](#주요-기능)
3. [설치](#설치)
4. [사용법](#사용법)
5. [데이터 모델](#데이터-모델)
6. [비용 계산](#비용-계산)
7. [에러 리포팅](#에러-리포팅)
8. [파일 출력](#파일-출력)
9. [예제](#예제)
10. [API 레퍼런스](#api-레퍼런스)

---

## 개요

Reporter는 PDF Agent의 전체 처리 파이프라인(추출 → OCR → 전처리 → LLM → 파일 분리)을 모니터링하고, 다음 정보를 포함하는 리포트를 생성합니다:

- **요약**: 입력 파일, 페이지 수, 생성된 파일 수, 총 처리 시간
- **추출 메트릭**: 텍스트 페이지 수, 이미지 수, 표 수
- **OCR 메트릭**: 처리된 이미지 수, 평균 신뢰도
- **전처리 메트릭**: 섹션 수, 기능 그룹 수
- **LLM 메트릭**: API 호출 횟수, 토큰 사용량, 비용
- **출력 파일**: 생성된 파일 목록 및 크기
- **에러**: 발생한 에러 및 경고

리포트는 콘솔 출력, 텍스트 파일(`.log`), JSON 파일(`.json`) 형식으로 저장할 수 있습니다.

---

## 주요 기능

### 1. 메트릭 수집 및 집계
- 각 처리 단계의 메트릭 자동 수집
- 총 처리 시간 자동 계산 (또는 수동 지정)

### 2. LLM 비용 계산
- Claude 3.5 Sonnet 기반 비용 계산
- 입력/출력 토큰 구분
- 다양한 모델 지원

### 3. 에러 추적
- 심각도별 분류 (warning, error, critical)
- 타임스탬프 및 스택 트레이스 포함
- 처리 단계별 에러 구분

### 4. 다양한 출력 형식
- **콘솔 출력**: 사람이 읽기 쉬운 텍스트 형식
- **텍스트 로그**: `report.log` 파일로 저장
- **JSON**: 기계 판독 가능한 `report.json`

---

## 설치

Reporter 모듈은 PDF Agent 프로젝트의 일부로 포함되어 있습니다.

```bash
# 프로젝트 클론
git clone <repository-url>
cd pdf-agent

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

---

## 사용법

### 기본 사용법

```python
from src.reporter import Reporter
from src.types.models import FileInfo, LLMMetrics

# Reporter 초기화
reporter = Reporter()

# 메트릭 생성
llm_metrics = LLMMetrics(
    planner_calls=1,
    task_writer_calls=3,
    total_tokens_used=15000,
    total_cost=0.225,
    processing_time=30.0
)

output_files = [
    FileInfo(
        file_path="./output/1_auth.md",
        file_name="1_auth.md",
        size_bytes=12800,
        task_index=1,
        task_name="인증 시스템"
    )
]

# 리포트 생성
report = reporter.generate_report(
    pdf_file="./spec.pdf",
    total_pages=50,
    output_files=output_files,
    llm_metrics=llm_metrics
)

# 출력
reporter.print_to_console(report)
reporter.save_json_report(report, "./output/report.json")
reporter.save_text_report(report, "./output/report.log")
```

### 전체 메트릭 사용

```python
from src.types.models import (
    ExtractionMetrics,
    OCRMetrics,
    PreprocessingMetrics,
    LLMMetrics,
    ErrorEntry
)

# 모든 메트릭 생성
extraction_metrics = ExtractionMetrics(
    text_pages=50,
    images_extracted=15,
    tables_found=8,
    processing_time=60.0
)

ocr_metrics = OCRMetrics(
    images_processed=15,
    average_confidence=89.5,
    total_ocr_time=120.0
)

preprocessing_metrics = PreprocessingMetrics(
    sections_identified=25,
    functional_groups=8,
    processing_time=15.0
)

llm_metrics = LLMMetrics(
    planner_calls=1,
    task_writer_calls=5,
    total_tokens_used=45000,
    total_cost=0.675,
    processing_time=90.0
)

errors = [
    ErrorEntry(
        stage="OCR",
        message="Low confidence on page 20",
        severity="warning",
        timestamp=datetime.now()
    )
]

# 리포트 생성
report = reporter.generate_report(
    pdf_file="./spec.pdf",
    total_pages=50,
    output_files=output_files,
    extraction_metrics=extraction_metrics,
    ocr_metrics=ocr_metrics,
    preprocessing_metrics=preprocessing_metrics,
    llm_metrics=llm_metrics,
    errors=errors
)
```

---

## 데이터 모델

### ReportResult

```python
class ReportResult(BaseModel):
    summary: ReportSummary
    extraction: Optional[ExtractionMetrics]
    ocr: Optional[OCRMetrics]
    preprocessing: Optional[PreprocessingMetrics]
    llm: Optional[LLMMetrics]
    output_files: List[FileInfo]
    errors: List[ErrorEntry]
```

### ReportSummary

```python
class ReportSummary(BaseModel):
    pdf_file: str
    total_pages: int
    generated_files: int
    total_processing_time: float  # seconds
    timestamp: datetime
```

### ExtractionMetrics

```python
class ExtractionMetrics(BaseModel):
    text_pages: int
    images_extracted: int
    tables_found: int
    processing_time: float  # seconds
```

### OCRMetrics

```python
class OCRMetrics(BaseModel):
    images_processed: int
    average_confidence: float  # 0-100
    total_ocr_time: float  # seconds
```

### PreprocessingMetrics

```python
class PreprocessingMetrics(BaseModel):
    sections_identified: int
    functional_groups: int
    processing_time: float  # seconds
```

### LLMMetrics

```python
class LLMMetrics(BaseModel):
    planner_calls: int
    task_writer_calls: int
    total_tokens_used: int
    total_cost: float  # USD
    processing_time: float  # seconds
```

### ErrorEntry

```python
class ErrorEntry(BaseModel):
    stage: str  # "PDF Extraction", "OCR", "Preprocessor", etc.
    message: str
    severity: str  # "warning", "error", "critical"
    timestamp: datetime
```

---

## 비용 계산

Reporter는 Claude API 사용량 기반 비용을 자동 계산합니다.

### 가격표 (Claude 3.5 Sonnet, 2024년 기준)

| 모델 | 입력 토큰 (per 1M) | 출력 토큰 (per 1M) |
|------|-------------------|-------------------|
| claude-3-5-sonnet-20241022 | $3.00 | $15.00 |
| claude-3-sonnet-20240229 | $3.00 | $15.00 |
| claude-3-opus-20240229 | $15.00 | $75.00 |
| claude-3-haiku-20240307 | $0.25 | $1.25 |

### 비용 계산 예시

```python
from src.reporter import calculate_cost

# 예시 1: 작은 태스크
cost = calculate_cost(
    input_tokens=5000,
    output_tokens=2000,
    model="claude-3-5-sonnet-20241022"
)
print(f"Cost: ${cost:.6f}")  # Output: Cost: $0.045000

# 예시 2: 큰 태스크
cost = calculate_cost(
    input_tokens=100000,
    output_tokens=50000
)
print(f"Cost: ${cost:.6f}")  # Output: Cost: $1.050000
```

### Reporter 메서드 사용

```python
reporter = Reporter()
cost = reporter.calculate_llm_cost(10000, 5000)
print(f"Cost: ${cost:.4f}")  # Output: Cost: $0.1050
```

---

## 에러 리포팅

Reporter는 처리 중 발생한 에러를 추적하고 리포트에 포함합니다.

### 심각도 레벨

- **warning**: 경미한 문제 (처리 계속 가능)
- **error**: 오류 (일부 기능 실패)
- **critical**: 치명적 오류 (처리 중단)

### 에러 추가 예시

```python
from datetime import datetime
from src.types.models import ErrorEntry

errors = [
    ErrorEntry(
        stage="OCR",
        message="Low confidence on page-15.png (45.2%)",
        severity="warning",
        timestamp=datetime.now()
    ),
    ErrorEntry(
        stage="LLM Planner",
        message="API rate limit reached",
        severity="critical",
        timestamp=datetime.now()
    )
]

report = reporter.generate_report(
    pdf_file="./spec.pdf",
    total_pages=30,
    output_files=output_files,
    errors=errors
)
```

### 리포트 출력 예시

```
--- Errors (2) ---
[WARNING] OCR: Low confidence on page-15.png (45.2%)
[CRITICAL] LLM Planner: API rate limit reached
```

---

## 파일 출력

### 텍스트 리포트 (report.log)

```python
reporter.save_text_report(report, "./output/report.log")
```

**출력 예시:**

```
Generated at: 2025-10-23T16:30:00

================================================================================
PDF2Tasks Processing Report
================================================================================

Input File: ./specs/app.pdf
Pages Processed: 50 pages
Files Generated: 5
Total Time: 4m 45s
Generated At: 2025-10-23 16:30:00

--- Extraction ---
Text Pages: 50
Images Extracted: 15
Tables Found: 8
Processing Time: 1m 0s

--- LLM Usage ---
Planner Calls: 1
TaskWriter Calls: 5
Total Tokens: 45,000
Total Cost: $0.675000
Processing Time: 1m 30s

Errors: None

================================================================================
```

### JSON 리포트 (report.json)

```python
reporter.save_json_report(report, "./output/report.json")
```

**출력 예시:**

```json
{
  "summary": {
    "pdf_file": "./specs/app.pdf",
    "total_pages": 50,
    "generated_files": 5,
    "total_processing_time": 285.0,
    "timestamp": "2025-10-23T16:30:00"
  },
  "extraction": {
    "text_pages": 50,
    "images_extracted": 15,
    "tables_found": 8,
    "processing_time": 60.0
  },
  "llm": {
    "planner_calls": 1,
    "task_writer_calls": 5,
    "total_tokens_used": 45000,
    "total_cost": 0.675,
    "processing_time": 90.0
  },
  "output_files": [
    {
      "file_path": "./output/1_auth.md",
      "file_name": "1_auth.md",
      "size_bytes": 12800,
      "task_index": 1,
      "task_name": "인증 시스템"
    }
  ],
  "errors": []
}
```

---

## 예제

프로젝트에는 7가지 사용 예제가 포함되어 있습니다:

```bash
# 모든 예제 실행
python examples/reporter_usage.py
```

### 예제 목록

1. **기본 리포트 생성**: 최소 메트릭으로 간단한 리포트
2. **전체 메트릭 리포트**: 모든 처리 단계 메트릭 포함
3. **에러 포함 리포트**: 에러 추적 및 리포팅
4. **파일 저장**: JSON 및 텍스트 파일로 저장
5. **비용 계산**: LLM API 비용 계산 예시
6. **커스텀 처리 시간**: 수동 처리 시간 설정
7. **프로그래매틱 분석**: 리포트 데이터 프로그래밍 방식 접근

---

## API 레퍼런스

### Reporter 클래스

#### `__init__()`

Reporter 인스턴스를 생성합니다.

```python
reporter = Reporter()
```

#### `generate_report(...) -> ReportResult`

리포트를 생성합니다.

**Parameters:**
- `pdf_file` (str): 소스 PDF 파일 경로
- `total_pages` (int): 총 페이지 수
- `output_files` (List[FileInfo]): 생성된 파일 목록
- `extraction_metrics` (Optional[ExtractionMetrics]): 추출 메트릭
- `ocr_metrics` (Optional[OCRMetrics]): OCR 메트릭
- `preprocessing_metrics` (Optional[PreprocessingMetrics]): 전처리 메트릭
- `llm_metrics` (Optional[LLMMetrics]): LLM 메트릭
- `errors` (Optional[List[ErrorEntry]]): 에러 목록
- `total_processing_time` (Optional[float]): 총 처리 시간 (초, 자동 계산 가능)

**Returns:** `ReportResult`

**Raises:** `ReportGenerationError`

#### `format_text_report(report: ReportResult) -> str`

리포트를 텍스트 형식으로 포맷합니다.

**Parameters:**
- `report` (ReportResult): 리포트 객체

**Returns:** 포맷된 텍스트 문자열

#### `print_to_console(report: ReportResult) -> None`

리포트를 콘솔에 출력합니다.

**Parameters:**
- `report` (ReportResult): 리포트 객체

#### `save_json_report(report: ReportResult, output_path: str) -> None`

리포트를 JSON 파일로 저장합니다.

**Parameters:**
- `report` (ReportResult): 리포트 객체
- `output_path` (str): 저장 경로 (예: `"./output/report.json"`)

**Raises:** `ReportSaveError`

#### `save_text_report(report: ReportResult, output_path: str) -> None`

리포트를 텍스트 파일로 저장합니다.

**Parameters:**
- `report` (ReportResult): 리포트 객체
- `output_path` (str): 저장 경로 (예: `"./output/report.log"`)

**Raises:** `ReportSaveError`

#### `calculate_llm_cost(input_tokens: int, output_tokens: int, model: str = "claude-3-5-sonnet-20241022") -> float`

LLM API 비용을 계산합니다.

**Parameters:**
- `input_tokens` (int): 입력 토큰 수
- `output_tokens` (int): 출력 토큰 수
- `model` (str): 모델명 (기본값: `"claude-3-5-sonnet-20241022"`)

**Returns:** 비용 (USD)

### 독립 함수

#### `calculate_cost(input_tokens: int, output_tokens: int, model: str = "claude-3-5-sonnet-20241022") -> float`

LLM API 비용을 계산합니다 (Reporter 인스턴스 없이 사용 가능).

```python
from src.reporter import calculate_cost

cost = calculate_cost(10000, 5000)
print(f"${cost:.4f}")  # Output: $0.1050
```

#### `get_pricing_info(model: str = "claude-3-5-sonnet-20241022") -> Dict[str, float]`

특정 모델의 가격 정보를 반환합니다.

```python
from src.reporter import get_pricing_info

pricing = get_pricing_info("claude-3-5-sonnet-20241022")
print(pricing)
# Output: {'input_per_1m': 3.0, 'output_per_1m': 15.0}
```

#### `estimate_cost_for_tokens(total_tokens: int, model: str = "claude-3-5-sonnet-20241022") -> float`

총 토큰 수로 비용을 추정합니다 (입력/출력 50/50 가정).

```python
from src.reporter import estimate_cost_for_tokens

cost = estimate_cost_for_tokens(10000)
print(f"${cost:.4f}")  # Output: $0.0900
```

---

## 테스트

```bash
# 단위 테스트 실행
python test_reporter.py
```

**테스트 항목:**
1. 비용 계산 함수
2. 기본 리포트 생성
3. 에러 포함 리포트
4. 텍스트 포맷팅
5. 파일 저장 작업
6. 전체 워크플로우

---

## 예외

### ReporterError

모든 Reporter 예외의 베이스 클래스.

### ReportGenerationError

리포트 생성 실패 시 발생.

```python
try:
    report = reporter.generate_report(...)
except ReportGenerationError as e:
    print(f"Failed to generate report: {e}")
```

### ReportSaveError

리포트 저장 실패 시 발생.

```python
try:
    reporter.save_json_report(report, "./output/report.json")
except ReportSaveError as e:
    print(f"Failed to save report: {e}")
```

### InvalidMetricsError

메트릭 데이터가 유효하지 않을 때 발생.

---

## 문제 해결

### Q: 리포트가 생성되지 않습니다.

**A:** `generate_report()`의 필수 파라미터를 확인하세요:
- `pdf_file` (str)
- `total_pages` (int)
- `output_files` (List[FileInfo])

### Q: JSON 저장 시 인코딩 오류가 발생합니다.

**A:** Pydantic의 `model_dump(mode="json")`을 사용하여 datetime 등이 자동으로 직렬화됩니다. 파일 경로가 유효한지 확인하세요.

### Q: 비용 계산이 정확하지 않습니다.

**A:** Claude API의 최신 가격표를 확인하세요. `src/reporter/cost_calculator.py`의 `CLAUDE_PRICING` 딕셔너리를 업데이트할 수 있습니다.

---

## 라이선스

이 프로젝트는 PDF Agent의 일부입니다.

---

## 기여

버그 리포트 및 기능 제안은 이슈 트래커를 통해 제출해주세요.

---

## 참고 문서

- [PDF Extractor README](./README_EXTRACTOR.md)
- [Preprocessor README](./README_PREPROCESSOR.md)
- [TaskWriter README](./README_TASKWRITER.md)
- [LLM Planner README](./README_LLM_PLANNER.md)
- [프로젝트 기획서](./AI_Agent_Project_Plan.md)
