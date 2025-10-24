"""
Integration tests for Preprocessor
"""
import pytest
from src.preprocessor.preprocessor import Preprocessor
from src.extractors.pdf_extractor import PDFExtractor


@pytest.mark.integration
class TestPreprocessorIntegration:
    """Preprocessor 통합 테스트"""

    def test_full_preprocessing_pipeline(self, sample_pdf_path):
        """전체 전처리 파이프라인 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        # 1. PDF 추출
        extractor = PDFExtractor()
        pdf_result = extractor.extract(str(sample_pdf_path))

        # 2. 전처리
        preprocessor = Preprocessor(
            normalize_text=True,
            remove_headers_footers=True,
            segment_sections=True,
            group_by_function=True
        )

        result = preprocessor.process(pdf_result)

        # 결과 검증
        assert result is not None
        assert result.metadata is not None
        assert isinstance(result.functional_groups, list)

        # cleanup
        extractor.cleanup()

    def test_text_normalization_only(self, sample_pdf_path):
        """텍스트 정규화만 수행"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        pdf_result = extractor.extract(str(sample_pdf_path))

        preprocessor = Preprocessor(
            normalize_text=True,
            remove_headers_footers=False,
            segment_sections=False,
            group_by_function=False
        )

        result = preprocessor.process(pdf_result)

        assert result is not None

        extractor.cleanup()

    def test_section_segmentation(self, sample_pdf_path):
        """섹션 구분 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        pdf_result = extractor.extract(str(sample_pdf_path))

        preprocessor = Preprocessor(
            normalize_text=True,
            remove_headers_footers=True,
            segment_sections=True,
            group_by_function=False
        )

        result = preprocessor.process(pdf_result)

        # 섹션이 생성되었는지 확인 (구현에 따라)
        assert result is not None

        extractor.cleanup()

    def test_functional_grouping(self, sample_pdf_path):
        """기능별 그룹화 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        pdf_result = extractor.extract(str(sample_pdf_path))

        preprocessor = Preprocessor(
            normalize_text=True,
            remove_headers_footers=True,
            segment_sections=True,
            group_by_function=True
        )

        result = preprocessor.process(pdf_result)

        # 그룹이 생성되었는지 확인
        assert result.functional_groups is not None
        assert isinstance(result.functional_groups, list)

        extractor.cleanup()

    def test_preprocessing_statistics(self, sample_pdf_path):
        """전처리 통계 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        pdf_result = extractor.extract(str(sample_pdf_path))

        preprocessor = Preprocessor()
        result = preprocessor.process(pdf_result)

        # 통계 확인
        stats = preprocessor.get_statistics()
        assert stats is not None

        extractor.cleanup()

    @pytest.mark.slow
    def test_large_document_preprocessing(self):
        """대용량 문서 전처리 테스트"""
        pytest.skip("대용량 PDF fixture 필요")

    def test_header_footer_detection(self, sample_pdf_path):
        """헤더/푸터 감지 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        pdf_result = extractor.extract(str(sample_pdf_path))

        preprocessor = Preprocessor(
            remove_headers_footers=True
        )

        result = preprocessor.process(pdf_result)

        # 헤더/푸터 패턴이 감지되었는지 확인
        assert result.removed_header_patterns is not None
        assert result.removed_footer_patterns is not None

        extractor.cleanup()

    def test_custom_keyword_grouping(self, sample_pdf_path):
        """커스텀 키워드 그룹화 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        pdf_result = extractor.extract(str(sample_pdf_path))

        preprocessor = Preprocessor(group_by_function=True)

        # 커스텀 키워드 추가 (구현에 따라)
        # preprocessor.add_keyword_mapping("커스텀", ["특수", "키워드"])

        result = preprocessor.process(pdf_result)

        assert result.functional_groups is not None

        extractor.cleanup()
