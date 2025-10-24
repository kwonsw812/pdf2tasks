"""Orchestrator for coordinating the entire PDF processing pipeline."""

import time
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from ..extractors.pdf_extractor import PDFExtractor
from ..preprocessor.preprocessor import Preprocessor
from ..llm.planner.llm_planner import LLMPlanner
from ..llm.task_writer import LLMTaskWriter
from ..llm.image_analyzer import ImageAnalyzer
from ..splitter.file_splitter import FileSplitter
from ..reporter.reporter import Reporter
from ..openapi.loader import OpenAPILoader
from ..openapi.parser import OpenAPIParser
from ..openapi.matcher import TaskMatcher
from ..types.models import (
    ReportResult,
    ReportSummary,
    ExtractionMetrics,
    PreprocessingMetrics,
    LLMMetrics,
    FileInfo,
    ErrorEntry,
    TaskWithMarkdown,
    FileMetadata,
    IdentifiedTask,
    OpenAPIComparison,
    ImageAnalysisBatchResult,
    PDFExtractResult,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OrchestratorConfig:
    """Configuration for Orchestrator."""

    def __init__(
        self,
        pdf_path: str,
        output_dir: str,
        extract_images: bool = True,
        extract_tables: bool = True,
        use_ocr: bool = False,
        analyze_images: bool = True,
        clean_output: bool = False,
        add_front_matter: bool = True,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        verbose: bool = False,
        openapi_dir: str = "./openapi",
        skip_implemented: bool = False,
        use_llm_preprocessing: bool = True,
        max_concurrent_llm_calls: int = 2,
        use_llm_context_extraction: bool = True,
        use_llm_openapi_matching: bool = True,
    ):
        """
        Initialize orchestrator configuration.

        Args:
            pdf_path: Path to input PDF file
            output_dir: Directory for output files
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            use_ocr: Whether to use OCR
            analyze_images: Whether to analyze extracted images with Claude Vision
            clean_output: Whether to clean output directory before processing
            add_front_matter: Whether to add YAML front matter to files
            api_key: Anthropic API key
            model: Claude model to use
            verbose: Enable verbose logging
            openapi_dir: Directory containing OpenAPI spec files
            skip_implemented: Skip tasks that are already implemented in OpenAPI
            use_llm_preprocessing: Use LLM for section segmentation and functional grouping
            max_concurrent_llm_calls: Maximum number of concurrent LLM API calls (default: 2)
            use_llm_context_extraction: Use LLM to extract task contexts (roles/environments)
            use_llm_openapi_matching: Use LLM for context-aware OpenAPI matching
        """
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.use_ocr = use_ocr
        self.analyze_images = analyze_images
        self.clean_output = clean_output
        self.add_front_matter = add_front_matter
        self.api_key = api_key
        self.model = model
        self.verbose = verbose
        self.openapi_dir = openapi_dir
        self.skip_implemented = skip_implemented
        self.use_llm_preprocessing = use_llm_preprocessing
        self.max_concurrent_llm_calls = max_concurrent_llm_calls
        self.use_llm_context_extraction = use_llm_context_extraction
        self.use_llm_openapi_matching = use_llm_openapi_matching


class Orchestrator:
    """
    Main orchestrator for PDF processing pipeline.

    Coordinates all processing stages:
    1. PDF Extraction
    2. OCR (optional)
    3. Preprocessing
    4. LLM Planner
    4.5. OpenAPI Comparison (optional)
    5. LLM TaskWriter
    6. File Splitting
    7. Report Generation
    """

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize orchestrator.

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        self.errors: list[ErrorEntry] = []
        self.start_time = None

        # Create output directory for intermediate results
        self.intermediate_dir = Path(config.output_dir) / "_intermediate"
        self.intermediate_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 80)
        logger.info("PDF Agent Orchestrator initialized")
        logger.info(f"PDF: {config.pdf_path}")
        logger.info(f"Output: {config.output_dir}")
        logger.info(f"Model: {config.model}")
        logger.info(f"Intermediate: {self.intermediate_dir}")
        logger.info("=" * 80)

    def run(self) -> ReportResult:
        """
        Execute the complete processing pipeline.

        Returns:
            ReportResult with processing metrics

        Raises:
            Exception: If critical error occurs during processing
        """
        self.start_time = time.time()
        logger.info("\n" + "=" * 80)
        logger.info("STARTING PDF PROCESSING PIPELINE")
        logger.info("=" * 80 + "\n")

        try:
            # Stage 1: PDF Extraction
            logger.info("[1/6] PDF 추출 중...")
            extraction_start = time.time()
            pdf_result, extraction_metrics = self._extract_pdf()
            extraction_time = time.time() - extraction_start
            self._save_intermediate_result("pdf_extraction", pdf_result, 1)
            logger.info(f"✓ PDF 추출 완료 ({extraction_time:.2f}초)\n")

            # Stage 2: OCR (optional)
            if self.config.use_ocr:
                logger.info("[2/6] OCR 처리 중...")
                ocr_start = time.time()
                pdf_result = self._process_ocr(pdf_result)
                ocr_time = time.time() - ocr_start
                self._save_intermediate_result("ocr_result", pdf_result, 2)
                logger.info(f"✓ OCR 처리 완료 ({ocr_time:.2f}초)\n")

            # Stage 2.5: Image Analysis (optional)
            image_analysis_result = None
            if self.config.analyze_images and self.config.extract_images:
                logger.info("[2.5/6] 이미지 분석 중 (Vision API)...")
                image_start = time.time()
                image_analysis_result = self._analyze_images(pdf_result)
                image_time = time.time() - image_start
                self._save_intermediate_result("image_analysis", image_analysis_result, 2.5)
                logger.info(
                    f"✓ 이미지 분석 완료: {image_analysis_result.success_count}/{image_analysis_result.total_images}개 "
                    f"({image_time:.2f}초, 비용: ${image_analysis_result.total_cost:.4f})\n"
                )

            # Stage 3: Preprocessing
            logger.info("[3/6] 전처리 중...")
            preprocess_start = time.time()
            preprocess_result, preprocessing_metrics = self._preprocess(pdf_result)
            preprocess_time = time.time() - preprocess_start
            self._save_intermediate_result("preprocessing", preprocess_result, 3)
            logger.info(f"✓ 전처리 완료 ({preprocess_time:.2f}초)\n")

            # Stage 4: LLM Planner
            logger.info("[3/6] 상위 태스크 식별 중 (LLM Planner)...")
            planner_start = time.time()
            planner_result = self._identify_tasks(
                preprocess_result,
                image_analyses=image_analysis_result.analyses if image_analysis_result else None
            )
            planner_time = time.time() - planner_start
            self._save_intermediate_result("planner_tasks", planner_result, 4)
            logger.info(f"✓ {len(planner_result.tasks)}개 태스크 식별 완료 ({planner_time:.2f}초)\n")

            # Stage 4.5: OpenAPI Comparison (optional)
            tasks_to_process = planner_result.tasks
            openapi_comparison = None

            if Path(self.config.openapi_dir).exists():
                logger.info("[3.5/6] OpenAPI 스펙과 비교 중...")
                comparison_start = time.time()
                openapi_comparison = self._compare_with_openapi(planner_result.tasks)
                comparison_time = time.time() - comparison_start

                if openapi_comparison:
                    self._save_intermediate_result("openapi_comparison", openapi_comparison, 4.5)
                    logger.info(f"✓ OpenAPI 비교 완료 ({comparison_time:.2f}초)")

                    # Filter tasks if skip_implemented is enabled
                    if self.config.skip_implemented:
                        tasks_to_process = self._filter_implemented_tasks(
                            planner_result.tasks, openapi_comparison
                        )
                        skipped_count = len(planner_result.tasks) - len(tasks_to_process)
                        logger.info(
                            f"  → {skipped_count}개 이미 구현된 태스크 스킵됨\n"
                        )
                    else:
                        logger.info(
                            f"  → 비교 완료 (스킵 비활성화, 모든 태스크 계속 처리)\n"
                        )
            else:
                logger.info(f"  OpenAPI 디렉토리를 찾을 수 없습니다: {self.config.openapi_dir}")
                logger.info("  OpenAPI 비교를 건너뜁니다.\n")

            # Stage 5: LLM TaskWriter
            logger.info(f"[4/6] 하위 태스크 작성 중 (LLM TaskWriter) - {len(tasks_to_process)}개 태스크...")
            taskwriter_start = time.time()
            tasks_with_markdown = self._write_tasks(
                tasks_to_process,
                preprocess_result.functional_groups,
                image_analyses=image_analysis_result.analyses if image_analysis_result else None
            )
            taskwriter_time = time.time() - taskwriter_start
            self._save_intermediate_result("tasks_with_markdown", tasks_with_markdown, 5)
            logger.info(f"✓ 하위 태스크 작성 완료 ({taskwriter_time:.2f}초)\n")

            # Stage 6: File Splitting
            logger.info("[5/6] 파일 분리 중...")
            split_start = time.time()
            split_result = self._split_files(tasks_with_markdown)
            split_time = time.time() - split_start
            self._save_intermediate_result("split_result", split_result, 6)
            logger.info(f"✓ {split_result.success_count}개 파일 생성 완료 ({split_time:.2f}초)\n")

            # Stage 7: Report Generation
            logger.info("[6/6] 리포트 생성 중...")
            report = self._generate_report(
                pdf_result,
                extraction_metrics,
                preprocessing_metrics,
                planner_result,
                taskwriter_time,
                split_result.saved_files,
            )
            logger.info("✓ 리포트 생성 완료\n")

            # Save reports
            self._save_reports(report)

            total_time = time.time() - self.start_time
            logger.info("=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info(f"Total time: {total_time:.2f}초")
            logger.info(f"Generated files: {len(split_result.saved_files)}")
            if report.llm:
                logger.info(f"Total cost: ${report.llm.total_cost:.6f}")
            logger.info("=" * 80)

            return report

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            self._add_error("Pipeline", str(e), "critical")
            raise

    def _extract_pdf(self):
        """Extract content from PDF."""
        try:
            extractor = PDFExtractor(
                output_dir=str(Path(self.config.output_dir) / "temp_images"),
                extract_images=self.config.extract_images,
                extract_tables=self.config.extract_tables,
            )

            result = extractor.extract(self.config.pdf_path)

            # Calculate metrics
            total_images = sum(len(page.images) for page in result.pages)
            total_tables = sum(len(page.tables) for page in result.pages)

            metrics = ExtractionMetrics(
                text_pages=len(result.pages),
                images_extracted=total_images,
                tables_found=total_tables,
                processing_time=0.0,  # Calculated externally
            )

            return result, metrics

        except Exception as e:
            self._add_error("PDF Extraction", str(e), "error")
            raise

    def _process_ocr(self, pdf_result):
        """Process OCR on extracted images."""
        try:
            from ..ocr.ocr_engine import OCREngine

            logger.info("  OCR 엔진 초기화 중...")
            ocr_engine = OCREngine(lang="kor+eng")

            # Process each page's images
            for page in pdf_result.pages:
                if page.images:
                    logger.info(f"  페이지 {page.page_number}: {len(page.images)}개 이미지 OCR 처리 중...")

                    for img in page.images:
                        try:
                            # Perform OCR
                            ocr_result = ocr_engine.process_image(img.image_path)

                            # Append OCR text to page text
                            if ocr_result.text.strip():
                                from ..types.models import ExtractedText, Position

                                ocr_text = ExtractedText(
                                    page_number=page.page_number,
                                    text=f"\n[OCR 텍스트]\n{ocr_result.text}",
                                    metadata={
                                        "font_size": None,
                                        "font_name": "OCR",
                                        "position": Position(x0=0, y0=0, x1=0, y1=0),
                                        "ocr_confidence": ocr_result.confidence,
                                    },
                                )
                                page.text.append(ocr_text)

                                logger.debug(f"    OCR 신뢰도: {ocr_result.confidence:.2f}%")

                        except Exception as e:
                            logger.warning(f"    이미지 {img.image_path} OCR 실패: {e}")
                            continue

            # Cleanup OCR engine
            ocr_engine.cleanup()

            logger.info("  OCR 처리 완료")
            return pdf_result

        except ImportError:
            logger.warning("OCR 모듈이 설치되지 않았습니다. OCR을 건너뜁니다.")
            return pdf_result
        except Exception as e:
            self._add_error("OCR Processing", str(e), "warning")
            logger.warning(f"OCR 처리 실패, 계속 진행: {e}")
            return pdf_result

    def _preprocess(self, pdf_result):
        """Preprocess extracted content."""
        try:
            preprocessor = Preprocessor(
                normalize_text=True,
                remove_headers_footers=True,
                segment_sections=True,
                group_by_function=True,
                use_llm=self.config.use_llm_preprocessing,
                llm_api_key=self.config.api_key,
                llm_model=self.config.model,
            )

            result = preprocessor.process(pdf_result)

            # Calculate metrics
            total_sections = sum(len(group.sections) for group in result.functional_groups)

            metrics = PreprocessingMetrics(
                sections_identified=total_sections,
                functional_groups=len(result.functional_groups),
                processing_time=0.0,  # Calculated externally
            )

            return result, metrics

        except Exception as e:
            self._add_error("Preprocessing", str(e), "error")
            raise

    def _identify_tasks(self, preprocess_result, image_analyses=None):
        """Identify high-level tasks using LLM Planner."""
        try:
            planner = LLMPlanner(
                api_key=self.config.api_key,
                model=self.config.model,
            )

            # Extract sections from functional groups
            all_sections = []
            for group in preprocess_result.functional_groups:
                all_sections.extend(group.sections)

            # Use sections method to support image analyses
            result = planner.identify_tasks_from_sections(
                all_sections,
                image_analyses=image_analyses
            )

            return result

        except Exception as e:
            self._add_error("LLM Planner", str(e), "error")
            raise

    def _write_tasks(self, tasks, functional_groups, image_analyses=None):
        """Write detailed sub-tasks using LLM TaskWriter (with parallel processing)."""
        try:
            # Run async version to enable parallel processing
            return asyncio.run(self._write_tasks_async(tasks, functional_groups, image_analyses))

        except Exception as e:
            self._add_error("LLM TaskWriter", str(e), "error")
            raise

    async def _write_tasks_async(self, tasks, functional_groups, image_analyses=None):
        """Write detailed sub-tasks using LLM TaskWriter (async version for parallel processing)."""
        task_writer = LLMTaskWriter(
            api_key=self.config.api_key,
            model=self.config.model,
        )

        # Flatten sections from functional groups
        all_sections = []
        for group in functional_groups:
            all_sections.extend(group.sections)

        # Use semaphore to limit concurrent API calls (avoid 429 errors)
        max_concurrent = self.config.max_concurrent_llm_calls
        semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(f"  🚀 Processing {len(tasks)} tasks with max {max_concurrent} concurrent requests...")

        async def process_task_with_limit(task):
            """Process a single task with rate limiting."""
            async with semaphore:
                logger.info(f"  [Started] Task {task.index}: {task.name}")
                try:
                    result = await task_writer.write_task_async(
                        task,
                        all_sections,
                        image_analyses=image_analyses
                    )
                    logger.info(f"  [Completed] Task {task.index}: {task.name}")
                    return result
                except Exception as e:
                    logger.error(f"  [Failed] Task {task.index}: {task.name} - {str(e)}")
                    raise

        # Create async tasks with rate limiting
        async_tasks = [process_task_with_limit(task) for task in tasks]

        # Execute all tasks with controlled concurrency
        results = await asyncio.gather(*async_tasks)

        # Convert results to TaskWithMarkdown
        tasks_with_markdown = []
        for i, (task, result) in enumerate(zip(tasks, results)):
            logger.info(f"  ✓ Completed task {task.index}: {task.name}")

            metadata = FileMetadata(
                title=task.name,
                index=task.index,
                generated=datetime.now(),
                source_pdf=self.config.pdf_path,
            )

            task_with_md = TaskWithMarkdown(
                task=task,
                markdown=result.markdown,
                metadata=metadata,
            )

            tasks_with_markdown.append(task_with_md)

        return tasks_with_markdown

    def _split_files(self, tasks_with_markdown):
        """Split tasks into individual markdown files."""
        try:
            splitter = FileSplitter(
                output_dir=self.config.output_dir,
                clean=self.config.clean_output,
                overwrite=True,
                add_front_matter=self.config.add_front_matter,
            )

            result = splitter.split(tasks_with_markdown)

            return result

        except Exception as e:
            self._add_error("File Splitting", str(e), "error")
            raise

    def _generate_report(
        self,
        pdf_result,
        extraction_metrics,
        preprocessing_metrics,
        planner_result,
        taskwriter_time,
        output_files,
    ):
        """Generate comprehensive report."""
        try:
            reporter = Reporter()

            # Calculate LLM metrics
            total_tokens = planner_result.token_usage.total_tokens
            total_cost = planner_result.estimated_cost_usd

            # Add TaskWriter metrics (assume similar token usage pattern)
            # In real implementation, track this from task_writer calls
            llm_metrics = LLMMetrics(
                planner_calls=1,
                task_writer_calls=len(planner_result.tasks),
                total_tokens_used=total_tokens,
                total_cost=total_cost,
                processing_time=taskwriter_time,
            )

            total_time = time.time() - self.start_time

            report = reporter.generate_report(
                pdf_file=self.config.pdf_path,
                total_pages=pdf_result.metadata.total_pages,
                output_files=output_files,
                extraction_metrics=extraction_metrics,
                preprocessing_metrics=preprocessing_metrics,
                llm_metrics=llm_metrics,
                errors=self.errors,
                total_processing_time=total_time,
            )

            return report

        except Exception as e:
            self._add_error("Report Generation", str(e), "error")
            raise

    def _save_reports(self, report: ReportResult):
        """Save reports to files."""
        try:
            reporter = Reporter()

            # Save text report
            text_path = Path(self.config.output_dir) / "report.log"
            reporter.save_text_report(report, str(text_path))

            # Save JSON report
            json_path = Path(self.config.output_dir) / "report.json"
            reporter.save_json_report(report, str(json_path))

            # Print to console
            reporter.print_to_console(report)

        except Exception as e:
            logger.error(f"Failed to save reports: {e}")
            self._add_error("Report Saving", str(e), "warning")

    def _add_error(self, stage: str, message: str, severity: str = "error"):
        """Add error to error list."""
        error = ErrorEntry(
            stage=stage,
            message=message,
            severity=severity,
            timestamp=datetime.now(),
        )
        self.errors.append(error)
        logger.error(f"[{severity.upper()}] {stage}: {message}")

    def _save_intermediate_result(self, stage_name: str, data: any, stage_num: int | float):
        """
        Save intermediate result to JSON file.

        Args:
            stage_name: Name of the processing stage
            data: Data to save (must be JSON serializable or Pydantic model)
            stage_num: Stage number (1-6, can include decimals like 4.5)
        """
        try:
            # Ensure intermediate directory exists (in case it was deleted)
            self.intermediate_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{stage_num}_{stage_name}.json"
            filepath = self.intermediate_dir / filename

            # Convert Pydantic models to dict
            if hasattr(data, 'model_dump'):
                data_dict = data.model_dump(mode='json')
            elif hasattr(data, '__dict__'):
                # Try to convert object to dict
                data_dict = {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
            else:
                data_dict = data

            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"  → 중간 결과 저장: {filename}")

        except Exception as e:
            logger.warning(f"Failed to save intermediate result {stage_name}: {e}")

    def _extract_task_contexts(
        self, tasks: List[IdentifiedTask], sections: List
    ) -> List[IdentifiedTask]:
        """
        Extract context information (roles and environments) from tasks using LLM.

        Args:
            tasks: List of identified tasks
            sections: All sections from preprocessing

        Returns:
            List of tasks with context information filled
        """
        if not self.config.use_llm_context_extraction or not self.config.api_key:
            logger.info("  Skipping context extraction (disabled or no API key)")
            return tasks

        try:
            from src.llm.context_extractor import LLMContextExtractor

            extractor = LLMContextExtractor(
                api_key=self.config.api_key,
                model=self.config.model
            )

            logger.info(f"  Extracting context for {len(tasks)} tasks...")
            tasks_with_context = []

            for task in tasks:
                try:
                    context = extractor.extract_task_context(task, sections)
                    task.context = context
                    tasks_with_context.append(task)
                    logger.debug(
                        f"    → Task '{task.name}': roles={context.actor_roles}, envs={context.deployment_envs}"
                    )
                except Exception as e:
                    logger.warning(f"  Failed to extract context for task '{task.name}': {e}")
                    tasks_with_context.append(task)  # Keep task with default context

            logger.info(f"  ✓ Context extraction completed for {len(tasks_with_context)} tasks")
            return tasks_with_context

        except Exception as e:
            logger.error(f"Context extraction failed: {e}")
            self._add_error("Context Extraction", str(e), "warning")
            return tasks  # Return tasks with default context

    def _analyze_openapi_specs(self) -> List:
        """
        Load and analyze OpenAPI specifications with LLM-based role/environment extraction.

        Returns:
            List of OpenAPISpec objects with context information
        """
        try:
            from src.openapi.llm_openapi_analyzer import LLMOpenAPIAnalyzer

            # Load OpenAPI specs
            loader = OpenAPILoader(self.config.openapi_dir)
            spec_dicts = loader.load_all_specs()

            if not spec_dicts:
                logger.warning("  No OpenAPI specs found")
                return []

            logger.info(f"  Loaded {len(spec_dicts)} OpenAPI spec(s)")

            # Parse specs
            parser = OpenAPIParser()
            analyzer = LLMOpenAPIAnalyzer(
                api_key=self.config.api_key,
                model=self.config.model
            ) if self.config.api_key else None

            specs = []
            total_endpoints = 0

            for spec_dict in spec_dicts:
                try:
                    spec = parser.parse(spec_dict)

                    # Extract deployment environment from filename
                    if analyzer:
                        spec.deployment_env = analyzer.extract_deployment_env(Path(spec.source_file or ""))

                    # Analyze each endpoint for roles (if LLM enabled)
                    if analyzer and self.config.use_llm_openapi_matching:
                        logger.info(f"    Analyzing roles for {spec.title} endpoints...")
                        for endpoint in spec.endpoints:
                            try:
                                role_result = analyzer.analyze_endpoint({
                                    "path": endpoint.path,
                                    "method": endpoint.method,
                                    "summary": endpoint.summary,
                                    "description": endpoint.description,
                                    "security": []  # TODO: Extract from spec if available
                                })
                                endpoint.required_roles = role_result["required_roles"]
                                endpoint.deployment_env = spec.deployment_env
                            except Exception as e:
                                logger.warning(f"    Failed to analyze endpoint {endpoint.path}: {e}")
                                # Keep default roles

                    specs.append(spec)
                    total_endpoints += len(spec.endpoints)
                    logger.info(
                        f"    - {spec.title} v{spec.version}: {len(spec.endpoints)} endpoints (env: {spec.deployment_env})"
                    )

                except Exception as e:
                    logger.warning(f"  Failed to parse spec: {e}")
                    continue

            logger.info(f"  ✓ Loaded and analyzed {len(specs)} spec(s) with {total_endpoints} endpoints")
            return specs

        except Exception as e:
            logger.error(f"OpenAPI analysis failed: {e}")
            self._add_error("OpenAPI Analysis", str(e), "error")
            return []

    def _match_tasks_with_openapi(
        self, tasks: List[IdentifiedTask], specs: List
    ) -> OpenAPIComparison:
        """
        Match tasks against OpenAPI specs with context awareness (LLM-based).

        Args:
            tasks: List of identified tasks (with context)
            specs: List of OpenAPISpec objects (with roles/envs)

        Returns:
            OpenAPIComparison result
        """
        try:
            from src.openapi.llm_task_matcher import LLMTaskMatcher

            # Create matcher (with fallback to rule-based)
            matcher = LLMTaskMatcher(
                specs=specs,
                api_key=self.config.api_key,
                use_llm=self.config.use_llm_openapi_matching,
                model=self.config.model,
                fallback=True
            )

            logger.info(f"  Matching {len(tasks)} tasks against OpenAPI...")
            match_results = []

            for task in tasks:
                try:
                    match_result = matcher.match_task(task)
                    match_results.append(match_result)
                    logger.debug(
                        f"    → Task '{task.name}': {match_result.match_status} "
                        f"(confidence: {match_result.confidence_score:.2f}, llm_based: {match_result.llm_based})"
                    )
                except Exception as e:
                    logger.warning(f"  Failed to match task '{task.name}': {e}")
                    # Continue with other tasks

            # Create comparison summary
            total_endpoints = sum(len(spec.endpoints) for spec in specs)
            spec_summaries = [
                {
                    "title": spec.title,
                    "version": spec.version,
                    "endpoints": len(spec.endpoints),
                    "source_file": spec.source_file,
                    "deployment_env": spec.deployment_env,
                }
                for spec in specs
            ]

            comparison = OpenAPIComparison(
                specs=spec_summaries,
                match_results=match_results,
                total_endpoints=total_endpoints,
            )

            # Log summary
            logger.info("\n  OpenAPI 매칭 결과:")
            fully_impl = sum(1 for r in match_results if r.match_status == "fully_implemented")
            partial_impl = sum(1 for r in match_results if r.match_status == "partially_implemented")
            new_tasks = sum(1 for r in match_results if r.match_status == "new")
            llm_based = sum(1 for r in match_results if r.llm_based)

            logger.info(f"    - 완전 구현: {fully_impl}개")
            logger.info(f"    - 부분 구현: {partial_impl}개")
            logger.info(f"    - 신규 기능: {new_tasks}개")
            logger.info(f"    - LLM 기반 매칭: {llm_based}개 / {len(match_results)}개")

            return comparison

        except Exception as e:
            logger.error(f"OpenAPI matching failed: {e}")
            self._add_error("OpenAPI Matching", str(e), "error")
            # Return empty comparison
            return OpenAPIComparison(
                specs=[],
                match_results=[],
                total_endpoints=0
            )

    def _compare_with_openapi(self, tasks: List[IdentifiedTask]) -> Optional[OpenAPIComparison]:
        """
        Compare identified tasks with OpenAPI specifications.
        Deprecated: Use _analyze_openapi_specs + _match_tasks_with_openapi instead.

        This method is kept for backward compatibility.

        Args:
            tasks: List of identified tasks

        Returns:
            OpenAPIComparison result or None if comparison fails
        """
        try:
            specs = self._analyze_openapi_specs()
            if not specs:
                return None

            comparison = self._match_tasks_with_openapi(tasks, specs)
            return comparison

        except Exception as e:
            logger.warning(f"OpenAPI comparison failed: {e}")
            self._add_error("OpenAPI Comparison", str(e), "warning")
            return None

    def _filter_implemented_tasks(
        self, tasks: List[IdentifiedTask], comparison: OpenAPIComparison
    ) -> List[IdentifiedTask]:
        """
        Filter out tasks that are fully implemented.

        Args:
            tasks: Original list of tasks
            comparison: OpenAPI comparison result

        Returns:
            Filtered list of tasks (excluding fully implemented ones)
        """
        filtered_tasks = []

        for match_result in comparison.match_results:
            if match_result.match_status != "fully_implemented":
                filtered_tasks.append(match_result.task)
            else:
                logger.info(
                    f"    → Skipping '{match_result.task.name}' "
                    f"(fully implemented, confidence: {match_result.confidence_score:.2f})"
                )

        return filtered_tasks

    def _analyze_images(self, pdf_result: PDFExtractResult) -> ImageAnalysisBatchResult:
        """
        Analyze extracted images using Claude Vision API.

        Args:
            pdf_result: PDF extraction result with images

        Returns:
            ImageAnalysisBatchResult with all image analyses

        Raises:
            Exception: If image analysis fails critically
        """
        try:
            # Collect all extracted images
            all_images = []
            for page in pdf_result.pages:
                all_images.extend(page.images)

            if not all_images:
                logger.warning("이미지가 추출되지 않았습니다. 이미지 분석을 건너뜁니다.")
                # Return empty result
                return ImageAnalysisBatchResult(
                    analyses=[],
                    total_images=0,
                    success_count=0,
                    failure_count=0,
                    total_processing_time=0.0,
                    total_tokens_used=0,
                    total_cost=0.0,
                )

            logger.info(f"총 {len(all_images)}개의 이미지를 분석합니다...")

            # Build context map (page number -> section text)
            context_map = {}
            for page in pdf_result.pages:
                page_text = " ".join([t.text for t in page.text])
                # Limit context to first 500 characters
                context_map[page.page_number] = page_text[:500]

            # Initialize ImageAnalyzer
            analyzer = ImageAnalyzer(
                api_key=self.config.api_key,
                model=self.config.model,
                max_retries=2,
            )

            # Perform batch analysis (max 3 concurrent)
            result = analyzer.analyze_batch(
                images=all_images,
                context_map=context_map,
                max_concurrent=3,
            )

            # Log summary
            logger.info("\n  이미지 분석 요약:")
            logger.info(f"    - 성공: {result.success_count}개")
            logger.info(f"    - 실패: {result.failure_count}개")
            logger.info(f"    - 토큰 사용량: {result.total_tokens_used:,}")
            logger.info(f"    - 총 비용: ${result.total_cost:.4f}")

            # Log each analyzed screen
            for analysis in result.analyses:
                logger.debug(
                    f"    → Page {analysis.page_number}: {analysis.screen_title or 'Unknown'} "
                    f"({analysis.screen_type}, {len(analysis.ui_components)} components)"
                )

            return result

        except Exception as e:
            logger.error(f"이미지 분석 실패: {e}")
            self._add_error("Image Analysis", str(e), "error")
            raise
