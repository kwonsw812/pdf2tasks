# PDF Extractor 구현 — 상위 태스크 2

## 상위 태스크 개요
- **설명:** PDF 파일에서 텍스트, 이미지, 메타데이터를 추출하는 모듈 구현
- **모듈/영역:** `src/extractors/`
- **관련 라이브러리:** `pdf-parse`, `pdfjs-dist`
- **선행 조건:** 프로젝트 초기 설정 완료 (상위 태스크 1)
- **참고:** AI_Agent_Project_Plan.md (Section 5 - PDF Extractor)

---

## 하위 태스크 목록

### 2.1 PDF 텍스트 추출 기능 구현
- **목적:** PDF의 모든 페이지에서 텍스트 추출
- **작업 내용:**
  - `pdf-parse` 또는 `pdfjs-dist`를 사용하여 PDF 파싱
  - 페이지별 텍스트 추출 및 구조화
  - 헤딩, 문단, 리스트 등 구조 정보 보존
- **입력:** PDF 파일 경로
- **출력:**
  ```typescript
  interface ExtractedText {
    pageNumber: number;
    text: string;
    metadata?: {
      fontSize?: number;
      fontName?: string;
      position?: { x: number; y: number };
    };
  }
  ```
- **로직 요약:**
  1. PDF 파일 로드
  2. 페이지별 순회하며 텍스트 추출
  3. 좌표 및 폰트 정보 함께 수집
- **예외 처리:**
  - 파일 없음: `FileNotFoundError`
  - 손상된 PDF: `PDFParseError`
  - 암호화된 PDF: `EncryptedPDFError`
- **테스트 포인트:**
  - 정상 PDF 파일에서 텍스트 정확히 추출
  - 다국어(한글/영문) 텍스트 추출 확인
  - 빈 페이지 처리 확인

### 2.2 PDF 이미지 추출 기능 구현
- **목적:** PDF 내 포함된 이미지(스크린샷, 다이어그램 등) 추출
- **작업 내용:**
  - `pdfjs-dist`의 Canvas API를 사용하여 페이지를 이미지로 렌더링
  - 또는 PDF 내 임베디드 이미지 직접 추출
  - 이미지를 임시 디렉토리에 저장 (PNG/JPEG)
- **입력:** PDF 파일 경로, 페이지 번호
- **출력:**
  ```typescript
  interface ExtractedImage {
    pageNumber: number;
    imagePath: string;  // 저장된 이미지 파일 경로
    width: number;
    height: number;
  }
  ```
- **로직 요약:**
  1. 페이지를 Canvas로 렌더링
  2. Canvas를 이미지 파일로 저장
  3. 이미지 경로 및 메타데이터 반환
- **예외 처리:**
  - 이미지 추출 실패: `ImageExtractionError`
  - 디스크 공간 부족: `DiskSpaceError`
- **테스트 포인트:**
  - 이미지가 포함된 PDF에서 이미지 추출 성공
  - 이미지 품질 및 해상도 확인
  - 여러 이미지가 있는 페이지 처리

### 2.3 PDF 메타데이터 추출
- **목적:** PDF 문서의 메타정보 수집 (제목, 작성자, 페이지 수 등)
- **작업 내용:**
  - PDF 메타데이터 파싱
  - 문서 구조 정보 수집 (목차, 북마크)
- **출력:**
  ```typescript
  interface PDFMetadata {
    title?: string;
    author?: string;
    subject?: string;
    creator?: string;
    producer?: string;
    creationDate?: Date;
    modificationDate?: Date;
    totalPages: number;
  }
  ```
- **테스트 포인트:**
  - 메타데이터가 있는 PDF 처리 확인
  - 메타데이터 없는 PDF에서도 기본 정보(페이지 수) 추출

### 2.4 표(Table) 구조 인식
- **목적:** PDF 내 표 형태의 데이터 식별 및 추출
- **작업 내용:**
  - 좌표 기반 텍스트 위치 분석
  - 표 경계선 감지 (선택 사항)
  - 행/열 구조로 데이터 변환
- **출력:**
  ```typescript
  interface ExtractedTable {
    pageNumber: number;
    rows: string[][];  // 2차원 배열
    position: { x: number; y: number; width: number; height: number };
  }
  ```
- **로직 요약:**
  1. 텍스트 좌표 분석으로 격자 패턴 감지
  2. 행/열 기준으로 텍스트 그룹화
  3. 표 데이터 구조화
- **예외 처리:**
  - 복잡한 중첩 표: 경고 로그 출력 및 최선의 노력 추출
- **테스트 포인트:**
  - 단순 표 구조 정확히 파싱
  - 병합된 셀이 있는 표 처리

### 2.5 PDF Extractor 통합 인터페이스
- **목적:** 텍스트, 이미지, 메타데이터, 표를 하나의 인터페이스로 통합
- **작업 내용:**
  - `PDFExtractor` 클래스 또는 함수 작성
  - 모든 추출 기능을 통합하여 호출
- **입력:** PDF 파일 경로
- **출력:**
  ```typescript
  interface PDFExtractResult {
    metadata: PDFMetadata;
    pages: Array<{
      pageNumber: number;
      text: ExtractedText[];
      images: ExtractedImage[];
      tables: ExtractedTable[];
    }>;
  }
  ```
- **사용 예시:**
  ```typescript
  const extractor = new PDFExtractor();
  const result = await extractor.extract('./input.pdf');
  ```
- **테스트 포인트:**
  - 전체 추출 프로세스 E2E 테스트
  - 50페이지 PDF 처리 시간 5분 이내 확인

### 2.6 에러 핸들링 및 로깅
- **목적:** 안정적인 PDF 처리 보장
- **작업 내용:**
  - 커스텀 에러 클래스 정의 (`PDFExtractorError`)
  - 페이지별 처리 실패 시 계속 진행 (일부 실패 허용)
  - 진행률 로깅 (예: "Processing page 10/50...")
- **로깅 정보:**
  - 현재 처리 중인 페이지
  - 추출된 텍스트/이미지 개수
  - 에러 발생 시 상세 정보
- **테스트 포인트:**
  - 손상된 페이지가 포함된 PDF에서도 나머지 페이지 처리 성공
  - 로그 출력 확인

---

## 완료 조건
- [ ] PDF 텍스트 추출 기능 동작 확인
- [ ] PDF 이미지 추출 및 파일 저장 성공
- [ ] PDF 메타데이터 파싱 구현
- [ ] 표 구조 인식 기본 기능 구현
- [ ] 통합 인터페이스 (`PDFExtractor`) 완성
- [ ] 에러 핸들링 및 로깅 시스템 구축
- [ ] 단위 테스트 및 통합 테스트 통과
