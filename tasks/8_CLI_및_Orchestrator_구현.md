# CLI 및 Orchestrator 구현 — 상위 태스크 8

## 상위 태스크 개요
- **설명:** 전체 워크플로우를 통합하고 CLI 인터페이스를 제공
- **모듈/영역:** `src/cli/`, `src/orchestrator/`
- **관련 기술:** Commander.js, 모듈 통합, 오케스트레이션
- **선행 조건:** FileSplitter 구현 완료 (상위 태스크 7)
- **참고:** AI_Agent_Project_Plan.md (Section 8 - CLI 사용 시나리오)

---

## 하위 태스크 목록

### 8.1 Commander.js 설치 및 CLI 기본 구조
- **목적:** CLI 명령어 파싱 및 옵션 처리
- **작업 내용:**
  - `commander` 패키지 설치
  - CLI 진입점 파일 작성 (`src/cli/index.ts`)
  - 명령어 및 옵션 정의
- **CLI 명령어 예시:**
  ```bash
  pdf2tasks analyze <pdf-path> --out <output-dir> [options]
  ```
- **옵션:**
  - `--out, -o`: 출력 디렉토리 (필수)
  - `--clean`: 기존 출력 파일 삭제
  - `--verbose, -v`: 상세 로그 출력
  - `--dry-run`: 실제 파일 생성 없이 미리보기
- **산출물:** `src/cli/index.ts`
- **테스트 포인트:**
  - `pdf2tasks --help` 실행 시 도움말 출력
  - 옵션 파싱 정확성 확인

### 8.2 CLI 진입점 및 파라미터 검증
- **목적:** 사용자 입력 유효성 검사
- **작업 내용:**
  - PDF 파일 경로 존재 여부 확인
  - 출력 디렉토리 경로 유효성 검사
  - 필수 인자 누락 시 에러 메시지 출력
- **입력:** CLI 인자
- **출력:** 검증된 옵션 객체
- **로직 요약:**
  ```typescript
  function validateCLIArgs(args: CLIArgs): ValidationResult {
    if (!fs.existsSync(args.pdfPath)) {
      return { valid: false, error: 'PDF 파일을 찾을 수 없습니다.' };
    }
    if (!args.outputDir) {
      return { valid: false, error: '출력 디렉토리를 지정하세요 (--out).' };
    }
    return { valid: true };
  }
  ```
- **테스트 포인트:**
  - 존재하지 않는 PDF 경로 입력 시 에러
  - 필수 옵션 누락 시 에러

### 8.3 Orchestrator 클래스 설계
- **목적:** 전체 워크플로우 단계를 순차 실행
- **작업 내용:**
  - `Orchestrator` 클래스 작성
  - 각 모듈(Extractor, OCR, Preprocessor, Planner, TaskWriter, Splitter) 호출
  - 단계별 진행률 표시
- **워크플로우:**
  1. PDF 추출 (Extractor)
  2. OCR 처리 (OCR Engine)
  3. 전처리 (Preprocessor)
  4. 상위 태스크 식별 (LLM Planner)
  5. 하위 태스크 세분화 (LLM TaskWriter)
  6. 파일 분리 (FileSplitter)
  7. 리포트 생성 (Reporter)
- **산출물:** `src/orchestrator/Orchestrator.ts`
- **테스트 포인트:**
  - 전체 플로우 E2E 테스트

### 8.4 단계별 워크플로우 구현
- **목적:** Orchestrator의 각 단계 구현
- **작업 내용:**
  - 각 단계를 비동기 함수로 구현
  - 단계 간 데이터 전달
  - 에러 발생 시 워크플로우 중단 또는 계속 진행 옵션
- **로직 예시:**
  ```typescript
  class Orchestrator {
    async run(pdfPath: string, options: Options): Promise<OrchestratorResult> {
      console.log('1/7 PDF 추출 중...');
      const pdfData = await this.extractor.extract(pdfPath);

      console.log('2/7 OCR 처리 중...');
      const ocrResults = await this.ocrEngine.processImages(pdfData.images);

      console.log('3/7 전처리 중...');
      const sections = await this.preprocessor.process({ pdfData, ocrResults });

      console.log('4/7 상위 태스크 식별 중...');
      const tasks = await this.planner.identifyTasks(sections);

      console.log('5/7 하위 태스크 작성 중...');
      const markdowns = await Promise.all(
        tasks.map(task => this.taskWriter.writeTask(task, sections))
      );

      console.log('6/7 파일 분리 중...');
      const files = await this.splitter.split(
        tasks.map((task, i) => ({ task, markdown: markdowns[i] })),
        options.outputDir
      );

      console.log('7/7 리포트 생성 중...');
      const report = await this.reporter.generate({ files, tasks, ... });

      return { files, report };
    }
  }
  ```
- **테스트 포인트:**
  - 각 단계 정상 완료 확인
  - 단계 간 데이터 전달 검증

### 8.5 진행률 표시 및 로깅
- **목적:** 사용자에게 실시간 진행 상황 표시
- **작업 내용:**
  - 콘솔에 진행률 출력 (예: "Processing page 10/50...")
  - 상세 로그 옵션 (`--verbose`)
  - 진행률 바 표시 (선택 사항, `cli-progress` 패키지)
- **로깅 수준:**
  - `info`: 주요 단계 진행 상황
  - `debug`: 상세 디버깅 정보 (`--verbose` 시)
  - `error`: 에러 메시지
- **산출물:** 콘솔 출력
- **테스트 포인트:**
  - 로그 출력 순서 및 내용 확인

### 8.6 에러 핸들링 및 종료 코드
- **목적:** 에러 발생 시 적절한 메시지 및 종료 코드 반환
- **작업 내용:**
  - Try-catch로 전체 워크플로우 감싸기
  - 에러 종류별 종료 코드 정의
  - 사용자 친화적 에러 메시지 출력
- **종료 코드:**
  - `0`: 성공
  - `1`: 일반 에러
  - `2`: 파일 없음
  - `3`: 권한 오류
  - `4`: API 오류
- **로직 예시:**
  ```typescript
  try {
    await orchestrator.run(pdfPath, options);
    process.exit(0);
  } catch (error) {
    if (error instanceof FileNotFoundError) {
      console.error('Error: PDF 파일을 찾을 수 없습니다.');
      process.exit(2);
    } else if (error instanceof APIError) {
      console.error('Error: LLM API 호출 실패:', error.message);
      process.exit(4);
    } else {
      console.error('Error:', error.message);
      process.exit(1);
    }
  }
  ```
- **테스트 포인트:**
  - 다양한 에러 시나리오 테스트
  - 종료 코드 정확성 확인

### 8.7 Dry-run 모드 구현 (선택 사항)
- **목적:** 실제 파일 생성 없이 미리보기
- **작업 내용:**
  - `--dry-run` 옵션 처리
  - FileSplitter 단계에서 파일 쓰기 스킵
  - 생성될 파일 목록 및 내용 일부 출력
- **출력 예시:**
  ```
  [Dry Run Mode]
  생성될 파일:
  1. ./out/1_인증_및_회원관리.md
  2. ./out/2_결제_시스템.md
  ...

  파일은 실제로 생성되지 않았습니다.
  ```
- **테스트 포인트:**
  - Dry-run 모드에서 파일 생성 안 됨 확인

### 8.8 Shebang 및 실행 파일 설정
- **목적:** CLI 도구를 전역 명령어로 사용
- **작업 내용:**
  - CLI 진입점에 shebang 추가 (`#!/usr/bin/env node`)
  - `package.json`에 `bin` 필드 추가
  - 실행 권한 부여
- **package.json 예시:**
  ```json
  {
    "name": "pdf2tasks",
    "bin": {
      "pdf2tasks": "./dist/cli/index.js"
    }
  }
  ```
- **설치 후 사용:**
  ```bash
  npm install -g .
  pdf2tasks analyze ./spec.pdf --out ./out
  ```
- **테스트 포인트:**
  - 전역 설치 후 명령어 실행 확인

---

## 완료 조건
- [ ] Commander.js 설치 및 CLI 기본 구조 완성
- [ ] CLI 진입점 및 파라미터 검증 구현
- [ ] Orchestrator 클래스 설계 및 구현
- [ ] 단계별 워크플로우 통합 완료
- [ ] 진행률 표시 및 로깅 시스템 구축
- [ ] 에러 핸들링 및 종료 코드 정의
- [ ] Dry-run 모드 구현 (선택 사항)
- [ ] Shebang 및 실행 파일 설정 완료
- [ ] 전체 E2E 테스트 통과
