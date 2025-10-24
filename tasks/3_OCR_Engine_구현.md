# OCR Engine 구현 — 상위 태스크 3

## 상위 태스크 개요
- **설명:** PDF 이미지 내 텍스트를 인식하는 OCR(Optical Character Recognition) 엔진 구현
- **모듈/영역:** `src/ocr/`
- **관련 라이브러리:** `tesseract.js`, `node-tesseract-ocr`
- **선행 조건:** PDF Extractor 구현 완료 (상위 태스크 2)
- **참고:** AI_Agent_Project_Plan.md (Section 5 - OCR Engine)

---

## 하위 태스크 목록

### 3.1 Tesseract.js 설정 및 초기화
- **목적:** OCR 라이브러리 설치 및 기본 설정
- **작업 내용:**
  - `tesseract.js` 패키지 설치
  - 한국어/영어 언어 데이터 다운로드
  - Tesseract Worker 초기화 함수 작성
- **설정 옵션:**
  ```typescript
  {
    lang: 'kor+eng',  // 한국어 + 영어
    oem: 1,           // LSTM OCR Engine Mode
    psm: 3            // Fully automatic page segmentation
  }
  ```
- **산출물:** `src/ocr/tesseract.config.ts`
- **테스트 포인트:**
  - Tesseract Worker 초기화 성공
  - 언어 데이터 로드 확인

### 3.2 이미지 전처리 기능 구현
- **목적:** OCR 정확도 향상을 위한 이미지 품질 개선
- **작업 내용:**
  - 이미지 그레이스케일 변환
  - 대비(Contrast) 조정
  - 노이즈 제거
  - 이미지 크기 조정 (해상도 최적화)
- **사용 라이브러리:** `sharp` 또는 `jimp`
- **입력:** 이미지 파일 경로
- **출력:** 전처리된 이미지 경로
- **로직 요약:**
  ```typescript
  async function preprocessImage(imagePath: string): Promise<string> {
    // 1. 이미지 로드
    // 2. 그레이스케일 변환
    // 3. 대비 증가
    // 4. 임시 파일로 저장
    // 5. 전처리된 이미지 경로 반환
  }
  ```
- **테스트 포인트:**
  - 저품질 이미지 전처리 후 OCR 정확도 향상 확인

### 3.3 OCR 텍스트 인식 함수 구현
- **목적:** 이미지에서 텍스트 추출
- **작업 내용:**
  - Tesseract.js를 사용하여 이미지 인식
  - 인식된 텍스트 및 신뢰도(confidence) 반환
  - 박스 좌표 정보 포함 (선택 사항)
- **입력:** 이미지 파일 경로
- **출력:**
  ```typescript
  interface OCRResult {
    text: string;
    confidence: number;  // 0-100
    words?: Array<{
      text: string;
      confidence: number;
      bbox: { x0: number; y0: number; x1: number; y1: number };
    }>;
  }
  ```
- **로직 요약:**
  ```typescript
  async function recognizeText(imagePath: string): Promise<OCRResult> {
    const worker = await createWorker();
    await worker.loadLanguage('kor+eng');
    await worker.initialize('kor+eng');
    const { data } = await worker.recognize(imagePath);
    await worker.terminate();
    return {
      text: data.text,
      confidence: data.confidence,
      words: data.words
    };
  }
  ```
- **예외 처리:**
  - 이미지 로드 실패: `ImageLoadError`
  - OCR 처리 타임아웃: `OCRTimeoutError`
- **테스트 포인트:**
  - 한글/영문 혼합 텍스트 정확히 인식
  - 신뢰도 70% 이상 확보

### 3.4 배치 OCR 처리
- **목적:** 여러 이미지를 효율적으로 일괄 처리
- **작업 내용:**
  - 이미지 배열을 받아 순차/병렬 OCR 수행
  - Worker Pool 관리 (동시 처리 수 제한)
  - 진행률 표시
- **입력:** 이미지 경로 배열
- **출력:** OCR 결과 배열
- **로직 요약:**
  ```typescript
  async function batchOCR(
    imagePaths: string[],
    options?: { maxConcurrency: number }
  ): Promise<OCRResult[]> {
    // Worker Pool 생성
    // 병렬 처리 (예: p-limit 사용)
    // 각 이미지 OCR 수행
    // 결과 수집 및 반환
  }
  ```
- **성능 고려:**
  - 동시 처리 워커 수: 2-4개 (CPU 코어 수 고려)
  - 메모리 사용량 모니터링
- **테스트 포인트:**
  - 10개 이미지 일괄 처리 성공
  - 메모리 누수 없음 확인

### 3.5 OCR 결과 후처리
- **목적:** 인식 오류 보정 및 텍스트 정제
- **작업 내용:**
  - 공백 문자 정규화
  - 특수문자 오인식 패턴 교정 (예: `0` vs `O`, `1` vs `l`)
  - 신뢰도 낮은 단어 필터링 또는 표시
- **입력:** OCR 원본 결과
- **출력:** 정제된 텍스트
- **로직 요약:**
  ```typescript
  function postprocessOCR(result: OCRResult): string {
    let text = result.text;
    // 1. 불필요한 공백 제거
    text = text.replace(/\s+/g, ' ').trim();
    // 2. 일반적인 오인식 패턴 교정
    // 3. 신뢰도 기반 필터링
    return text;
  }
  ```
- **테스트 포인트:**
  - 후처리 전후 텍스트 품질 비교

### 3.6 OCR Engine 통합 인터페이스
- **목적:** OCR 기능을 통합하여 외부 모듈에서 쉽게 사용
- **작업 내용:**
  - `OCREngine` 클래스 작성
  - 전처리 → OCR → 후처리 파이프라인 구성
- **사용 예시:**
  ```typescript
  const ocrEngine = new OCREngine();
  const results = await ocrEngine.processImages([
    './image1.png',
    './image2.png'
  ]);
  ```
- **산출물:** `src/ocr/OCREngine.ts`
- **테스트 포인트:**
  - E2E OCR 처리 플로우 테스트
  - PDF Extractor와 통합 테스트

### 3.7 OCR 성능 모니터링 및 로깅
- **목적:** OCR 처리 시간 및 품질 추적
- **로깅 정보:**
  - 처리한 이미지 수
  - 평균 OCR 시간 (이미지당)
  - 평균 신뢰도
  - 에러 발생 이미지 목록
- **산출물:** `report.log` 또는 콘솔 출력
- **테스트 포인트:**
  - 로그에 필요한 정보 모두 포함 확인

---

## 완료 조건
- [ ] Tesseract.js 초기화 및 언어 데이터 설정 완료
- [ ] 이미지 전처리 기능 구현 및 테스트
- [ ] OCR 텍스트 인식 기능 동작 확인
- [ ] 배치 OCR 처리 및 Worker Pool 관리 구현
- [ ] OCR 결과 후처리 로직 구현
- [ ] OCR Engine 통합 인터페이스 완성
- [ ] 성능 모니터링 및 로깅 시스템 구축
- [ ] 한글/영문 혼합 이미지 테스트 통과
