"""Batch OCR processing with concurrent execution."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable
from ..types.models import OCRResult, OCRBatchResult
from ..utils.logger import get_logger
from .recognizer import OCRRecognizer
from .exceptions import OCRError

logger = get_logger(__name__)


class BatchOCRProcessor:
    """Process multiple images with OCR concurrently."""

    def __init__(
        self,
        recognizer: Optional[OCRRecognizer] = None,
        max_workers: int = 2,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """
        Initialize BatchOCRProcessor.

        Args:
            recognizer: OCRRecognizer instance (default: create new)
            max_workers: Maximum number of concurrent workers (default: 2)
            progress_callback: Callback function for progress updates (current, total)
        """
        self.recognizer = recognizer or OCRRecognizer()
        self.max_workers = max_workers
        self.progress_callback = progress_callback

        logger.info(
            f"BatchOCRProcessor initialized: max_workers={max_workers}, "
            f"recognizer={self.recognizer}"
        )

    def process_batch(self, image_paths: list[str]) -> OCRBatchResult:
        """
        Process multiple images with OCR.

        Args:
            image_paths: List of image file paths

        Returns:
            OCRBatchResult with all results

        Raises:
            OCRError: If all images fail to process
        """
        if not image_paths:
            logger.warning("Empty image list provided")
            return OCRBatchResult(
                results=[],
                image_paths=[],
                total_processing_time=0.0,
                average_confidence=0.0,
                success_count=0,
                failure_count=0,
            )

        logger.info(f"Starting batch OCR on {len(image_paths)} images...")
        start_time = time.time()

        results = []
        processed_paths = []
        success_count = 0
        failure_count = 0
        total_confidence = 0.0

        # Process images concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self._process_single, path): path
                for path in image_paths
            }

            # Process results as they complete
            for i, future in enumerate(as_completed(future_to_path), 1):
                image_path = future_to_path[future]

                try:
                    result = future.result()
                    results.append(result)
                    processed_paths.append(image_path)
                    total_confidence += result.confidence
                    success_count += 1

                    logger.info(
                        f"Processed {i}/{len(image_paths)}: {image_path} "
                        f"(confidence={result.confidence:.2f}%)"
                    )

                except Exception as e:
                    logger.error(f"Failed to process {image_path}: {e}")
                    failure_count += 1

                # Call progress callback
                if self.progress_callback:
                    self.progress_callback(i, len(image_paths))

        # Calculate statistics
        total_processing_time = time.time() - start_time
        average_confidence = (
            total_confidence / success_count if success_count > 0 else 0.0
        )

        batch_result = OCRBatchResult(
            results=results,
            image_paths=processed_paths,
            total_processing_time=total_processing_time,
            average_confidence=average_confidence,
            success_count=success_count,
            failure_count=failure_count,
        )

        logger.info(
            f"Batch OCR completed: {success_count} succeeded, {failure_count} failed, "
            f"avg_confidence={average_confidence:.2f}%, time={total_processing_time:.2f}s"
        )

        # Check if all failed
        if success_count == 0:
            raise OCRError("All images failed to process")

        return batch_result

    def _process_single(self, image_path: str) -> OCRResult:
        """
        Process a single image (called by thread pool).

        Args:
            image_path: Path to image file

        Returns:
            OCRResult

        Raises:
            Exception: If processing fails
        """
        return self.recognizer.recognize(image_path)

    def process_batch_sequential(self, image_paths: list[str]) -> OCRBatchResult:
        """
        Process multiple images sequentially (no concurrency).

        Useful for debugging or when thread safety is a concern.

        Args:
            image_paths: List of image file paths

        Returns:
            OCRBatchResult with all results
        """
        if not image_paths:
            logger.warning("Empty image list provided")
            return OCRBatchResult(
                results=[],
                image_paths=[],
                total_processing_time=0.0,
                average_confidence=0.0,
                success_count=0,
                failure_count=0,
            )

        logger.info(f"Starting sequential batch OCR on {len(image_paths)} images...")
        start_time = time.time()

        results = []
        processed_paths = []
        success_count = 0
        failure_count = 0
        total_confidence = 0.0

        for i, image_path in enumerate(image_paths, 1):
            try:
                result = self.recognizer.recognize(image_path)
                results.append(result)
                processed_paths.append(image_path)
                total_confidence += result.confidence
                success_count += 1

                logger.info(
                    f"Processed {i}/{len(image_paths)}: {image_path} "
                    f"(confidence={result.confidence:.2f}%)"
                )

            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                failure_count += 1

            # Call progress callback
            if self.progress_callback:
                self.progress_callback(i, len(image_paths))

        # Calculate statistics
        total_processing_time = time.time() - start_time
        average_confidence = (
            total_confidence / success_count if success_count > 0 else 0.0
        )

        batch_result = OCRBatchResult(
            results=results,
            image_paths=processed_paths,
            total_processing_time=total_processing_time,
            average_confidence=average_confidence,
            success_count=success_count,
            failure_count=failure_count,
        )

        logger.info(
            f"Sequential batch OCR completed: {success_count} succeeded, {failure_count} failed, "
            f"avg_confidence={average_confidence:.2f}%, time={total_processing_time:.2f}s"
        )

        # Check if all failed
        if success_count == 0:
            raise OCRError("All images failed to process")

        return batch_result

    def set_progress_callback(
        self, callback: Callable[[int, int], None]
    ) -> None:
        """
        Set progress callback function.

        Args:
            callback: Function that takes (current, total) as arguments
        """
        self.progress_callback = callback
        logger.info("Progress callback set")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"BatchOCRProcessor(max_workers={self.max_workers}, "
            f"recognizer={self.recognizer})"
        )
