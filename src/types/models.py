"""Data models for PDF extraction."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Position(BaseModel):
    """Position information for PDF elements."""

    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")
    width: Optional[float] = Field(default=None, description="Width of element")
    height: Optional[float] = Field(default=None, description="Height of element")


class TextMetadata(BaseModel):
    """Metadata for extracted text."""

    font_size: Optional[float] = Field(default=None, description="Font size")
    font_name: Optional[str] = Field(default=None, description="Font name")
    position: Optional[Position] = Field(default=None, description="Text position")


class ExtractedText(BaseModel):
    """Extracted text from PDF page."""

    page_number: int = Field(description="Page number (1-indexed)")
    text: str = Field(description="Extracted text content")
    metadata: Optional[TextMetadata] = Field(default=None, description="Text metadata")


class ExtractedImage(BaseModel):
    """Extracted image from PDF page."""

    page_number: int = Field(description="Page number (1-indexed)")
    image_path: str = Field(description="Path to saved image file")
    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")


class PDFMetadata(BaseModel):
    """PDF document metadata."""

    title: Optional[str] = Field(default=None, description="Document title")
    author: Optional[str] = Field(default=None, description="Document author")
    subject: Optional[str] = Field(default=None, description="Document subject")
    creator: Optional[str] = Field(default=None, description="Creator application")
    producer: Optional[str] = Field(default=None, description="Producer application")
    creation_date: Optional[datetime] = Field(default=None, description="Creation date")
    modification_date: Optional[datetime] = Field(default=None, description="Modification date")
    total_pages: int = Field(description="Total number of pages")


class ExtractedTable(BaseModel):
    """Extracted table from PDF page."""

    page_number: int = Field(description="Page number (1-indexed)")
    rows: List[List[str]] = Field(description="Table data as 2D array")
    position: Position = Field(description="Table position and dimensions")


class PDFPage(BaseModel):
    """Single PDF page with all extracted content."""

    page_number: int = Field(description="Page number (1-indexed)")
    text: List[ExtractedText] = Field(default_factory=list, description="Extracted text blocks")
    images: List[ExtractedImage] = Field(
        default_factory=list, description="Extracted images"
    )
    tables: List[ExtractedTable] = Field(default_factory=list, description="Extracted tables")


class PDFExtractResult(BaseModel):
    """Complete PDF extraction result."""

    metadata: PDFMetadata = Field(description="Document metadata")
    pages: List[PDFPage] = Field(description="Extracted pages")


# OCR-specific models


class BoundingBox(BaseModel):
    """Bounding box coordinates for OCR text."""

    x0: float = Field(description="Left x coordinate")
    y0: float = Field(description="Top y coordinate")
    x1: float = Field(description="Right x coordinate")
    y1: float = Field(description="Bottom y coordinate")


class OCRWord(BaseModel):
    """Individual word recognized by OCR."""

    text: str = Field(description="Recognized text")
    confidence: float = Field(description="Confidence score (0-100)", ge=0, le=100)
    bbox: BoundingBox = Field(description="Bounding box coordinates")


class OCRResult(BaseModel):
    """Result from OCR processing."""

    text: str = Field(description="Complete recognized text")
    confidence: float = Field(description="Overall confidence score (0-100)", ge=0, le=100)
    words: Optional[List[OCRWord]] = Field(
        default=None, description="Individual words with positions"
    )
    processing_time: Optional[float] = Field(
        default=None, description="Processing time in seconds"
    )


class OCRBatchResult(BaseModel):
    """Result from batch OCR processing."""

    results: List[OCRResult] = Field(description="OCR results for each image")
    image_paths: List[str] = Field(description="Paths to processed images")
    total_processing_time: float = Field(description="Total processing time in seconds")
    average_confidence: float = Field(description="Average confidence across all results")
    success_count: int = Field(description="Number of successfully processed images")
    failure_count: int = Field(description="Number of failed images")


# Preprocessor models


class PageRange(BaseModel):
    """Page range information."""

    start: int = Field(description="Start page number (1-indexed)")
    end: int = Field(description="End page number (1-indexed)")


class Section(BaseModel):
    """Document section with hierarchical structure."""

    title: str = Field(description="Section title")
    level: int = Field(description="Heading level (1, 2, 3, ...)", ge=1)
    content: str = Field(description="Section content text")
    page_range: PageRange = Field(description="Source PDF page range")
    subsections: List["Section"] = Field(
        default_factory=list, description="Nested subsections"
    )


class FunctionalGroup(BaseModel):
    """Functional grouping of related sections."""

    name: str = Field(description="Group name (e.g., '인증', '결제')")
    sections: List[Section] = Field(description="Sections in this group")
    keywords: List[str] = Field(
        default_factory=list, description="Keywords that defined this group"
    )


class PreprocessResult(BaseModel):
    """Complete preprocessing result."""

    functional_groups: List[FunctionalGroup] = Field(
        description="Functional groups of sections"
    )
    metadata: PDFMetadata = Field(description="Original PDF metadata")
    removed_header_patterns: List[str] = Field(
        default_factory=list, description="Detected and removed header patterns"
    )
    removed_footer_patterns: List[str] = Field(
        default_factory=list, description="Detected and removed footer patterns"
    )


# LLM Planner models


class TaskContext(BaseModel):
    """Task execution context (roles and deployment environments)."""

    deployment_envs: List[str] = Field(
        default_factory=lambda: ["all"],
        description="Deployment environments: development, staging, production, all"
    )
    actor_roles: List[str] = Field(
        default_factory=lambda: ["all"],
        description="User roles: user, admin, partner_admin, super_admin, all"
    )
    role_based_features: dict = Field(
        default_factory=dict,
        description="Role-specific feature descriptions (e.g., {'user': 'read only', 'admin': 'CRUD'})"
    )
    env_based_features: dict = Field(
        default_factory=dict,
        description="Environment-specific feature descriptions (e.g., {'dev': 'test PG', 'prod': 'real PG'})"
    )


class IdentifiedTask(BaseModel):
    """Identified high-level task from LLM Planner."""

    index: int = Field(description="Task index (1, 2, 3, ...)", ge=1)
    name: str = Field(description="Task name (e.g., '인증', '결제')")
    description: str = Field(description="Task description")
    module: str = Field(description="Module/area name (e.g., 'AuthModule')")
    entities: List[str] = Field(
        default_factory=list, description="Related entities (e.g., ['User', 'Session'])"
    )
    prerequisites: List[str] = Field(
        default_factory=list, description="Prerequisites for this task"
    )
    related_sections: List[int] = Field(
        default_factory=list, description="Indices of related sections"
    )
    context: TaskContext = Field(
        default_factory=TaskContext,
        description="Task context (roles and environments)"
    )


class TokenUsage(BaseModel):
    """Token usage information from LLM API."""

    input_tokens: int = Field(description="Number of input tokens")
    output_tokens: int = Field(description="Number of output tokens")
    total_tokens: int = Field(description="Total tokens used")


class LLMPlannerResult(BaseModel):
    """Complete LLM Planner result."""

    tasks: List[IdentifiedTask] = Field(description="Identified high-level tasks")
    token_usage: TokenUsage = Field(description="Total token usage")
    estimated_cost_usd: float = Field(description="Estimated cost in USD", ge=0)
    model: str = Field(description="Model used for generation")


# LLM TaskWriter models


class SubTask(BaseModel):
    """Detailed sub-task generated by TaskWriter."""

    index: str = Field(description="Sub-task index (e.g., '1.1', '1.2')")
    title: str = Field(description="Sub-task title")
    purpose: str = Field(description="Purpose of this sub-task")
    endpoint: Optional[str] = Field(default=None, description="API endpoint (e.g., 'POST /api/auth/login')")
    data_model: Optional[str] = Field(default=None, description="Data model description")
    logic: str = Field(description="Logic summary (1-3 lines)")
    security: Optional[str] = Field(default=None, description="Security/authorization requirements")
    exceptions: Optional[str] = Field(default=None, description="Exception handling")
    test_points: Optional[str] = Field(default=None, description="Testing points")


class TaskWriterResult(BaseModel):
    """Complete TaskWriter result."""

    task: IdentifiedTask = Field(description="Original high-level task")
    sub_tasks: List[SubTask] = Field(description="Generated sub-tasks")
    markdown: str = Field(description="Generated Markdown document")
    token_usage: TokenUsage = Field(description="Token usage for this task")


class ValidationResult(BaseModel):
    """Result of sub-task validation."""

    is_valid: bool = Field(description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


# FileSplitter models


class FileMetadata(BaseModel):
    """Metadata for generated markdown file (used in YAML front matter)."""

    title: str = Field(description="Task title")
    index: int = Field(description="Task index")
    generated: datetime = Field(description="File generation timestamp")
    source_pdf: Optional[str] = Field(default=None, description="Source PDF path")


class TaskWithMarkdown(BaseModel):
    """Task with its generated markdown content."""

    task: IdentifiedTask = Field(description="The identified task")
    markdown: str = Field(description="Generated markdown content")
    metadata: Optional[FileMetadata] = Field(default=None, description="File metadata for front matter")


class FileInfo(BaseModel):
    """Information about a saved file."""

    file_path: str = Field(description="Full path to the file")
    file_name: str = Field(description="File name only")
    size_bytes: int = Field(description="File size in bytes")
    task_index: int = Field(description="Task index")
    task_name: str = Field(description="Task name")


class FailedFile(BaseModel):
    """Information about a failed file write."""

    task_name: str = Field(description="Name of the task that failed")
    task_index: int = Field(description="Index of the task that failed")
    error: str = Field(description="Error message")


class SplitResult(BaseModel):
    """Result from file splitting operation."""

    saved_files: List[FileInfo] = Field(
        default_factory=list, description="Successfully saved files"
    )
    failed_files: List[FailedFile] = Field(
        default_factory=list, description="Failed file writes"
    )
    total_files: int = Field(description="Total number of files attempted")
    success_count: int = Field(description="Number of successfully saved files")
    failure_count: int = Field(description="Number of failed files")
    processing_time: float = Field(description="Total processing time in seconds")
    output_directory: str = Field(description="Output directory path")


# Reporter models


class ErrorEntry(BaseModel):
    """Error entry in report."""

    stage: str = Field(description="Stage where error occurred")
    message: str = Field(description="Error message")
    severity: str = Field(description="Severity level (warning, error, critical)")
    timestamp: datetime = Field(description="When the error occurred")


class ExtractionMetrics(BaseModel):
    """Metrics from PDF extraction stage."""

    text_pages: int = Field(description="Number of pages with text")
    images_extracted: int = Field(description="Number of images extracted")
    tables_found: int = Field(description="Number of tables found")
    processing_time: float = Field(description="Processing time in seconds")


class OCRMetrics(BaseModel):
    """Metrics from OCR stage."""

    images_processed: int = Field(description="Number of images processed")
    average_confidence: float = Field(description="Average OCR confidence (0-100)")
    total_ocr_time: float = Field(description="Total OCR processing time in seconds")


class PreprocessingMetrics(BaseModel):
    """Metrics from preprocessing stage."""

    sections_identified: int = Field(description="Number of sections identified")
    functional_groups: int = Field(description="Number of functional groups created")
    processing_time: float = Field(description="Processing time in seconds")


class LLMMetrics(BaseModel):
    """Metrics from LLM operations."""

    planner_calls: int = Field(description="Number of planner API calls")
    task_writer_calls: int = Field(description="Number of task writer API calls")
    total_tokens_used: int = Field(description="Total tokens consumed")
    total_cost: float = Field(description="Total cost in USD")
    processing_time: float = Field(description="Processing time in seconds")


class ReportSummary(BaseModel):
    """Summary information for report."""

    pdf_file: str = Field(description="Path to source PDF file")
    total_pages: int = Field(description="Total number of pages in PDF")
    generated_files: int = Field(description="Number of files generated")
    total_processing_time: float = Field(description="Total processing time in seconds")
    timestamp: datetime = Field(description="Report generation timestamp")


class ReportResult(BaseModel):
    """Complete report result."""

    summary: ReportSummary = Field(description="Report summary")
    extraction: Optional[ExtractionMetrics] = Field(
        default=None, description="Extraction metrics"
    )
    ocr: Optional[OCRMetrics] = Field(default=None, description="OCR metrics")
    preprocessing: Optional[PreprocessingMetrics] = Field(
        default=None, description="Preprocessing metrics"
    )
    llm: Optional[LLMMetrics] = Field(default=None, description="LLM metrics")
    output_files: List[FileInfo] = Field(
        default_factory=list, description="Generated output files"
    )
    errors: List[ErrorEntry] = Field(default_factory=list, description="Errors encountered")


# OpenAPI Integration models


class OpenAPIEndpoint(BaseModel):
    """OpenAPI endpoint information."""

    path: str = Field(description="API path (e.g., '/api/products')")
    method: str = Field(description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    tags: List[str] = Field(default_factory=list, description="Endpoint tags")
    summary: Optional[str] = Field(default=None, description="Endpoint summary")
    description: Optional[str] = Field(default=None, description="Endpoint description")
    operation_id: Optional[str] = Field(default=None, description="Operation ID")
    required_roles: List[str] = Field(
        default_factory=lambda: ["all"],
        description="Required user roles (extracted by LLM from security schema, etc.)"
    )
    deployment_env: str = Field(
        default="all",
        description="Deployment environment (extracted from filename)"
    )


class OpenAPISpec(BaseModel):
    """Parsed OpenAPI specification."""

    title: str = Field(description="API title")
    version: str = Field(description="API version")
    endpoints: List[OpenAPIEndpoint] = Field(description="List of endpoints")
    source_file: Optional[str] = Field(default=None, description="Source file path")
    deployment_env: str = Field(
        default="all",
        description="Deployment environment for this spec file"
    )


class TaskMatchResult(BaseModel):
    """Result of matching a task against OpenAPI specs."""

    task: IdentifiedTask = Field(description="The task being matched")
    match_status: str = Field(
        description="Match status: 'fully_implemented', 'partially_implemented', 'new'"
    )
    matched_endpoints: List[OpenAPIEndpoint] = Field(
        default_factory=list, description="Endpoints that matched this task"
    )
    confidence_score: float = Field(
        description="Confidence score (0.0 - 1.0)", ge=0.0, le=1.0
    )
    missing_features: List[str] = Field(
        default_factory=list, description="Features mentioned in task but not in OpenAPI"
    )
    context_match_matrix: dict = Field(
        default_factory=dict,
        description="""
        Role x Environment matrix showing implementation status.
        Example:
        {
          "user": {"development": "fully_implemented", "production": "fully_implemented"},
          "admin": {"development": "fully_implemented", "production": "partially_implemented"},
          "partner_admin": {"development": "new", "production": "new"}
        }
        """
    )
    llm_based: bool = Field(
        default=False,
        description="Whether this match was performed using LLM (True) or rule-based (False)"
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Detailed explanation from LLM (if llm_based=True)"
    )


class OpenAPIComparison(BaseModel):
    """Complete OpenAPI comparison result."""

    specs: List[dict] = Field(
        default_factory=list, description="Summary of loaded OpenAPI specs"
    )
    match_results: List[TaskMatchResult] = Field(
        description="Match results for each task"
    )
    total_endpoints: int = Field(description="Total number of endpoints across all specs")


# Image Analysis models


class UIComponent(BaseModel):
    """UI component extracted from screen design image."""

    type: str = Field(description="Component type (button, input, card, navigation, etc.)")
    label: Optional[str] = Field(default=None, description="Component label or text")
    position: Optional[str] = Field(default=None, description="Component position (header, footer, center, etc.)")
    description: str = Field(description="Component description")


class ImageAnalysis(BaseModel):
    """Result from analyzing a screen design image."""

    image_path: str = Field(description="Path to the analyzed image")
    page_number: int = Field(description="PDF page number where image was found")
    screen_title: Optional[str] = Field(default=None, description="Title or name of the screen")
    screen_type: str = Field(description="Screen type (login, dashboard, list, detail, form, etc.)")
    ui_components: List[UIComponent] = Field(
        default_factory=list, description="UI components identified in the screen"
    )
    layout_structure: str = Field(description="Overall layout structure description")
    user_flow: Optional[str] = Field(default=None, description="User flow or interaction description")
    confidence: float = Field(description="Overall confidence score (0-100)", ge=0, le=100)
    processing_time: float = Field(description="Processing time in seconds")
    token_usage: TokenUsage = Field(description="Token usage for this analysis")


class ImageAnalysisBatchResult(BaseModel):
    """Result from batch image analysis."""

    analyses: List[ImageAnalysis] = Field(description="Analysis results for each image")
    total_images: int = Field(description="Total number of images processed")
    success_count: int = Field(description="Number of successfully analyzed images")
    failure_count: int = Field(description="Number of failed analyses")
    total_processing_time: float = Field(description="Total processing time in seconds")
    total_tokens_used: int = Field(description="Total tokens consumed")
    total_cost: float = Field(description="Total cost in USD")

