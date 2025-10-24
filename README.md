# PDF Agent

> AI 기반 PDF 기획서 분석 및 백엔드 태스크 자동 추출 시스템

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [시스템 아키텍처](#시스템-아키텍처)
- [설치](#설치)
- [사용법](#사용법)
- [모듈 구조](#모듈-구조)
- [테스트](#테스트)
- [문서](#문서)
- [트러블슈팅](#트러블슈팅)

## 개요

PDF Agent는 화면 설계/사용자 흐름 중심의 PDF 기획서에서 **백엔드 개발 태스크를 자동으로 추출**하고 **구조화된 Markdown 파일**로 생성하는 시스템입니다.

### 문제점
- 기획서를 읽고 백엔드 작업을 수동으로 분해하는 데 많은 시간 소요
- 기능 누락 및 중복 작업 발생
- 태스크 우선순위 파악 어려움
- **기존 API와의 연관성 파악 어려움**

### 해결책
- AI 기반 자동 요구사항 추출 및 분류
- 상위/하위 태스크로 구조화
- **OpenAPI 기반 기존 엔드포인트 자동 매칭** ⭐
- **프레임워크 비의존적 요구사항 정의** (구현 AI가 기술 선택)
- Claude Code 호환 Markdown 파일 생성
- **개발 착수 전 기획서 이해 시간 50% 이상 단축**

## 주요 기능

### 🔍 PDF 분석
- **텍스트 추출**: PyMuPDF 기반 고속 텍스트 추출
- **이미지 추출**: PDF 내 임베디드 이미지 및 페이지 렌더링
- **표 인식**: pdfplumber 기반 정확한 표 추출
- **메타데이터**: 문서 정보 및 페이지별 속성 파싱

### 🔤 OCR (광학 문자 인식)
- **Tesseract 기반**: 한국어/영어 다국어 지원
- **이미지 전처리**: 그레이스케일, 대비 향상, 노이즈 제거
- **배치 처리**: 병렬 처리로 대량 이미지 OCR
- **후처리**: OCR 오인식 패턴 자동 교정

### 🧹 전처리 (Preprocessor)
- **텍스트 정규화**: Unicode NFC, 공백/줄바꿈 정규화
- **헤더/푸터 제거**: 반복 패턴 자동 감지 및 제거
- **섹션 구분**: 제목 패턴 및 폰트 크기 기반 계층 구조 생성
- **기능별 그룹화**: 키워드 매칭으로 자동 분류 (인증, 결제, 알림 등)

### 🤖 LLM 기반 태스크 식별
- **Claude 3.5 Sonnet**: 고품질 태스크 생성
- **상위 태스크 식별**: 기능별 그룹을 상위 태스크로 분류
- **하위 태스크 생성**: 상위 태스크를 구현 가능한 하위 작업으로 분해
- **프레임워크 비의존적 출력**: "무엇을" 구현해야 하는지에 집중 (특정 프레임워크 코드 제외)
- **OpenAPI 컨텍스트 매칭**: 기존 API 엔드포인트와 태스크 자동 매칭
- **LLM 기반 전처리**: 규칙 기반 대신 AI로 섹션 구분 및 그룹화 (35% 비용 절감)

### 📄 Markdown 파일 생성
- **상위 태스크별 파일 분리**: `1_인증.md`, `2_결제.md`, ...
- **구조화된 형식**: 목적, 엔드포인트, 데이터 모델, 로직, 보안, 예외 처리, 테스트
- **YAML Front Matter**: 메타데이터 자동 생성
- **Claude Code 호환**: 직접 복사하여 구현 가능

## 시스템 아키텍처

```
┌─────────────┐
│   PDF 입력  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│   PDF Extractor             │
│   - 텍스트/이미지/표 추출  │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│   OCR Engine (선택)         │
│   - 이미지 → 텍스트 변환   │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│   Preprocessor              │
│   - 정규화/섹션 구분/그룹화│
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│   LLM Planner               │
│   - 상위 태스크 식별       │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│   LLM TaskWriter            │
│   - 하위 태스크 생성       │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│   FileSplitter              │
│   - Markdown 파일 분리     │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│   출력 (Markdown 파일들)    │
│   - 1_인증.md              │
│   - 2_결제.md              │
│   - report.log             │
└─────────────────────────────┘
```

## 설치

### 사전 요구사항

- **Python 3.10 이상**
- **Tesseract OCR** (선택 - OCR 기능 사용 시)
  ```bash
  # macOS
  brew install tesseract tesseract-lang

  # Ubuntu/Debian
  sudo apt-get install tesseract-ocr tesseract-ocr-kor

  # Windows
  # https://github.com/UB-Mannheim/tesseract/wiki 에서 다운로드
  ```

### Python 패키지 설치

```bash
# 1. 저장소 클론
git clone <repository-url>
cd pdf-agent

# 2. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 설정
```

## 사용법

### CLI 사용법

#### 설치 후 전역 명령어 사용

```bash
# 개발 모드로 설치 (추천)
pip install -e .

# 전역 명령어로 사용
pdf2tasks analyze ./specs/app-v1.pdf --out ./output/
```

#### 기본 사용

```bash
# 기본 실행
pdf2tasks analyze test.pdf --out ./output

# 모든 기능 활성화
pdf2tasks analyze test.pdf --out ./output \
  --extract-images \
  --extract-tables \
  --ocr \
  --verbose
```

#### OpenAPI 컨텍스트 매칭 (권장)

```bash
# OpenAPI 디렉토리 지정하여 자동 엔드포인트 매칭
pdf2tasks analyze test.pdf --out ./output \
  --openapi-dir ./openapi \
  --use-llm-context \
  --use-llm-matching \
  --extract-tables \
  --extract-images

# OpenAPI JSON 파일 구조 예시:
# ./openapi/
#   ├── admin-api.json
#   ├── user-api.json
#   └── partner-api.json
```

#### 주요 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--out DIR` | 출력 디렉토리 | 필수 |
| `--clean` | 출력 디렉토리 정리 | False |
| `--extract-images` | 이미지 추출 | False |
| `--extract-tables` | 표 추출 | True |
| `--ocr` | OCR 사용 | False |
| `--analyze-images` | 이미지 분석 (Vision API) | False |
| `--openapi-dir DIR` | OpenAPI JSON 디렉토리 | None |
| `--use-llm-context` | LLM 기반 컨텍스트 추출 | False |
| `--use-llm-matching` | LLM 기반 엔드포인트 매칭 | False |
| `--verbose, -v` | 상세 로그 | False |

### Python 코드 사용

#### 1. PDF 추출

```python
from src.extractors.pdf_extractor import PDFExtractor

extractor = PDFExtractor(
    output_dir="./temp_images",
    extract_images=True,
    extract_tables=True
)

result = extractor.extract("sample.pdf")
print(f"총 {result.metadata.total_pages} 페이지")
print(f"추출된 텍스트: {len(result.pages)} 페이지")

extractor.cleanup()
```

#### 2. 전처리

```python
from src.preprocessor.preprocessor import Preprocessor

preprocessor = Preprocessor(
    normalize_text=True,
    remove_headers_footers=True,
    segment_sections=True,
    group_by_function=True
)

preprocess_result = preprocessor.process(pdf_result)
print(f"기능 그룹: {len(preprocess_result.functional_groups)}개")
```

#### 3. LLM 기반 태스크 식별

```python
from src.llm.planner.llm_planner import LLMPlanner

planner = LLMPlanner()
identified_tasks = planner.identify_tasks(preprocess_result)

print(f"식별된 태스크: {len(identified_tasks.tasks)}개")
```

#### 4. 하위 태스크 생성

```python
from src.llm.task_writer import LLMTaskWriter

writer = LLMTaskWriter()

for task in identified_tasks.tasks:
    result = writer.write_task(task, all_sections)
    print(f"{task.name}: {len(result.sub_tasks)}개 하위 태스크")
```

#### 5. Markdown 파일 생성

```python
from src.splitter.file_splitter import FileSplitter

splitter = FileSplitter(
    output_dir="./output",
    clean=True,
    add_front_matter=True
)

split_result = splitter.split(tasks_with_markdown)
print(f"생성된 파일: {split_result.success_count}개")

# 리포트 저장
splitter.save_report(split_result, filename="report.log")
```

## 모듈 구조

```
src/
├── extractors/         # PDF 추출
│   ├── pdf_extractor.py
│   ├── text_extractor.py
│   ├── image_extractor.py
│   ├── metadata_extractor.py
│   └── table_extractor.py
│
├── ocr/                # OCR 처리
│   ├── ocr_engine.py
│   ├── config.py
│   ├── preprocessor.py
│   ├── recognizer.py
│   └── postprocessor.py
│
├── preprocessor/       # 전처리
│   ├── preprocessor.py
│   ├── text_normalizer.py
│   ├── header_footer_remover.py
│   ├── section_segmenter.py
│   └── functional_grouper.py
│
├── llm/                # LLM 연동
│   ├── claude_client.py
│   ├── planner/        # 태스크 식별
│   │   └── llm_planner.py
│   ├── task_writer.py  # 하위 태스크 생성
│   └── prompts.py
│
├── splitter/           # 파일 분리
│   ├── file_splitter.py
│   └── filename_generator.py
│
├── types/              # 데이터 모델
│   └── models.py
│
└── utils/              # 유틸리티
    └── logger.py
```

## 테스트

```bash
# 전체 테스트 실행
pytest

# 단위 테스트만
pytest tests/unit/ -v

# 통합 테스트만
pytest tests/integration/ -v

# 특정 모듈 테스트
pytest tests/unit/test_filename_generator.py -v

# Coverage 리포트
pytest --cov=src --cov-report=html
open htmlcov/index.html

# 특정 마커 테스트만 실행
pytest -m unit  # 단위 테스트만
pytest -m integration  # 통합 테스트만
pytest -m "not slow"  # 느린 테스트 제외
```

## 문서

- [PDF Extractor 상세 문서](README_EXTRACTOR.md)
- [Preprocessor 상세 문서](README_PREPROCESSOR.md)
- [LLM Planner 상세 문서](README_LLM_PLANNER.md)
- [LLM TaskWriter 상세 문서](README_TASKWRITER.md)
- [FileSplitter 상세 문서](README_SPLITTER.md)
- [개발 세션 기록](CLAUDE.md)

## 트러블슈팅

### Tesseract 설치 확인

```bash
tesseract --version
tesseract --list-langs  # 한국어(kor) 확인
```

### API 키 오류

```bash
# .env 파일에 올바른 API 키 설정 확인
cat .env | grep ANTHROPIC_API_KEY
```

### 암호화된 PDF

암호화된 PDF는 현재 지원되지 않습니다. PDF 암호를 해제한 후 사용하세요.

### 메모리 부족

대용량 PDF 처리 시 메모리 부족 문제가 발생할 수 있습니다:
- 이미지 추출 옵션 비활성화 (`extract_images=False`)
- 페이지별 처리 (`extract_page()` 사용)

### 느린 처리 속도

- OCR 비활성화 (텍스트 PDF인 경우)
- 병렬 처리 worker 수 조정
- LLM 호출 최적화 (배치 처리)

## 성능

### 처리 속도
- **15페이지 PDF**: 약 9-10분 (LLM 호출 포함)
- **50페이지 PDF**: 약 20-30분 (LLM 호출 포함)
- **병목 구간**: LLM API 호출 (Planner + TaskWriter)

### 비용 (Claude 3.5 Sonnet 기준)
- **전처리 (LLM 기반)**: 약 $0.003/문서
- **태스크 식별**: 약 $0.01-$0.02/문서
- **태스크 작성**: 약 $0.01-$0.05/태스크
- **OpenAPI 분석**: 약 $0.001/엔드포인트
- **총 비용**: 문서당 평균 **$0.02-$0.10** (10개 태스크 기준)

### LLM 기반 전처리 효과
- **비용 절감**: 규칙 기반 대비 **35% 저렴**
- **섹션 통합**: **59% 개선** (39개 → 16개)
- **토큰 효율**: **45% 향상** (6,504 → 3,552 토큰)
- **처리 시간**: +10초 (허용 범위)

### 메모리 사용량
- **기본**: ~200-300 MB
- **이미지 추출 시**: ~500-800 MB
- **대용량 PDF**: ~1-2 GB

## 최근 개선사항 (2025-10)

### ✅ 완료
- **프레임워크 비의존적 프롬프트**: Prisma 스키마, NestJS 데코레이터 등 제거, "무엇을" 구현할지에 집중
- **OpenAPI 컨텍스트 매칭**: 기존 API 엔드포인트 자동 분석 및 태스크 매칭
- **LLM 기반 전처리**: 규칙 기반 대신 AI로 섹션 구분 및 그룹화 (35% 비용 절감, 59% 섹션 통합 개선)
- **비동기 병렬 TaskWriter**: Semaphore 기반 동시 요청 제한으로 429 에러 방지
- **로직 요약 필드 통일**: 프롬프트-파서 불일치 해결

### 🚀 로드맵

#### 단기 (1-2개월)
- [ ] E2E 테스트 자동화
- [ ] 성능 최적화 (병렬 처리 개선)
- [ ] 커스텀 프롬프트 템플릿 지원

#### 중기 (3-6개월)
- [ ] NestJS/Prisma 코드 생성기 연결
- [ ] Notion/Jira 자동 등록
- [ ] 다양한 기술 스택 템플릿 (Django, Spring 등)
- [ ] 프롬프트 A/B 테스트 및 자동 최적화

#### 장기 (6개월+)
- [ ] 실시간 협업 기능 (웹 UI)
- [ ] 기획서 변경 감지 및 차분 분석
- [ ] 다국어 지원 (영어, 일본어)

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 라이센스

MIT License

## 연락처

프로젝트 관련 문의: [GitHub Issues](https://github.com/...)
