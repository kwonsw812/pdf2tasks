# LLM Planner 구현 — 상위 태스크 5

## 상위 태스크 개요
- **설명:** 전처리된 섹션들을 LLM을 사용하여 상위 기능(태스크)으로 분류하고 식별
- **모듈/영역:** `src/llm/planner/`
- **관련 기술:** Anthropic Claude API, 프롬프트 엔지니어링
- **선행 조건:** Preprocessor 구현 완료 (상위 태스크 4)
- **참고:** AI_Agent_Project_Plan.md (Section 5 - LLM Planner, Section 6 - 프롬프트 설계)

---

## 하위 태스크 목록

### 5.1 Anthropic Claude API 클라이언트 설정
- **목적:** Claude API와의 통신 인프라 구축
- **작업 내용:**
  - `@anthropic-ai/sdk` 패키지 설치 및 초기화
  - API 키 환경 변수 설정
  - 기본 API 호출 래퍼 함수 작성
- **설정:**
  ```typescript
  import Anthropic from '@anthropic-ai/sdk';

  const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY
  });
  ```
- **산출물:** `src/llm/claude-client.ts`
- **테스트 포인트:**
  - API 연결 테스트 (간단한 프롬프트 실행)
  - 에러 처리 확인 (잘못된 API 키, 네트워크 오류)

### 5.2 LLM Planner 프롬프트 설계
- **목적:** 상위 기능 식별을 위한 효과적인 프롬프트 작성
- **프롬프트 구조:**
  ```
  역할: 당신은 시니어 백엔드 아키텍트입니다.

  목표: 주어진 기획서 섹션들을 분석하여 백엔드 개발 관점에서 상위 기능(태스크)을 식별하고 분류하세요.

  지시사항:
  - NestJS와 Prisma를 사용하는 프로젝트입니다.
  - 각 상위 기능은 독립적인 모듈 또는 도메인으로 구성됩니다.
  - 관련된 섹션들을 하나의 상위 기능으로 그룹화하세요.
  - 가정이 필요한 경우 "가정 필요" 표기하세요.

  입력 형식:
  [섹션 목록 + 내용]

  출력 형식 (JSON):
  {
    "tasks": [
      {
        "index": 1,
        "name": "인증 및 회원관리",
        "description": "사용자 인증, 로그인, 회원가입 등",
        "module": "AuthModule",
        "relatedSections": [1, 2, 3],
        "entities": ["User", "Session"],
        "dependencies": []
      }
    ]
  }
  ```
- **산출물:** `src/llm/planner/prompts.ts`
- **테스트 포인트:**
  - 다양한 기획서 샘플로 프롬프트 품질 검증
  - JSON 출력 형식 일관성 확인

### 5.3 섹션 데이터를 프롬프트로 변환
- **목적:** Preprocessor 출력을 LLM이 이해할 수 있는 형식으로 변환
- **작업 내용:**
  - 섹션 목록 → 구조화된 텍스트 또는 JSON
  - 토큰 제한 고려 (섹션이 많을 경우 요약 또는 분할)
- **입력:** `FunctionalGroup[]` 또는 `Section[]`
- **출력:** 프롬프트 문자열
- **로직 요약:**
  ```typescript
  function buildPlannerPrompt(sections: Section[]): string {
    let prompt = systemPrompt + '\n\n입력 섹션:\n';
    sections.forEach((section, idx) => {
      prompt += `[${idx + 1}] ${section.title}\n`;
      prompt += `내용: ${section.content.substring(0, 500)}...\n\n`;
    });
    prompt += '\n출력 (JSON):';
    return prompt;
  }
  ```
- **토큰 관리:**
  - 섹션이 100개 이상일 경우 청크 분할
  - 각 청크별로 LLM 호출 후 결과 병합
- **테스트 포인트:**
  - 프롬프트 길이가 LLM 토큰 제한 내에 있는지 확인

### 5.4 LLM 호출 및 응답 파싱
- **목적:** Claude API 호출 및 결과 파싱
- **작업 내용:**
  - Claude Messages API 사용
  - JSON 응답 파싱 및 검증
  - 재시도 로직 (API 오류 시)
- **입력:** 프롬프트
- **출력:**
  ```typescript
  interface IdentifiedTask {
    index: number;
    name: string;
    description: string;
    module?: string;
    relatedSections: number[];
    entities?: string[];
    dependencies?: string[];
  }
  ```
- **로직 요약:**
  ```typescript
  async function callLLMPlanner(prompt: string): Promise<IdentifiedTask[]> {
    const response = await client.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 4096,
      messages: [{ role: 'user', content: prompt }]
    });

    const jsonText = extractJSON(response.content[0].text);
    const parsed = JSON.parse(jsonText);
    return parsed.tasks;
  }
  ```
- **예외 처리:**
  - JSON 파싱 실패 → 재시도 또는 에러 로그
  - API 타임아웃 → 재시도 (최대 3회)
- **테스트 포인트:**
  - 정상 응답 파싱 성공
  - 잘못된 JSON 응답 처리 확인

### 5.5 상위 태스크 중복 제거 및 병합
- **목적:** LLM이 유사한 태스크를 중복 식별한 경우 병합
- **작업 내용:**
  - 태스크 이름 유사도 계산 (예: Levenshtein distance)
  - 중복 태스크 병합 규칙 적용
- **입력:** `IdentifiedTask[]`
- **출력:** 중복 제거된 `IdentifiedTask[]`
- **로직 요약:**
  ```typescript
  function deduplicateTasks(tasks: IdentifiedTask[]): IdentifiedTask[] {
    const unique: IdentifiedTask[] = [];
    for (const task of tasks) {
      const similar = unique.find(t => similarity(t.name, task.name) > 0.8);
      if (similar) {
        similar.relatedSections.push(...task.relatedSections);
      } else {
        unique.push(task);
      }
    }
    return unique;
  }
  ```
- **테스트 포인트:**
  - 유사 태스크 병합 확인
  - 서로 다른 태스크는 유지

### 5.6 상위 태스크 우선순위 및 의존성 분석
- **목적:** 태스크 간 의존 관계 식별 및 구현 순서 제안
- **작업 내용:**
  - LLM에게 의존성 정보 요청 (추가 프롬프트)
  - 선행 조건 명시 (예: "인증 모듈이 먼저 구현되어야 함")
- **출력:**
  ```typescript
  interface TaskWithDependency extends IdentifiedTask {
    dependencies: string[];  // 다른 태스크 이름들
    priority: number;         // 1(높음) - 5(낮음)
  }
  ```
- **로직 요약:**
  - LLM에게 "각 태스크의 선행 조건과 우선순위를 분석하세요" 프롬프트
  - 응답에서 의존성 추출
- **테스트 포인트:**
  - 일반적인 의존성 패턴 확인 (인증 → 권한 관리)

### 5.7 LLM Planner 통합 인터페이스
- **목적:** Planner 기능을 하나의 인터페이스로 통합
- **작업 내용:**
  - `LLMPlanner` 클래스 작성
  - 섹션 입력 → 프롬프트 생성 → LLM 호출 → 파싱 → 중복 제거 → 반환
- **사용 예시:**
  ```typescript
  const planner = new LLMPlanner();
  const tasks = await planner.identifyTasks(preprocessedSections);
  ```
- **산출물:** `src/llm/planner/LLMPlanner.ts`
- **테스트 포인트:**
  - E2E Planner 플로우 테스트

### 5.8 토큰 사용량 추적 및 비용 로깅
- **목적:** LLM API 사용 비용 모니터링
- **작업 내용:**
  - API 응답에서 토큰 사용량 추출
  - 누적 비용 계산 (Claude 가격표 기준)
  - 로그 파일 또는 콘솔 출력
- **로깅 정보:**
  - 프롬프트 토큰 수
  - 응답 토큰 수
  - 총 비용 (USD)
- **산출물:** `report.log` 또는 실시간 콘솔 출력
- **테스트 포인트:**
  - 토큰 사용량 정확히 추적
  - 비용 계산 검증

---

## 완료 조건
- [ ] Anthropic Claude API 클라이언트 설정 완료
- [ ] LLM Planner 프롬프트 설계 및 검증
- [ ] 섹션 데이터 → 프롬프트 변환 로직 구현
- [ ] LLM 호출 및 JSON 응답 파싱 성공
- [ ] 상위 태스크 중복 제거 및 병합 구현
- [ ] 태스크 의존성 분석 기능 추가
- [ ] LLM Planner 통합 인터페이스 완성
- [ ] 토큰 사용량 추적 및 비용 로깅 구현
- [ ] 실제 기획서로 E2E 테스트 통과
