# LLM 기반 OpenAPI 컨텍스트 매칭 시스템

## 개요

PDF 기획서와 OpenAPI 스펙에서 **사용자 역할(user/admin/partner)** 및 **배포 환경(dev/staging/prod)**을 LLM으로 자동 추출하고, 컨텍스트를 고려한 태스크 매칭 시스템입니다.

### 핵심 기능

1. **LLM 기반 컨텍스트 추출**: PDF에서 역할별/환경별 기능 구분 자동 감지
2. **OpenAPI 역할/환경 추출**: LLM을 사용하여 엔드포인트별 역할 및 환경 정보 추출
3. **컨텍스트 기반 매칭**: 역할 x 환경 매트릭스로 정확한 구현 상태 파악
4. **매트릭스 시각화**: 역할 및 환경별 구현 상태를 한눈에 확인

---

## 문제점 및 해결책

### 기존 문제점

- 기존 OpenAPI 매칭은 **키워드 기반 (규칙 기반)**
- **역할(사용자/관리자/파트너) 구분 없음**
- **배포 환경(개발/스테이징/운영) 구분 없음**
- PDF 기획서의 "일반 사용자는 조회만, 관리자는 CRUD 가능" 같은 정보 무시됨

### 실제 사례

**PDF 기획서:**
```markdown
## 상품 관리
- 일반 사용자: 상품 조회만 가능
- 관리자: 상품 등록/수정/삭제 가능
- 파트너 관리자: 자신의 상품만 관리 가능

## 결제 (개발환경)
- 테스트 PG 사용, 자동 승인

## 결제 (운영환경)
- 실제 PG 연동, 수동 검수
```

**OpenAPI 스펙:**
```yaml
# openapi-dev.yaml
/api/products:
  get:
    security:
      - bearerAuth: [user, admin]
  post:
    security:
      - bearerAuth: [admin]

# openapi-prod.yaml
/api/products:
  get:
    security:
      - bearerAuth: [user]
  # POST 엔드포인트 없음 (아직 미구현)
```

**기대 결과:**
- "상품 조회"는 `user` 역할로 `dev`/`prod` 모두 구현됨
- "상품 등록"은 `admin` 역할로 `dev`만 구현됨, `prod`는 미구현
- "파트너 상품 관리"는 모든 환경에서 미구현

---

## 아키텍처

### 데이터 모델

#### TaskContext
```python
class TaskContext(BaseModel):
    deployment_envs: List[str]  # ["development", "staging", "production", "all"]
    actor_roles: List[str]      # ["user", "admin", "partner_admin", "super_admin", "all"]
    role_based_features: dict   # {"user": "조회만", "admin": "CRUD"}
    env_based_features: dict    # {"dev": "테스트 PG", "prod": "실제 PG"}
```

#### OpenAPIEndpoint (확장)
```python
class OpenAPIEndpoint(BaseModel):
    # ... existing fields ...
    required_roles: List[str]   # LLM이 추출한 역할 (security 스키마, 경로, 설명 분석)
    deployment_env: str         # 파일명에서 추출 (openapi-dev.yaml → "development")
```

#### TaskMatchResult (확장)
```python
class TaskMatchResult(BaseModel):
    # ... existing fields ...
    context_match_matrix: dict  # 역할 x 환경 매트릭스
    llm_based: bool             # LLM 기반 매칭 여부
    explanation: Optional[str]  # LLM의 상세 설명
```

### 파이프라인 흐름

```
PDF 추출 (Step 1)
    ↓
OCR (Step 2, optional)
    ↓
Preprocessing (Step 3)
    ↓
LLM Planner (Step 4) ← ★ 컨텍스트 추출 추가
    ↓
    ├─→ TaskContext 추출 (역할, 배포환경)
    ├─→ IdentifiedTask에 context 필드 추가
    ↓
OpenAPI 분석 (새로운 Step)
    ↓
    ├─→ LLM OpenAPI Context Analyzer
    ├─→ 엔드포인트별 역할/환경 추출
    ├─→ OpenAPIEndpoint에 required_roles, deployment_env 추가
    ↓
LLM Task Matcher (새로운 Step) ← ★ 컨텍스트 기반 매칭
    ↓
    ├─→ 태스크 컨텍스트 vs 엔드포인트 컨텍스트 비교
    ├─→ 역할 x 환경 매트릭스 생성
    ├─→ TaskMatchResult 생성
    ↓
TaskWriter (Step 5)
    ↓
File Splitting (Step 6)
    ↓
Report Generation (Step 7)
```

---

## 사용 방법

### 1. CLI 사용

#### 기본 사용법 (LLM 컨텍스트 매칭 활성화)
```bash
python -m src.cli.main analyze ./specs/app-v1.pdf \
  --out ./output \
  --openapi-dir ./openapi \
  --use-llm-context \
  --use-llm-matching
```

#### LLM 기능 비활성화 (규칙 기반으로 폴백)
```bash
python -m src.cli.main analyze ./specs/app-v1.pdf \
  --out ./output \
  --openapi-dir ./openapi \
  --no-llm-context \
  --no-llm-matching
```

### 2. Python API 사용

#### 컨텍스트 추출
```python
from src.llm.context_extractor import LLMContextExtractor
from src.types.models import IdentifiedTask, Section

# Initialize extractor
extractor = LLMContextExtractor(api_key="your-api-key")

# Extract context
task = IdentifiedTask(...)
sections = [Section(...), ...]
context = extractor.extract_task_context(task, sections)

print(f"Roles: {context.actor_roles}")
print(f"Envs: {context.deployment_envs}")
print(f"Role Features: {context.role_based_features}")
```

#### OpenAPI 역할 추출
```python
from src.openapi.llm_openapi_analyzer import LLMOpenAPIAnalyzer
from pathlib import Path

# Initialize analyzer
analyzer = LLMOpenAPIAnalyzer(api_key="your-api-key")

# Analyze endpoint
endpoint_spec = {
    "path": "/api/products",
    "method": "POST",
    "summary": "상품 등록 (관리자 전용)",
    "security": [{"bearerAuth": ["admin"]}]
}

result = analyzer.analyze_endpoint(endpoint_spec)
print(f"Required Roles: {result['required_roles']}")
print(f"Explanation: {result['explanation']}")

# Extract deployment environment
env = analyzer.extract_deployment_env(Path("openapi-dev.yaml"))
print(f"Deployment Env: {env}")  # "development"
```

#### 컨텍스트 기반 매칭
```python
from src.openapi.llm_task_matcher import LLMTaskMatcher

# Initialize matcher
matcher = LLMTaskMatcher(
    specs=openapi_specs,
    api_key="your-api-key",
    use_llm=True,
    fallback=True  # 실패 시 규칙 기반으로 폴백
)

# Match task
match_result = matcher.match_task(task)

print(f"Status: {match_result.match_status}")
print(f"Confidence: {match_result.confidence_score:.2f}")
print(f"Context Matrix: {match_result.context_match_matrix}")
```

---

## 컨텍스트 매트릭스 예시

### 출력 예시
```json
{
  "context_match_matrix": {
    "user": {
      "development": "fully_implemented",
      "staging": "fully_implemented",
      "production": "fully_implemented"
    },
    "admin": {
      "development": "fully_implemented",
      "staging": "partially_implemented",
      "production": "new"
    },
    "partner_admin": {
      "development": "new",
      "staging": "new",
      "production": "new"
    }
  }
}
```

### 매트릭스 해석
- **fully_implemented**: 해당 역할+환경 조합의 모든 기능이 구현됨
- **partially_implemented**: 일부만 구현됨
- **new**: 구현 안 됨

### 시각화 예시
```
역할 x 환경 구현 상태 매트릭스:

            | Development | Staging | Production |
------------|-------------|---------|------------|
User        | ✅ Full     | ✅ Full | ✅ Full    |
Admin       | ✅ Full     | ⚠️  Part | ❌ New     |
Partner     | ❌ New      | ❌ New  | ❌ New     |
```

---

## 비용 및 성능

### 추가 LLM 호출 (태스크 10개, 엔드포인트 50개 기준)

| 단계 | 호출 수 | 토큰/호출 | 총 토큰 | 비용 (Claude 3.5 Sonnet) |
|------|---------|-----------|---------|-------------------------|
| 컨텍스트 추출 (PDF) | 10회 | 1,500 | 15,000 | $0.05 |
| 역할 추출 (OpenAPI) | 50회 | 800 | 40,000 | $0.13 |
| 매칭 | 10회 | 2,500 | 25,000 | $0.08 |
| **합계** | 70회 | - | **80,000** | **$0.26** |

**기존 파이프라인**: ~$0.20
**새 파이프라인**: ~$0.46 (**+130%**)

**BUT**: 정확도 향상으로 수동 수정 시간 절감, 중복 구현 방지 → **실질적 비용 절감 가능**

### 처리 시간 (예상)
- **컨텍스트 추출**: 10개 태스크 기준 ~30-60초
- **OpenAPI 역할 추출**: 50개 엔드포인트 기준 ~2-5분
- **매칭**: 10개 태스크 기준 ~30-60초
- **전체 추가 시간**: ~3-7분

---

## 설정 옵션

### OrchestratorConfig
```python
config = OrchestratorConfig(
    # ... existing options ...
    use_llm_context_extraction=True,  # LLM 컨텍스트 추출 활성화
    use_llm_openapi_matching=True,    # LLM 컨텍스트 기반 매칭 활성화
)
```

### CLI 옵션
```bash
# 활성화 (기본값)
--use-llm-context
--use-llm-matching

# 비활성화 (규칙 기반으로 폴백)
--no-llm-context
--no-llm-matching
```

---

## 폴백 메커니즘

### LLM 실패 시 자동 폴백
1. **API 키 없음**: 자동으로 규칙 기반 사용
2. **LLM 호출 실패**: 기존 규칙 기반 매칭으로 폴백
3. **파싱 실패**: 재시도 후 폴백

### 예외 처리
- 일부 태스크 실패 시 나머지 태스크 계속 처리
- 모든 에러는 로그 및 리포트에 기록됨

---

## 제한사항 및 개선 방향

### 현재 제한사항
1. API 키 필수 (LLM 기능 사용 시)
2. 네트워크 연결 필요
3. 추가 LLM 비용 발생 (~$0.26 추가)
4. 처리 시간 증가 (~3-7분 추가)

### 향후 개선 방향
1. **배치 처리 최적화**: 여러 엔드포인트를 한 번에 분석
2. **캐싱**: 동일한 엔드포인트 재분석 방지
3. **프롬프트 최적화**: 토큰 사용량 감소
4. **다국어 지원**: 영어 기획서 지원
5. **커스텀 역할 정의**: 도메인별 역할 확장

---

## 파일 구조

```
pdf-agent/
├── src/
│   ├── llm/
│   │   ├── context_extractor.py       # LLM 기반 PDF 컨텍스트 추출
│   │   └── ...
│   ├── openapi/
│   │   ├── llm_openapi_analyzer.py    # LLM 기반 OpenAPI 역할/환경 추출
│   │   ├── llm_task_matcher.py        # LLM 기반 컨텍스트 매칭
│   │   └── matcher.py                 # 규칙 기반 (폴백용)
│   ├── cli/
│   │   ├── orchestrator.py            # 파이프라인 통합
│   │   └── main.py                    # CLI 엔트리포인트
│   └── types/
│       └── models.py                  # TaskContext 등 데이터 모델
├── test_llm_context_matching.py       # 테스트 스크립트
└── README_LLM_CONTEXT_MATCHING.md      # 이 문서
```

---

## 테스트

### 기본 테스트 실행
```bash
python test_llm_context_matching.py
```

**출력:**
```
============================================================
LLM CONTEXT MATCHING TESTS
============================================================

✅ TaskContext model test passed!
✅ IdentifiedTask with context test passed!
✅ OpenAPIEndpoint with roles test passed!

All basic tests passed! ✅
```

### 통합 테스트 (API 키 필요)
```bash
export ANTHROPIC_API_KEY='your-api-key'
python test_llm_context_matching.py
```

---

## 예제

### 예제 1: 전체 파이프라인 실행
```bash
python -m src.cli.main analyze ./specs/app-v1.pdf \
  --out ./output \
  --openapi-dir ./openapi \
  --clean \
  --verbose
```

### 예제 2: 컨텍스트 추출만
```python
from src.llm.context_extractor import LLMContextExtractor

extractor = LLMContextExtractor(api_key=api_key)
context = extractor.extract_task_context(task, sections)
```

### 예제 3: OpenAPI 역할만 추출
```python
from src.openapi.llm_openapi_analyzer import LLMOpenAPIAnalyzer

analyzer = LLMOpenAPIAnalyzer(api_key=api_key)
result = analyzer.analyze_endpoint(endpoint_spec)
```

---

## FAQ

### Q1: LLM 없이도 사용 가능한가요?
A: 네, `--no-llm-context --no-llm-matching` 옵션을 사용하면 기존 규칙 기반으로 동작합니다.

### Q2: 비용이 얼마나 증가하나요?
A: 태스크 10개, 엔드포인트 50개 기준 약 $0.26 추가됩니다. 그러나 정확도 향상으로 수동 수정 시간이 절감됩니다.

### Q3: 처리 시간이 얼마나 걸리나요?
A: LLM 기반 컨텍스트 매칭 사용 시 기존 대비 약 3-7분 추가됩니다.

### Q4: 어떤 역할과 환경을 지원하나요?
A:
- **역할**: user, admin, partner_admin, super_admin, all
- **환경**: development, staging, production, all

### Q5: 커스텀 역할을 추가할 수 있나요?
A: 현재는 고정된 역할만 지원합니다. 향후 업데이트에서 커스텀 역할 지원 예정입니다.

---

## 참고 자료

- [프로젝트 메인 README](/Users/kwonsangwon/nudge-commerce/pdf-agent/README.md)
- [태스크 명세](/Users/kwonsangwon/nudge-commerce/pdf-agent/tasks/LLM_OpenAPI_Context_Matching.md)
- [개발 세션 기록](/Users/kwonsangwon/nudge-commerce/pdf-agent/CLAUDE.md)

---

## 라이선스

This project is part of the PDF-Agent system.
