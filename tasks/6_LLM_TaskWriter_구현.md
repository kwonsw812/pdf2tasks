# LLM TaskWriter 구현 — 상위 태스크 6

## 상위 태스크 개요
- **설명:** 상위 태스크를 LLM을 사용하여 하위 개발 작업으로 세분화
- **모듈/영역:** `src/llm/task-writer/`
- **관련 기술:** Anthropic Claude API, 프롬프트 엔지니어링
- **선행 조건:** LLM Planner 구현 완료 (상위 태스크 5)
- **참고:** AI_Agent_Project_Plan.md (Section 5 - LLM TaskWriter, Section 6, 7)

---

## 하위 태스크 목록

### 6.1 TaskWriter 프롬프트 설계
- **목적:** 상위 태스크를 하위 작업으로 분해하는 프롬프트 작성
- **프롬프트 구조:**
  ```
  역할: 당신은 시니어 백엔드 개발자입니다.

  목표: 주어진 상위 기능(태스크)을 구체적인 하위 개발 작업으로 세분화하세요.

  지시사항:
  - NestJS와 Prisma를 사용합니다.
  - 각 하위 태스크는 실제 구현 가능한 단위로 작성하세요.
  - 엔드포인트, 데이터 모델, 로직, 권한, 예외처리, 테스트를 포함하세요.
  - Claude Code가 바로 실행할 수 있도록 구체적으로 작성하세요.

  입력:
  상위 태스크: {name}
  설명: {description}
  관련 섹션 내용: {sectionContents}

  출력 형식 (Markdown):
  ## {index}.1 {하위 태스크명}
  - **목적:** {설명}
  - **엔드포인트:** `POST /api/...`
  - **데이터 모델:** ...
  - **로직 요약:** ...
  - **권한/보안:** ...
  - **예외:** ...
  - **테스트 포인트:** ...

  ## {index}.2 {하위 태스크명}
  ...
  ```
- **산출물:** `src/llm/task-writer/prompts.ts`
- **테스트 포인트:**
  - 다양한 상위 태스크로 프롬프트 품질 검증
  - Markdown 출력 형식 일관성 확인

### 6.2 상위 태스크 데이터를 프롬프트로 변환
- **목적:** Planner의 출력을 TaskWriter 입력으로 변환
- **작업 내용:**
  - 상위 태스크 정보 + 관련 섹션 내용 결합
  - 토큰 제한 고려 (섹션 내용 요약)
- **입력:** `IdentifiedTask` + 관련 `Section[]`
- **출력:** 프롬프트 문자열
- **로직 요약:**
  ```typescript
  function buildTaskWriterPrompt(
    task: IdentifiedTask,
    sections: Section[]
  ): string {
    let prompt = systemPrompt + '\n\n';
    prompt += `상위 태스크: ${task.name}\n`;
    prompt += `설명: ${task.description}\n\n`;
    prompt += '관련 섹션 내용:\n';

    task.relatedSections.forEach(idx => {
      const section = sections[idx];
      prompt += `[${section.title}]\n${section.content}\n\n`;
    });

    prompt += '\n출력 (Markdown):';
    return prompt;
  }
  ```
- **테스트 포인트:**
  - 프롬프트 길이가 적절한지 확인
  - 관련 섹션 모두 포함되었는지 검증

### 6.3 LLM 호출 및 Markdown 응답 파싱
- **목적:** Claude API 호출 및 Markdown 형식 결과 파싱
- **작업 내용:**
  - Claude Messages API 사용
  - Markdown 응답 검증 (필수 필드 존재 확인)
  - 하위 태스크 구조 추출
- **입력:** 프롬프트
- **출력:**
  ```typescript
  interface SubTask {
    index: string;        // 예: "1.1", "1.2"
    title: string;
    purpose: string;
    endpoint?: string;
    dataModel?: string;
    logic: string;
    security?: string;
    exceptions?: string;
    testPoints?: string;
  }
  ```
- **로직 요약:**
  ```typescript
  async function callTaskWriter(prompt: string): Promise<string> {
    const response = await client.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 8192,
      messages: [{ role: 'user', content: prompt }]
    });

    return response.content[0].text;  // Markdown 텍스트
  }

  function parseSubTasks(markdown: string): SubTask[] {
    // Markdown 파싱 (예: marked 라이브러리 사용)
    // "## X.Y" 패턴으로 하위 태스크 분리
    // 각 필드 추출
  }
  ```
- **예외 처리:**
  - Markdown 형식 불일치 → 재시도
  - 필수 필드 누락 → 경고 로그
- **테스트 포인트:**
  - 정상 Markdown 응답 파싱 성공
  - 다양한 필드 조합 처리

### 6.4 Markdown 산출 구조 생성
- **목적:** 기획서(Section 7)에 정의된 Markdown 형식 준수
- **작업 내용:**
  - 상위 태스크 개요 섹션 생성
  - 하위 태스크 목록 추가
  - 페이지 참조 정보 삽입
- **출력 예시:**
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
  - **엔드포인트:** ...
  ...
  ```
- **산출물:** 구조화된 Markdown 문자열
- **테스트 포인트:**
  - 출력 Markdown이 기획서 예시와 일치
  - Claude Code에서 인식 가능한 형식

### 6.5 하위 태스크 검증 및 품질 체크
- **목적:** 생성된 하위 태스크의 완성도 확인
- **검증 항목:**
  - 필수 필드 존재 여부 (목적, 로직 등)
  - 너무 추상적이지 않은지 (구체성 확인)
  - 중복 하위 태스크 없는지
- **작업 내용:**
  - 규칙 기반 검증
  - 선택적으로 LLM에게 품질 평가 요청
- **로직 요약:**
  ```typescript
  function validateSubTasks(subTasks: SubTask[]): ValidationResult {
    const errors: string[] = [];

    subTasks.forEach(task => {
      if (!task.purpose) errors.push(`${task.index}: 목적 누락`);
      if (!task.logic) errors.push(`${task.index}: 로직 누락`);
      if (task.logic.length < 50) {
        errors.push(`${task.index}: 로직이 너무 간단함`);
      }
    });

    return { isValid: errors.length === 0, errors };
  }
  ```
- **테스트 포인트:**
  - 정상 케이스 검증 통과
  - 오류 케이스 감지

### 6.6 NestJS/Prisma 문맥 반영
- **목적:** 프롬프트에 NestJS/Prisma 관련 지침 명확히 명시
- **작업 내용:**
  - 프롬프트에 NestJS 모듈 구조, 데코레이터 사용 등 가이드 추가
  - Prisma 스키마 예시 포함
- **프롬프트 추가 지침:**
  ```
  - 엔드포인트는 NestJS 컨트롤러로 구현됩니다 (예: @Controller, @Post).
  - 데이터 모델은 Prisma 스키마로 정의됩니다.
  - 서비스 레이어에서 비즈니스 로직을 처리합니다.
  - 인증은 JWT 기반 Guard를 사용합니다.
  ```
- **테스트 포인트:**
  - 생성된 하위 태스크에 NestJS/Prisma 용어 포함 확인

### 6.7 LLM TaskWriter 통합 인터페이스
- **목적:** TaskWriter 기능을 하나의 인터페이스로 통합
- **작업 내용:**
  - `LLMTaskWriter` 클래스 작성
  - 상위 태스크 입력 → 프롬프트 생성 → LLM 호출 → Markdown 생성 → 반환
- **사용 예시:**
  ```typescript
  const taskWriter = new LLMTaskWriter();
  const markdown = await taskWriter.writeTask(task, sections);
  ```
- **산출물:** `src/llm/task-writer/LLMTaskWriter.ts`
- **테스트 포인트:**
  - E2E TaskWriter 플로우 테스트

### 6.8 토큰 사용량 추적
- **목적:** TaskWriter의 LLM 비용 모니터링
- **작업 내용:**
  - LLM Planner와 동일한 방식으로 토큰 추적
  - 총 비용 누적
- **로깅 정보:**
  - 각 상위 태스크별 토큰 사용량
  - 총 비용
- **테스트 포인트:**
  - 토큰 사용량 정확히 기록

---

## 완료 조건
- [ ] TaskWriter 프롬프트 설계 및 검증
- [ ] 상위 태스크 → 프롬프트 변환 로직 구현
- [ ] LLM 호출 및 Markdown 응답 파싱 성공
- [ ] 기획서 형식에 맞는 Markdown 구조 생성
- [ ] 하위 태스크 검증 및 품질 체크 구현
- [ ] NestJS/Prisma 문맥 프롬프트에 반영
- [ ] LLM TaskWriter 통합 인터페이스 완성
- [ ] 토큰 사용량 추적 구현
- [ ] 실제 상위 태스크로 E2E 테스트 통과
