# LLM 기반 OpenAPI 컨텍스트 매칭 시스템 개발 명세서

## 프로젝트 개요

**목표**: PDF 기획서와 OpenAPI 스펙을 분석하여 사용자 역할(user/admin/partner) 및 배포 환경(dev/staging/prod)을 자동으로 추출하고, 컨텍스트를 고려한 태스크 매칭 시스템 구현

**핵심 기능**:
1. LLM을 사용하여 PDF에서 역할별/환경별 기능 구분 자동 추출
2. LLM을 사용하여 OpenAPI에서 엔드포인트별 역할/환경 자동 추출
3. LLM을 사용하여 컨텍스트를 고려한 태스크-엔드포인트 매칭
4. 역할 x 환경 매트릭스 기반 구현 상태 시각화

---

## 배경 및 문제점

### 현재 상황
- 기존 OpenAPI 매칭은 키워드 기반 (규칙 기반)
- 역할(사용자/관리자/파트너) 구분 없음
- 배포 환경(개발/스테이징/운영) 구분 없음
- PDF 기획서의 "일반 사용자는 조회만, 관리자는 CRUD 가능" 같은 정보 무시됨

### 실제 사례
**PDF 기획서**:
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

**OpenAPI 스펙**:
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

**기대 결과**:
- "상품 조회"는 user 역할로 dev/prod 모두 구현됨
- "상품 등록"은 admin 역할로 dev만 구현됨, prod는 미구현
- "파트너 상품 관리"는 모든 환경에서 미구현

---

## 아키텍처 설계

### 전체 파이프라인

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
OpenAPI 로딩 (새로운 Step)
    ↓
    ├─→ LLM OpenAPI Context Analyzer
    ├─→ 엔드포인트별 역할/환경 추출
    ├─→ OpenAPIEndpoint에 required_roles, deployment_env 추가
    ↓
LLM Task Matcher (새로운 Step) ← ★ 새로 구현
    ↓
    ├─→ 태스크 컨텍스트 vs 엔드포인트 컨텍스트 비교
    ├─→ 역할 x 환경 매트릭스 생성
    ├─→ TaskMatchResult 생성
    ↓
TaskWriter (Step 5)
    ↓
    ├─→ 매칭 결과를 반영하여 하위 태스크 작성
    ├─→ "이미 구현됨" vs "신규 구현 필요" 명시
    ↓
File Splitting (Step 6)
    ↓
Report Generation (Step 7)
    ↓
    ├─→ 컨텍스트 매트릭스 포함
```

---

## 구현 태스크

### Task 1: 데이터 모델 설계 및 추가

**파일**: `src/types/models.py`

**추가할 모델**:

```python
class TaskContext(BaseModel):
    """태스크 실행 컨텍스트"""
    deployment_envs: List[str] = Field(
        default_factory=lambda: ["all"],
        description="배포 환경: development, staging, production, all"
    )
    actor_roles: List[str] = Field(
        default_factory=lambda: ["all"],
        description="사용자 역할: user, admin, partner_admin, super_admin, all"
    )
    role_based_features: Dict[str, str] = Field(
        default_factory=dict,
        description="역할별 상세 기능 설명 (예: {'user': '조회만', 'admin': 'CRUD'})"
    )
    env_based_features: Dict[str, str] = Field(
        default_factory=dict,
        description="환경별 상세 기능 설명 (예: {'dev': '테스트 PG', 'prod': '실제 PG'})"
    )
```

**수정할 모델**:

```python
class OpenAPIEndpoint(BaseModel):
    # 기존 필드들...
    path: str
    method: str
    tags: List[str]
    summary: Optional[str]
    description: Optional[str]
    operation_id: Optional[str]

    # NEW
    required_roles: List[str] = Field(
        default_factory=lambda: ["all"],
        description="필요한 역할 (LLM이 security 스키마 등에서 추출)"
    )
    deployment_env: str = Field(
        default="all",
        description="배포 환경 (파일명에서 추출)"
    )

class OpenAPISpec(BaseModel):
    # 기존 필드들...
    title: str
    version: str
    endpoints: List[OpenAPIEndpoint]
    source_file: Optional[str]

    # NEW
    deployment_env: str = Field(
        default="all",
        description="이 스펙 파일의 배포 환경"
    )

class IdentifiedTask(BaseModel):
    # 기존 필드들...
    index: int
    name: str
    description: str
    module: str
    entities: List[str]
    prerequisites: List[str]
    related_sections: List[int]

    # NEW
    context: TaskContext = Field(
        default_factory=TaskContext,
        description="태스크 컨텍스트 (역할, 환경)"
    )

class TaskMatchResult(BaseModel):
    # 기존 필드들...
    task: IdentifiedTask
    match_status: str
    matched_endpoints: List[OpenAPIEndpoint]
    confidence_score: float
    missing_features: List[str]

    # NEW
    context_match_matrix: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="""
        역할 x 환경 매트릭스
        {
          "user": {"development": "fully", "production": "fully"},
          "admin": {"development": "fully", "production": "partial"},
          "partner_admin": {"development": "new", "production": "new"}
        }
        """
    )
    llm_based: bool = Field(
        default=False,
        description="LLM 기반 매칭 여부"
    )
    explanation: Optional[str] = Field(
        default=None,
        description="LLM의 상세 설명"
    )
```

---

### Task 2: LLM 기반 PDF 컨텍스트 추출

**파일**: `src/llm/context_extractor.py` (새 파일)

**기능**:
- PDF 전처리 결과(Section)에서 역할/환경 정보 자동 추출
- LLM 프롬프트를 통해 "일반 사용자", "관리자", "개발환경", "운영환경" 등의 키워드 감지
- IdentifiedTask에 TaskContext 추가

**클래스 설계**:
```python
class LLMContextExtractor:
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def extract_task_context(
        self,
        task: IdentifiedTask,
        sections: List[Section]
    ) -> TaskContext:
        """
        태스크와 관련 섹션에서 컨텍스트 추출

        Returns:
            TaskContext with deployment_envs, actor_roles, role_based_features
        """
        pass

    def _build_context_extraction_prompt(
        self,
        task: IdentifiedTask,
        sections: List[Section]
    ) -> str:
        """컨텍스트 추출 프롬프트 생성"""
        pass

    def _parse_context_response(self, response: str) -> TaskContext:
        """LLM 응답을 TaskContext로 파싱"""
        pass
```

**프롬프트 예시**:
```
당신은 기획서 분석 전문가입니다. 다음 태스크의 컨텍스트를 추출하세요.

## 분석 대상 태스크
- 이름: {task.name}
- 설명: {task.description}

## 관련 섹션 내용
{format_sections(sections)}

## 추출 항목

### 1. 사용자 역할 구분
다음 키워드를 찾아 역할을 식별하세요:
- "일반 사용자", "사용자", "user", "회원" → user
- "관리자", "admin", "어드민", "운영자" → admin
- "파트너 관리자", "partner admin", "파트너" → partner_admin
- "슈퍼 관리자", "super admin", "시스템 관리자" → super_admin

역할별로 서로 다른 기능이 명시되어 있다면 role_based_features에 요약하세요.

### 2. 배포 환경 구분
다음 키워드를 찾아 환경을 식별하세요:
- "개발환경", "개발", "dev", "local", "로컬" → development
- "스테이징", "staging", "qa", "테스트 서버" → staging
- "프로덕션", "운영", "production", "prod", "실서버" → production

환경별로 다른 동작이 명시되어 있다면 env_based_features에 요약하세요.

## 출력 (JSON 형식)
{
  "deployment_envs": ["development", "production"],
  "actor_roles": ["user", "admin"],
  "role_based_features": {
    "user": "상품 조회만 가능",
    "admin": "상품 등록/수정/삭제 가능"
  },
  "env_based_features": {
    "development": "테스트 PG 사용",
    "production": "실제 PG 연동"
  }
}

**주의**:
- 명시되지 않았으면 ["all"] 반환
- 모든 역할/환경에서 동일하면 ["all"] 반환
```

---

### Task 3: LLM 기반 OpenAPI 역할/환경 추출

**파일**: `src/openapi/llm_openapi_analyzer.py` (새 파일)

**기능**:
- OpenAPI 스펙에서 엔드포인트별 역할 자동 추출 (security 스키마, 경로, 설명 분석)
- 파일명에서 배포 환경 추출 (openapi-dev.yaml → development)
- OpenAPIEndpoint에 required_roles, deployment_env 추가

**클래스 설계**:
```python
class LLMOpenAPIAnalyzer:
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def analyze_endpoint(self, endpoint_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        단일 엔드포인트의 역할 정보 추출

        Args:
            endpoint_spec: OpenAPI operation object (path, method, security, summary 등)

        Returns:
            {
                "required_roles": ["admin"],
                "explanation": "POST /api/products는 관리자 전용 API"
            }
        """
        pass

    def extract_deployment_env(self, file_path: Path) -> str:
        """
        파일명에서 배포 환경 추출

        Examples:
            openapi-dev.yaml → "development"
            api-staging.json → "staging"
            spec-prod.yaml → "production"
        """
        pass

    def _build_role_extraction_prompt(self, endpoint_spec: Dict) -> str:
        """역할 추출 프롬프트 생성"""
        pass
```

**프롬프트 예시**:
```
당신은 OpenAPI 스펙 분석 전문가입니다. 다음 엔드포인트의 사용자 역할을 추출하세요.

## 엔드포인트 정보
- Path: {path}
- Method: {method}
- Summary: {summary}
- Description: {description}
- Security: {security}

## 역할 추출 규칙

### 1. security 스키마 분석
security:
  - bearerAuth: [admin] → admin 역할 필요
  - bearerAuth: [user, admin] → user 또는 admin
  - bearerAuth: [] → 인증만 필요 (역할 무관 → all)

### 2. 경로 패턴 분석
- /api/admin/* → admin
- /api/partner/* → partner_admin
- /api/user/* → user
- /api/public/* → all (인증 불필요)

### 3. 설명 분석
- "관리자 전용", "admin only" → admin
- "파트너 관리자" → partner_admin
- 명시 없음 → all

## 출력 (JSON)
{
  "required_roles": ["admin"],
  "explanation": "security 스키마에 [admin] 명시됨"
}
```

---

### Task 4: LLM 기반 태스크 매칭 (컨텍스트 고려)

**파일**: `src/openapi/llm_task_matcher.py` (새 파일)

**기능**:
- 태스크의 컨텍스트와 엔드포인트의 컨텍스트를 비교하여 매칭
- 역할 x 환경 매트릭스 생성
- 기존 규칙 기반 매칭으로 폴백 가능

**클래스 설계**:
```python
class LLMTaskMatcher:
    def __init__(
        self,
        specs: List[OpenAPISpec],
        api_key: str,
        use_llm: bool = True,
        fallback: bool = True
    ):
        self.specs = specs
        self.api_key = api_key
        self.use_llm = use_llm
        self.client = Anthropic(api_key=api_key) if use_llm else None

        # Fallback to rule-based
        if fallback:
            from .matcher import TaskMatcher
            self.rule_based_matcher = TaskMatcher(specs)

    def match_task(self, task: IdentifiedTask) -> TaskMatchResult:
        """
        태스크와 OpenAPI 엔드포인트 매칭 (컨텍스트 고려)

        Returns:
            TaskMatchResult with context_match_matrix
        """
        if not self.use_llm or not self.api_key:
            logger.info("Using rule-based matching")
            return self.rule_based_matcher.match_task(task)

        try:
            # LLM 기반 매칭
            prompt = self._build_matching_prompt(task)
            response = self._call_llm(prompt)
            result = self._parse_matching_response(response, task)
            return result
        except Exception as e:
            logger.warning(f"LLM matching failed, falling back: {e}")
            return self.rule_based_matcher.match_task(task)

    def _build_matching_prompt(self, task: IdentifiedTask) -> str:
        """컨텍스트 기반 매칭 프롬프트 생성"""
        pass

    def _call_llm(self, prompt: str) -> str:
        """Claude API 호출"""
        pass

    def _parse_matching_response(
        self,
        response: str,
        task: IdentifiedTask
    ) -> TaskMatchResult:
        """LLM 응답을 TaskMatchResult로 파싱"""
        pass

    def _generate_context_matrix(
        self,
        task: IdentifiedTask,
        matched_endpoints: List[OpenAPIEndpoint]
    ) -> Dict[str, Dict[str, str]]:
        """역할 x 환경 매트릭스 생성"""
        pass
```

**프롬프트 예시**:
```
당신은 API 설계 분석 전문가입니다. 태스크와 OpenAPI 엔드포인트를 비교하여 구현 상태를 판단하세요.

## 분석 대상 태스크
- 이름: {task.name}
- 설명: {task.description}
- 컨텍스트:
  - 역할: {task.context.actor_roles}
  - 환경: {task.context.deployment_envs}
  - 역할별 기능: {task.context.role_based_features}

## 기존 OpenAPI 엔드포인트
{format_endpoints_with_context(endpoints)}

## 매칭 기준

### 1. 역할별 매칭
태스크의 각 역할별 기능이 엔드포인트에 구현되어 있는지 확인:
- user 기능 → required_roles에 "user" 포함된 엔드포인트
- admin 기능 → required_roles에 "admin" 포함된 엔드포인트

### 2. 환경별 매칭
태스크가 특정 환경을 명시했다면:
- development → deployment_env="development" 엔드포인트만 확인
- production → deployment_env="production" 엔드포인트만 확인
- all → 모든 환경 확인

### 3. 구현 상태
- fully_implemented: 해당 역할+환경 조합의 모든 기능이 구현됨
- partially_implemented: 일부만 구현됨
- new: 구현 안 됨

## 출력 (JSON)
{
  "match_status": "partially_implemented",
  "confidence_score": 0.75,
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
  },
  "matched_endpoints": [
    {
      "path": "/api/products",
      "method": "GET",
      "required_roles": ["user", "admin"],
      "deployment_env": "all",
      "reason": "user/admin 조회 기능과 일치"
    },
    {
      "path": "/api/products",
      "method": "POST",
      "required_roles": ["admin"],
      "deployment_env": "development",
      "reason": "admin 등록 기능, 개발환경에만 존재"
    }
  ],
  "missing_features": [
    "파트너 관리자용 상품 관리 API 없음",
    "관리자 등록 기능이 production 환경에 없음"
  ],
  "explanation": "조회 기능은 모든 환경에 구현되어 있으나, 등록/수정/삭제는 개발환경에만 존재. 파트너 관리자 기능은 완전히 새로운 기능."
}
```

---

### Task 5: Orchestrator 통합

**파일**: `src/cli/orchestrator.py`

**변경 사항**:

1. **OrchestratorConfig 파라미터 추가**:
```python
class OrchestratorConfig:
    # 기존 파라미터들...

    # NEW
    openapi_dir: Optional[str] = None  # OpenAPI 스펙 디렉토리
    use_llm_context_extraction: bool = True  # LLM 컨텍스트 추출
    use_llm_openapi_matching: bool = True  # LLM 매칭
```

2. **새로운 단계 추가**:
```python
def run(self):
    # Step 1-3: 기존 (PDF 추출, OCR, 전처리)

    # Step 4: LLM Planner (컨텍스트 추출 추가)
    tasks = self._identify_tasks(...)
    tasks_with_context = self._extract_task_contexts(tasks, sections)  # NEW

    # Step 4.5: OpenAPI 분석 (NEW)
    openapi_specs = None
    if self.config.openapi_dir:
        openapi_specs = self._analyze_openapi_specs()
        match_results = self._match_tasks_with_openapi(
            tasks_with_context,
            openapi_specs
        )

    # Step 5: TaskWriter (매칭 결과 반영)
    tasks_with_markdown = self._write_tasks(
        tasks_with_context,
        functional_groups,
        match_results  # NEW
    )

    # Step 6-7: 기존 (파일 분리, 리포트)
```

3. **새로운 메서드 구현**:
```python
def _extract_task_contexts(
    self,
    tasks: List[IdentifiedTask],
    sections: List[Section]
) -> List[IdentifiedTask]:
    """LLM으로 태스크 컨텍스트 추출"""
    if not self.config.use_llm_context_extraction:
        return tasks

    from src.llm.context_extractor import LLMContextExtractor

    extractor = LLMContextExtractor(
        api_key=self.config.api_key,
        model=self.config.model
    )

    tasks_with_context = []
    for task in tasks:
        context = extractor.extract_task_context(task, sections)
        task.context = context
        tasks_with_context.append(task)

    return tasks_with_context

def _analyze_openapi_specs(self) -> List[OpenAPISpec]:
    """OpenAPI 스펙 로드 및 분석"""
    from src.openapi.loader import OpenAPILoader
    from src.openapi.parser import OpenAPIParser
    from src.openapi.llm_openapi_analyzer import LLMOpenAPIAnalyzer

    loader = OpenAPILoader(self.config.openapi_dir)
    parser = OpenAPIParser()
    analyzer = LLMOpenAPIAnalyzer(
        api_key=self.config.api_key,
        model=self.config.model
    )

    specs = []
    for spec_dict in loader.load_all_specs():
        # Parse
        spec = parser.parse(spec_dict)

        # LLM 분석으로 역할/환경 추출
        for endpoint in spec.endpoints:
            roles = analyzer.analyze_endpoint({
                "path": endpoint.path,
                "method": endpoint.method,
                "summary": endpoint.summary,
                "description": endpoint.description
            })
            endpoint.required_roles = roles["required_roles"]

        # 배포 환경 추출
        spec.deployment_env = analyzer.extract_deployment_env(
            Path(spec.source_file)
        )

        specs.append(spec)

    return specs

def _match_tasks_with_openapi(
    self,
    tasks: List[IdentifiedTask],
    specs: List[OpenAPISpec]
) -> List[TaskMatchResult]:
    """LLM 기반 태스크 매칭"""
    from src.openapi.llm_task_matcher import LLMTaskMatcher

    matcher = LLMTaskMatcher(
        specs=specs,
        api_key=self.config.api_key,
        use_llm=self.config.use_llm_openapi_matching
    )

    results = []
    for task in tasks:
        result = matcher.match_task(task)
        results.append(result)

    return results
```

---

### Task 6: CLI 옵션 추가

**파일**: `src/cli/main.py`

**추가할 옵션**:
```python
@click.option(
    "--openapi",
    type=click.Path(exists=True),
    help="OpenAPI spec directory path"
)
@click.option(
    "--use-llm-context/--no-llm-context",
    default=True,
    help="Use LLM for context extraction (default: True)"
)
@click.option(
    "--use-llm-matching/--no-llm-matching",
    default=True,
    help="Use LLM for OpenAPI matching (default: True)"
)
@click.option(
    "--filter-role",
    type=str,
    help="Filter by role (user,admin,partner_admin)"
)
@click.option(
    "--filter-env",
    type=str,
    help="Filter by environment (development,staging,production)"
)
def analyze(
    pdf_path,
    out,
    openapi,  # NEW
    use_llm_context,  # NEW
    use_llm_matching,  # NEW
    filter_role,  # NEW
    filter_env,  # NEW
    # 기존 파라미터들...
):
    config = OrchestratorConfig(
        pdf_path=pdf_path,
        output_dir=out,
        openapi_dir=openapi,  # NEW
        use_llm_context_extraction=use_llm_context,  # NEW
        use_llm_openapi_matching=use_llm_matching,  # NEW
        # ...
    )
```

---

### Task 7: 테스트 작성

**파일**: `test_llm_context_matching.py` (새 파일)

**테스트 항목**:
1. TaskContext 추출 (Mock LLM)
2. OpenAPI 역할 추출 (Mock LLM)
3. 컨텍스트 기반 매칭 (Mock LLM)
4. 매트릭스 생성
5. Orchestrator 통합
6. CLI 옵션

---

### Task 8: 문서화

**파일**: `README_LLM_CONTEXT_MATCHING.md` (새 파일)

**내용**:
- 기능 개요
- 컨텍스트 추출 예시
- 매칭 매트릭스 예시
- 사용 방법
- 비용/성능 정보

---

## 파일 구조 (최종)

```
pdf-agent/
├── src/
│   ├── llm/
│   │   ├── context_extractor.py       # NEW - PDF 컨텍스트 추출
│   │   ├── planner/                   # 기존 (프롬프트 개선)
│   │   └── task_writer.py             # 기존 (매칭 결과 반영)
│   ├── openapi/
│   │   ├── llm_openapi_analyzer.py    # NEW - OpenAPI 역할/환경 추출
│   │   ├── llm_task_matcher.py        # NEW - 컨텍스트 기반 매칭
│   │   ├── matcher.py                 # 기존 (규칙 기반, 폴백용)
│   │   ├── parser.py                  # 기존
│   │   └── loader.py                  # 기존
│   ├── cli/
│   │   ├── orchestrator.py            # 수정 - 통합
│   │   └── main.py                    # 수정 - CLI 옵션
│   └── types/
│       └── models.py                  # 수정 - 모델 추가
├── test_llm_context_matching.py       # NEW
├── README_LLM_CONTEXT_MATCHING.md     # NEW
└── tasks/
    └── LLM_OpenAPI_Context_Matching.md # 이 문서
```

---

## 예상 비용/성능

### 추가 LLM 호출

**태스크 10개, 엔드포인트 50개 기준**:

| 단계 | 호출 수 | 토큰/호출 | 총 토큰 | 비용 |
|------|---------|-----------|---------|------|
| 컨텍스트 추출 (PDF) | 10회 | 1,500 | 15,000 | $0.05 |
| 역할 추출 (OpenAPI) | 50회 | 800 | 40,000 | $0.13 |
| 매칭 | 10회 | 2,500 | 25,000 | $0.08 |
| **합계** | 70회 | - | 80,000 | **$0.26** |

**기존 파이프라인**: $0.20
**새 파이프라인**: $0.46 (+130%)

**BUT**: 정확도 향상으로 수동 수정 시간 절감, 중복 구현 방지 → 실질적 비용 절감 가능

---

## 성공 기준

1. ✅ 역할별/환경별 컨텍스트 자동 추출 (정확도 85% 이상)
2. ✅ 컨텍스트 매트릭스 생성 및 시각화
3. ✅ 기존 규칙 기반으로 폴백 가능
4. ✅ 전체 파이프라인 E2E 테스트 통과
5. ✅ 문서화 완료

---

## 참고 사항

### 기존 코드 재사용
- `src/llm/claude_client.py`: 재사용
- `src/llm/planner/*`: 프롬프트만 개선
- `src/openapi/matcher.py`: 폴백용으로 유지

### 신규 구현 필요
- `context_extractor.py`: 완전 신규
- `llm_openapi_analyzer.py`: 완전 신규
- `llm_task_matcher.py`: 완전 신규

---

## 다음 단계

1. Agent 실행하여 구현
2. 실제 PDF/OpenAPI로 테스트
3. 성능 측정 및 최적화
4. 문서화 및 배포
