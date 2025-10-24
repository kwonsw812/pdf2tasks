"""Test script for OCR Engine."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ocr import (
    OCREngine,
    create_ocr_engine,
    TesseractConfig,
    ImagePreprocessor,
    OCRPostprocessor,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_tesseract_installation():
    """Test 1: Check Tesseract installation."""
    print("\n" + "=" * 60)
    print("Test 1: Tesseract Installation Check")
    print("=" * 60)

    try:
        config = TesseractConfig()
        print(f"✓ Tesseract found at: {config.tesseract_cmd}")
        print(f"✓ Language: {config.lang}")
        print(f"✓ Configuration: {config}")
        return True
    except Exception as e:
        print(f"✗ Tesseract check failed: {e}")
        return False


def test_image_preprocessing(test_image_path: str):
    """Test 2: Image preprocessing."""
    print("\n" + "=" * 60)
    print("Test 2: Image Preprocessing")
    print("=" * 60)

    if not os.path.exists(test_image_path):
        print(f"✗ Test image not found: {test_image_path}")
        print("  Please provide a test image path")
        return False

    try:
        preprocessor = ImagePreprocessor()

        # Get original image info
        info = preprocessor.get_image_info(test_image_path)
        print(f"Original image: {info['width']}x{info['height']}, mode={info['mode']}")

        # Preprocess
        preprocessed_path = preprocessor.preprocess(test_image_path)
        print(f"✓ Preprocessed image saved: {preprocessed_path}")

        # Get preprocessed image info
        info_after = preprocessor.get_image_info(preprocessed_path)
        print(
            f"Preprocessed: {info_after['width']}x{info_after['height']}, mode={info_after['mode']}"
        )

        # Cleanup
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)
            print("✓ Cleanup completed")

        return True
    except Exception as e:
        print(f"✗ Preprocessing failed: {e}")
        return False


def test_single_image_ocr(test_image_path: str):
    """Test 3: Single image OCR."""
    print("\n" + "=" * 60)
    print("Test 3: Single Image OCR")
    print("=" * 60)

    if not os.path.exists(test_image_path):
        print(f"✗ Test image not found: {test_image_path}")
        return False

    try:
        # Create OCR engine with preprocessing and postprocessing
        engine = create_ocr_engine(
            lang="kor+eng",
            preprocessing=True,
            postprocessing=True,
        )

        print(f"Processing: {test_image_path}")

        # Process image
        result = engine.process_image(test_image_path)

        print(f"\n✓ OCR completed successfully!")
        print(f"  Confidence: {result.confidence:.2f}%")
        print(f"  Text length: {len(result.text)} characters")
        print(f"  Processing time: {result.processing_time:.2f}s")

        if result.text:
            print(f"\nRecognized text (first 200 chars):")
            print("-" * 60)
            print(result.text[:200])
            if len(result.text) > 200:
                print(f"... ({len(result.text) - 200} more characters)")
            print("-" * 60)

        # Cleanup
        engine.cleanup()

        return True
    except Exception as e:
        print(f"✗ OCR failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_batch_ocr(test_images: list[str]):
    """Test 4: Batch OCR processing."""
    print("\n" + "=" * 60)
    print("Test 4: Batch OCR Processing")
    print("=" * 60)

    # Filter existing images
    existing_images = [img for img in test_images if os.path.exists(img)]

    if not existing_images:
        print("✗ No test images found")
        return False

    print(f"Processing {len(existing_images)} images...")

    try:
        # Create OCR engine
        engine = create_ocr_engine(
            lang="kor+eng",
            preprocessing=True,
            postprocessing=True,
            max_workers=2,
        )

        # Progress callback
        def progress(current, total):
            print(f"  Progress: {current}/{total} images")

        # Process batch
        batch_result = engine.process_images(existing_images, progress_callback=progress)

        print(f"\n✓ Batch OCR completed!")
        print(f"  Success: {batch_result.success_count}")
        print(f"  Failed: {batch_result.failure_count}")
        print(f"  Average confidence: {batch_result.average_confidence:.2f}%")
        print(f"  Total time: {batch_result.total_processing_time:.2f}s")

        # Show results
        print(f"\nResults:")
        for i, (path, result) in enumerate(
            zip(batch_result.image_paths, batch_result.results), 1
        ):
            filename = os.path.basename(path)
            print(
                f"  {i}. {filename}: {result.confidence:.1f}% "
                f"({len(result.text)} chars)"
            )

        # Cleanup
        engine.cleanup()

        return True
    except Exception as e:
        print(f"✗ Batch OCR failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ocr_without_preprocessing(test_image_path: str):
    """Test 5: OCR without preprocessing."""
    print("\n" + "=" * 60)
    print("Test 5: OCR Without Preprocessing")
    print("=" * 60)

    if not os.path.exists(test_image_path):
        print(f"✗ Test image not found: {test_image_path}")
        return False

    try:
        # Create OCR engine without preprocessing
        engine = create_ocr_engine(
            lang="kor+eng",
            preprocessing=False,  # Disable preprocessing
            postprocessing=True,
        )

        result = engine.process_image(test_image_path)

        print(f"✓ OCR without preprocessing completed!")
        print(f"  Confidence: {result.confidence:.2f}%")
        print(f"  Processing time: {result.processing_time:.2f}s")

        return True
    except Exception as e:
        print(f"✗ OCR failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OCR Engine Test Suite")
    print("=" * 60)

    # Test 1: Check Tesseract installation
    test1_passed = test_tesseract_installation()

    if not test1_passed:
        print("\n⚠️  Tesseract not installed. Please install Tesseract OCR:")
        print("  - macOS: brew install tesseract tesseract-lang")
        print("  - Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-kor")
        print("  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        return

    # Check for test images
    test_image_paths = [
        "./test_data/test_image.png",
        "./test_data/sample.png",
        "./examples/test.png",
        "./temp_images/page_1_rendered.png",
    ]

    # Find first existing test image
    test_image = None
    for path in test_image_paths:
        if os.path.exists(path):
            test_image = path
            break

    if test_image is None:
        print("\n⚠️  No test images found. Tests 2-5 will be skipped.")
        print("  Please provide a test image at one of these locations:")
        for path in test_image_paths:
            print(f"    - {path}")
        print("\n✓ Test 1 passed: Tesseract installation OK")
        return

    print(f"\nUsing test image: {test_image}")

    # Run remaining tests
    test2_passed = test_image_preprocessing(test_image)
    test3_passed = test_single_image_ocr(test_image)
    test4_passed = test_batch_ocr([test_image])  # Batch with single image
    test5_passed = test_ocr_without_preprocessing(test_image)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    results = [
        ("Tesseract Installation", test1_passed),
        ("Image Preprocessing", test2_passed),
        ("Single Image OCR", test3_passed),
        ("Batch OCR", test4_passed),
        ("OCR Without Preprocessing", test5_passed),
    ]

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\n{total_passed}/{len(results)} tests passed")


if __name__ == "__main__":
    main()
