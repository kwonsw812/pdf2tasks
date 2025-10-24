"""OpenAPI specification file loader."""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from .exceptions import OpenAPILoadError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OpenAPILoader:
    """
    Load OpenAPI specification files from a directory.

    Supports .yaml, .yml, and .json files.
    """

    def __init__(self, openapi_dir: str = "./openapi"):
        """
        Initialize loader.

        Args:
            openapi_dir: Directory containing OpenAPI spec files
        """
        self.openapi_dir = Path(openapi_dir)
        logger.debug(f"OpenAPILoader initialized with directory: {self.openapi_dir}")

    def find_spec_files(self) -> List[Path]:
        """
        Find all OpenAPI spec files in the directory.

        Returns:
            List of paths to OpenAPI spec files
        """
        if not self.openapi_dir.exists():
            logger.warning(f"OpenAPI directory not found: {self.openapi_dir}")
            return []

        if not self.openapi_dir.is_dir():
            logger.warning(f"OpenAPI path is not a directory: {self.openapi_dir}")
            return []

        # Find all YAML and JSON files
        spec_files = []

        for pattern in ["*.yaml", "*.yml", "*.json"]:
            spec_files.extend(self.openapi_dir.glob(pattern))

        logger.info(f"Found {len(spec_files)} OpenAPI spec files")

        return sorted(spec_files)

    def load_spec(self, file_path: Path) -> Dict[str, Any]:
        """
        Load a single OpenAPI spec file.

        Args:
            file_path: Path to the spec file

        Returns:
            Parsed OpenAPI specification as dict

        Raises:
            OpenAPILoadError: If file cannot be loaded or parsed
        """
        try:
            logger.debug(f"Loading OpenAPI spec: {file_path.name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Determine format by extension
            if file_path.suffix in ['.yaml', '.yml']:
                spec_dict = yaml.safe_load(content)
            elif file_path.suffix == '.json':
                spec_dict = json.loads(content)
            else:
                raise OpenAPILoadError(f"Unsupported file format: {file_path.suffix}")

            if not isinstance(spec_dict, dict):
                raise OpenAPILoadError(f"Invalid OpenAPI spec format in {file_path.name}")

            # Validate basic structure
            if 'openapi' not in spec_dict and 'swagger' not in spec_dict:
                logger.warning(
                    f"File {file_path.name} may not be a valid OpenAPI spec "
                    "(missing 'openapi' or 'swagger' field)"
                )

            logger.info(f"Loaded OpenAPI spec: {file_path.name}")
            return spec_dict

        except yaml.YAMLError as e:
            raise OpenAPILoadError(f"Failed to parse YAML file {file_path.name}: {e}")
        except json.JSONDecodeError as e:
            raise OpenAPILoadError(f"Failed to parse JSON file {file_path.name}: {e}")
        except Exception as e:
            raise OpenAPILoadError(f"Failed to load {file_path.name}: {e}")

    def load_all_specs(self) -> List[Dict[str, Any]]:
        """
        Load all OpenAPI spec files from the directory.

        Returns:
            List of parsed OpenAPI specifications
        """
        spec_files = self.find_spec_files()

        if not spec_files:
            logger.warning("No OpenAPI spec files found")
            return []

        specs = []
        failed_files = []

        for file_path in spec_files:
            try:
                spec = self.load_spec(file_path)
                # Add source file metadata
                spec['_source_file'] = str(file_path)
                specs.append(spec)
            except OpenAPILoadError as e:
                logger.warning(f"Failed to load {file_path.name}: {e}")
                failed_files.append(file_path.name)
                continue

        if failed_files:
            logger.warning(
                f"Failed to load {len(failed_files)} files: {', '.join(failed_files)}"
            )

        logger.info(f"Successfully loaded {len(specs)} OpenAPI specs")
        return specs

    def get_latest_spec(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest version OpenAPI spec.

        Attempts to find the spec with the highest version number.
        If version parsing fails, returns the first spec.

        Returns:
            Latest OpenAPI spec or None if no specs found
        """
        specs = self.load_all_specs()

        if not specs:
            return None

        if len(specs) == 1:
            return specs[0]

        # Try to find the latest version
        try:
            def get_version(spec: Dict[str, Any]) -> tuple:
                """Extract version tuple for comparison."""
                info = spec.get('info', {})
                version_str = info.get('version', '0.0.0')

                # Parse version string (e.g., "1.2.3" -> (1, 2, 3))
                parts = version_str.split('.')
                return tuple(int(p) for p in parts if p.isdigit())

            latest_spec = max(specs, key=get_version)
            logger.info(
                f"Selected latest version: "
                f"{latest_spec.get('info', {}).get('version', 'unknown')}"
            )
            return latest_spec

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse versions, using first spec: {e}")
            return specs[0]
