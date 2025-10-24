"""OCR Engine usage examples."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ocr import (
    OCREngine,
    create_ocr_engine,
    TesseractConfig,
    ImagePreprocessor,
    OCRPostprocessor,
)


def example1_basic_ocr():
    """Example 1: Basic single image OCR."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Single Image OCR")
    print("=" * 60)

    # Create OCR engine with default settings
    engine = create_ocr_engine()

    # Process image
    result = engine.process_image("path/to/your/image.png")

    print(f"Recognized text:\n{result.text}")
    print(f"Confidence: {result.confidence:.2f}%")

    # Don't forget to cleanup
    engine.cleanup()


def example2_batch_processing():
    """Example 2: Batch process multiple images."""
    print("\n" + "=" * 60)
    print("Example 2: Batch OCR Processing")
    print("=" * 60)

    # List of images to process
    image_paths = [
        "image1.png",
        "image2.png",
        "image3.png",
    ]

    # Create OCR engine
    engine = create_ocr_engine(max_workers=4)  # Use 4 parallel workers

    # Progress callback
    def progress(current, total):
        print(f"Progress: {current}/{total}")

    # Process all images
    batch_result = engine.process_images(image_paths, progress_callback=progress)

    print(f"\nBatch Results:")
    print(f"  Success: {batch_result.success_count}")
    print(f"  Failed: {batch_result.failure_count}")
    print(f"  Average Confidence: {batch_result.average_confidence:.2f}%")

    # Access individual results
    for i, result in enumerate(batch_result.results):
        print(f"\nImage {i+1}:")
        print(f"  Text: {result.text[:100]}...")
        print(f"  Confidence: {result.confidence:.2f}%")

    engine.cleanup()


def example3_custom_configuration():
    """Example 3: Custom Tesseract configuration."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Configuration")
    print("=" * 60)

    # Create custom Tesseract config
    config = TesseractConfig(
        lang="eng",  # English only
        oem=TesseractConfig.OEM_LSTM,  # Use LSTM engine
        psm=TesseractConfig.PSM_SINGLE_BLOCK,  # Single block mode
    )

    # Create engine with custom config
    engine = OCREngine(
        config=config,
        use_preprocessing=True,
        use_postprocessing=True,
        include_words=True,  # Include word-level details
    )

    result = engine.process_image("document.png")

    print(f"Text: {result.text}")

    # Access word-level details
    if result.words:
        print(f"\nWord-level details:")
        for word in result.words[:5]:  # First 5 words
            print(f"  '{word.text}': confidence={word.confidence:.1f}%")

    engine.cleanup()


def example4_preprocessing_only():
    """Example 4: Image preprocessing without OCR."""
    print("\n" + "=" * 60)
    print("Example 4: Image Preprocessing Only")
    print("=" * 60)

    # Create preprocessor
    preprocessor = ImagePreprocessor(
        grayscale=True,
        enhance_contrast=True,
        contrast_factor=1.8,  # Higher contrast
        denoise=True,
        sharpen=True,  # Enable sharpening
    )

    # Preprocess image
    preprocessed_path = preprocessor.preprocess(
        "input.png", output_path="preprocessed_output.png"
    )

    print(f"Preprocessed image saved: {preprocessed_path}")

    # Get image info
    info = preprocessor.get_image_info(preprocessed_path)
    print(f"Size: {info['width']}x{info['height']}")
    print(f"Mode: {info['mode']}")


def example5_no_preprocessing():
    """Example 5: OCR without preprocessing."""
    print("\n" + "=" * 60)
    print("Example 5: OCR Without Preprocessing")
    print("=" * 60)

    # Create engine without preprocessing
    # Useful for already-clean images
    engine = create_ocr_engine(
        preprocessing=False,  # Disable preprocessing
        postprocessing=True,
    )

    result = engine.process_image("clean_document.png")

    print(f"Text: {result.text}")
    print(f"Processing time: {result.processing_time:.2f}s")


def example6_custom_postprocessing():
    """Example 6: Custom postprocessing."""
    print("\n" + "=" * 60)
    print("Example 6: Custom Postprocessing")
    print("=" * 60)

    # Create custom postprocessor
    postprocessor = OCRPostprocessor(
        normalize_whitespace=True,
        fix_misrecognition=True,
        filter_low_confidence=True,
        confidence_threshold=50.0,  # Filter words below 50% confidence
        remove_special_chars=False,
    )

    # Create engine with custom postprocessor
    engine = OCREngine(postprocessor=postprocessor)

    result = engine.process_image("noisy_document.png")

    print(f"Cleaned text: {result.text}")
    engine.cleanup()


def example7_context_manager():
    """Example 7: Using context manager for auto-cleanup."""
    print("\n" + "=" * 60)
    print("Example 7: Context Manager for Auto-Cleanup")
    print("=" * 60)

    # Use context manager - automatically cleans up temp files
    with create_ocr_engine() as engine:
        result = engine.process_image("document.png")
        print(f"Text: {result.text[:100]}...")
        print(f"Confidence: {result.confidence:.2f}%")

    # Cleanup happens automatically when exiting the context


def example8_pdf_page_images():
    """Example 8: Process images extracted from PDF pages."""
    print("\n" + "=" * 60)
    print("Example 8: PDF Page Images OCR")
    print("=" * 60)

    # Assume you have extracted images from PDF pages
    page_images = [
        "page_1.png",
        "page_2.png",
        "page_3.png",
    ]

    page_numbers = [1, 2, 3]

    engine = create_ocr_engine()

    # Process PDF page images
    page_results = engine.process_pdf_images(page_images, page_numbers)

    # Access results by page number
    for page_num, result in page_results.items():
        print(f"\nPage {page_num}:")
        print(f"  Confidence: {result.confidence:.2f}%")
        print(f"  Text length: {len(result.text)} chars")

    engine.cleanup()


def example9_sequential_processing():
    """Example 9: Sequential (non-parallel) batch processing."""
    print("\n" + "=" * 60)
    print("Example 9: Sequential Batch Processing")
    print("=" * 60)

    from src.ocr import BatchOCRProcessor, OCRRecognizer

    # Create recognizer
    recognizer = OCRRecognizer()

    # Create batch processor with max_workers=1 for sequential
    processor = BatchOCRProcessor(recognizer=recognizer, max_workers=1)

    image_paths = ["img1.png", "img2.png"]

    # Sequential processing
    result = processor.process_batch_sequential(image_paths)

    print(f"Processed {result.success_count} images sequentially")


def example10_error_handling():
    """Example 10: Proper error handling."""
    print("\n" + "=" * 60)
    print("Example 10: Error Handling")
    print("=" * 60)

    from src.ocr import (
        OCRError,
        ImageLoadError,
        TesseractNotFoundError,
    )

    try:
        engine = create_ocr_engine()
        result = engine.process_image("might_not_exist.png")
        print(f"Success: {result.text[:50]}")

    except TesseractNotFoundError as e:
        print(f"Tesseract not installed: {e}")
        print("Please install Tesseract OCR")

    except ImageLoadError as e:
        print(f"Image load error: {e}")
        print("Check if the image file exists and is valid")

    except OCRError as e:
        print(f"OCR processing error: {e}")

    finally:
        # Always cleanup
        if "engine" in locals():
            engine.cleanup()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("OCR Engine Usage Examples")
    print("=" * 60)

    print("\nNote: These examples require test images to run.")
    print("Replace 'path/to/your/image.png' with actual image paths.")
    print("\nTo run a specific example:")
    print("  python examples/ocr_usage.py")

    # Uncomment the examples you want to run:

    # example1_basic_ocr()
    # example2_batch_processing()
    # example3_custom_configuration()
    # example4_preprocessing_only()
    # example5_no_preprocessing()
    # example6_custom_postprocessing()
    # example7_context_manager()
    # example8_pdf_page_images()
    # example9_sequential_processing()
    # example10_error_handling()

    print("\n Examples defined successfully!")
    print("Uncomment the examples in main() to run them.")


if __name__ == "__main__":
    main()
