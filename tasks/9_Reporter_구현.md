# Reporter 구현 — 상위 태스크 9

## 상위 태스크 개요
- **설명:** 처리 결과, 통계, 비용, 에러를 종합한 리포트 생성
- **모듈/영역:** `src/reporter/`
- **관련 기술:** 파일 I/O, 데이터 집계
- **선행 조건:** CLI 및 Orchestrator 구현 완료 (상위 태스크 8)
- **참고:** AI_Agent_Project_Plan.md (Section 5 - Reporter)

---

## 하위 태스크 목록

### 9.1 리포트 데이터 구조 설계
- **목적:** 리포트에 포함될 정보 정의
- **작업 내용:**
  - 리포트 데이터 인터페이스 설계
  - 각 모듈에서 수집할 메트릭 정의
- **데이터 구조:**
  ```typescript
  interface Report {
    summary: {
      pdfFile: string;
      totalPages: number;
      generatedFiles: number;
      totalProcessingTime: number;  // 초
      timestamp: Date;
    };
    extraction: {
      textPages: number;
      imagesExtracted: number;
      tablesFound: number;
    };
    ocr: {
      imagesProcessed: number;
      averageConfidence: number;
      totalOCRTime: number;
    };
    preprocessing: {
      sectionsIdentified: number;
      functionalGroups: number;
    };
    llm: {
      plannerCalls: number;
      taskWriterCalls: number;
      totalTokensUsed: number;
      totalCost: number;  // USD
    };
    output: {
      files: Array<{ name: string; size: number; path: string }>;
    };
    errors: Array<{ stage: string; message: string; severity: string }>;
  }
  ```
- **산출물:** `src/reporter/types.ts`
- **테스트 포인트:**
  - 리포트 데이터 구조 검증

### 9.2 각 모듈별 메트릭 수집
- **목적:** 각 모듈에서 처리 통계 수집
- **작업 내용:**
  - 각 모듈에 메트릭 수집 로직 추가
  - 처리 시간 측정 (시작/종료 타임스탬프)
  - 성공/실패 카운트
- **수집 예시:**
  ```typescript
  class PDFExtractor {
    async extract(pdfPath: string): Promise<ExtractResult> {
      const startTime = Date.now();
      // ... 추출 로직
      const endTime = Date.now();

      return {
        data: extractedData,
        metrics: {
          processingTime: (endTime - startTime) / 1000,
          textPages: extractedData.pages.length,
          imagesExtracted: extractedData.images.length
        }
      };
    }
  }
  ```
- **테스트 포인트:**
  - 각 모듈에서 메트릭 정확히 수집

### 9.3 LLM 비용 계산 로직
- **목적:** LLM 토큰 사용량을 비용으로 환산
- **작업 내용:**
  - Claude API 가격표 기반 계산 (2025년 기준)
  - 입력/출력 토큰 구분하여 계산
- **가격표 (예시):**
  ```typescript
  const CLAUDE_PRICING = {
    'claude-3-5-sonnet-20241022': {
      inputTokenPer1M: 3.0,   // $3 per 1M input tokens
      outputTokenPer1M: 15.0  // $15 per 1M output tokens
    }
  };
  ```
- **계산 로직:**
  ```typescript
  function calculateCost(
    inputTokens: number,
    outputTokens: number,
    model: string
  ): number {
    const pricing = CLAUDE_PRICING[model];
    const inputCost = (inputTokens / 1_000_000) * pricing.inputTokenPer1M;
    const outputCost = (outputTokens / 1_000_000) * pricing.outputTokenPer1M;
    return inputCost + outputCost;
  }
  ```
- **테스트 포인트:**
  - 비용 계산 정확성 검증

### 9.4 리포트 생성 함수 구현
- **목적:** 수집된 메트릭을 종합하여 리포트 생성
- **작업 내용:**
  - 각 모듈의 메트릭 통합
  - 요약 정보 생성
  - 에러 목록 정리
- **입력:** 각 모듈의 메트릭
- **출력:** `Report` 객체
- **로직 요약:**
  ```typescript
  class Reporter {
    generate(data: {
      pdfMetrics: any;
      ocrMetrics: any;
      preprocessorMetrics: any;
      plannerMetrics: any;
      taskWriterMetrics: any;
      splitterMetrics: any;
      errors: Error[];
    }): Report {
      return {
        summary: {
          pdfFile: data.pdfMetrics.filePath,
          totalPages: data.pdfMetrics.totalPages,
          generatedFiles: data.splitterMetrics.filesCreated,
          totalProcessingTime: this.calculateTotalTime(data),
          timestamp: new Date()
        },
        // ... 나머지 필드
      };
    }
  }
  ```
- **테스트 포인트:**
  - 리포트 생성 성공 확인

### 9.5 텍스트 리포트 포맷 (콘솔 출력)
- **목적:** 사용자 친화적 리포트를 콘솔에 출력
- **작업 내용:**
  - 표 형식으로 정보 표시
  - 색상 코딩 (선택 사항, `chalk` 패키지)
  - 주요 메트릭 강조
- **출력 예시:**
  ```
  ===================================
  PDF2Tasks 처리 리포트
  ===================================

  입력 파일: ./specs/app-v1.pdf
  처리 페이지: 50 페이지
  생성 파일: 5개
  총 처리 시간: 4분 32초

  --- 추출 ---
  이미지 추출: 12개
  표 인식: 3개

  --- OCR ---
  처리 이미지: 12개
  평균 신뢰도: 87.3%

  --- LLM 사용 ---
  총 토큰: 245,320
  총 비용: $1.23

  --- 생성 파일 ---
  1. 1_인증_및_회원관리.md (12.5 KB)
  2. 2_결제_시스템.md (8.3 KB)
  ...

  에러: 없음

  ===================================
  ```
- **테스트 포인트:**
  - 콘솔 출력 확인

### 9.6 JSON 리포트 저장
- **목적:** 기계 판독 가능한 JSON 형식 리포트 저장
- **작업 내용:**
  - `Report` 객체를 JSON으로 직렬화
  - `report.json` 파일로 저장
- **저장 경로:** `{outputDir}/report.json`
- **로직:**
  ```typescript
  async function saveJSONReport(report: Report, outputDir: string): Promise<void> {
    const filePath = path.join(outputDir, 'report.json');
    await fs.writeFile(filePath, JSON.stringify(report, null, 2), 'utf-8');
  }
  ```
- **테스트 포인트:**
  - JSON 파일 생성 확인
  - 파싱 가능성 검증

### 9.7 텍스트 리포트 로그 파일 저장
- **목적:** 콘솔 출력과 동일한 내용을 `report.log`로 저장
- **작업 내용:**
  - 텍스트 리포트를 파일로 저장
  - 타임스탬프 포함
- **저장 경로:** `{outputDir}/report.log`
- **로직:**
  ```typescript
  async function saveTextReport(reportText: string, outputDir: string): Promise<void> {
    const filePath = path.join(outputDir, 'report.log');
    const header = `Generated at: ${new Date().toISOString()}\n\n`;
    await fs.writeFile(filePath, header + reportText, 'utf-8');
  }
  ```
- **테스트 포인트:**
  - 로그 파일 생성 확인

### 9.8 에러 리포팅
- **목적:** 처리 중 발생한 에러를 리포트에 포함
- **작업 내용:**
  - 각 단계에서 발생한 에러 수집
  - 심각도 분류 (warning, error, critical)
  - 에러 메시지 및 스택 트레이스 포함
- **에러 구조:**
  ```typescript
  interface ErrorEntry {
    stage: string;        // 예: "PDF Extraction", "OCR"
    message: string;
    severity: 'warning' | 'error' | 'critical';
    timestamp: Date;
    stackTrace?: string;
  }
  ```
- **리포트 출력:**
  ```
  --- 에러 (2) ---
  [ERROR] OCR: 이미지 page-10.png 처리 실패 - 신뢰도 낮음
  [WARNING] Preprocessor: 섹션 제목 누락 (p.23)
  ```
- **테스트 포인트:**
  - 에러 발생 시 리포트에 포함 확인

### 9.9 Reporter 통합 인터페이스
- **목적:** Reporter 기능을 하나의 인터페이스로 통합
- **작업 내용:**
  - `Reporter` 클래스 작성
  - 메트릭 수집 → 리포트 생성 → 출력/저장
- **사용 예시:**
  ```typescript
  const reporter = new Reporter();
  const report = reporter.generate(allMetrics);
  reporter.printToConsole(report);
  await reporter.saveJSON(report, './out');
  await reporter.saveTextLog(report, './out');
  ```
- **산출물:** `src/reporter/Reporter.ts`
- **테스트 포인트:**
  - E2E Reporter 플로우 테스트

---

## 완료 조건
- [ ] 리포트 데이터 구조 설계 완료
- [ ] 각 모듈별 메트릭 수집 로직 추가
- [ ] LLM 비용 계산 로직 구현
- [ ] 리포트 생성 함수 완성
- [ ] 텍스트 리포트 포맷 (콘솔 출력) 구현
- [ ] JSON 리포트 저장 기능 완성
- [ ] 텍스트 리포트 로그 파일 저장 구현
- [ ] 에러 리포팅 기능 추가
- [ ] Reporter 통합 인터페이스 완성
- [ ] 전체 워크플로우와 통합 테스트
