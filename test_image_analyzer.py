"""Test script for ImageAnalyzer module."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.llm.image_analyzer import ImageAnalyzer
from src.llm.vision_client import VisionClient
from src.llm.vision_prompts import (
    build_vision_analysis_prompt,
    validate_vision_response,
    estimate_vision_tokens,
)
from src.types.models import ExtractedImage


def test_vision_prompts():
    """Test prompt generation functions."""
    print("\n" + "=" * 60)
    print("Test 1: Vision Prompts")
    print("=" * 60)

    # Test basic prompt
    prompt = build_vision_analysis_prompt()
    assert "JSON" in prompt
    assert "screen_title" in prompt
    assert "ui_components" in prompt
    print("✓ Basic prompt generation OK")

    # Test with context
    prompt_with_context = build_vision_analysis_prompt(context="로그인 기능 설명")
    assert "로그인" in prompt_with_context
    print("✓ Prompt with context OK")

    # Test token estimation
    tokens = estimate_vision_tokens(500)
    assert tokens > 0
    print(f"✓ Token estimation OK (500KB image ≈ {tokens} tokens)")

    # Test response validation
    valid_response = {
        "screen_title": "로그인 화면",
        "screen_type": "login",
        "ui_components": [
            {
                "type": "input",
                "label": "이메일",
                "position": "center",
                "description": "이메일 입력 필드",
            }
        ],
        "layout_structure": "중앙 정렬 폼",
        "confidence": 95,
    }
    assert validate_vision_response(valid_response) is True
    print("✓ Response validation OK")

    # Test invalid response
    invalid_response = {"screen_type": "login"}  # Missing required fields
    assert validate_vision_response(invalid_response) is False
    print("✓ Invalid response detection OK")


def test_vision_client_encoding():
    """Test VisionClient image encoding."""
    print("\n" + "=" * 60)
    print("Test 2: VisionClient Image Encoding")
    print("=" * 60)

    # Create a test image (1x1 PNG)
    import base64

    # Minimal PNG (1x1 transparent pixel)
    minimal_png = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )

    test_image_path = Path("test_image.png")
    with open(test_image_path, "wb") as f:
        f.write(minimal_png)

    try:
        # Skip API key requirement for encoding test
        os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
        client = VisionClient()

        # Test encoding
        encoded = client.encode_image(str(test_image_path))
        assert "media_type" in encoded
        assert "data" in encoded
        assert encoded["media_type"] == "image/png"
        print("✓ Image encoding OK")

        # Test image info
        info = client.get_image_info(str(test_image_path))
        assert info["format"] == ".png"
        assert info["size_bytes"] > 0
        print(f"✓ Image info OK (size: {info['size_bytes']} bytes)")

    finally:
        # Clean up
        if test_image_path.exists():
            test_image_path.unlink()
        print("✓ Cleanup OK")


def test_image_analyzer_integration():
    """Test ImageAnalyzer with real API (requires API key)."""
    print("\n" + "=" * 60)
    print("Test 3: ImageAnalyzer Integration (requires API key)")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ Skipping integration test (no API key)")
        return

    # Create a test image
    import base64

    minimal_png = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )

    test_image_path = Path("test_screen.png")
    with open(test_image_path, "wb") as f:
        f.write(minimal_png)

    try:
        analyzer = ImageAnalyzer(api_key=api_key)

        # Test single image analysis
        print("\nAnalyzing single image...")
        result = analyzer.analyze_image(
            image_path=str(test_image_path),
            page_number=1,
            context="테스트 화면",
        )

        print(f"✓ Analysis completed")
        print(f"  Screen Type: {result.screen_type}")
        print(f"  Components: {len(result.ui_components)}")
        print(f"  Confidence: {result.confidence}%")
        print(f"  Tokens: {result.token_usage.total_tokens}")
        print(f"  Time: {result.processing_time:.2f}s")

        # Test batch analysis
        print("\nTesting batch analysis...")
        images = [
            ExtractedImage(
                page_number=1,
                image_path=str(test_image_path),
                width=100,
                height=100,
            )
        ]

        batch_result = analyzer.analyze_batch(images, max_concurrent=1)
        print(f"✓ Batch analysis completed")
        print(f"  Total: {batch_result.total_images}")
        print(f"  Success: {batch_result.success_count}")
        print(f"  Cost: ${batch_result.total_cost:.4f}")

        # Test summary
        summary = analyzer.get_analysis_summary(batch_result)
        print(f"\n✓ Summary generated")
        print(summary)

    finally:
        # Clean up
        if test_image_path.exists():
            test_image_path.unlink()


def test_cost_estimation():
    """Test cost estimation."""
    print("\n" + "=" * 60)
    print("Test 4: Cost Estimation")
    print("=" * 60)

    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    analyzer = ImageAnalyzer()

    # Estimate cost for 10 images
    cost_10 = analyzer.estimate_cost(num_images=10)
    print(f"✓ Estimated cost for 10 images: ${cost_10:.4f}")

    # Estimate cost for 50 images
    cost_50 = analyzer.estimate_cost(num_images=50)
    print(f"✓ Estimated cost for 50 images: ${cost_50:.4f}")

    # Estimate cost for 100 images
    cost_100 = analyzer.estimate_cost(num_images=100)
    print(f"✓ Estimated cost for 100 images: ${cost_100:.4f}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ImageAnalyzer Test Suite")
    print("=" * 60)

    try:
        # Unit tests (no API key required)
        test_vision_prompts()
        test_vision_client_encoding()
        test_cost_estimation()

        # Integration test (requires API key)
        test_image_analyzer_integration()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
