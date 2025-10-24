# PDF Preprocessor 모듈 사용 가이드

PDF Agent의 전처리(Preprocessor) 모듈은 추출된 PDF 콘텐츠를 정규화하고 구조화하여 LLM 분석에 적합한 형태로 변환합니다.

## 목차

1. [개요](#개요)
2. [설치](#설치)
3. [주요 기능](#주요-기능)
4. [사용 방법](#사용-방법)
5. [API 레퍼런스](#api-레퍼런스)
6. [고급 사용법](#고급-사용법)
7. [성능 고려사항](#성능-고려사항)

---

## 개요

Preprocessor 모듈은 다음과 같은 전처리 파이프라인을 제공합니다:

1. **텍스트 정규화**: 유니코드 정규화, 공백 제거, 특수문자 정제
2. **헤더/푸터 제거**: 반복되는 페이지 번호, 헤더, 푸터 자동 감지 및 제거
3. **섹션 구분**: 제목 패턴 인식 및 계층 구조 생성
4. **기능별 그룹화**: 키워드 기반 섹션 분류 (인증, 결제, 관리자 등)

---

## 설치

프로젝트의 requirements.txt에 포함된 패키지를 설치하세요:

```bash
pip install -r requirements.txt
```

---

## 주요 기능

### 1. 텍스트 정규화 (TextNormalizer)

- Unicode NFC 정규화
- 제어 문자 제거
- 연속 공백/줄바꿈 정규화
- 특수 따옴표 표준화
- 전각 문자 → 반각 문자 변환

### 2. 헤더/푸터 제거 (HeaderFooterRemover)

- 페이지별 반복 텍스트 패턴 감지
- 좌표 기반 상단/하단 영역 필터링
- 페이지 번호 패턴 인식 (e.g., "Page 1", "1/10")

### 3. 섹션 구분 (SectionSegmenter)

- 제목 패턴 매칭:
  - "1. 제목", "1.1 제목"
  - "## 제목" (Markdown)
  - "가. 제목" (한글 열거)
- 폰트 크기 기반 헤딩 감지
- 계층적 섹션 구조 생성

### 4. 기능별 그룹화 (FunctionalGrouper)

- 키워드 기반 자동 분류
- 기본 제공 카테고리: 인증, 결제, 사용자관리, 상품관리, 검색, 알림, 관리자, API, 보안
- 커스텀 키워드 지원

---

## 사용 방법

### 기본 사용법

```python
from src.extractors.pdf_extractor import PDFExtractor
from src.preprocessor.preprocessor import Preprocessor

# 1. PDF 추출
extractor = PDFExtractor()
pdf_result = extractor.extract("document.pdf")

# 2. 전처리
preprocessor = Preprocessor()
result = preprocessor.process(pdf_result)

# 3. 결과 확인
print(f"기능 그룹 수: {len(result.functional_groups)}")
for group in result.functional_groups:
    print(f"- {group.name}: {len(group.sections)} sections")
```

### 선택적 기능 사용

```python
# 텍스트 정규화와 섹션 구분만 수행
preprocessor = Preprocessor(
    normalize_text=True,
    remove_headers_footers=False,
    segment_sections=True,
    group_by_function=False
)

result = preprocessor.process(pdf_result)
```

### 커스텀 키워드로 그룹화

```python
custom_keywords = {
    "배송": ["배송", "택배", "운송", "물류"],
    "재고": ["재고", "입고", "출고", "수량"],
    "마케팅": ["프로모션", "광고", "이벤트"]
}

preprocessor = Preprocessor(custom_keywords=custom_keywords)
result = preprocessor.process(pdf_result)
```

---

## API 레퍼런스

### Preprocessor

**초기화 파라미터:**

```python
Preprocessor(
    normalize_text: bool = True,
    remove_headers_footers: bool = True,
    segment_sections: bool = True,
    group_by_function: bool = True,
    custom_keywords: Optional[Dict[str, List[str]]] = None
)
```

**주요 메서드:**

- `process(pdf_result: PDFExtractResult) -> PreprocessResult`
  - PDF 추출 결과를 전처리합니다.

- `get_statistics() -> Dict[str, float]`
  - 각 단계별 처리 시간 통계를 반환합니다.

### TextNormalizer

```python
normalizer = TextNormalizer(
    normalize_unicode=True,
    remove_control_chars=True,
    normalize_whitespace=True
)

normalized_text = normalizer.normalize("여러    공백    텍스트")
```

**추가 메서드:**

- `clean_special_characters(text, keep_chars=None)`
- `remove_excessive_punctuation(text)`
- `normalize_quotes(text)`
- `remove_urls(text)`
- `normalize_numbers(text)`

### HeaderFooterRemover

```python
remover = HeaderFooterRemover(
    min_repetition=3,          # 최소 반복 횟수
    position_threshold=50.0,   # 상단/하단 임계값 (points)
    similarity_threshold=0.9   # 유사도 임계값
)

cleaned_result, headers, footers = remover.remove_headers_footers(pdf_result)
```

### SectionSegmenter

```python
segmenter = SectionSegmenter(
    min_heading_font_size=12.0,
    font_size_ratio_threshold=1.2
)

sections = segmenter.segment(pdf_result)
```

**유틸리티 메서드:**

- `flatten_sections(sections)` - 계층 구조를 평면 리스트로 변환
- `get_section_by_title(sections, title)` - 제목으로 섹션 검색

### FunctionalGrouper

```python
grouper = FunctionalGrouper(custom_keywords={
    "배송": ["배송", "택배"]
})

groups = grouper.group_sections(sections)
```

**유틸리티 메서드:**

- `add_keyword_mapping(group_name, keywords)` - 키워드 추가
- `remove_group(group_name)` - 그룹 제거
- `get_group_keywords(group_name)` - 그룹의 키워드 조회
- `list_all_groups()` - 모든 그룹 이름 나열

---

## 고급 사용법

### 1. Markdown 문서 생성

```python
def export_to_markdown(result: PreprocessResult, output_path: str):
    """전처리 결과를 Markdown으로 출력"""
    lines = [f"# {result.metadata.title or 'Document'}\n\n"]

    for group in result.functional_groups:
        lines.append(f"## {group.name}\n\n")

        for section in group.sections:
            lines.append(f"### {section.title}\n\n")
            lines.append(f"*참고: PDF p.{section.page_range.start}-{section.page_range.end}*\n\n")
            lines.append(f"{section.content}\n\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
```

### 2. 특정 기능 그룹만 추출

```python
result = preprocessor.process(pdf_result)

# '인증' 그룹만 추출
auth_group = next((g for g in result.functional_groups if g.name == "인증"), None)
if auth_group:
    for section in auth_group.sections:
        print(f"- {section.title}")
```

### 3. 섹션 계층 구조 순회

```python
def print_section_tree(section, indent=0):
    prefix = "  " * indent
    print(f"{prefix}- {section.title} (Level {section.level})")
    for subsection in section.subsections:
        print_section_tree(subsection, indent + 1)

for group in result.functional_groups:
    for section in group.sections:
        print_section_tree(section)
```

### 4. 성능 모니터링

```python
preprocessor = Preprocessor()
result = preprocessor.process(pdf_result)

# 통계 확인
stats = preprocessor.get_statistics()
print(f"Total time: {stats['total_time']:.2f}s")
print(f"  - Normalization: {stats['normalization_time']:.2f}s")
print(f"  - Header/Footer removal: {stats['header_footer_removal_time']:.2f}s")
print(f"  - Segmentation: {stats['segmentation_time']:.2f}s")
print(f"  - Grouping: {stats['grouping_time']:.2f}s")
```

---

## 성능 고려사항

### 처리 시간

- **소형 문서** (10-20 페이지): < 5초
- **중형 문서** (50 페이지): < 15초
- **대형 문서** (100+ 페이지): < 30초

### 최적화 팁

1. **이미지/표 추출 비활성화**: 텍스트만 필요한 경우
   ```python
   extractor = PDFExtractor(extract_images=False, extract_tables=False)
   ```

2. **선택적 전처리**: 필요한 단계만 활성화
   ```python
   preprocessor = Preprocessor(
       normalize_text=True,
       remove_headers_footers=False,  # 헤더/푸터 없는 문서
       segment_sections=True,
       group_by_function=False  # 그룹화 불필요
   )
   ```

3. **헤더/푸터 제거 파라미터 조정**:
   ```python
   # 헤더/푸터가 많이 반복되지 않는 경우
   remover = HeaderFooterRemover(min_repetition=2)
   ```

### 메모리 사용량

- 페이지당 약 1-2 MB
- 100 페이지 문서: ~100-200 MB 메모리 사용

---

## 데이터 모델

### PreprocessResult

```python
{
    "functional_groups": [FunctionalGroup],
    "metadata": PDFMetadata,
    "removed_header_patterns": [str],
    "removed_footer_patterns": [str]
}
```

### FunctionalGroup

```python
{
    "name": str,
    "sections": [Section],
    "keywords": [str]
}
```

### Section

```python
{
    "title": str,
    "level": int,
    "content": str,
    "page_range": PageRange,
    "subsections": [Section]
}
```

---

## 에러 처리

```python
from src.preprocessor.exceptions import (
    PreprocessorError,
    NormalizationError,
    SegmentationError,
    GroupingError,
    InvalidContentError
)

try:
    result = preprocessor.process(pdf_result)
except InvalidContentError as e:
    print(f"Invalid content: {e}")
except SegmentationError as e:
    print(f"Segmentation failed: {e}")
except PreprocessorError as e:
    print(f"Preprocessing error: {e}")
```

---

## 테스트

테스트 스크립트 실행:

```bash
# 기본 테스트 (PDF 파일 없이)
python test_preprocessor.py

# PDF 파일로 전체 파이프라인 테스트
python test_preprocessor.py path/to/your/document.pdf
```

예제 실행:

```bash
python examples/preprocessor_usage.py
```

---

## 트러블슈팅

### 1. 섹션이 감지되지 않음

**원인**: 폰트 정보가 없거나 제목 패턴이 일치하지 않음

**해결책**:
```python
# 폰트 크기 임계값 낮추기
segmenter = SectionSegmenter(
    min_heading_font_size=10.0,
    font_size_ratio_threshold=1.1
)
```

### 2. 헤더/푸터가 제거되지 않음

**원인**: 반복 횟수가 부족하거나 위치 임계값이 부적절

**해결책**:
```python
# 파라미터 조정
remover = HeaderFooterRemover(
    min_repetition=2,        # 최소 반복 횟수 낮추기
    position_threshold=100.0  # 영역 확대
)
```

### 3. 기능 그룹이 생성되지 않음

**원인**: 키워드 매칭 실패

**해결책**:
```python
# 커스텀 키워드 추가
custom_keywords = {
    "인증": ["로그인", "회원가입", "sign in", "sign up"]
}
preprocessor = Preprocessor(custom_keywords=custom_keywords)
```

---

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## 문의

문제가 발생하거나 기능 요청이 있으면 GitHub Issues에 등록해주세요.
