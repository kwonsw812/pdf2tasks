#!/usr/bin/env python3
"""
Test script for OpenAPI integration.

Tests:
1. OpenAPI file loading
2. Spec parsing
3. Task matching
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.openapi.loader import OpenAPILoader
from src.openapi.parser import OpenAPIParser
from src.openapi.matcher import TaskMatcher
from src.types.models import IdentifiedTask


def test_loader():
    """Test OpenAPI file loading."""
    print("\n" + "=" * 60)
    print("TEST 1: OpenAPI File Loading")
    print("=" * 60)

    loader = OpenAPILoader("./openapi")

    # Find files
    files = loader.find_spec_files()
    print(f"\nFound {len(files)} OpenAPI files:")
    for file in files:
        print(f"  - {file.name}")

    # Load all specs
    specs = loader.load_all_specs()
    print(f"\nSuccessfully loaded {len(specs)} specs")

    for spec in specs:
        title = spec.get('info', {}).get('title', 'Unknown')
        version = spec.get('info', {}).get('version', 'Unknown')
        print(f"  - {title} v{version}")

    print("\n✓ TEST 1 PASSED\n")
    return specs


def test_parser(spec_dicts):
    """Test OpenAPI spec parsing."""
    print("\n" + "=" * 60)
    print("TEST 2: OpenAPI Spec Parsing")
    print("=" * 60)

    parser = OpenAPIParser()
    specs = []

    for spec_dict in spec_dicts:
        spec = parser.parse(spec_dict)
        specs.append(spec)
        print(f"\nParsed: {spec.title} v{spec.version}")
        print(f"  Endpoints: {len(spec.endpoints)}")
        print(f"  Sample endpoints:")
        for endpoint in spec.endpoints[:3]:  # Show first 3
            print(f"    {endpoint.method} {endpoint.path}")
            if endpoint.tags:
                print(f"      Tags: {', '.join(endpoint.tags)}")

    print("\n✓ TEST 2 PASSED\n")
    return specs


def test_matcher(specs):
    """Test task matching."""
    print("\n" + "=" * 60)
    print("TEST 3: Task Matching")
    print("=" * 60)

    # Create sample tasks
    sample_tasks = [
        IdentifiedTask(
            index=1,
            name="상품 관리",
            description="상품 등록, 수정, 삭제 기능",
            module="ProductModule",
            entities=["Product", "Category"],
            prerequisites=[],
            related_sections=[1, 2],
        ),
        IdentifiedTask(
            index=2,
            name="주문 처리",
            description="주문 생성 및 관리",
            module="OrderModule",
            entities=["Order", "OrderItem"],
            prerequisites=[],
            related_sections=[3, 4],
        ),
        IdentifiedTask(
            index=3,
            name="사용자 인증",
            description="로그인 및 회원가입",
            module="AuthModule",
            entities=["User", "Session"],
            prerequisites=[],
            related_sections=[5],
        ),
        IdentifiedTask(
            index=4,
            name="새로운 기능",
            description="완전히 새로운 기능",
            module="NewFeatureModule",
            entities=["NewEntity"],
            prerequisites=[],
            related_sections=[6],
        ),
    ]

    # Match tasks
    matcher = TaskMatcher(specs)

    print(f"\nMatching {len(sample_tasks)} tasks against {len(matcher.all_endpoints)} endpoints...\n")

    for task in sample_tasks:
        result = matcher.match_task(task)
        print(f"Task: {task.name}")
        print(f"  Status: {result.match_status}")
        print(f"  Confidence: {result.confidence_score:.2f}")
        print(f"  Matched endpoints: {len(result.matched_endpoints)}")
        if result.matched_endpoints:
            print(f"  Sample matches:")
            for endpoint in result.matched_endpoints[:2]:
                print(f"    - {endpoint.method} {endpoint.path}")
        print()

    print("✓ TEST 3 PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OPENAPI INTEGRATION TEST SUITE")
    print("=" * 60)

    try:
        # Test 1: Load specs
        spec_dicts = test_loader()

        if not spec_dicts:
            print("⚠ No OpenAPI specs found. Please add some .yaml or .json files to ./openapi/")
            return

        # Test 2: Parse specs
        specs = test_parser(spec_dicts)

        # Test 3: Match tasks
        test_matcher(specs)

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
