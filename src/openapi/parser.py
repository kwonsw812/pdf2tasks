"""OpenAPI specification parser."""

from typing import Dict, Any, List
from ..types.models import OpenAPISpec, OpenAPIEndpoint
from .exceptions import OpenAPIParseError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OpenAPIParser:
    """
    Parse OpenAPI specifications into structured format.

    Supports OpenAPI 3.0 format.
    """

    def parse(self, spec_dict: Dict[str, Any]) -> OpenAPISpec:
        """
        Parse OpenAPI dictionary into OpenAPISpec model.

        Args:
            spec_dict: Dictionary containing OpenAPI specification

        Returns:
            Parsed OpenAPISpec object

        Raises:
            OpenAPIParseError: If spec cannot be parsed
        """
        try:
            # Extract basic info
            info = spec_dict.get('info', {})
            title = info.get('title', 'Untitled API')
            version = info.get('version', '1.0.0')

            # Extract endpoints
            endpoints = self.extract_endpoints(spec_dict)

            # Get source file if available
            source_file = spec_dict.get('_source_file')

            spec = OpenAPISpec(
                title=title,
                version=version,
                endpoints=endpoints,
                source_file=source_file,
            )

            logger.info(
                f"Parsed OpenAPI spec: {title} v{version} ({len(endpoints)} endpoints)"
            )

            return spec

        except Exception as e:
            raise OpenAPIParseError(f"Failed to parse OpenAPI spec: {e}")

    def extract_endpoints(self, spec_dict: Dict[str, Any]) -> List[OpenAPIEndpoint]:
        """
        Extract all endpoints from OpenAPI spec.

        Args:
            spec_dict: OpenAPI specification dictionary

        Returns:
            List of OpenAPIEndpoint objects
        """
        endpoints = []
        paths = spec_dict.get('paths', {})

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Iterate through HTTP methods
            for method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                if method not in path_item:
                    continue

                operation = path_item[method]
                if not isinstance(operation, dict):
                    continue

                # Extract operation details
                tags = operation.get('tags', [])
                summary = operation.get('summary')
                description = operation.get('description')
                operation_id = operation.get('operationId')

                endpoint = OpenAPIEndpoint(
                    path=path,
                    method=method.upper(),
                    tags=tags,
                    summary=summary,
                    description=description,
                    operation_id=operation_id,
                )

                endpoints.append(endpoint)

        logger.debug(f"Extracted {len(endpoints)} endpoints from spec")
        return endpoints

    def extract_tags(self, spec_dict: Dict[str, Any]) -> List[str]:
        """
        Extract all unique tags from OpenAPI spec.

        Args:
            spec_dict: OpenAPI specification dictionary

        Returns:
            List of unique tag names
        """
        tags = set()

        # Extract from global tags definition
        if 'tags' in spec_dict:
            for tag_obj in spec_dict['tags']:
                if isinstance(tag_obj, dict) and 'name' in tag_obj:
                    tags.add(tag_obj['name'])

        # Extract from operations
        paths = spec_dict.get('paths', {})
        for path_item in paths.values():
            if not isinstance(path_item, dict):
                continue

            for method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                if method not in path_item:
                    continue

                operation = path_item[method]
                if isinstance(operation, dict) and 'tags' in operation:
                    tags.update(operation['tags'])

        return sorted(list(tags))
