"""Run full pipeline with LLM preprocessing and generate detailed report."""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from src.cli.orchestrator import Orchestrator, OrchestratorConfig

# Load API key
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not found in .env")
    exit(1)

print("=" * 80)
print("RUNNING FULL PIPELINE WITH LLM PREPROCESSING")
print("=" * 80)
print(f"\nPDF: test_pdf.pdf")
print(f"Output: ./test_full_pipeline")
print(f"LLM Model: claude-3-5-sonnet-20241022")
print(f"Preprocessing: LLM-based (default)")
print("\n" + "=" * 80)

# Create configuration
config = OrchestratorConfig(
    pdf_path="test_pdf.pdf",
    output_dir="./test_full_pipeline",
    extract_images=False,
    extract_tables=True,
    use_ocr=False,
    analyze_images=False,
    clean_output=True,
    add_front_matter=True,
    api_key=api_key,
    model="claude-3-5-sonnet-20241022",
    verbose=True,
    use_llm_preprocessing=True,  # LLM-based (default)
)

# Run orchestrator
start_time = time.time()
orchestrator = Orchestrator(config)
report = orchestrator.run()
total_time = time.time() - start_time

print("\n" + "=" * 80)
print("PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 80)
print(f"\nGenerated {len(report.output_files)} task files")
print(f"Total processing time: {total_time:.2f}s")
print(f"Total cost: ${report.llm.total_cost:.6f}")
print(f"Total tokens: {report.llm.total_tokens_used:,}")

# List generated files
print(f"\nGenerated files in ./test_full_pipeline:")
for file_info in report.output_files:
    print(f"  - {file_info.file_name} ({file_info.size_bytes:,} bytes)")

print("\n" + "=" * 80)
print("Check intermediate results in: ./test_full_pipeline/_intermediate/")
print("=" * 80)
