# 전처리 모드 변경 가이드

## 📢 변경 사항

**2025-10-23부터 전처리 기본 모드가 LLM 기반으로 변경되었습니다.**

### 이유

실험 결과, LLM 기반 전처리가:
- ✅ **35% 더 저렴** ($0.030 → $0.020)
- ✅ **45% 토큰 효율적** (6,504 → 3,552 tokens)
- ✅ **더 정확한 섹션 구분** (39개 → 16개로 최적화)
- ✅ **더 일관된 태스크 구조**
- ⚠️ 처리 시간은 단 10초 증가 (2:49 → 2:59)

자세한 분석: `LLM_PREPROCESSING_COMPARISON_REPORT.md` 참조

---

## 🔄 마이그레이션 가이드

### 기존 사용자 (규칙 기반 → LLM 기반)

#### 변경 전 (이전 버전)
```bash
# 기본: 규칙 기반
pdf2tasks analyze spec.pdf --out ./out

# LLM 기반 사용 (옵션)
pdf2tasks analyze spec.pdf --out ./out --use-llm-preprocessing
```

#### 변경 후 (현재 버전)
```bash
# 기본: LLM 기반 (권장) ★
pdf2tasks analyze spec.pdf --out ./out

# 규칙 기반으로 되돌리기 (필요 시)
pdf2tasks analyze spec.pdf --out ./out --no-llm-preprocessing
```

### 영향 받는 사용자

#### ✅ 영향 없음 (대부분의 경우)
- 기본 명령어 그대로 사용하면 더 나은 결과 얻음
- 비용도 오히려 감소
- API 키만 있으면 자동 적용

#### ⚠️ 확인 필요
다음 경우 `--no-llm-preprocessing` 옵션 사용 고려:

1. **네트워크 제한 환경**
   - 오프라인 처리 필요
   - API 호출 불가

2. **CI/CD 파이프라인**
   - 100% 재현성 필요
   - 비결정적 출력 허용 안 됨

3. **대량 배치 처리**
   - 수백 개 PDF 동시 처리
   - 속도가 품질보다 중요

4. **레거시 호환성**
   - 기존 결과와 동일한 출력 필요
   - 기존 테스트 케이스 유지

---

## 🎯 각 모드 비교

### LLM 기반 (기본값, 권장)

#### 장점
- ✅ 더 저렴 (35% 비용 절감)
- ✅ 더 정확 (90-95% 정확도)
- ✅ 토큰 효율적 (45% 감소)
- ✅ 의미 기반 섹션 구분
- ✅ 빈 섹션 자동 제거
- ✅ 암묵적 계층 구조 파악

#### 단점
- ⚠️ 약간 느림 (+10초)
- ⚠️ 네트워크 필요
- ⚠️ 약간의 비결정성

#### 사용법
```bash
# 기본 (자동으로 LLM 사용)
pdf2tasks analyze spec.pdf --out ./out
```

### 규칙 기반 (--no-llm-preprocessing)

#### 장점
- ✅ 빠름 (-10초)
- ✅ 오프라인 작동
- ✅ 100% 재현성
- ✅ 네트워크 불필요

#### 단점
- ❌ 비용 35% 더 비쌈
- ❌ 토큰 45% 더 많음
- ❌ 과도한 섹션 분리 (39개)
- ❌ 빈 섹션 생성
- ❌ 패턴 기반 제한

#### 사용법
```bash
# 명시적으로 규칙 기반 사용
pdf2tasks analyze spec.pdf --out ./out --no-llm-preprocessing
```

---

## 📝 Python API 변경

### 기존 코드 (이전 버전)
```python
from src.preprocessor.preprocessor import Preprocessor

# 기본: 규칙 기반
preprocessor = Preprocessor()  # use_llm=False (default)

# LLM 기반 (명시적)
preprocessor = Preprocessor(
    use_llm=True,
    llm_api_key="your_key"
)
```

### 새 코드 (현재 버전)
```python
from src.preprocessor.preprocessor import Preprocessor

# 기본: LLM 기반 (권장) ★
preprocessor = Preprocessor(
    use_llm=True,  # Default changed to True
    llm_api_key="your_key"
)

# 규칙 기반으로 되돌리기
preprocessor = Preprocessor(use_llm=False)
```

### 호환성 유지

**걱정하지 마세요!**
- API 키가 없으면 자동으로 규칙 기반으로 폴백
- 기존 코드는 그대로 작동
- 단, API 키 설정하면 자동 업그레이드

```python
# API 키 없으면 자동 폴백
preprocessor = Preprocessor(use_llm=True)  # → 규칙 기반으로 자동 전환
# Warning: "LLM enabled but no API key provided. Falling back to rule-based."
```

---

## 🔧 환경 변수 설정

### API 키 설정 (필수)

LLM 기반 전처리 사용을 위해 API 키 필요:

```bash
# .env 파일에 추가
ANTHROPIC_API_KEY=your_api_key_here

# 또는 환경 변수로 설정
export ANTHROPIC_API_KEY=your_api_key_here

# 또는 CLI 옵션으로 전달
pdf2tasks analyze spec.pdf --out ./out --api-key your_api_key_here
```

API 키가 없으면:
- ⚠️ 자동으로 규칙 기반으로 폴백
- 경고 메시지 출력
- 처리는 계속 진행

---

## 📊 예상 비용 업데이트

### 이전 (규칙 기반)
```
50페이지 PDF 기준:
- 전처리: $0 (규칙)
- LLM Planner: $0.005
- LLM TaskWriter: $0.025
- 합계: $0.030
```

### 현재 (LLM 기반)
```
50페이지 PDF 기준:
- 전처리: $0.003 (LLM)
- LLM Planner: $0.003 (효율화)
- LLM TaskWriter: $0.014 (효율화)
- 합계: $0.020 (-35%)
```

### 결론
**LLM을 더 많이 사용했지만 전체 비용은 오히려 감소!**

---

## ❓ FAQ

### Q1: 비용이 증가하나요?
**A**: 아니요! 오히려 **35% 감소**합니다.
- 전처리에 LLM 사용 → +$0.003
- 후속 단계 효율화 → -$0.013
- 순 절감: -$0.010

### Q2: 처리 시간은 얼마나 증가하나요?
**A**: 약 **10초 증가** (2:49 → 2:59, 6%)
- 50페이지 PDF 기준
- 전체 파이프라인의 6%만 증가
- 허용 가능한 범위

### Q3: 기존 결과와 다른가요?
**A**: 네, **더 나은 결과**가 생성됩니다.
- 섹션 수: 39개 → 16개 (최적화)
- 태스크 수: 6개 → 5개 (중복 제거)
- 품질: 75-85% → 90-95%

### Q4: 기존 결과가 필요하면?
**A**: `--no-llm-preprocessing` 옵션 사용
```bash
pdf2tasks analyze spec.pdf --out ./out --no-llm-preprocessing
```

### Q5: API 키가 없으면?
**A**: 자동으로 규칙 기반으로 폴백되어 계속 작동합니다.

### Q6: 네트워크 없이 사용 가능한가요?
**A**: `--no-llm-preprocessing` 옵션으로 오프라인 사용 가능

### Q7: 결과가 매번 다른가요?
**A**: Temperature=0.0으로 최소화했지만, 완벽히 동일하지는 않습니다.
- 대부분의 경우 차이가 미미
- CI/CD에서 100% 재현성 필요 시 `--no-llm-preprocessing` 권장

---

## 🎓 권장 사항

### 일반 사용
```bash
# 기본 명령어 그대로 사용 (LLM 기반)
pdf2tasks analyze spec.pdf --out ./out
```

### CI/CD 파이프라인
```bash
# 재현성 필요 시
pdf2tasks analyze spec.pdf --out ./out --no-llm-preprocessing
```

### 프로덕션 배포
```bash
# 최고 품질 (기본값)
pdf2tasks analyze spec.pdf --out ./out

# .env 파일에 API 키 설정 필수
ANTHROPIC_API_KEY=your_api_key
```

---

## 📚 추가 문서

- **상세 비교**: `LLM_PREPROCESSING_COMPARISON_REPORT.md`
- **설치 가이드**: `README.md`
- **API 문서**: `README_PREPROCESSOR.md`
- **예제**: `examples/preprocessor_usage.py`

---

**업데이트 일시**: 2025-10-23
**버전**: 0.2.0 (LLM 전처리 기본값 변경)
