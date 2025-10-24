"""
CLI Usage Examples for PDF2Tasks

This file demonstrates various ways to use the PDF2Tasks CLI.
"""

import subprocess
import os

# ================================================================================
# Example 1: Basic Usage
# ================================================================================

def example_1_basic_usage():
    """
    Example 1: Basic PDF processing

    Minimum required parameters:
    - PDF file path
    - Output directory
    - API key (via environment variable or --api-key)
    """
    print("\n" + "=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    cmd = [
        "python", "-m", "src.cli.main", "analyze",
        "./specs/app-v1.pdf",
        "--out", "./output"
    ]

    print("Command:")
    print(" ".join(cmd))
    print("\nDescription:")
    print("  - Analyzes app-v1.pdf")
    print("  - Generates task files in ./output")
    print("  - Uses default model (claude-3-5-sonnet-20241022)")
    print("  - Extracts tables (default)")
    print("  - Does NOT extract images (default)")
    print("\nNote: Set ANTHROPIC_API_KEY environment variable before running")


# ================================================================================
# Example 2: With Clean Option
# ================================================================================

def example_2_clean_output():
    """
    Example 2: Clean output directory before processing

    Use --clean to remove existing files in output directory
    """
    print("\n" + "=" * 60)
    print("Example 2: Clean Output Directory")
    print("=" * 60)

    cmd = [
        "python", "-m", "src.cli.main", "analyze",
        "./specs/app-v1.pdf",
        "--out", "./output",
        "--clean"
    ]

    print("Command:")
    print(" ".join(cmd))
    print("\nDescription:")
    print("  - Removes all existing files in ./output before processing")
    print("  - Useful for fresh start")


# ================================================================================
# Example 3: With Verbose Logging
# ================================================================================

def example_3_verbose():
    """
    Example 3: Enable verbose logging

    Use -v or --verbose for detailed logs
    """
    print("\n" + "=" * 60)
    print("Example 3: Verbose Logging")
    print("=" * 60)

    cmd = [
        "python", "-m", "src.cli.main", "analyze",
        "./specs/app-v1.pdf",
        "--out", "./output",
        "--verbose"
    ]

    print("Command:")
    print(" ".join(cmd))
    print("\nDescription:")
    print("  - Shows detailed DEBUG-level logs")
    print("  - Useful for troubleshooting")
    print("  - Shows progress for each page/section")


# ================================================================================
# Example 4: With Custom Model and API Key
# ================================================================================

def example_4_custom_model():
    """
    Example 4: Use custom Claude model and explicit API key

    Override default model and provide API key via command line
    """
    print("\n" + "=" * 60)
    print("Example 4: Custom Model and API Key")
    print("=" * 60)

    cmd = [
        "python", "-m", "src.cli.main", "analyze",
        "./specs/app-v1.pdf",
        "--out", "./output",
        "--model", "claude-3-5-sonnet-20241022",
        "--api-key", "sk-ant-api03-xxx"  # Replace with actual key
    ]

    print("Command:")
    print(" ".join(cmd))
    print("\nDescription:")
    print("  - Uses specified Claude model")
    print("  - API key provided via --api-key (overrides env var)")
    print("\nWarning: Don't hardcode API keys! Use environment variables.")


# ================================================================================
# Example 5: With Image and Table Extraction
# ================================================================================

def example_5_full_extraction():
    """
    Example 5: Extract images and tables

    Enable image extraction (disabled by default)
    """
    print("\n" + "=" * 60)
    print("Example 5: Full Extraction (Images + Tables)")
    print("=" * 60)

    cmd = [
        "python", "-m", "src.cli.main", "analyze",
        "./specs/app-v1.pdf",
        "--out", "./output",
        "--extract-images",
        "--extract-tables",
        "--clean",
        "--verbose"
    ]

    print("Command:")
    print(" ".join(cmd))
    print("\nDescription:")
    print("  - Extracts images from PDF")
    print("  - Extracts tables (enabled by default)")
    print("  - Cleans output directory")
    print("  - Verbose logging enabled")
    print("\nImages will be saved to: ./output/temp_images/")


# ================================================================================
# Example 6: Environment Variable Usage
# ================================================================================

def example_6_env_var():
    """
    Example 6: Using environment variables

    Recommended way to provide API key
    """
    print("\n" + "=" * 60)
    print("Example 6: Environment Variable Usage")
    print("=" * 60)

    print("1. Set environment variable:")
    print("   export ANTHROPIC_API_KEY='your-api-key-here'")
    print("\n2. Run command:")

    cmd = [
        "python", "-m", "src.cli.main", "analyze",
        "./specs/app-v1.pdf",
        "--out", "./output"
    ]

    print("   " + " ".join(cmd))
    print("\nAlternatively, use .env file:")
    print("   echo 'ANTHROPIC_API_KEY=your-key' > .env")
    print("\nThe CLI will automatically read from ANTHROPIC_API_KEY env var")


# ================================================================================
# Example 7: Help and Version
# ================================================================================

def example_7_help():
    """
    Example 7: Get help and version information
    """
    print("\n" + "=" * 60)
    print("Example 7: Help and Version")
    print("=" * 60)

    print("Show version:")
    print("  python -m src.cli.main --version")
    print("\nShow general help:")
    print("  python -m src.cli.main --help")
    print("\nShow analyze command help:")
    print("  python -m src.cli.main analyze --help")


# ================================================================================
# Example 8: Practical Shell Script
# ================================================================================

def example_8_shell_script():
    """
    Example 8: Practical shell script for automation
    """
    print("\n" + "=" * 60)
    print("Example 8: Practical Shell Script")
    print("=" * 60)

    script = """#!/bin/bash
# process_pdf.sh - Batch PDF processing script

set -e  # Exit on error

# Configuration
API_KEY="${ANTHROPIC_API_KEY}"
INPUT_DIR="./specs"
OUTPUT_BASE="./output"

if [ -z "$API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY not set"
    exit 1
fi

# Process all PDFs in specs directory
for pdf in "$INPUT_DIR"/*.pdf; do
    if [ -f "$pdf" ]; then
        filename=$(basename "$pdf" .pdf)
        output_dir="$OUTPUT_BASE/$filename"

        echo "Processing: $pdf"
        echo "Output: $output_dir"

        python -m src.cli.main analyze \\
            "$pdf" \\
            --out "$output_dir" \\
            --clean \\
            --verbose

        echo "✓ Completed: $filename"
        echo "---"
    fi
done

echo "All PDFs processed successfully!"
"""

    print(script)
    print("\nSave as process_pdf.sh and run:")
    print("  chmod +x process_pdf.sh")
    print("  ./process_pdf.sh")


# ================================================================================
# Example 9: Error Handling
# ================================================================================

def example_9_error_handling():
    """
    Example 9: Understanding error codes and handling
    """
    print("\n" + "=" * 60)
    print("Example 9: Error Handling")
    print("=" * 60)

    print("Exit codes:")
    print("  0: Success")
    print("  1: General error")
    print("  2: File not found or invalid argument")
    print("  4: API key missing or invalid")
    print("  130: Interrupted by user (Ctrl+C)")
    print("\nExample error scenarios:")
    print("\n1. Missing PDF file:")
    print("   python -m src.cli.main analyze nonexistent.pdf --out ./out")
    print("   Exit code: 2")
    print("\n2. Missing API key:")
    print("   python -m src.cli.main analyze test.pdf --out ./out")
    print("   Exit code: 4")
    print("\n3. User interruption:")
    print("   python -m src.cli.main analyze large.pdf --out ./out")
    print("   [Press Ctrl+C during execution]")
    print("   Exit code: 130")


# ================================================================================
# Example 10: Complete Workflow
# ================================================================================

def example_10_complete_workflow():
    """
    Example 10: Complete workflow from start to finish
    """
    print("\n" + "=" * 60)
    print("Example 10: Complete Workflow")
    print("=" * 60)

    workflow = """
1. Setup:
   export ANTHROPIC_API_KEY='your-api-key'
   mkdir -p output

2. Analyze PDF:
   python -m src.cli.main analyze \\
       ./specs/app-v1.pdf \\
       --out ./output \\
       --clean \\
       --extract-tables \\
       --verbose

3. Check output:
   ls -lh output/
   # Expected files:
   # - 1_인증.md
   # - 2_결제.md
   # - ...
   # - report.log
   # - report.json

4. Review report:
   cat output/report.log
   # Shows:
   # - Processing statistics
   # - Token usage
   # - Estimated cost
   # - Any errors/warnings

5. Use generated tasks:
   # Review each markdown file
   # Each file contains:
   # - High-level task overview
   # - Detailed sub-tasks
   # - Implementation guidelines
"""

    print(workflow)


# ================================================================================
# Main
# ================================================================================

def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("PDF2TASKS CLI - USAGE EXAMPLES")
    print("=" * 80)
    print("\nThese examples show how to use the PDF2Tasks command-line interface.")
    print("Note: These are demonstrations only. To actually run the commands,")
    print("copy them to your terminal.")

    example_1_basic_usage()
    example_2_clean_output()
    example_3_verbose()
    example_4_custom_model()
    example_5_full_extraction()
    example_6_env_var()
    example_7_help()
    example_8_shell_script()
    example_9_error_handling()
    example_10_complete_workflow()

    print("\n" + "=" * 80)
    print("For more information, run:")
    print("  python -m src.cli.main --help")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
