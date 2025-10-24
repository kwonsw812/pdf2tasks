# PDF2Tasks CLI 사용 가이드

PDF2Tasks는 PDF 기획서를 AI 기반으로 분석하여 개발 태스크로 자동 변환하는 명령줄 도구입니다.

## 목차

1. [개요](#개요)
2. [설치](#설치)
3. [빠른 시작](#빠른-시작)
4. [사용법](#사용법)
5. [워크플로우](#워크플로우)
6. [출력 파일](#출력-파일)
7. [문제 해결](#문제-해결)
8. [고급 사용법](#고급-사용법)

---

## 개요

PDF2Tasks CLI는 다음과 같은 전체 파이프라인을 자동으로 실행합니다:

```
PDF 파일
  ↓
[1] PDF 추출 (텍스트, 표, 이미지)
  ↓
[2] OCR 처리 (선택 사항)
  ↓
[3] 전처리 (정규화, 섹션 구분)
  ↓
[4] LLM Planner (상위 태스크 식별)
  ↓
[5] LLM TaskWriter (하위 태스크 작성)
  ↓
[6] 파일 분리 (Markdown 파일 생성)
  ↓
[7] 리포트 생성
  ↓
출력 디렉토리
```

**특징:**
- ✅ 완전 자동화된 파이프라인
- ✅ Claude 3.5 Sonnet 활용
- ✅ NestJS/Prisma 기술 스택 최적화
- ✅ 상세한 로깅 및 리포트
- ✅ 에러 처리 및 복구 메커니즘

---

## 설치

### 1. 요구사항

- Python 3.10 이상
- Anthropic API 키 (Claude 접근용)
- Tesseract OCR (OCR 기능 사용 시)

### 2. 패키지 설치

```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. API 키 설정

Anthropic API 키를 환경 변수로 설정하세요:

```bash
# Linux/macOS
export ANTHROPIC_API_KEY='your-api-key-here'

# Windows (CMD)
set ANTHROPIC_API_KEY=your-api-key-here

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

또는 `.env` 파일 생성:

```bash
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

**API 키 발급 방법:**
1. [Anthropic Console](https://console.anthropic.com/) 접속
2. 로그인 또는 회원가입
3. Settings → API Keys → Create Key

---

## 빠른 시작

### 기본 사용법

```bash
python -m src.cli.main analyze <PDF파일> --out <출력디렉토리>
```

### 예시

```bash
# 간단한 예시
python -m src.cli.main analyze ./specs/app-v1.pdf --out ./output

# 출력 디렉토리 정리하고 처리
python -m src.cli.main analyze ./specs/app-v1.pdf --out ./output --clean

# 상세 로그 출력
python -m src.cli.main analyze ./specs/app-v1.pdf --out ./output --verbose
```

### 실행 결과

```
================================================================================
STARTING PDF PROCESSING PIPELINE
================================================================================

[1/6] PDF 추출 중...
✓ PDF 추출 완료 (2.35초)

[2/6] 전처리 중...
✓ 전처리 완료 (1.82초)

[3/6] 상위 태스크 식별 중 (LLM Planner)...
✓ 5개 태스크 식별 완료 (8.42초)

[4/6] 하위 태스크 작성 중 (LLM TaskWriter)...
  Writing task 1: 인증 및 회원관리
  Writing task 2: 결제 시스템
  ...
✓ 하위 태스크 작성 완료 (45.23초)

[5/6] 파일 분리 중...
✓ 5개 파일 생성 완료 (0.12초)

[6/6] 리포트 생성 중...
✓ 리포트 생성 완료

================================================================================
PIPELINE COMPLETED SUCCESSFULLY
Total time: 58.02초
Generated files: 5
Total cost: $0.153420
================================================================================
```

---

## 사용법

### 명령어 구조

```bash
python -m src.cli.main [OPTIONS] COMMAND [ARGS]...
```

### 명령어

#### `analyze`

PDF 문서를 분석하고 개발 태스크를 생성합니다.

```bash
python -m src.cli.main analyze <PDF_PATH> --out <OUTPUT_DIR> [OPTIONS]
```

**필수 인자:**
- `PDF_PATH`: 분석할 PDF 파일 경로
- `--out, -o <DIR>`: 출력 디렉토리

**선택 옵션:**

| 옵션 | 설명 | 기본값 |
|-----|------|--------|
| `--clean` | 출력 디렉토리의 기존 파일 삭제 | False |
| `--extract-images` | PDF에서 이미지 추출 | False |
| `--extract-tables` / `--no-extract-tables` | 표 추출 활성화/비활성화 | True |
| `--ocr` | OCR을 사용한 이미지 기반 텍스트 추출 | False |
| `--front-matter` / `--no-front-matter` | YAML Front Matter 추가 | True |
| `--api-key <KEY>` | Anthropic API 키 (환경 변수 대신 사용) | ANTHROPIC_API_KEY |
| `--model <MODEL>` | 사용할 Claude 모델 | claude-3-5-sonnet-20241022 |
| `--verbose, -v` | 상세 로그 출력 | False |
| `--dry-run` | 실제 처리 없이 미리보기 (구현 중) | False |

### 사용 예시

#### 1. 기본 분석

```bash
python -m src.cli.main analyze ./docs/spec.pdf --out ./tasks
```

#### 2. 이미지 및 표 추출 포함

```bash
python -m src.cli.main analyze ./docs/spec.pdf \
  --out ./tasks \
  --extract-images \
  --extract-tables
```

#### 3. 기존 출력 파일 정리 후 처리

```bash
python -m src.cli.main analyze ./docs/spec.pdf \
  --out ./tasks \
  --clean
```

#### 4. 상세 로그와 함께 실행

```bash
python -m src.cli.main analyze ./docs/spec.pdf \
  --out ./tasks \
  --verbose
```

#### 5. OCR 활성화 (이미지 기반 텍스트 추출)

```bash
python -m src.cli.main analyze ./scanned-doc.pdf \
  --out ./tasks \
  --ocr \
  --extract-images
```

**참고:** OCR 사용을 위해서는 시스템에 Tesseract OCR이 설치되어 있어야 합니다.

```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-kor

# Windows
# https://github.com/UB-Mannheim/tesseract/wiki 에서 설치
```

#### 6. 커스텀 모델 및 API 키 사용

```bash
python -m src.cli.main analyze ./docs/spec.pdf \
  --out ./tasks \
  --model claude-3-5-sonnet-20241022 \
  --api-key sk-ant-api03-your-key-here
```

#### 7. Front Matter 제외

```bash
python -m src.cli.main analyze ./docs/spec.pdf \
  --out ./tasks \
  --no-front-matter
```

---

## 워크플로우

### 1단계: PDF 추출

**처리 내용:**
- 텍스트 블록 추출 (폰트 정보 포함)
- 표 구조 인식 (pdfplumber)
- 이미지 추출 (옵션)
- 메타데이터 파싱

**출력:**
- 페이지별 텍스트 데이터
- 표 데이터 (2D 배열)
- 이미지 파일 (옵션)

### 2단계: OCR 처리 (선택 사항)

**처리 내용:**
- 추출된 이미지에 OCR 적용
- Tesseract OCR 사용
- 신뢰도 기반 필터링

**활성화 조건:**
- `--ocr` 옵션 사용 시
- `--extract-images`와 함께 사용 권장

### 3단계: 전처리

**처리 내용:**
- 텍스트 정규화 (유니코드 NFC, 공백 정리)
- 헤더/푸터 자동 제거
- 섹션 구분 (제목 패턴 인식)
- 기능별 그룹화 (인증, 결제, 관리자 등)

**출력:**
- 계층화된 섹션 구조
- 기능별 그룹 (FunctionalGroup)

### 4단계: LLM Planner

**처리 내용:**
- Claude를 사용한 상위 태스크 식별
- 중복 제거 (유사도 기반)
- 의존성 분석
- 우선순위 정렬

**출력:**
- 상위 태스크 목록 (IdentifiedTask)
- 토큰 사용량 및 비용

### 5단계: LLM TaskWriter

**처리 내용:**
- 각 상위 태스크를 하위 태스크로 세분화
- NestJS/Prisma 기술 스택 적용
- Markdown 문서 생성

**출력:**
- 상위 태스크별 Markdown 문서
- 하위 태스크 목록 (SubTask)

### 6단계: 파일 분리

**처리 내용:**
- 각 상위 태스크를 개별 파일로 저장
- 파일명 생성 (`{index}_{태스크명}.md`)
- YAML Front Matter 추가 (옵션)

**출력:**
- `1_인증_및_회원관리.md`
- `2_결제_시스템.md`
- `3_상품_관리.md`
- ...

### 7단계: 리포트 생성

**처리 내용:**
- 처리 통계 수집
- 토큰 사용량 및 비용 계산
- JSON 및 텍스트 리포트 생성

**출력:**
- `report.json` (JSON 형식)
- `report.log` (텍스트 형식)

---

## 출력 파일

### 디렉토리 구조

```
output/
├── 1_인증_및_회원관리.md
├── 2_결제_시스템.md
├── 3_상품_관리.md
├── 4_알림_시스템.md
├── 5_관리자_대시보드.md
├── report.json
├── report.log
└── temp_images/  (이미지 추출 시)
    ├── page_1_img_0.png
    ├── page_2_img_0.png
    └── ...
```

### Markdown 파일 형식

각 태스크 파일은 다음과 같은 구조를 가집니다:

```markdown
---
title: 인증 및 회원관리
index: 1
generated: 2025-10-23T16:30:42.123456
source_pdf: ./specs/app-v1.pdf
---

# 인증 및 회원관리 — 상위 태스크 1

## 상위 태스크 개요
- **설명:** 사용자 인증 및 회원 정보 관리 기능
- **모듈/영역:** AuthModule
- **관련 엔티티:** User, Session, Token
- **참고:** PDF 원문 p.1–5

---

## 하위 태스크 목록

### 1.1 회원가입 API 구현
- **목적:** 신규 사용자 등록 기능 제공
- **엔드포인트:** `POST /api/auth/register`
- **데이터 모델:** User { email, password, name, ... }
- **로직 요약:**
  1. 이메일 중복 체크
  2. 비밀번호 해싱 (bcrypt)
  3. DB 저장 (Prisma)
  4. 환영 이메일 발송
- **권한/보안:** Public 엔드포인트
- **예외 처리:**
  - 409: 이메일 중복
  - 400: 유효하지 않은 입력
- **테스트 포인트:**
  - 정상 가입 시나리오
  - 중복 이메일 체크
  - 비밀번호 해싱 확인

### 1.2 로그인 API 구현
...
```

### report.json

JSON 형식의 상세 리포트:

```json
{
  "summary": {
    "pdf_file": "./specs/app-v1.pdf",
    "total_pages": 50,
    "generated_files": 5,
    "total_processing_time": 58.02,
    "timestamp": "2025-10-23T16:30:00"
  },
  "extraction": {
    "text_pages": 50,
    "images_extracted": 12,
    "tables_found": 8,
    "processing_time": 2.35
  },
  "preprocessing": {
    "sections_identified": 45,
    "functional_groups": 10,
    "processing_time": 1.82
  },
  "llm": {
    "planner_calls": 1,
    "task_writer_calls": 5,
    "total_tokens_used": 45320,
    "total_cost": 0.15342,
    "processing_time": 53.65
  },
  "output_files": [
    {
      "file_path": "./output/1_인증_및_회원관리.md",
      "file_name": "1_인증_및_회원관리.md",
      "size_bytes": 8430,
      "task_index": 1,
      "task_name": "인증 및 회원관리"
    },
    ...
  ],
  "errors": []
}
```

### report.log

텍스트 형식의 요약 리포트:

```
[PDF2Tasks Report]
============================================================

PDF File: ./specs/app-v1.pdf
Total Pages: 50
Generated Files: 5
Processing Date: 2025-10-23 16:30:00
Total Processing Time: 58.02s

--- Extraction ---
Text Pages: 50
Images Extracted: 12
Tables Found: 8
Processing Time: 2.35s

--- Preprocessing ---
Sections Identified: 45
Functional Groups: 10
Processing Time: 1.82s

--- LLM Analysis ---
Planner Calls: 1
TaskWriter Calls: 5
Total Tokens Used: 45,320
Total Cost: $0.153420
Processing Time: 53.65s

--- Output Files ---
1. 1_인증_및_회원관리.md (8.2 KB)
2. 2_결제_시스템.md (9.5 KB)
3. 3_상품_관리.md (7.8 KB)
4. 4_알림_시스템.md (6.2 KB)
5. 5_관리자_대시보드.md (5.9 KB)

--- Errors ---
None

============================================================
```

---

## 문제 해결

### 일반적인 오류

#### 1. API 키 오류

**증상:**
```
Error: Anthropic API key not provided.
```

**해결 방법:**
```bash
# 환경 변수 설정
export ANTHROPIC_API_KEY='your-api-key-here'

# 또는 --api-key 옵션 사용
python -m src.cli.main analyze ./doc.pdf --out ./out --api-key your-key
```

#### 2. PDF 파일 없음

**증상:**
```
Error: Invalid value for 'PDF_PATH': Path 'file.pdf' does not exist.
```

**해결 방법:**
- 파일 경로 확인
- 절대 경로 사용 권장

```bash
python -m src.cli.main analyze /absolute/path/to/file.pdf --out ./out
```

#### 3. Tesseract OCR 미설치 (OCR 사용 시)

**증상:**
```
Warning: OCR 모듈이 설치되지 않았습니다. OCR을 건너뜁니다.
```

**해결 방법:**
```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-kor
```

#### 4. 메모리 부족

**증상:**
- 대용량 PDF 처리 시 느린 속도 또는 중단

**해결 방법:**
- 이미지 추출 비활성화: `--no-extract-images`
- 표 추출 비활성화: `--no-extract-tables`
- PDF를 작은 단위로 분할하여 처리

#### 5. LLM API 오류

**증상:**
```
Error: LLM Planner: Rate limit exceeded
```

**해결 방법:**
- API 사용량 제한 확인
- 잠시 후 재시도
- Anthropic Console에서 사용량 확인

### 종료 코드

| 코드 | 의미 | 조치 사항 |
|-----|------|----------|
| 0 | 성공 | - |
| 1 | 일반 에러 | 로그 확인 |
| 2 | 파일 없음 또는 잘못된 인자 | 경로 및 인자 확인 |
| 4 | API 키 없음 또는 잘못됨 | API 키 확인 |
| 130 | 사용자 중단 (Ctrl+C) | - |

### 로그 파일 확인

상세한 오류 정보는 로그에서 확인 가능:

```bash
# 상세 로그 출력
python -m src.cli.main analyze ./doc.pdf --out ./out --verbose 2>&1 | tee debug.log
```

---

## 고급 사용법

### 1. 배치 처리

여러 PDF 파일을 순차적으로 처리:

```bash
#!/bin/bash
# batch_process.sh

for pdf in ./specs/*.pdf; do
  filename=$(basename "$pdf" .pdf)
  echo "Processing: $filename"

  python -m src.cli.main analyze \
    "$pdf" \
    --out "./output/$filename" \
    --clean \
    --verbose

  echo "✓ Completed: $filename"
done
```

### 2. Docker 사용

Dockerfile 예시:

```dockerfile
FROM python:3.10-slim

# Install Tesseract (for OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-kor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set environment variable
ENV ANTHROPIC_API_KEY=""

# Run CLI
ENTRYPOINT ["python", "-m", "src.cli.main"]
CMD ["analyze", "--help"]
```

실행:

```bash
docker build -t pdf2tasks .
docker run -e ANTHROPIC_API_KEY=your-key \
  -v $(pwd)/specs:/specs \
  -v $(pwd)/output:/output \
  pdf2tasks analyze /specs/app-v1.pdf --out /output
```

### 3. CI/CD 통합

GitHub Actions 예시:

```yaml
name: Generate Tasks from PDF

on:
  push:
    paths:
      - 'specs/**.pdf'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Generate tasks
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python -m src.cli.main analyze \
            ./specs/app-v1.pdf \
            --out ./tasks \
            --clean

      - name: Commit results
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add tasks/
          git commit -m "Auto-generate tasks from PDF"
          git push
```

### 4. 커스터마이징

프로그래밍 방식으로 CLI 사용:

```python
from src.cli.orchestrator import Orchestrator, OrchestratorConfig

config = OrchestratorConfig(
    pdf_path="./specs/app-v1.pdf",
    output_dir="./output",
    extract_images=False,
    extract_tables=True,
    use_ocr=False,
    clean_output=True,
    add_front_matter=True,
    api_key="your-api-key",
    model="claude-3-5-sonnet-20241022",
    verbose=True,
)

orchestrator = Orchestrator(config)
report = orchestrator.run()

print(f"Generated {report.summary.generated_files} files")
print(f"Total cost: ${report.llm.total_cost:.6f}")
```

---

## 성능 및 비용

### 처리 속도

| PDF 크기 | 예상 시간 | 비고 |
|---------|-----------|------|
| 10 페이지 | ~20초 | 주로 LLM 호출 시간 |
| 50 페이지 | ~1분 | 중간 규모 기획서 |
| 100 페이지 | ~2-3분 | 대규모 기획서 |

### 토큰 사용량 및 비용

Claude 3.5 Sonnet 기준:

- **입력:** $3 per 1M tokens
- **출력:** $15 per 1M tokens

**예상 비용:**
- 10 페이지: ~$0.05
- 50 페이지: ~$0.15-$0.30
- 100 페이지: ~$0.50-$0.80

**참고:** 실제 비용은 PDF 내용의 복잡도에 따라 달라질 수 있습니다.

---

## 관련 문서

- [PDF Extractor 사용 가이드](./README_EXTRACTOR.md)
- [Preprocessor 사용 가이드](./README_PREPROCESSOR.md)
- [LLM Planner 사용 가이드](./README_LLM_PLANNER.md)
- [TaskWriter 사용 가이드](./README_TASKWRITER.md)
- [프로젝트 전체 문서](./CLAUDE.md)

---

## 라이센스

이 프로젝트는 내부용입니다.

---

## 문의

문제가 발생하거나 질문이 있는 경우 프로젝트 관리자에게 문의하세요.
