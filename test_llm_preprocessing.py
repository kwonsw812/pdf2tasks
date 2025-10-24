"""Test LLM-based preprocessing functionality."""

import os
from dotenv import load_dotenv
from src.cli.orchestrator import Orchestrator, OrchestratorConfig

# Load API key
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not found in .env")
    exit(1)

print("=" * 80)
print("Testing LLM-based Preprocessing")
print("=" * 80)

# Test 1: Rule-based preprocessing
print("\n[Test 1] Rule-based preprocessing (baseline)")
print("-" * 80)

config_rule = OrchestratorConfig(
    pdf_path="test_pdf.pdf",
    output_dir="./test_llm_preprocessing/rule_based",
    extract_images=False,
    extract_tables=True,
    clean_output=True,
    api_key=api_key,
    use_llm_preprocessing=False,  # Rule-based
)

try:
    orchestrator = Orchestrator(config_rule)
    report = orchestrator.run()
    print(f"\n✓ Rule-based preprocessing completed")
    print(f"  - Generated {len(report.output_files)} files")
    print(f"  - Total cost: ${report.llm.total_cost:.6f}")
except Exception as e:
    print(f"\n✗ Rule-based preprocessing failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: LLM-based preprocessing
print("\n" + "=" * 80)
print("[Test 2] LLM-based preprocessing")
print("-" * 80)

config_llm = OrchestratorConfig(
    pdf_path="test_pdf.pdf",
    output_dir="./test_llm_preprocessing/llm_based",
    extract_images=False,
    extract_tables=True,
    clean_output=True,
    api_key=api_key,
    use_llm_preprocessing=True,  # LLM-based ★
)

try:
    orchestrator = Orchestrator(config_llm)
    report = orchestrator.run()
    print(f"\n✓ LLM-based preprocessing completed")
    print(f"  - Generated {len(report.output_files)} files")
    print(f"  - Total cost: ${report.llm.total_cost:.6f}")
except Exception as e:
    print(f"\n✗ LLM-based preprocessing failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Testing completed!")
print("=" * 80)
