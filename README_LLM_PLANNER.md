# LLM Planner - 상위 태스크 식별 시스템

## 목차
- [개요](#개요)
- [기능](#기능)
- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [상세 사용법](#상세-사용법)
- [아키텍처](#아키텍처)
- [API 레퍼런스](#api-레퍼런스)
- [예제](#예제)
- [문제 해결](#문제-해결)

---

## 개요

LLM Planner는 PDF 기획서에서 추출한 섹션들을 분석하여 백엔드 개발 관점에서 상위 기능(태스크)을 자동으로 식별하는 시스템입니다.

### 주요 특징
- **AI 기반 태스크 식별**: Claude API를 사용하여 문서에서 백엔드 태스크 자동 추출
- **중복 제거**: 유사한 태스크를 자동으로 병합
- **의존성 분석**: 태스크 간 의존 관계 자동 분석
- **토큰 추적**: API 사용량 및 비용 실시간 모니터링
- **에러 핸들링**: 재시도 로직 및 포괄적인 예외 처리

### 워크플로우
```
PDF 섹션/기능 그룹
    ↓
프롬프트 생성 (PromptBuilder)
    ↓
LLM API 호출 (LLMCaller)
    ↓
응답 파싱 및 검증
    ↓
중복 제거 (TaskDeduplicator)
    ↓
의존성 분석 (DependencyAnalyzer)
    ↓
IdentifiedTask 목록 반환
```

---

## 기능

### 1. Claude API 클라이언트 (ClaudeClient)
- Anthropic Claude API 연동
- 자동 재시도 및 에러 핸들링
- 토큰 사용량 계산
- 비용 추정

### 2. 프롬프트 빌더 (PromptBuilder)
- 섹션/기능 그룹에서 프롬프트 생성
- 토큰 제한 관리 (최대 150k 토큰)
- 자동 텍스트 절단
- 대용량 문서 청크 분할

### 3. LLM 호출기 (LLMCaller)
- JSON 응답 파싱
- 지수 백오프 재시도 (최대 3회)
- API 오류 처리 (rate limit, timeout 등)

### 4. 태스크 중복 제거기 (TaskDeduplicator)
- 문자열 유사도 기반 중복 탐지
- Jaccard 유사도 계산
- 자동 태스크 병합

### 5. 의존성 분석기 (DependencyAnalyzer)
- 태스크 간 의존 관계 자동 추론
- 순환 의존성 탐지
- 위상 정렬 (Topological Sort)

### 6. 토큰 추적기 (TokenTracker)
- 실시간 토큰 사용량 추적
- 비용 계산 (모델별 가격 적용)
- 누적 통계 제공

---

## 설치

### 필수 요구사항
- Python 3.10 이상
- Anthropic API 키

### 패키지 설치
```bash
# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# API 키 설정
echo "ANTHROPIC_API_KEY=your_actual_api_key_here" > .env
```

---

## 빠른 시작

### 기본 사용 예제

```python
from src.llm.planner.llm_planner import LLMPlanner
from src.types.models import Section, PageRange

# 섹션 생성
sections = [
    Section(
        title="사용자 인증",
        level=1,
        content="로그인, 회원가입, 비밀번호 재설정 기능",
        page_range=PageRange(start=1, end=2),
    ),
    Section(
        title="상품 관리",
        level=1,
        content="상품 등록, 수정, 삭제, 조회 기능",
        page_range=PageRange(start=3, end=4),
    ),
]

# LLM Planner 초기화
planner = LLMPlanner()

# 태스크 식별
result = planner.identify_tasks_from_sections(sections)

# 결과 출력
for task in result.tasks:
    print(f"{task.index}. {task.name}")
    print(f"   Module: {task.module}")
    print(f"   Description: {task.description}")
    print(f"   Entities: {task.entities}")

# 토큰 사용량 출력
print(f"\nTotal cost: ${result.estimated_cost_usd:.6f}")
```

---

## 상세 사용법

### 1. 기본 태스크 식별

```python
from src.llm.planner.llm_planner import LLMPlanner
from src.types.models import Section, PageRange

sections = [
    Section(
        title="결제 시스템",
        level=1,
        content="PG사 연동 결제 처리 및 결제 내역 관리",
        page_range=PageRange(start=5, end=7),
    ),
]

planner = LLMPlanner()
result = planner.identify_tasks_from_sections(sections)

# 결과 접근
print(f"Identified {len(result.tasks)} tasks")
print(f"Model used: {result.model}")
print(f"Total tokens: {result.token_usage.total_tokens}")
```

### 2. 기능 그룹에서 식별

```python
from src.types.models import FunctionalGroup

# 기능 그룹 생성
auth_group = FunctionalGroup(
    name="인증",
    sections=[...],  # Section 객체 리스트
    keywords=["인증", "로그인", "권한"],
)

payment_group = FunctionalGroup(
    name="결제",
    sections=[...],
    keywords=["결제", "구매"],
)

# 태스크 식별
planner = LLMPlanner()
result = planner.identify_tasks_from_functional_groups([auth_group, payment_group])
```

### 3. 커스텀 설정

```python
planner = LLMPlanner(
    model="claude-3-5-sonnet-20241022",  # 사용할 모델
    max_tokens=2048,                      # 최대 응답 토큰
    temperature=0.7,                      # 샘플링 온도
    similarity_threshold=0.85,            # 중복 제거 임계값
    enable_dependency_analysis=True,      # 의존성 분석 활성화
)
```

### 4. 의존성 그래프 확인

```python
result = planner.identify_tasks_from_sections(sections)

# 의존성 그래프 추출
dep_graph = planner.get_dependency_graph(result.tasks)

for task_name, dependencies in dep_graph.items():
    print(f"{task_name}:")
    for dep in dependencies:
        print(f"  - {dep}")
```

### 5. 토큰 사용량 추적

```python
# 여러 번 호출
result1 = planner.identify_tasks_from_sections(sections1)
result2 = planner.identify_tasks_from_sections(sections2)

# 누적 통계
summary = planner.get_token_summary()
print(f"Total calls: {summary['total_calls']}")
print(f"Total tokens: {summary['total_tokens']}")
print(f"Total cost: ${summary['total_cost_usd']:.6f}")

# 상세 로그
planner.log_token_summary()
```

---

## 아키텍처

### 모듈 구조

```
src/llm/
├── claude_client.py         # Claude API 클라이언트
├── exceptions.py            # 커스텀 예외
└── planner/
    ├── llm_planner.py       # 통합 인터페이스 (메인)
    ├── prompt_builder.py    # 프롬프트 생성
    ├── llm_caller.py        # API 호출 및 파싱
    ├── task_deduplicator.py # 중복 제거
    ├── dependency_analyzer.py # 의존성 분석
    ├── token_tracker.py     # 토큰 추적
    └── prompts.py           # 프롬프트 템플릿
```

### 데이터 모델

#### IdentifiedTask
```python
class IdentifiedTask(BaseModel):
    index: int                      # 태스크 인덱스
    name: str                       # 태스크 이름
    description: str                # 설명
    module: str                     # 모듈명
    entities: List[str]             # 관련 엔티티
    prerequisites: List[str]        # 선행 조건
    related_sections: List[int]     # 관련 섹션
```

#### LLMPlannerResult
```python
class LLMPlannerResult(BaseModel):
    tasks: List[IdentifiedTask]     # 식별된 태스크
    token_usage: TokenUsage         # 토큰 사용량
    estimated_cost_usd: float       # 예상 비용
    model: str                      # 사용 모델
```

---

## API 레퍼런스

### LLMPlanner

#### `__init__()`
```python
def __init__(
    api_key: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 4096,
    temperature: float = 1.0,
    similarity_threshold: float = 0.8,
    enable_dependency_analysis: bool = True,
)
```

**파라미터:**
- `api_key`: Anthropic API 키 (기본값: 환경변수 `ANTHROPIC_API_KEY`)
- `model`: 사용할 Claude 모델
- `max_tokens`: 최대 응답 토큰 수
- `temperature`: 샘플링 온도 (0-1)
- `similarity_threshold`: 중복 제거 임계값 (0-1)
- `enable_dependency_analysis`: 의존성 분석 활성화 여부

#### `identify_tasks_from_sections()`
```python
def identify_tasks_from_sections(
    sections: List[Section]
) -> LLMPlannerResult
```

**파라미터:**
- `sections`: 문서 섹션 리스트

**반환값:**
- `LLMPlannerResult`: 식별된 태스크 및 통계

#### `identify_tasks_from_functional_groups()`
```python
def identify_tasks_from_functional_groups(
    functional_groups: List[FunctionalGroup]
) -> LLMPlannerResult
```

**파라미터:**
- `functional_groups`: 기능 그룹 리스트

**반환값:**
- `LLMPlannerResult`: 식별된 태스크 및 통계

#### `get_token_summary()`
```python
def get_token_summary() -> dict
```

**반환값:**
- 토큰 사용 통계 딕셔너리

#### `get_dependency_graph()`
```python
def get_dependency_graph(
    tasks: List[IdentifiedTask]
) -> dict
```

**파라미터:**
- `tasks`: 태스크 리스트

**반환값:**
- 의존성 그래프 (태스크명 → 의존 태스크 리스트)

---

## 예제

### 예제 1: 기본 식별
```python
# examples/llm_planner_usage.py 참조
python examples/llm_planner_usage.py
```

### 예제 2: 테스트 실행
```python
# 단위 테스트 (API 호출 없음)
python test_llm_planner.py
```

### 예제 3: 커스텀 프롬프트
```python
from src.llm.planner.prompts import build_task_identification_prompt

sections = [...]
prompt = build_task_identification_prompt(sections)
print(prompt)
```

---

## 문제 해결

### 1. API 키 오류
```
APIKeyError: ANTHROPIC_API_KEY not found
```

**해결:**
```bash
export ANTHROPIC_API_KEY=your_key_here
# 또는 .env 파일에 추가
```

### 2. 토큰 제한 초과
```
PromptTooLongError: Prompt exceeds token limit
```

**해결:**
- 섹션 수 줄이기
- 청크 분할 사용:
```python
builder = PromptBuilder()
chunks = builder.split_sections_into_chunks(sections, max_sections_per_chunk=50)
```

### 3. JSON 파싱 오류
```
JSONParseError: Invalid JSON in response
```

**해결:**
- LLM이 유효한 JSON을 반환하지 않을 수 있음
- 자동으로 최대 3회 재시도됨
- 프롬프트 개선 필요 시 `prompts.py` 수정

### 4. Rate Limit 초과
```
APIRateLimitError: Rate limit exceeded
```

**해결:**
- 자동으로 재시도됨 (지수 백오프)
- API 사용량 제한 확인
- 요청 간 간격 늘리기

---

## 비용 정보

### Claude 3.5 Sonnet 가격 (2024년 기준)
- **입력 토큰**: $3 per million tokens
- **출력 토큰**: $15 per million tokens

### 예상 비용
- 10개 섹션 → 약 $0.01-0.03
- 50개 섹션 → 약 $0.05-0.15
- 100개 섹션 → 약 $0.10-0.30

실제 비용은 섹션 내용 길이와 LLM 응답 길이에 따라 달라집니다.

---

## 제한사항

1. **토큰 제한**: 한 번에 최대 150k 토큰 (보수적 설정)
2. **API 의존성**: Anthropic API 필요
3. **비용**: API 호출마다 비용 발생
4. **정확도**: LLM 응답의 일관성은 100% 보장되지 않음
5. **언어**: 현재 한국어 프롬프트로 최적화됨

---

## 향후 개선 사항

- [ ] 다국어 지원
- [ ] 커스텀 프롬프트 템플릿
- [ ] 배치 처리 최적화
- [ ] 캐싱 메커니즘
- [ ] 더 정교한 의존성 분석
- [ ] 태스크 우선순위 자동 할당

---

## 라이센스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.

---

## 문의

문제 발생 시 이슈 트래커를 사용하거나 개발팀에 문의하세요.
