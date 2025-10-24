# PDF Extractor

Python 기반 PDF 추출 라이브러리로, PDF 파일에서 텍스트, 이미지, 메타데이터, 표를 추출합니다.

## 기능

- **텍스트 추출**: PDF의 모든 텍스트를 폰트 정보, 위치 메타데이터와 함께 추출
- **이미지 추출**: PDF 내의 모든 이미지를 파일로 저장
- **메타데이터 추출**: PDF 문서 정보 (제목, 저자, 페이지 수 등) 추출
- **표 추출**: PDF 내의 표 구조를 인식하여 2차원 배열로 추출
- **에러 핸들링**: 강력한 예외 처리 및 로깅 시스템

## 설치

### 1. 가상환경 생성 및 활성화

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

## 빠른 시작

### 기본 사용법

```python
from extractors import PDFExtractor
from utils.logger import setup_logging

# 로깅 설정
setup_logging()

# Extractor 초기화
extractor = PDFExtractor()

# PDF 전체 추출
result = extractor.extract("sample.pdf")

# 결과 확인
print(f"총 페이지: {result.metadata.total_pages}")
for page in result.pages:
    print(f"페이지 {page.page_number}: "
          f"{len(page.text)} 텍스트, "
          f"{len(page.images)} 이미지, "
          f"{len(page.tables)} 표")

# 임시 파일 정리
extractor.cleanup()
```

### 텍스트만 추출 (빠른 모드)

```python
extractor = PDFExtractor()
text = extractor.extract_text_only("sample.pdf")
print(text)
```

### 메타데이터만 추출

```python
extractor = PDFExtractor()
metadata = extractor.get_metadata("sample.pdf")
print(f"제목: {metadata.title}")
print(f"저자: {metadata.author}")
print(f"페이지 수: {metadata.total_pages}")
```

### 특정 페이지만 추출

```python
extractor = PDFExtractor()
page = extractor.extract_page("sample.pdf", page_number=1)
print(f"페이지 1의 텍스트 블록: {len(page.text)}")
```

### 선택적 추출 (이미지 제외)

```python
extractor = PDFExtractor(
    extract_images=False,  # 이미지 추출 건너뛰기
    extract_tables=True
)
result = extractor.extract("sample.pdf")
```

## 주요 클래스

### PDFExtractor

통합 PDF 추출 인터페이스

**초기화 매개변수:**
- `output_dir`: 추출된 이미지를 저장할 디렉토리 (기본값: `"./temp_images"`)
- `extract_images`: 이미지 추출 여부 (기본값: `True`)
- `extract_tables`: 표 추출 여부 (기본값: `True`)

**주요 메서드:**
- `extract(pdf_path)`: PDF 전체 추출
- `extract_page(pdf_path, page_number)`: 특정 페이지 추출
- `extract_text_only(pdf_path)`: 텍스트만 추출
- `get_metadata(pdf_path)`: 메타데이터만 추출
- `cleanup()`: 임시 파일 정리

## 데이터 모델

### PDFExtractResult

```python
{
    "metadata": PDFMetadata,
    "pages": List[PDFPage]
}
```

### PDFMetadata

```python
{
    "title": Optional[str],
    "author": Optional[str],
    "subject": Optional[str],
    "creator": Optional[str],
    "producer": Optional[str],
    "creation_date": Optional[datetime],
    "modification_date": Optional[datetime],
    "total_pages": int
}
```

### PDFPage

```python
{
    "page_number": int,
    "text": List[ExtractedText],
    "images": List[ExtractedImage],
    "tables": List[ExtractedTable]
}
```

### ExtractedText

```python
{
    "page_number": int,
    "text": str,
    "metadata": {
        "font_size": Optional[float],
        "font_name": Optional[str],
        "position": {
            "x": float,
            "y": float,
            "width": Optional[float],
            "height": Optional[float]
        }
    }
}
```

### ExtractedImage

```python
{
    "page_number": int,
    "image_path": str,
    "width": int,
    "height": int
}
```

### ExtractedTable

```python
{
    "page_number": int,
    "rows": List[List[str]],  # 2차원 배열
    "position": Position
}
```

## 예외 처리

```python
from extractors.exceptions import (
    FileNotFoundError,
    PDFParseError,
    EncryptedPDFError,
    ImageExtractionError,
    DiskSpaceError
)

try:
    result = extractor.extract("sample.pdf")
except FileNotFoundError as e:
    print(f"파일을 찾을 수 없습니다: {e}")
except EncryptedPDFError as e:
    print(f"암호화된 PDF입니다: {e}")
except PDFParseError as e:
    print(f"PDF 파싱 실패: {e}")
```

## 테스트

```bash
# 테스트 스크립트 실행
python test_extractor.py

# 예제 실행
python examples/basic_usage.py
```

## 프로젝트 구조

```
pdf-agent/
├── src/
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py      # 통합 인터페이스
│   │   ├── text_extractor.py     # 텍스트 추출
│   │   ├── image_extractor.py    # 이미지 추출
│   │   ├── metadata_extractor.py # 메타데이터 추출
│   │   ├── table_extractor.py    # 표 추출
│   │   └── exceptions.py         # 예외 정의
│   ├── types/
│   │   ├── __init__.py
│   │   └── models.py             # 데이터 모델
│   └── utils/
│       ├── __init__.py
│       └── logger.py             # 로깅 설정
├── examples/
│   └── basic_usage.py            # 사용 예제
├── test_extractor.py             # 테스트 스크립트
├── requirements.txt              # 패키지 의존성
├── pyproject.toml                # 프로젝트 설정
└── README_EXTRACTOR.md           # 이 파일
```

## 사용된 라이브러리

- **PyMuPDF (fitz)**: 텍스트 및 이미지 추출, 메타데이터 파싱
- **pdfplumber**: 표 구조 인식 및 추출
- **Pillow**: 이미지 처리
- **Pydantic**: 데이터 검증 및 타입 힌트

## 성능

- 50페이지 PDF 처리 시간: 약 5분 이내
- 메모리 효율적인 페이지별 처리
- 일부 페이지 실패 시에도 나머지 페이지 계속 처리

## 제한사항

- 암호화된 PDF는 처리할 수 없습니다
- 복잡한 중첩 표는 정확도가 떨어질 수 있습니다
- 손상된 PDF 파일은 PDFParseError를 발생시킵니다

## 라이선스

이 프로젝트는 PDF Agent의 일부입니다.

## 작성자

PDF Agent Development Team

## 버전

0.1.0 - 초기 구현
