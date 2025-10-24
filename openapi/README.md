# OpenAPI Integration Guide

This directory contains OpenAPI specification files that are used to check if extracted tasks from PDFs are already implemented in your system.

## Purpose

When the PDF Agent extracts tasks from requirement documents, it can automatically compare them against your existing OpenAPI specifications to:

- Identify tasks that are already fully implemented
- Detect partially implemented features
- Focus development efforts on truly new functionality
- Avoid duplicate work

## Supported Formats

Place your OpenAPI specification files in this directory. Supported formats:

- `.yaml` - YAML format (recommended)
- `.yml` - YAML format (alternative extension)
- `.json` - JSON format

## File Naming

Files can have any name. The system will automatically detect and load all OpenAPI files in this directory.

Examples:
- `api-v1.yaml`
- `shop-openapi.json`
- `backend-spec.yml`

## OpenAPI Version Support

Currently supports **OpenAPI 3.0** specifications.

## How It Works

1. **Automatic Detection**: The system scans this directory for all `.yaml`, `.yml`, and `.json` files
2. **Loading**: Each file is loaded and validated
3. **Endpoint Extraction**: All API endpoints are extracted from the specs
4. **Matching**: Extracted PDF tasks are compared against OpenAPI endpoints using:
   - Tag-based matching (e.g., "User Management" tag → "User" task)
   - Path-based matching (e.g., `/api/products` → "Product Management" task)
   - Module name matching
5. **Confidence Scoring**: Each match gets a confidence score (0.0 - 1.0):
   - >= 0.8: **Fully Implemented** (can be skipped)
   - 0.4 - 0.8: **Partially Implemented** (needs review)
   - < 0.4: **New Feature** (requires implementation)

## Usage Example

### 1. Place OpenAPI Files

```bash
# Copy your OpenAPI specs to this directory
cp path/to/your/api-spec.yaml openapi/
```

### 2. Run PDF Analysis

```bash
# Basic usage
pdf2tasks analyze specs/requirements.pdf --out ./output

# Skip already implemented tasks
pdf2tasks analyze specs/requirements.pdf --out ./output --skip-implemented

# Use custom OpenAPI directory
pdf2tasks analyze specs/requirements.pdf --out ./output --openapi-dir ./my-specs
```

### 3. Review Results

The system generates a comparison file:
```
output/_intermediate/4.5_openapi_comparison.json
```

This file contains:
- All matched endpoints
- Confidence scores
- Missing features
- Implementation status for each task

## OpenAPI Structure Example

Your OpenAPI file should include tags for better matching:

```yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
paths:
  /api/users:
    post:
      tags:
        - User Management
      summary: Create a new user
      operationId: createUser
      ...
  /api/products:
    get:
      tags:
        - Product Management
      summary: List products
      operationId: listProducts
      ...
```

## Tag Naming Best Practices

For optimal matching, use clear, descriptive tags:

- Good: "User Management", "Payment Processing", "Product Catalog"
- Avoid: "API", "Endpoints", "Misc"

Korean tags are also supported:
- "사용자 관리", "결제 처리", "상품 관리"

## Troubleshooting

### No Files Detected

Check that:
- Files are in the `openapi/` directory (or your custom `--openapi-dir`)
- Files have correct extensions (`.yaml`, `.yml`, `.json`)
- Files are valid OpenAPI 3.0 format

### Low Match Confidence

Improve matching by:
- Adding relevant tags to your OpenAPI endpoints
- Using consistent naming between PDF requirements and API tags
- Ensuring endpoint paths match module names

### Parsing Errors

If a file fails to load:
- Validate your OpenAPI file using online validators
- Check YAML/JSON syntax
- Ensure all required OpenAPI 3.0 fields are present

## Disabling OpenAPI Comparison

If you don't want to use OpenAPI comparison:

1. Remove all files from this directory, OR
2. Don't use the `--skip-implemented` flag

The system will continue normally without OpenAPI comparison.

## Multiple API Versions

You can include multiple OpenAPI files for different versions or services:

```
openapi/
  - api-v1.yaml
  - api-v2.yaml
  - admin-api.yaml
  - mobile-api.yaml
```

All will be loaded and compared against extracted tasks.

## Output

When OpenAPI comparison is enabled, check the logs for:

```
Found 3 OpenAPI spec files
Loaded OpenAPI spec: api-v1.yaml (title: My API v1, endpoints: 45)
OpenAPI spec comparison complete
  - User Management: fully_implemented (confidence: 0.95)
  - Payment Processing: partially_implemented (confidence: 0.65)
  - New Feature XYZ: new (confidence: 0.20)
```

## Advanced Configuration

Currently, matching parameters are built-in. Future versions may support:
- Custom matching rules
- Confidence threshold adjustment
- Endpoint filtering

---

For more information, see the main project README.md
