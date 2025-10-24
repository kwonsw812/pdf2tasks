# LLM TaskWriter 문서

## 개요

LLM TaskWriter는 상위 태스크를 LLM(Claude API)을 사용하여 구체적인 하위 개발 작업으로 세분화하는 모듈입니다.

### 주요 기능

- 상위 태스크를 하위 개발 작업으로 자동 분해
- NestJS/Prisma 기술 스택 문맥 반영
- 구조화된 Markdown 형식 출력
- 하위 태스크 품질 검증
- 토큰 사용량 및 비용 추적
- 에러 발생 시 자동 재시도

---

## 설치

### 필수 요구사항

- Python 3.10 이상
- Anthropic API Key

### 패키지 설치

```bash
# 가상환경 활성화
source venv/bin/activate

# 패키지 설치 (이미 설치되어 있을 경우 생략)
pip install -r requirements.txt
```

### API Key 설정

```bash
# 환경 변수로 설정
export ANTHROPIC_API_KEY='your-api-key-here'

# 또는 .env 파일에 추가
echo "ANTHROPIC_API_KEY=your-api-key-here" >> .env
```

---

## 빠른 시작

### 기본 사용법

```python
from src.types.models import IdentifiedTask, Section, PageRange
from src.llm.task_writer import LLMTaskWriter

# 상위 태스크 정의
task = IdentifiedTask(
    index=1,
    name="인증",
    description="사용자 회원가입 및 로그인 기능",
    module="AuthModule",
    entities=["User", "Session"],
    prerequisites=[],
    related_sections=[0]
)

# 관련 섹션 정의
sections = [
    Section(
        title="인증 기능",
        level=1,
        content="사용자는 이메일과 비밀번호로 회원가입하고 로그인할 수 있다.",
        page_range=PageRange(start=1, end=5),
        subsections=[]
    )
]

# TaskWriter 초기화 및 실행
writer = LLMTaskWriter()
result = writer.write_task(task, sections)

# 결과 확인
print(f"생성된 하위 태스크: {len(result.sub_tasks)}개")
for sub_task in result.sub_tasks:
    print(f"  - {sub_task.index} {sub_task.title}")

# Markdown 저장
with open(f"{task.index}_{task.name}.md", "w") as f:
    f.write(result.markdown)
```

---

## 데이터 모델

### IdentifiedTask

상위 태스크 (Planner의 출력)

```python
IdentifiedTask(
    index=1,                      # 태스크 번호
    name="인증",                  # 태스크 이름
    description="...",            # 설명
    module="AuthModule",          # 모듈명
    entities=["User", "Session"], # 관련 엔티티
    prerequisites=[],             # 선행 조건
    related_sections=[0, 1]       # 관련 섹션 인덱스
)
```

### SubTask

하위 태스크 (TaskWriter의 출력)

```python
SubTask(
    index="1.1",                          # 하위 태스크 인덱스
    title="회원가입 API 구현",            # 제목
    purpose="사용자 회원가입 기능 제공",  # 목적
    endpoint="POST /api/auth/register",   # 엔드포인트
    data_model="User { ... }",            # 데이터 모델
    logic="...",                          # 로직 요약
    security="Public 엔드포인트",         # 보안
    exceptions="409: 이메일 중복",        # 예외
    test_points="정상 가입, 중복 체크"    # 테스트 포인트
)
```

### TaskWriterResult

전체 결과

```python
TaskWriterResult(
    task=IdentifiedTask(...),      # 원본 상위 태스크
    sub_tasks=[SubTask(...)],      # 생성된 하위 태스크 목록
    markdown="# 인증 ...",         # 최종 Markdown 문서
    token_usage=TokenUsage(...)    # 토큰 사용량
)
```

---

## 주요 클래스 및 함수

### LLMTaskWriter

메인 클래스

```python
writer = LLMTaskWriter(
    api_key=None,                          # API key (기본값: 환경변수)
    model="claude-3-5-sonnet-20241022",    # 모델명
    max_tokens=8192,                       # 최대 출력 토큰
    temperature=0.0                        # Temperature (0.0 = 결정적)
)

# 하위 태스크 생성
result = writer.write_task(
    task=identified_task,       # 상위 태스크
    sections=all_sections,      # 섹션 목록
    validate=True,              # 검증 활성화
    retry_on_failure=True       # 실패 시 재시도
)

# 비용 추정
cost = writer.estimate_cost(result.token_usage)
print(f"예상 비용: ${cost:.4f}")
```

### 프롬프트 빌더

```python
from src.llm.prompts import build_task_writer_prompt, estimate_token_count

# 프롬프트 생성
prompt = build_task_writer_prompt(task, sections)

# 토큰 수 추정
token_count = estimate_token_count(prompt)
```

### Markdown 파서

```python
from src.llm.parser import parse_sub_tasks, validate_markdown_structure

# Markdown에서 하위 태스크 파싱
sub_tasks = parse_sub_tasks(markdown_text, task_index=1)

# Markdown 구조 검증
is_valid = validate_markdown_structure(markdown_text, task_index=1)
```

### 검증기

```python
from src.llm.validator import validate_sub_tasks, check_completeness

# 하위 태스크 검증
validation = validate_sub_tasks(sub_tasks, task_index=1)
if validation.is_valid:
    print("검증 통과")
else:
    print(f"오류: {validation.errors}")
    print(f"경고: {validation.warnings}")

# 완성도 점수
completeness = check_completeness(sub_tasks)
print(f"완성도: {completeness:.2%}")
```

---

## 출력 Markdown 형식

TaskWriter는 다음과 같은 구조의 Markdown을 생성합니다:

```markdown
# {기능명} — 상위 태스크 {index}

## 상위 태스크 개요
- **설명:** ...
- **모듈/영역:** ...
- **관련 엔티티:** ...
- **선행 조건:** ...
- **참고:** PDF 원문 p.12–15

---

## 하위 태스크 목록

### {index}.1 {하위 태스크명}
- **목적:** ...
- **엔드포인트:** `POST /api/...`
- **데이터 모델:** ...
- **로직 요약:** ...
- **권한/보안:** ...
- **예외:** ...
- **테스트 포인트:** ...

### {index}.2 {하위 태스크명}
...
```

---

## 예제

### 예제 1: 기본 사용

```python
# 예제 실행
python examples/task_writer_usage.py
```

### 예제 2: 배치 처리

```python
tasks = [task1, task2, task3]
writer = LLMTaskWriter()

results = []
for task in tasks:
    result = writer.write_task(task, sections)
    results.append(result)

# 전체 통계
total_tokens = sum(r.token_usage.total_tokens for r in results)
total_cost = sum(writer.estimate_cost(r.token_usage) for r in results)
```

### 예제 3: 커스텀 설정

```python
writer = LLMTaskWriter(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    temperature=0.2  # 약간의 창의성
)
```

---

## 에러 핸들링

### 주요 예외

- `APIKeyError`: API 키가 없거나 유효하지 않음
- `LLMCallError`: LLM API 호출 실패
- `MarkdownParseError`: Markdown 파싱 실패
- `SubTaskValidationError`: 하위 태스크 검증 실패

### 예외 처리 예제

```python
from src.llm.exceptions import (
    APIKeyError,
    LLMCallError,
    MarkdownParseError,
    SubTaskValidationError,
)

try:
    result = writer.write_task(task, sections)
except APIKeyError as e:
    print(f"API Key 오류: {e}")
except LLMCallError as e:
    print(f"LLM 호출 오류: {e}")
except MarkdownParseError as e:
    print(f"파싱 오류: {e}")
except SubTaskValidationError as e:
    print(f"검증 오류: {e}")
```

---

## 검증 기준

TaskWriter는 다음 항목을 검증합니다:

### 필수 필드
- ✓ 제목 (3자 이상)
- ✓ 목적 (10자 이상)
- ✓ 로직 요약 (20자 이상)

### 권장 필드
- ⚠ 엔드포인트
- ⚠ 데이터 모델
- ⚠ 테스트 포인트

### 품질 체크
- ✓ 인덱스 형식 (예: 1.1, 1.2)
- ✓ 인덱스 중복 확인
- ✓ 순차적 번호 확인
- ⚠ 너무 추상적인 설명 경고

---

## 성능 및 비용

### 토큰 사용량 (평균)

| 항목 | 토큰 수 |
|------|---------|
| 입력 프롬프트 | 1,000 - 3,000 |
| 출력 응답 | 2,000 - 5,000 |
| 총합 | 3,000 - 8,000 |

### 예상 비용 (Claude 3.5 Sonnet 기준)

- 입력: $3 per 1M tokens
- 출력: $15 per 1M tokens
- **태스크당 평균: $0.01 - $0.05**

### 처리 시간

- 단일 태스크: 10-30초
- 배치 처리 (10개): 2-5분

---

## 프롬프트 커스터마이징

### 프롬프트 수정

`src/llm/prompts.py`의 `SYSTEM_PROMPT`를 수정하여 프롬프트를 커스터마이즈할 수 있습니다.

```python
SYSTEM_PROMPT = """
당신은 시니어 백엔드 개발자입니다.
...
(커스터마이징)
...
"""
```

### 기술 스택 변경

NestJS/Prisma 외의 기술 스택을 사용하려면 프롬프트의 기술 스택 섹션을 수정하세요:

```python
**기술 스택:**
- Spring Boot (Java)
- JPA (Hibernate)
- JWT 기반 인증
```

---

## 테스트

### 단위 테스트

```bash
# 검증 함수 테스트 (API key 불필요)
python test_task_writer.py
```

### 통합 테스트 (API key 필요)

```bash
# API key 설정
export ANTHROPIC_API_KEY='your-key'

# 전체 테스트 실행
python test_task_writer.py
```

### 테스트 커버리지

- ✓ Prompt 생성
- ✓ Markdown 파싱
- ✓ 하위 태스크 검증
- ✓ LLM 호출 (API key 필요)
- ✓ 에러 핸들링

---

## 문제 해결

### Q: API 호출이 실패합니다

A: 다음을 확인하세요:
- ANTHROPIC_API_KEY 환경 변수 설정 확인
- API key 유효성 확인
- 네트워크 연결 확인
- Anthropic API 상태 확인

### Q: Markdown 파싱 오류가 발생합니다

A: `retry_on_failure=True` 옵션을 사용하면 자동으로 재시도합니다:
```python
result = writer.write_task(task, sections, retry_on_failure=True)
```

### Q: 생성된 하위 태스크가 너무 추상적입니다

A: 프롬프트에 더 구체적인 예제를 추가하거나, `related_sections`에 더 상세한 섹션을 포함하세요.

### Q: 토큰 제한을 초과했습니다

A: 섹션 내용을 요약하거나 `max_tokens` 값을 조정하세요:
```python
writer = LLMTaskWriter(max_tokens=4096)  # 기본값: 8192
```

---

## 디렉토리 구조

```
src/llm/
├── __init__.py
├── task_writer.py       # LLMTaskWriter 클래스
├── prompts.py           # 프롬프트 템플릿
├── parser.py            # Markdown 파싱
├── validator.py         # 하위 태스크 검증
└── exceptions.py        # 커스텀 예외

examples/
└── task_writer_usage.py # 사용 예제

test_task_writer.py      # 테스트 스크립트
README_TASKWRITER.md     # 이 문서
```

---

## 추가 자료

- [AI Agent Project Plan](AI_Agent_Project_Plan.md) - 전체 프로젝트 기획서
- [Task 6 명세](tasks/6_LLM_TaskWriter_구현.md) - 상세 태스크 명세
- [Anthropic API 문서](https://docs.anthropic.com/) - Claude API 공식 문서

---

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

---

## 업데이트 기록

- **2025-10-23**: Task 6 (LLM TaskWriter) 구현 완료
  - 프롬프트 엔지니어링
  - Markdown 파싱 및 검증
  - 토큰 추적 및 비용 추정
  - 자동 재시도 기능
