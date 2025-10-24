"""
Unit tests for FilenameGenerator
"""
import pytest
from src.splitter.filename_generator import FilenameGenerator


@pytest.mark.unit
class TestFilenameGenerator:
    """파일명 생성기 테스트"""

    def test_basic_generation(self):
        """기본 파일명 생성 테스트"""
        generator = FilenameGenerator()
        filename = generator.generate(1, "인증 및 회원관리")

        assert filename == "1_인증_및_회원관리.md"
        assert filename.endswith(".md")
        assert filename.startswith("1_")

    def test_special_characters_removed(self):
        """특수문자 제거 테스트"""
        generator = FilenameGenerator()

        # 슬래시 제거
        filename = generator.generate(2, "결제/주문 시스템")
        assert "/" not in filename
        assert "\\" not in filename

        # 기타 특수문자 제거
        filename = generator.generate(3, "API?설계*문서<>")
        assert "?" not in filename
        assert "*" not in filename
        assert "<" not in filename
        assert ">" not in filename

    def test_spaces_to_underscores(self):
        """공백을 언더스코어로 변환 테스트"""
        generator = FilenameGenerator()
        filename = generator.generate(1, "사용자 관리 시스템")

        assert "_사용자_관리_시스템" in filename
        assert "  " not in filename  # 연속 공백 없음

    def test_long_filename_truncation(self):
        """긴 파일명 잘림 테스트"""
        generator = FilenameGenerator(max_length=20)
        long_name = "매우매우매우매우매우매우긴제목입니다"
        filename = generator.generate(1, long_name)

        # 파일명 길이 제한 (확장자 포함)
        assert len(filename) <= 20 + len(".md")

    def test_duplicate_prevention(self):
        """중복 파일명 방지 테스트"""
        generator = FilenameGenerator()

        # 동일 이름으로 두 번 생성
        filename1 = generator.generate(1, "인증")
        filename2 = generator.generate(1, "인증")

        assert filename1 != filename2
        assert "1_인증.md" == filename1
        assert "1_인증_2.md" == filename2 or "1_인증_1.md" == filename2

    def test_reset_functionality(self):
        """리셋 기능 테스트"""
        generator = FilenameGenerator()

        filename1 = generator.generate(1, "인증")
        generator.reset()
        filename2 = generator.generate(1, "인증")

        # 리셋 후 동일한 이름 가능
        assert filename1 == filename2

    def test_korean_characters_preserved(self):
        """한글 문자 유지 테스트"""
        generator = FilenameGenerator()
        filename = generator.generate(1, "사용자인증")

        assert "사용자인증" in filename

    def test_numbers_preserved(self):
        """숫자 유지 테스트"""
        generator = FilenameGenerator()
        filename = generator.generate(123, "API v2.0")

        assert "123_" in filename
        assert "v2" in filename or "v20" in filename

    def test_empty_name_handling(self):
        """빈 이름 처리 테스트"""
        generator = FilenameGenerator()
        filename = generator.generate(1, "")

        assert filename.startswith("1_")
        assert filename.endswith(".md")

    def test_whitespace_only_name(self):
        """공백만 있는 이름 테스트"""
        generator = FilenameGenerator()
        filename = generator.generate(1, "   ")

        assert filename.startswith("1_")
        assert filename.endswith(".md")

    def test_mixed_content(self):
        """혼합 콘텐츠 테스트"""
        generator = FilenameGenerator()
        filename = generator.generate(1, "API v2.0 - 사용자/인증 (NEW)")

        assert "API" in filename
        assert "v2" in filename or "v20" in filename
        assert "사용자" in filename
        assert "인증" in filename
        # 특수문자는 제거됨
        assert "/" not in filename
        assert "(" not in filename
        assert ")" not in filename

    def test_custom_max_length(self):
        """커스텀 최대 길이 테스트"""
        generator = FilenameGenerator(max_length=30)
        long_name = "아주아주아주아주아주긴제목입니다정말정말긴제목"
        filename = generator.generate(1, long_name)

        assert len(filename) <= 30 + len(".md")

    def test_sequential_generation(self):
        """순차적 생성 테스트"""
        generator = FilenameGenerator()

        filenames = [
            generator.generate(1, "인증"),
            generator.generate(2, "결제"),
            generator.generate(3, "알림")
        ]

        assert len(filenames) == 3
        assert all(fn.endswith(".md") for fn in filenames)
        assert filenames[0].startswith("1_")
        assert filenames[1].startswith("2_")
        assert filenames[2].startswith("3_")
