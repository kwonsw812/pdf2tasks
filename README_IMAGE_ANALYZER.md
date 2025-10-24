# Image Analyzer Module

Claude Vision API를 사용하여 PDF 기획서 내 화면 설계 이미지를 자동 분석하고 UI/UX 요구사항을 추출하는 모듈입니다.

## 개요

Image Analyzer는 다음과 같은 기능을 제공합니다:

- **화면 설계 이미지 자동 분석**: Claude Vision API를 통해 UI 컴포넌트, 레이아웃, 사용자 플로우 자동 인식
- **배치 처리**: 여러 이미지를 병렬로 분석 (최대 3개 동시 처리)
- **컨텍스트 기반 분석**: 주변 텍스트를 활용한 정확한 분석
- **비용 및 토큰 추적**: 실시간 비용 계산 및 토큰 사용량 모니터링

## 주요 구성 요소

### 1. VisionClient (`src/llm/vision_client.py`)

Claude Vision API와의 통신을 담당하는 클라이언트입니다.

**주요 기능:**
- 이미지 base64 인코딩
- Vision API 호출 및 응답 처리
- 에러 핸들링 및 재시도
- 비용 계산

**지원 포맷:**
- PNG, JPG/JPEG, GIF, WebP

### 2. ImageAnalyzer (`src/llm/image_analyzer.py`)

이미지 분석을 위한 통합 인터페이스입니다.

**주요 메서드:**
- `analyze_image()`: 단일 이미지 분석
- `analyze_batch()`: 배치 이미지 분석 (병렬)
- `estimate_cost()`: 비용 추정
- `get_analysis_summary()`: 분석 결과 요약

### 3. Vision Prompts (`src/llm/vision_prompts.py`)

Vision API용 프롬프트 템플릿 및 검증 함수를 제공합니다.

**주요 함수:**
- `build_vision_analysis_prompt()`: 분석용 프롬프트 생성
- `validate_vision_response()`: 응답 검증
- `estimate_vision_tokens()`: 토큰 사용량 추정

## 데이터 모델

### UIComponent
```python
{
    "type": str,           # button, input, card, navigation, modal 등
    "label": Optional[str], # 컴포넌트 라벨
    "position": Optional[str], # top, center, bottom 등
    "description": str     # 컴포넌트 기능 설명
}
```

### ImageAnalysis
```python
{
    "image_path": str,
    "page_number": int,
    "screen_title": Optional[str],
    "screen_type": str,    # login, dashboard, list, detail, form 등
    "ui_components": List[UIComponent],
    "layout_structure": str,
    "user_flow": Optional[str],
    "confidence": float,   # 0-100
    "processing_time": float,
    "token_usage": TokenUsage
}
```

### ImageAnalysisBatchResult
```python
{
    "analyses": List[ImageAnalysis],
    "total_images": int,
    "success_count": int,
    "failure_count": int,
    "total_processing_time": float,
    "total_tokens_used": int,
    "total_cost": float
}
```

## 사용 방법

### 기본 사용 (단일 이미지)

```python
from src.llm.image_analyzer import ImageAnalyzer

# Initialize analyzer
analyzer = ImageAnalyzer(
    api_key="your-anthropic-api-key",
    model="claude-3-5-sonnet-20241022"
)

# Analyze single image
result = analyzer.analyze_image(
    image_path="./screenshots/login_screen.png",
    page_number=5,
    context="사용자 인증 기능 섹션"
)

# Display results
print(f"Screen: {result.screen_title}")
print(f"Type: {result.screen_type}")
print(f"Components: {len(result.ui_components)}")
print(f"Confidence: {result.confidence}%")
```

### 배치 분석 (여러 이미지)

```python
from src.types.models import ExtractedImage

# Prepare images
images = [
    ExtractedImage(
        page_number=5,
        image_path="./screens/login.png",
        width=800,
        height=600
    ),
    ExtractedImage(
        page_number=7,
        image_path="./screens/dashboard.png",
        width=1200,
        height=800
    ),
]

# Context for each page
context_map = {
    5: "사용자 로그인 기능",
    7: "관리자 대시보드"
}

# Analyze batch
batch_result = analyzer.analyze_batch(
    images=images,
    context_map=context_map,
    max_concurrent=3
)

# Display summary
print(f"Total: {batch_result.total_images}")
print(f"Success: {batch_result.success_count}")
print(f"Cost: ${batch_result.total_cost:.4f}")
```

### CLI 사용

```bash
# 이미지 추출 및 분석 활성화
python -m src.cli.main analyze ./specs/app-v1.pdf \
    --out ./output \
    --extract-images \
    --analyze-images \
    --api-key YOUR_API_KEY

# 환경 변수 사용
export ANTHROPIC_API_KEY='your-key-here'
python -m src.cli.main analyze ./specs/app-v1.pdf \
    --out ./output \
    --extract-images \
    --analyze-images
```

## 분석 결과 예시

```json
{
  "screen_title": "로그인 화면",
  "screen_type": "login",
  "ui_components": [
    {
      "type": "input",
      "label": "이메일",
      "position": "center",
      "description": "사용자 이메일 입력 필드"
    },
    {
      "type": "input",
      "label": "비밀번호",
      "position": "center",
      "description": "비밀번호 입력 필드 (마스킹)"
    },
    {
      "type": "button",
      "label": "로그인",
      "position": "center",
      "description": "로그인 버튼 클릭 시 인증 수행"
    },
    {
      "type": "navigation",
      "label": "회원가입",
      "position": "bottom",
      "description": "회원가입 페이지로 이동"
    }
  ],
  "layout_structure": "단일 컬럼 중앙 정렬, 모바일 최적화 레이아웃",
  "user_flow": "이메일 입력 → 비밀번호 입력 → 로그인 버튼 → 대시보드 이동",
  "confidence": 95.0
}
```

## 성능 및 비용

### 처리 속도
- 단일 이미지: 5-10초
- 배치 처리 (10개, 동시 3개): 30-60초

### 토큰 사용량 (평균)
- 입력: 1,200 tokens/image (이미지 크기 포함)
- 출력: 500 tokens/image
- 총합: 1,700 tokens/image

### 예상 비용 (Claude 3.5 Sonnet)
- 단일 이미지: $0.01-$0.02
- 10개 이미지: $0.10-$0.20
- 50개 이미지: $0.50-$1.00

**참고**: 실제 비용은 이미지 크기 및 복잡도에 따라 달라질 수 있습니다.

## 오류 처리

### 재시도 로직
- 최대 2회 자동 재시도
- JSON 파싱 실패 시 재시도
- API 에러 시 로깅 후 재시도

### 부분 실패 허용
- 배치 처리 시 일부 이미지 실패해도 나머지 계속 진행
- 실패한 이미지는 failure_count에 기록

### 에러 종류
- `FileNotFoundError`: 이미지 파일 없음
- `ValueError`: 지원하지 않는 이미지 포맷
- `APIConnectionError`: API 연결 실패
- `APIRateLimitError`: Rate limit 초과
- `JSONParseError`: JSON 파싱 실패
- `LLMError`: 일반 LLM 에러

## 테스트

### 단위 테스트 실행

```bash
# 전체 테스트
python test_image_analyzer.py

# API 키 없이 실행 (일부 테스트 스킵)
python test_image_analyzer.py
# ✓ Vision Prompts
# ✓ VisionClient Encoding
# ✓ Cost Estimation
# ⚠ ImageAnalyzer Integration (SKIPPED - no API key)
```

### 예제 실행

```bash
# 예제 코드 실행
python examples/image_analyzer_usage.py
```

## 제한사항

1. **API 키 필수**: Anthropic API 키 필요
2. **지원 포맷**: PNG, JPG, JPEG, GIF, WebP만 지원
3. **이미지 크기**: 최대 5MB 권장
4. **동시 처리**: 최대 3개 권장 (API Rate Limit)
5. **한국어 중심**: 프롬프트가 한국어 기획서에 최적화됨

## 개선 계획

- [ ] 다국어 프롬프트 지원
- [ ] 커스텀 UI 컴포넌트 타입 지원
- [ ] 이미지 품질 검증
- [ ] 분석 결과 캐싱
- [ ] 비용 알림 및 예산 관리

## 관련 모듈

- **PDF Extractor**: 이미지 추출
- **Preprocessor**: 텍스트 전처리 및 컨텍스트 생성
- **LLM Planner**: 상위 태스크 식별
- **Reporter**: 비용 및 통계 리포트

## 참고 문서

- [Claude Vision API 문서](https://docs.anthropic.com/claude/docs/vision)
- [README_CLI.md](./README_CLI.md): CLI 사용 가이드
- [examples/image_analyzer_usage.py](./examples/image_analyzer_usage.py): 코드 예제
- [test_image_analyzer.py](./test_image_analyzer.py): 테스트 코드
