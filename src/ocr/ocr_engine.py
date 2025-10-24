"""Unified OCR Engine interface."""

import os
import time
from typing import Optional, Callable
from ..types.models import OCRResult, OCRBatchResult
from ..utils.logger import get_logger
from .config import TesseractConfig, get_default_config
from .preprocessor import ImagePreprocessor, create_default_preprocessor
from .recognizer import OCRRecognizer
from .postprocessor import OCRPostprocessor, create_default_postprocessor
from .batch_processor import BatchOCRProcessor
from .exceptions import OCRError

logger = get_logger(__name__)


class OCREngine:
    """Unified OCR engine with preprocessing, recognition, and postprocessing."""

    def __init__(
        self,
        config: Optional[TesseractConfig] = None,
        preprocessor: Optional[ImagePreprocessor] = None,
        postprocessor: Optional[OCRPostprocessor] = None,
        use_preprocessing: bool = True,
        use_postprocessing: bool = True,
        max_workers: int = 2,
        include_words: bool = False,
    ):
        """
        Initialize OCREngine.

        Args:
            config: Tesseract configuration (default: auto-detect)
            preprocessor: Image preprocessor (default: create default)
            postprocessor: Result postprocessor (default: create default)
            use_preprocessing: Enable preprocessing (default: True)
            use_postprocessing: Enable postprocessing (default: True)
            max_workers: Max concurrent workers for batch processing (default: 2)
            include_words: Include word-level details (default: False)
        """
        self.config = config or get_default_config()
        self.preprocessor = preprocessor or create_default_preprocessor()
        self.postprocessor = postprocessor or create_default_postprocessor()
        self.use_preprocessing = use_preprocessing
        self.use_postprocessing = use_postprocessing
        self.include_words = include_words

        # Initialize recognizer
        self.recognizer = OCRRecognizer(
            config=self.config,
            include_words=include_words,
        )

        # Initialize batch processor
        self.batch_processor = BatchOCRProcessor(
            recognizer=self.recognizer,
            max_workers=max_workers,
        )

        # Temporary files to clean up
        self._temp_files = []

        logger.info(
            f"OCREngine initialized: "
            f"preprocessing={use_preprocessing}, "
            f"postprocessing={use_postprocessing}, "
            f"max_workers={max_workers}, "
            f"include_words={include_words}"
        )

    def process_image(self, image_path: str) -> OCRResult:
        """
        Process a single image through the complete OCR pipeline.

        Pipeline: Preprocess -> Recognize -> Postprocess

        Args:
            image_path: Path to image file

        Returns:
            OCRResult with recognized and processed text

        Raises:
            OCRError: If processing fails
        """
        logger.info(f"Processing image: {image_path}")
        start_time = time.time()

        try:
            # Step 1: Preprocess
            if self.use_preprocessing:
                logger.info("Step 1/3: Preprocessing image")
                preprocessed_path = self.preprocessor.preprocess(image_path)
                self._temp_files.append(preprocessed_path)
                processing_path = preprocessed_path
            else:
                processing_path = image_path

            # Step 2: Recognize
            logger.info("Step 2/3: Recognizing text")
            result = self.recognizer.recognize(processing_path)

            # Step 3: Postprocess
            if self.use_postprocessing:
                logger.info("Step 3/3: Postprocessing result")
                result = self.postprocessor.postprocess(result)

            total_time = time.time() - start_time
            logger.info(
                f"Image processing complete: "
                f"confidence={result.confidence:.2f}%, "
                f"chars={len(result.text)}, "
                f"total_time={total_time:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise OCRError(f"Failed to process image: {str(e)}")

    def process_images(
        self,
        image_paths: list[str],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> OCRBatchResult:
        """
        Process multiple images through the complete OCR pipeline.

        Args:
            image_paths: List of image file paths
            progress_callback: Optional callback for progress updates (current, total)

        Returns:
            OCRBatchResult with all processed results

        Raises:
            OCRError: If all images fail to process
        """
        logger.info(f"Processing {len(image_paths)} images...")
        start_time = time.time()

        try:
            # Step 1: Preprocess all images
            if self.use_preprocessing:
                logger.info("Step 1/3: Preprocessing images")
                preprocessed_paths = self.preprocessor.preprocess_batch(image_paths)
                self._temp_files.extend(preprocessed_paths)
                processing_paths = preprocessed_paths
            else:
                processing_paths = image_paths

            # Step 2: Batch OCR
            logger.info("Step 2/3: Recognizing text (batch)")
            self.batch_processor.set_progress_callback(progress_callback)
            batch_result = self.batch_processor.process_batch(processing_paths)

            # Step 3: Postprocess results
            if self.use_postprocessing:
                logger.info("Step 3/3: Postprocessing results")
                batch_result.results = self.postprocessor.postprocess_batch(
                    batch_result.results
                )

                # Recalculate average confidence after postprocessing
                if batch_result.results:
                    total_conf = sum(r.confidence for r in batch_result.results)
                    batch_result.average_confidence = (
                        total_conf / len(batch_result.results)
                    )

            total_time = time.time() - start_time
            logger.info(
                f"Batch processing complete: "
                f"{batch_result.success_count} succeeded, "
                f"{batch_result.failure_count} failed, "
                f"avg_confidence={batch_result.average_confidence:.2f}%, "
                f"total_time={total_time:.2f}s"
            )

            return batch_result

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise OCRError(f"Failed to process images: {str(e)}")

    def process_pdf_images(
        self,
        image_paths: list[str],
        page_numbers: Optional[list[int]] = None,
    ) -> dict[int, OCRResult]:
        """
        Process images extracted from PDF pages.

        Args:
            image_paths: List of image file paths
            page_numbers: Corresponding page numbers (default: auto-number from 1)

        Returns:
            Dictionary mapping page numbers to OCR results

        Raises:
            OCRError: If processing fails
        """
        if page_numbers is None:
            page_numbers = list(range(1, len(image_paths) + 1))

        if len(image_paths) != len(page_numbers):
            raise OCRError(
                f"Mismatch: {len(image_paths)} images but {len(page_numbers)} page numbers"
            )

        logger.info(f"Processing {len(image_paths)} PDF page images...")

        batch_result = self.process_images(image_paths)

        # Map results to page numbers
        page_results = {}
        for page_num, result in zip(page_numbers, batch_result.results):
            page_results[page_num] = result

        logger.info(f"PDF page OCR complete: {len(page_results)} pages processed")

        return page_results

    def cleanup(self) -> None:
        """Remove temporary preprocessed files."""
        logger.info(f"Cleaning up {len(self._temp_files)} temporary files...")

        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Removed: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove {temp_file}: {e}")

        self._temp_files.clear()
        logger.info("Cleanup complete")

    def get_config_info(self) -> dict:
        """
        Get configuration information.

        Returns:
            Dictionary with configuration details
        """
        return {
            "tesseract_config": repr(self.config),
            "preprocessing_enabled": self.use_preprocessing,
            "postprocessing_enabled": self.use_postprocessing,
            "max_workers": self.batch_processor.max_workers,
            "include_words": self.include_words,
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temporary files."""
        self.cleanup()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OCREngine(preprocessing={self.use_preprocessing}, "
            f"postprocessing={self.use_postprocessing}, "
            f"workers={self.batch_processor.max_workers})"
        )


def create_ocr_engine(
    lang: str = "kor+eng",
    preprocessing: bool = True,
    postprocessing: bool = True,
    max_workers: int = 2,
) -> OCREngine:
    """
    Create an OCR engine with common settings.

    Args:
        lang: Language code (default: 'kor+eng')
        preprocessing: Enable preprocessing (default: True)
        postprocessing: Enable postprocessing (default: True)
        max_workers: Max concurrent workers (default: 2)

    Returns:
        Configured OCREngine instance
    """
    config = TesseractConfig(lang=lang)

    return OCREngine(
        config=config,
        use_preprocessing=preprocessing,
        use_postprocessing=postprocessing,
        max_workers=max_workers,
    )
