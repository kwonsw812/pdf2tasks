"""Image Analyzer for analyzing UI/UX design images using Claude Vision API."""

import json
import time
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..types.models import (
    ImageAnalysis,
    ImageAnalysisBatchResult,
    UIComponent,
    TokenUsage,
    ExtractedImage,
)
from ..utils.logger import get_logger
from .vision_client import VisionClient
from .vision_prompts import (
    build_vision_analysis_prompt,
    VISION_SYSTEM_PROMPT,
    validate_vision_response,
)
from .exceptions import JSONParseError, LLMError

logger = get_logger(__name__)


class ImageAnalyzer:
    """
    Analyzes UI/UX design images from PDF specifications.

    Uses Claude Vision API to extract UI components, layout structure,
    and user flows from screen design images.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 2048,
        temperature: float = 0.0,
        max_retries: int = 2,
    ):
        """
        Initialize ImageAnalyzer.

        Args:
            api_key: Anthropic API key (defaults to env var)
            model: Claude model to use
            max_tokens: Maximum tokens per response
            temperature: Sampling temperature (0 = deterministic)
            max_retries: Maximum number of retry attempts on failure
        """
        self.vision_client = VisionClient(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        self.max_retries = max_retries
        logger.info("ImageAnalyzer initialized")

    def analyze_image(
        self,
        image_path: str,
        page_number: int,
        context: str = "",
    ) -> ImageAnalysis:
        """
        Analyze a single screen design image.

        Args:
            image_path: Path to the image file
            page_number: PDF page number where image was found
            context: Additional context (e.g., section text near the image)

        Returns:
            ImageAnalysis object with extracted information

        Raises:
            FileNotFoundError: If image file doesn't exist
            JSONParseError: If response parsing fails
            LLMError: If API call fails after retries
        """
        logger.info(f"Analyzing image: {image_path} (page {page_number})")
        start_time = time.time()

        # Build prompt
        prompt = build_vision_analysis_prompt(context=context)

        # Try analysis with retry logic
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Call Vision API
                response = self.vision_client.analyze_image(
                    image_path=image_path,
                    prompt=prompt,
                    system=VISION_SYSTEM_PROMPT,
                )

                # Parse JSON response
                analysis_data = self._parse_vision_response(response["content"])

                # Validate response
                if not validate_vision_response(analysis_data):
                    raise JSONParseError("Invalid vision response structure")

                # Extract token usage
                token_usage = TokenUsage(
                    input_tokens=response["usage"]["input_tokens"],
                    output_tokens=response["usage"]["output_tokens"],
                    total_tokens=response["usage"]["total_tokens"],
                )

                # Build ImageAnalysis object
                ui_components = [
                    UIComponent(
                        type=comp["type"],
                        label=comp.get("label"),
                        position=comp.get("position"),
                        description=comp["description"],
                    )
                    for comp in analysis_data["ui_components"]
                ]

                processing_time = time.time() - start_time

                image_analysis = ImageAnalysis(
                    image_path=image_path,
                    page_number=page_number,
                    screen_title=analysis_data.get("screen_title"),
                    screen_type=analysis_data["screen_type"],
                    ui_components=ui_components,
                    layout_structure=analysis_data["layout_structure"],
                    user_flow=analysis_data.get("user_flow"),
                    confidence=float(analysis_data["confidence"]),
                    processing_time=processing_time,
                    token_usage=token_usage,
                )

                logger.info(
                    f"Image analysis completed: {image_analysis.screen_title or 'Unknown'} "
                    f"({len(ui_components)} components, {processing_time:.2f}s)"
                )

                return image_analysis

            except (JSONParseError, KeyError) as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {str(e)}"
                )
                if attempt < self.max_retries:
                    logger.info("Retrying...")
                    time.sleep(1)  # Brief delay before retry
                continue

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during image analysis: {str(e)}")
                raise LLMError(f"Image analysis failed: {str(e)}")

        # All retries failed
        raise LLMError(
            f"Image analysis failed after {self.max_retries + 1} attempts: {str(last_error)}"
        )

    def analyze_batch(
        self,
        images: List[ExtractedImage],
        context_map: Optional[Dict[int, str]] = None,
        max_concurrent: int = 3,
    ) -> ImageAnalysisBatchResult:
        """
        Analyze multiple images in parallel.

        Args:
            images: List of ExtractedImage objects
            context_map: Dictionary mapping page_number to context text
            max_concurrent: Maximum number of concurrent API calls

        Returns:
            ImageAnalysisBatchResult with all analyses

        Raises:
            ValueError: If images list is empty
        """
        if not images:
            raise ValueError("Images list is empty")

        logger.info(f"Starting batch analysis of {len(images)} images (max_concurrent={max_concurrent})")
        start_time = time.time()

        context_map = context_map or {}
        analyses = []
        failures = []

        # Process images in parallel
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all tasks
            future_to_image = {
                executor.submit(
                    self.analyze_image,
                    img.image_path,
                    img.page_number,
                    context_map.get(img.page_number, ""),
                ): img
                for img in images
            }

            # Collect results
            for future in as_completed(future_to_image):
                image = future_to_image[future]
                try:
                    analysis = future.result()
                    analyses.append(analysis)
                    logger.debug(f"Completed analysis for page {image.page_number}")
                except Exception as e:
                    logger.error(f"Failed to analyze image on page {image.page_number}: {str(e)}")
                    failures.append(image)

        # Calculate totals
        total_processing_time = time.time() - start_time
        total_tokens = sum(a.token_usage.total_tokens for a in analyses)
        total_cost = sum(
            self.vision_client.calculate_cost(
                a.token_usage.input_tokens,
                a.token_usage.output_tokens,
            )
            for a in analyses
        )

        result = ImageAnalysisBatchResult(
            analyses=analyses,
            total_images=len(images),
            success_count=len(analyses),
            failure_count=len(failures),
            total_processing_time=total_processing_time,
            total_tokens_used=total_tokens,
            total_cost=total_cost,
        )

        logger.info(
            f"Batch analysis completed: {result.success_count}/{result.total_images} successful "
            f"({result.total_tokens_used} tokens, ${result.total_cost:.4f}, {total_processing_time:.2f}s)"
        )

        return result

    def _parse_vision_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from Vision API.

        Args:
            response_text: Raw response text

        Returns:
            Parsed dictionary

        Raises:
            JSONParseError: If parsing fails
        """
        try:
            # Try to find JSON in response (may be wrapped in markdown)
            response_text = response_text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first and last lines (```)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = "\n".join(lines)

            # Parse JSON
            data = json.loads(response_text)
            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise JSONParseError(f"Failed to parse JSON response: {str(e)}")

    def estimate_cost(self, num_images: int, avg_image_size_kb: float = 500) -> float:
        """
        Estimate the cost of analyzing a batch of images.

        Args:
            num_images: Number of images to analyze
            avg_image_size_kb: Average image size in KB

        Returns:
            Estimated cost in USD
        """
        # Rough estimate:
        # - Image encoding: ~1000 tokens per image
        # - Text prompt: ~200 tokens
        # - Response: ~500 tokens
        # Total: ~1700 tokens per image (input ~1200, output ~500)

        estimated_input_tokens = num_images * 1200
        estimated_output_tokens = num_images * 500

        total_cost = self.vision_client.calculate_cost(
            estimated_input_tokens, estimated_output_tokens
        )

        return total_cost

    def get_analysis_summary(self, result: ImageAnalysisBatchResult) -> str:
        """
        Generate a text summary of batch analysis results.

        Args:
            result: ImageAnalysisBatchResult object

        Returns:
            Formatted summary text
        """
        summary_lines = [
            "=" * 60,
            "Image Analysis Summary",
            "=" * 60,
            f"Total Images: {result.total_images}",
            f"Successful: {result.success_count}",
            f"Failed: {result.failure_count}",
            f"Processing Time: {result.total_processing_time:.2f}s",
            f"Total Tokens: {result.total_tokens_used:,}",
            f"Total Cost: ${result.total_cost:.4f}",
            "",
            "Screen Types:",
        ]

        # Count screen types
        screen_types = {}
        for analysis in result.analyses:
            screen_type = analysis.screen_type
            screen_types[screen_type] = screen_types.get(screen_type, 0) + 1

        for screen_type, count in sorted(screen_types.items()):
            summary_lines.append(f"  - {screen_type}: {count}")

        summary_lines.append("")
        summary_lines.append("Screens Analyzed:")
        for i, analysis in enumerate(result.analyses, 1):
            title = analysis.screen_title or "Unknown"
            summary_lines.append(
                f"  {i}. {title} (page {analysis.page_number}, "
                f"{len(analysis.ui_components)} components, "
                f"confidence: {analysis.confidence:.0f}%)"
            )

        summary_lines.append("=" * 60)

        return "\n".join(summary_lines)
