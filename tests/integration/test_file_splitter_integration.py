"""
Integration tests for FileSplitter
"""
import pytest
from pathlib import Path
from datetime import datetime
from src.splitter.file_splitter import FileSplitter
from src.types.models import TaskWithMarkdown, IdentifiedTask, FileMetadata


@pytest.mark.integration
class TestFileSplitterIntegration:
    """FileSplitter 통합 테스트"""

    def test_basic_file_splitting(self, temp_output_dir):
        """기본 파일 분리 테스트"""
        splitter = FileSplitter(output_dir=str(temp_output_dir))

        # 테스트 태스크 생성
        tasks = [
            TaskWithMarkdown(
                task=IdentifiedTask(
                    index=i,
                    name=f"태스크{i}",
                    description=f"테스트 태스크 {i}",
                    module=f"Module{i}",
                    entities=[],
                    prerequisites=[],
                    related_sections=[]
                ),
                markdown=f"# 태스크 {i}\n\n테스트 내용",
                metadata=FileMetadata(
                    title=f"태스크{i}",
                    index=i,
                    generated=datetime.now()
                )
            )
            for i in range(1, 4)
        ]

        result = splitter.split(tasks)

        # 결과 검증
        assert result.success_count == 3
        assert result.failure_count == 0
        assert len(result.saved_files) == 3

        # 파일 생성 확인
        output_path = Path(temp_output_dir)
        md_files = list(output_path.glob("*.md"))
        assert len(md_files) == 3

    def test_file_splitting_with_front_matter(self, temp_output_dir):
        """Front Matter 포함 파일 분리"""
        splitter = FileSplitter(
            output_dir=str(temp_output_dir),
            add_front_matter=True
        )

        task = TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="인증",
                description="사용자 인증",
                module="AuthModule",
                entities=["User"],
                prerequisites=[],
                related_sections=[]
            ),
            markdown="# 인증\n\n내용",
            metadata=FileMetadata(
                title="인증",
                index=1,
                generated=datetime.now(),
                source_pdf="test.pdf"
            )
        )

        result = splitter.split([task])

        assert result.success_count == 1

        # 파일 내용 확인
        md_file = list(Path(temp_output_dir).glob("*.md"))[0]
        content = md_file.read_text(encoding="utf-8")

        # Front Matter 확인
        assert "---" in content
        assert "title:" in content
        assert "index:" in content

    def test_file_splitting_without_front_matter(self, temp_output_dir):
        """Front Matter 없이 파일 분리"""
        splitter = FileSplitter(
            output_dir=str(temp_output_dir),
            add_front_matter=False
        )

        task = TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="인증",
                description="사용자 인증",
                module="AuthModule",
                entities=[],
                prerequisites=[],
                related_sections=[]
            ),
            markdown="# 인증\n\n내용",
            metadata=None
        )

        result = splitter.split([task])

        assert result.success_count == 1

        # 파일 내용 확인
        md_file = list(Path(temp_output_dir).glob("*.md"))[0]
        content = md_file.read_text(encoding="utf-8")

        # Front Matter 없음
        assert content.strip().startswith("# 인증")

    def test_clean_directory_option(self, temp_output_dir):
        """디렉토리 정리 옵션 테스트"""
        output_path = Path(temp_output_dir)

        # 기존 파일 생성
        (output_path / "existing.md").write_text("기존 파일")

        splitter = FileSplitter(
            output_dir=str(temp_output_dir),
            clean=True
        )

        task = TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="새로운",
                description="새로운 태스크",
                module="NewModule",
                entities=[],
                prerequisites=[],
                related_sections=[]
            ),
            markdown="# 새로운",
            metadata=None
        )

        result = splitter.split([task])

        # 기존 파일 삭제 확인
        assert not (output_path / "existing.md").exists()

        # 새 파일만 존재
        md_files = list(output_path.glob("*.md"))
        assert len(md_files) == 1

    def test_report_generation(self, temp_output_dir):
        """리포트 생성 테스트"""
        splitter = FileSplitter(output_dir=str(temp_output_dir))

        tasks = [
            TaskWithMarkdown(
                task=IdentifiedTask(
                    index=i,
                    name=f"태스크{i}",
                    description="테스트",
                    module="TestModule",
                    entities=[],
                    prerequisites=[],
                    related_sections=[]
                ),
                markdown=f"# 태스크 {i}",
                metadata=None
            )
            for i in range(1, 4)
        ]

        result = splitter.split(tasks)

        # 리포트 생성
        report = splitter.generate_report(result)

        assert isinstance(report, str)
        assert "3개" in report or "3" in report
        assert "성공" in report or "생성" in report

        # 리포트 파일 저장
        report_path = splitter.save_report(result)

        assert Path(report_path).exists()

    def test_partial_failure_handling(self, temp_output_dir):
        """부분 실패 처리 테스트"""
        splitter = FileSplitter(output_dir=str(temp_output_dir))

        # 정상 태스크와 문제가 있을 수 있는 태스크 혼합
        tasks = []

        for i in range(1, 6):
            try:
                task = TaskWithMarkdown(
                    task=IdentifiedTask(
                        index=i,
                        name=f"태스크{i}",
                        description="테스트",
                        module="TestModule",
                        entities=[],
                        prerequisites=[],
                        related_sections=[]
                    ),
                    markdown=f"# 태스크 {i}",
                    metadata=None
                )
                tasks.append(task)
            except Exception:
                pass

        if tasks:
            result = splitter.split(tasks)

            # 최소한 일부는 성공해야 함
            assert result.success_count > 0

    def test_special_characters_in_filename(self, temp_output_dir):
        """파일명 특수문자 처리 테스트"""
        splitter = FileSplitter(output_dir=str(temp_output_dir))

        task = TaskWithMarkdown(
            task=IdentifiedTask(
                index=1,
                name="API/설계?문서*<테스트>",
                description="특수문자 포함",
                module="TestModule",
                entities=[],
                prerequisites=[],
                related_sections=[]
            ),
            markdown="# 테스트",
            metadata=None
        )

        result = splitter.split([task])

        # 성공 확인
        assert result.success_count == 1

        # 파일명에 특수문자 없음
        md_files = list(Path(temp_output_dir).glob("*.md"))
        filename = md_files[0].name

        assert "/" not in filename
        assert "?" not in filename
        assert "*" not in filename
        assert "<" not in filename
        assert ">" not in filename

    @pytest.mark.slow
    def test_large_batch_splitting(self, temp_output_dir):
        """대량 태스크 분리 테스트"""
        splitter = FileSplitter(output_dir=str(temp_output_dir))

        # 100개 태스크 생성
        tasks = [
            TaskWithMarkdown(
                task=IdentifiedTask(
                    index=i,
                    name=f"태스크{i}",
                    description="테스트",
                    module="TestModule",
                    entities=[],
                    prerequisites=[],
                    related_sections=[]
                ),
                markdown=f"# 태스크 {i}",
                metadata=None
            )
            for i in range(1, 101)
        ]

        result = splitter.split(tasks)

        assert result.success_count == 100
        assert result.failure_count == 0

    def test_duplicate_task_names(self, temp_output_dir):
        """중복 태스크 이름 처리"""
        splitter = FileSplitter(output_dir=str(temp_output_dir))

        tasks = [
            TaskWithMarkdown(
                task=IdentifiedTask(
                    index=i,
                    name="동일한이름",
                    description="테스트",
                    module="TestModule",
                    entities=[],
                    prerequisites=[],
                    related_sections=[]
                ),
                markdown=f"# 태스크 {i}",
                metadata=None
            )
            for i in range(1, 4)
        ]

        result = splitter.split(tasks)

        # 모두 성공 (파일명에 숫자 추가로 구분)
        assert result.success_count == 3

        # 파일 개수 확인
        md_files = list(Path(temp_output_dir).glob("*.md"))
        assert len(md_files) == 3
