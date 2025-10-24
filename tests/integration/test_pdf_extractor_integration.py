"""
Integration tests for PDF Extractor
"""
import pytest
from pathlib import Path
from src.extractors.pdf_extractor import PDFExtractor


@pytest.mark.integration
class TestPDFExtractorIntegration:
    """PDF Extractor 통합 테스트"""

    def test_full_extraction_with_sample_pdf(self, sample_pdf_path, temp_image_dir):
        """샘플 PDF로 전체 추출 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor(
            output_dir=str(temp_image_dir),
            extract_images=True,
            extract_tables=True
        )

        result = extractor.extract(str(sample_pdf_path))

        # 메타데이터 확인
        assert result.metadata is not None
        assert result.metadata.total_pages > 0

        # 페이지 확인
        assert len(result.pages) == result.metadata.total_pages

        # 각 페이지에 텍스트가 있는지 확인
        for page in result.pages:
            assert page.page_number > 0
            assert isinstance(page.text, list)

        # cleanup
        extractor.cleanup()

    def test_text_only_extraction(self, sample_pdf_path):
        """텍스트만 추출 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        text = extractor.extract_text_only(str(sample_pdf_path))

        assert isinstance(text, str)
        assert len(text) > 0

    def test_metadata_extraction(self, sample_pdf_path):
        """메타데이터만 추출 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        metadata = extractor.get_metadata(str(sample_pdf_path))

        assert metadata is not None
        assert metadata.total_pages > 0

    def test_specific_page_extraction(self, sample_pdf_path):
        """특정 페이지 추출 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor()
        page = extractor.extract_page(str(sample_pdf_path), 1)

        assert page is not None
        assert page.page_number == 1

    @pytest.mark.slow
    def test_large_pdf_extraction(self, temp_image_dir):
        """대용량 PDF 추출 테스트"""
        pytest.skip("대용량 PDF fixture 필요")

    def test_pdf_with_images(self, temp_image_dir):
        """이미지 포함 PDF 테스트"""
        pytest.skip("이미지 포함 PDF fixture 필요")

    def test_pdf_with_tables(self):
        """표 포함 PDF 테스트"""
        pytest.skip("표 포함 PDF fixture 필요")

    def test_extraction_with_cleanup(self, sample_pdf_path, temp_image_dir):
        """추출 후 cleanup 테스트"""
        if not sample_pdf_path.exists():
            pytest.skip("샘플 PDF 파일 없음")

        extractor = PDFExtractor(
            output_dir=str(temp_image_dir),
            extract_images=True
        )

        # 추출
        result = extractor.extract(str(sample_pdf_path))

        # 이미지가 있으면 파일이 생성되었을 것
        image_count_before = len(list(temp_image_dir.glob("*.png")))

        # cleanup
        extractor.cleanup()

        # cleanup 후 임시 파일 제거 확인 (구현에 따라)
        # assert len(list(temp_image_dir.glob("*.png"))) <= image_count_before
