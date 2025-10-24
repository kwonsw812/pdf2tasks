# FileSplitter 구현 — 상위 태스크 7

## 상위 태스크 개요
- **설명:** 상위 태스크별로 Markdown 파일을 분리하여 저장하는 모듈 구현
- **모듈/영역:** `src/splitter/`
- **관련 기술:** 파일 시스템 I/O, 파일명 생성 규칙
- **선행 조건:** LLM TaskWriter 구현 완료 (상위 태스크 6)
- **참고:** AI_Agent_Project_Plan.md (Section 5 - FileSplitter, Section 7 - Markdown 산출 구조)

---

## 하위 태스크 목록

### 7.1 파일명 생성 규칙 구현
- **목적:** 일관된 파일명 생성 (`{index}_{기능명}.md`)
- **작업 내용:**
  - 상위 태스크 이름을 파일명으로 안전하게 변환
  - 특수문자 제거/대체 (공백 → 언더스코어, 슬래시 제거 등)
  - 중복 방지 (동일 이름 시 숫자 추가)
- **입력:** `IdentifiedTask` (index, name)
- **출력:** 파일명 문자열
- **로직 요약:**
  ```typescript
  function generateFileName(task: IdentifiedTask): string {
    const safeName = task.name
      .replace(/\s+/g, '_')
      .replace(/[\/\\?%*:|"<>]/g, '')
      .substring(0, 50);  // 파일명 길이 제한

    return `${task.index}_${safeName}.md`;
  }
  ```
- **예시:**
  - 입력: `{ index: 1, name: "인증 및 회원관리" }`
  - 출력: `1_인증_및_회원관리.md`
- **테스트 포인트:**
  - 특수문자 포함 이름 처리
  - 긴 이름 자르기 확인

### 7.2 출력 디렉토리 관리
- **목적:** 결과 파일을 저장할 디렉토리 생성 및 관리
- **작업 내용:**
  - 출력 디렉토리 존재 여부 확인
  - 없으면 생성 (재귀적)
  - 기존 파일 덮어쓰기 옵션 제공
- **입력:** 출력 디렉토리 경로
- **로직 요약:**
  ```typescript
  async function ensureOutputDirectory(outputPath: string): Promise<void> {
    const fs = require('fs-extra');
    await fs.ensureDir(outputPath);
  }
  ```
- **옵션:**
  - `--clean`: 기존 파일 모두 삭제 후 생성
  - `--overwrite`: 덮어쓰기 허용 (기본값)
- **테스트 포인트:**
  - 존재하지 않는 디렉토리 생성 확인
  - 권한 오류 처리

### 7.3 Markdown 파일 쓰기 함수
- **목적:** 생성된 Markdown 콘텐츠를 파일로 저장
- **작업 내용:**
  - `fs-extra` 또는 Node.js `fs` 모듈 사용
  - UTF-8 인코딩으로 저장
  - 에러 처리 (디스크 공간 부족, 권한 문제 등)
- **입력:** 파일 경로, Markdown 콘텐츠
- **출력:** 저장 성공 여부
- **로직 요약:**
  ```typescript
  async function writeMarkdownFile(
    filePath: string,
    content: string
  ): Promise<void> {
    const fs = require('fs-extra');
    await fs.writeFile(filePath, content, 'utf-8');
  }
  ```
- **예외 처리:**
  - 디스크 공간 부족: `DiskSpaceError`
  - 권한 없음: `PermissionError`
- **테스트 포인트:**
  - 정상 파일 쓰기 성공
  - 파일 내용 정확히 저장되었는지 읽어서 확인

### 7.4 상위 태스크별 파일 분리 로직
- **목적:** 각 상위 태스크를 개별 Markdown 파일로 저장
- **작업 내용:**
  - 상위 태스크 배열 순회
  - 각 태스크의 Markdown 생성 (TaskWriter 결과)
  - 파일명 생성 후 저장
- **입력:** `Array<{ task: IdentifiedTask, markdown: string }>`
- **출력:** 저장된 파일 경로 배열
- **로직 요약:**
  ```typescript
  async function splitAndSave(
    tasks: Array<{ task: IdentifiedTask, markdown: string }>,
    outputDir: string
  ): Promise<string[]> {
    const savedFiles: string[] = [];

    for (const { task, markdown } of tasks) {
      const fileName = generateFileName(task);
      const filePath = path.join(outputDir, fileName);
      await writeMarkdownFile(filePath, markdown);
      savedFiles.push(filePath);
    }

    return savedFiles;
  }
  ```
- **테스트 포인트:**
  - 여러 태스크 파일 모두 생성 확인
  - 파일 개수가 상위 태스크 개수와 일치

### 7.5 파일 메타정보 생성 (선택 사항)
- **목적:** 각 Markdown 파일에 메타정보 헤더 추가
- **작업 내용:**
  - YAML Front Matter 추가 (선택 사항)
  - 생성 일시, 원본 PDF 경로 등 메타데이터 포함
- **출력 예시:**
  ```markdown
  ---
  title: 인증 및 회원관리
  index: 1
  generated: 2025-01-15T10:30:00Z
  source_pdf: ./specs/app-v1.pdf
  ---

  # 인증 및 회원관리 — 상위 태스크 1
  ...
  ```
- **테스트 포인트:**
  - Front Matter 파싱 확인 (예: gray-matter 라이브러리)

### 7.6 FileSplitter 통합 인터페이스
- **목적:** FileSplitter 기능을 하나의 인터페이스로 통합
- **작업 내용:**
  - `FileSplitter` 클래스 작성
  - 출력 디렉토리 관리 → 파일 분리 → 저장
- **사용 예시:**
  ```typescript
  const splitter = new FileSplitter('./out');
  const files = await splitter.split(tasksWithMarkdown);
  console.log(`생성된 파일: ${files.length}개`);
  ```
- **산출물:** `src/splitter/FileSplitter.ts`
- **테스트 포인트:**
  - E2E FileSplitter 플로우 테스트

### 7.7 요약 로그 파일 생성
- **목적:** 생성된 파일 목록 및 통계를 `report.log`로 저장
- **작업 내용:**
  - 생성된 파일 경로 목록
  - 각 파일 크기
  - 총 처리 시간
  - 에러 발생 파일 (있을 경우)
- **로그 예시:**
  ```
  [FileSplitter Report]
  총 생성 파일: 5개

  1. ./out/1_인증_및_회원관리.md (12.5 KB)
  2. ./out/2_결제_시스템.md (8.3 KB)
  ...

  총 처리 시간: 3.2초
  에러: 없음
  ```
- **산출물:** `./out/report.log`
- **테스트 포인트:**
  - 로그 파일 생성 확인
  - 정보 정확성 검증

### 7.8 에러 핸들링 및 복구
- **목적:** 파일 쓰기 실패 시 복구 메커니즘
- **작업 내용:**
  - 일부 파일 저장 실패 시 나머지 계속 처리
  - 실패한 파일 정보 로깅
  - 재시도 옵션 제공 (선택 사항)
- **로직 요약:**
  ```typescript
  async function splitAndSaveWithRetry(...): Promise<SaveResult> {
    const savedFiles: string[] = [];
    const failedFiles: Array<{ task: string, error: Error }> = [];

    for (const item of tasks) {
      try {
        const filePath = await saveFile(item);
        savedFiles.push(filePath);
      } catch (error) {
        failedFiles.push({ task: item.task.name, error });
      }
    }

    return { savedFiles, failedFiles };
  }
  ```
- **테스트 포인트:**
  - 권한 오류 발생 시 계속 진행 확인
  - 실패 파일 로그 기록

---

## 완료 조건
- [ ] 파일명 생성 규칙 구현 및 테스트
- [ ] 출력 디렉토리 관리 기능 완성
- [ ] Markdown 파일 쓰기 함수 동작 확인
- [ ] 상위 태스크별 파일 분리 로직 구현
- [ ] 파일 메타정보 생성 (선택 사항)
- [ ] FileSplitter 통합 인터페이스 완성
- [ ] 요약 로그 파일 (`report.log`) 생성
- [ ] 에러 핸들링 및 복구 메커니즘 구현
- [ ] 여러 상위 태스크로 E2E 테스트 통과
