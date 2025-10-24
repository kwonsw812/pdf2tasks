# Preprocessor 구현 — 상위 태스크 4

## 상위 태스크 개요
- **설명:** PDF 및 OCR 결과를 정규화하고 섹션별로 구분하는 전처리 모듈 구현
- **모듈/영역:** `src/preprocessor/`
- **관련 기술:** 텍스트 정규화, 자연어 처리, 섹션 구분 알고리즘
- **선행 조건:** PDF Extractor, OCR Engine 구현 완료 (상위 태스크 2, 3)
- **참고:** AI_Agent_Project_Plan.md (Section 5 - Preprocessor)

---

## 하위 태스크 목록

### 4.1 텍스트 정규화 함수 구현
- **목적:** 추출된 텍스트의 일관성 확보 및 노이즈 제거
- **작업 내용:**
  - 불필요한 공백, 줄바꿈 제거
  - 특수문자 및 이스케이프 문자 정제
  - 유니코드 정규화 (NFC/NFD)
  - 영문 대소문자 일관성 처리 (선택 사항)
- **입력:** 원본 텍스트 (PDF 또는 OCR 결과)
- **출력:** 정규화된 텍스트
- **로직 요약:**
  ```typescript
  function normalizeText(text: string): string {
    // 1. 유니코드 정규화
    text = text.normalize('NFC');
    // 2. 연속 공백 → 단일 공백
    text = text.replace(/\s+/g, ' ');
    // 3. 줄바꿈 정리 (의미 있는 줄바꿈 유지)
    text = text.replace(/\n{3,}/g, '\n\n');
    // 4. 특수문자 정제
    return text.trim();
  }
  ```
- **테스트 포인트:**
  - 다양한 공백/줄바꿈 패턴 정규화 확인
  - 한글 자모 분리 현상 방지

### 4.2 헤더/푸터 제거 로직
- **목적:** PDF 페이지 상하단 반복 텍스트(페이지 번호, 회사명 등) 제거
- **작업 내용:**
  - 페이지별로 동일 위치의 반복 텍스트 패턴 감지
  - 헤더/푸터 영역 좌표 기반 필터링
  - 정규표현식을 사용한 패턴 매칭 (예: "Page 1 of 10")
- **입력:** 페이지별 텍스트 + 좌표 정보
- **출력:** 헤더/푸터가 제거된 텍스트
- **로직 요약:**
  ```typescript
  function removeHeadersFooters(pages: ExtractedText[][]): string[] {
    // 1. 각 페이지의 상단/하단 텍스트 추출
    // 2. 페이지 간 반복 패턴 식별
    // 3. 반복 패턴 텍스트 제거
    // 4. 정제된 텍스트 반환
  }
  ```
- **테스트 포인트:**
  - 헤더/푸터가 있는 PDF에서 제거 성공
  - 본문 내용은 유지되는지 확인

### 4.3 섹션 구분 알고리즘
- **목적:** 기획서를 의미 있는 섹션(챕터)으로 분리
- **작업 내용:**
  - 제목/헤딩 패턴 인식 (예: "## 1. 기능 요구사항", "2.1 회원가입")
  - 폰트 크기/스타일 기반 헤딩 감지
  - 페이지 구조 기반 섹션 경계 식별
- **입력:** 정규화된 전체 텍스트 + 메타데이터
- **출력:**
  ```typescript
  interface Section {
    title: string;
    level: number;       // 1, 2, 3 (헤딩 레벨)
    content: string;
    pageRange: [number, number];
    subsections?: Section[];
  }
  ```
- **로직 요약:**
  ```typescript
  function segmentIntoSections(text: string, metadata: any): Section[] {
    // 1. 헤딩 패턴 정규식 매칭 (예: /^#+\s/, /^\d+\.\s/)
    // 2. 폰트 크기 기반 헤딩 감지
    // 3. 섹션 경계 결정
    // 4. 계층 구조 생성
  }
  ```
- **헤딩 패턴 예시:**
  - `# 1. 개요` → Level 1
  - `## 1.1 목표` → Level 2
  - `### 1.1.1 상세` → Level 3
- **테스트 포인트:**
  - 다양한 헤딩 스타일 인식 확인
  - 중첩 섹션 구조 정확히 생성

### 4.4 기능별 요구사항 그룹화
- **목적:** 섹션을 기능 영역별로 재그룹화 (예: 인증, 결제, 알림)
- **작업 내용:**
  - 키워드 기반 기능 분류 (로그인, 회원가입 → 인증)
  - 섹션 제목 분석
  - 사용자 정의 매핑 룰 적용 (선택 사항)
- **입력:** 섹션 목록
- **출력:**
  ```typescript
  interface FunctionalGroup {
    name: string;        // 예: "인증", "결제"
    sections: Section[];
  }
  ```
- **로직 요약:**
  ```typescript
  function groupByFunctionality(sections: Section[]): FunctionalGroup[] {
    const groups: Map<string, Section[]> = new Map();
    for (const section of sections) {
      const category = classifySection(section.title);
      if (!groups.has(category)) groups.set(category, []);
      groups.get(category)!.push(section);
    }
    return Array.from(groups, ([name, sections]) => ({ name, sections }));
  }

  function classifySection(title: string): string {
    if (/로그인|회원가입|인증/.test(title)) return '인증';
    if (/결제|구매|정산/.test(title)) return '결제';
    // ... 추가 분류 규칙
    return '기타';
  }
  ```
- **테스트 포인트:**
  - 일반적인 기능 키워드로 정확히 분류
  - 애매한 섹션은 "기타"로 분류

### 4.5 페이지 번호 및 원본 참조 매핑
- **목적:** 각 섹션/텍스트가 원본 PDF 어디에서 나왔는지 추적
- **작업 내용:**
  - 섹션별로 원본 PDF 페이지 범위 기록
  - 나중에 Markdown에 "참고: PDF p.10-15" 형태로 삽입 가능
- **출력:**
  ```typescript
  interface SectionWithReference extends Section {
    sourcePages: number[];  // 원본 PDF 페이지 번호들
  }
  ```
- **테스트 포인트:**
  - 섹션의 페이지 범위 정확히 추적
  - Markdown 출력 시 참조 정보 포함 확인

### 4.6 Preprocessor 통합 인터페이스
- **목적:** 전처리 파이프라인을 하나의 인터페이스로 통합
- **작업 내용:**
  - `Preprocessor` 클래스 작성
  - PDF/OCR 결과 → 정규화 → 헤더/푸터 제거 → 섹션 구분 → 그룹화
- **사용 예시:**
  ```typescript
  const preprocessor = new Preprocessor();
  const groups = await preprocessor.process({
    pdfResult: extractedPDF,
    ocrResults: ocrTexts
  });
  ```
- **산출물:** `src/preprocessor/Preprocessor.ts`
- **테스트 포인트:**
  - E2E 전처리 플로우 테스트
  - 실제 PDF 기획서 파일로 검증

### 4.7 전처리 결과 검증 및 로깅
- **목적:** 전처리 품질 확인 및 디버깅 지원
- **로깅 정보:**
  - 제거된 헤더/푸터 패턴
  - 식별된 섹션 수
  - 기능 그룹 개수 및 이름
  - 각 단계별 처리 시간
- **검증 규칙:**
  - 섹션 제목이 비어있지 않은지
  - 섹션 내용이 과도하게 길지 않은지 (페이지 수 기준)
- **테스트 포인트:**
  - 로그 출력 확인
  - 비정상 케이스 감지 테스트

---

## 완료 조건
- [ ] 텍스트 정규화 함수 구현 및 테스트
- [ ] 헤더/푸터 제거 로직 동작 확인
- [ ] 섹션 구분 알고리즘 구현 및 계층 구조 생성
- [ ] 기능별 요구사항 그룹화 로직 완성
- [ ] 페이지 번호 참조 매핑 구현
- [ ] Preprocessor 통합 인터페이스 완성
- [ ] 전처리 결과 검증 및 로깅 시스템 구축
- [ ] 실제 PDF 기획서로 E2E 테스트 통과
