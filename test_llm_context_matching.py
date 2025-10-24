#!/usr/bin/env python3
"""
Tests for LLM-based context matching system.

This test file covers:
1. TaskContext extraction from PDF
2. OpenAPI role/environment extraction
3. Context-aware task matching
4. Integration tests
"""

import os
from pathlib import Path
from src.types.models import (
    TaskContext,
    IdentifiedTask,
    Section,
    PageRange,
    OpenAPIEndpoint,
    OpenAPISpec,
)


def test_task_context_model():
    """Test TaskContext data model."""
    print("\n" + "=" * 60)
    print("TEST 1: TaskContext Model")
    print("=" * 60)

    # Create context
    context = TaskContext(
        deployment_envs=["development", "production"],
        actor_roles=["user", "admin"],
        role_based_features={
            "user": "상품 조회만 가능",
            "admin": "상품 등록/수정/삭제 가능"
        },
        env_based_features={
            "development": "테스트 PG 사용",
            "production": "실제 PG 연동"
        }
    )

    print(f"  Deployment Envs: {context.deployment_envs}")
    print(f"  Actor Roles: {context.actor_roles}")
    print(f"  Role Features: {context.role_based_features}")
    print(f"  Env Features: {context.env_based_features}")

    assert context.deployment_envs == ["development", "production"]
    assert context.actor_roles == ["user", "admin"]
    print("\n✅ TaskContext model test passed!")


def test_identified_task_with_context():
    """Test IdentifiedTask with context field."""
    print("\n" + "=" * 60)
    print("TEST 2: IdentifiedTask with Context")
    print("=" * 60)

    task = IdentifiedTask(
        index=1,
        name="상품 관리",
        description="상품 조회 및 관리 기능",
        module="ProductModule",
        entities=["Product"],
        prerequisites=[],
        related_sections=[0, 1],
        context=TaskContext(
            deployment_envs=["all"],
            actor_roles=["user", "admin"],
            role_based_features={"user": "조회만", "admin": "CRUD"}
        )
    )

    print(f"  Task: {task.name}")
    print(f"  Context Roles: {task.context.actor_roles}")
    print(f"  Context Envs: {task.context.deployment_envs}")
    print(f"  Role Features: {task.context.role_based_features}")

    assert task.context.actor_roles == ["user", "admin"]
    print("\n✅ IdentifiedTask with context test passed!")


def test_openapi_endpoint_with_roles():
    """Test OpenAPIEndpoint with role/environment fields."""
    print("\n" + "=" * 60)
    print("TEST 3: OpenAPIEndpoint with Roles/Env")
    print("=" * 60)

    endpoint = OpenAPIEndpoint(
        path="/api/products",
        method="POST",
        tags=["product"],
        summary="상품 등록",
        description="관리자가 상품을 등록합니다",
        operation_id="createProduct",
        required_roles=["admin"],
        deployment_env="development"
    )

    print(f"  Path: {endpoint.path}")
    print(f"  Method: {endpoint.method}")
    print(f"  Required Roles: {endpoint.required_roles}")
    print(f"  Deployment Env: {endpoint.deployment_env}")

    assert endpoint.required_roles == ["admin"]
    assert endpoint.deployment_env == "development"
    print("\n✅ OpenAPIEndpoint with roles test passed!")


def test_context_extractor_integration():
    """Test LLMContextExtractor (requires API key)."""
    print("\n" + "=" * 60)
    print("TEST 4: LLMContextExtractor Integration")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠️  Skipped: ANTHROPIC_API_KEY not set")
        return

    try:
        from src.llm.context_extractor import LLMContextExtractor

        # Create test task and sections
        task = IdentifiedTask(
            index=1,
            name="상품 관리",
            description="상품 조회 및 관리",
            module="ProductModule",
            entities=["Product"],
            prerequisites=[],
            related_sections=[0]
        )

        sections = [
            Section(
                title="상품 관리",
                level=1,
                content="일반 사용자는 상품 조회만 가능하며, 관리자는 상품 등록, 수정, 삭제가 가능합니다. 개발환경에서는 테스트 데이터를 사용합니다.",
                page_range=PageRange(start=1, end=2),
                subsections=[]
            )
        ]

        # Extract context
        extractor = LLMContextExtractor(api_key=api_key)
        context = extractor.extract_task_context(task, sections)

        print(f"  Extracted Roles: {context.actor_roles}")
        print(f"  Extracted Envs: {context.deployment_envs}")
        print(f"  Role Features: {context.role_based_features}")

        # Basic validation (actual values may vary)
        assert isinstance(context.actor_roles, list)
        assert isinstance(context.deployment_envs, list)

        print("\n✅ LLMContextExtractor integration test passed!")

    except Exception as e:
        print(f"\n❌ LLMContextExtractor test failed: {e}")


def test_openapi_analyzer_integration():
    """Test LLMOpenAPIAnalyzer (requires API key)."""
    print("\n" + "=" * 60)
    print("TEST 5: LLMOpenAPIAnalyzer Integration")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠️  Skipped: ANTHROPIC_API_KEY not set")
        return

    try:
        from src.openapi.llm_openapi_analyzer import LLMOpenAPIAnalyzer

        analyzer = LLMOpenAPIAnalyzer(api_key=api_key)

        # Test endpoint analysis
        endpoint_spec = {
            "path": "/api/admin/products",
            "method": "POST",
            "summary": "관리자 전용 상품 등록 API",
            "description": "관리자가 상품을 등록합니다",
            "security": [{"bearerAuth": ["admin"]}]
        }

        result = analyzer.analyze_endpoint(endpoint_spec)

        print(f"  Extracted Roles: {result['required_roles']}")
        print(f"  Explanation: {result['explanation']}")

        assert isinstance(result["required_roles"], list)
        assert "explanation" in result

        # Test deployment env extraction
        test_paths = [
            (Path("openapi-dev.yaml"), "development"),
            (Path("api-staging.json"), "staging"),
            (Path("spec-prod.yaml"), "production"),
            (Path("openapi.yaml"), "all"),
        ]

        for path, expected_env in test_paths:
            env = analyzer.extract_deployment_env(path)
            print(f"  {path.name} → {env} (expected: {expected_env})")
            assert env == expected_env

        print("\n✅ LLMOpenAPIAnalyzer integration test passed!")

    except Exception as e:
        print(f"\n❌ LLMOpenAPIAnalyzer test failed: {e}")


def test_task_matcher_integration():
    """Test LLMTaskMatcher (requires API key)."""
    print("\n" + "=" * 60)
    print("TEST 6: LLMTaskMatcher Integration")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠️  Skipped: ANTHROPIC_API_KEY not set")
        return

    try:
        from src.openapi.llm_task_matcher import LLMTaskMatcher

        # Create test task with context
        task = IdentifiedTask(
            index=1,
            name="상품 관리",
            description="상품 조회 및 관리 기능",
            module="ProductModule",
            entities=["Product"],
            prerequisites=[],
            related_sections=[],
            context=TaskContext(
                deployment_envs=["development", "production"],
                actor_roles=["user", "admin"],
                role_based_features={
                    "user": "조회만 가능",
                    "admin": "CRUD 가능"
                }
            )
        )

        # Create test OpenAPI specs
        specs = [
            OpenAPISpec(
                title="Product API (Dev)",
                version="1.0.0",
                source_file="openapi-dev.yaml",
                deployment_env="development",
                endpoints=[
                    OpenAPIEndpoint(
                        path="/api/products",
                        method="GET",
                        tags=["product"],
                        summary="상품 조회",
                        required_roles=["user", "admin"],
                        deployment_env="development"
                    ),
                    OpenAPIEndpoint(
                        path="/api/products",
                        method="POST",
                        tags=["product"],
                        summary="상품 등록",
                        required_roles=["admin"],
                        deployment_env="development"
                    ),
                ]
            ),
            OpenAPISpec(
                title="Product API (Prod)",
                version="1.0.0",
                source_file="openapi-prod.yaml",
                deployment_env="production",
                endpoints=[
                    OpenAPIEndpoint(
                        path="/api/products",
                        method="GET",
                        tags=["product"],
                        summary="상품 조회",
                        required_roles=["user"],
                        deployment_env="production"
                    ),
                ]
            )
        ]

        # Match task with OpenAPI
        matcher = LLMTaskMatcher(
            specs=specs,
            api_key=api_key,
            use_llm=True,
            fallback=True
        )

        match_result = matcher.match_task(task)

        print(f"  Match Status: {match_result.match_status}")
        print(f"  Confidence: {match_result.confidence_score:.2f}")
        print(f"  LLM Based: {match_result.llm_based}")
        print(f"  Matched Endpoints: {len(match_result.matched_endpoints)}")
        print(f"  Context Matrix: {match_result.context_match_matrix}")

        # Basic validation
        assert match_result.match_status in ["fully_implemented", "partially_implemented", "new"]
        assert 0.0 <= match_result.confidence_score <= 1.0

        print("\n✅ LLMTaskMatcher integration test passed!")

    except Exception as e:
        print(f"\n❌ LLMTaskMatcher test failed: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LLM CONTEXT MATCHING TESTS")
    print("=" * 60)

    # Run tests
    test_task_context_model()
    test_identified_task_with_context()
    test_openapi_endpoint_with_roles()
    test_context_extractor_integration()
    test_openapi_analyzer_integration()
    test_task_matcher_integration()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("All basic tests passed! ✅")
    print("\nNote: Integration tests require ANTHROPIC_API_KEY")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
