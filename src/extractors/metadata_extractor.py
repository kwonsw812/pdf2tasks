"""Metadata extraction from PDF files."""

import os
from datetime import datetime
from typing import Optional
import fitz  # PyMuPDF
from ..types.models import PDFMetadata
from ..utils.logger import get_logger
from .exceptions import FileNotFoundError, PDFParseError

logger = get_logger(__name__)


class MetadataExtractor:
    """Extract metadata from PDF files."""

    def extract_metadata(self, pdf_path: str) -> PDFMetadata:
        """
        Extract metadata from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            PDFMetadata object containing document metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            metadata_dict = doc.metadata

            logger.info(f"Extracting metadata from PDF with {doc.page_count} pages")

            # Parse dates
            creation_date = self._parse_pdf_date(metadata_dict.get("creationDate"))
            modification_date = self._parse_pdf_date(metadata_dict.get("modDate"))

            metadata = PDFMetadata(
                title=metadata_dict.get("title") or None,
                author=metadata_dict.get("author") or None,
                subject=metadata_dict.get("subject") or None,
                creator=metadata_dict.get("creator") or None,
                producer=metadata_dict.get("producer") or None,
                creation_date=creation_date,
                modification_date=modification_date,
                total_pages=doc.page_count,
            )

            doc.close()

            logger.info(
                f"Extracted metadata: Title='{metadata.title}', "
                f"Author='{metadata.author}', Pages={metadata.total_pages}"
            )

            return metadata

        except fitz.FileDataError as e:
            raise PDFParseError(f"Failed to parse PDF: {str(e)}")
        except Exception as e:
            raise PDFParseError(f"Error extracting metadata: {str(e)}")

    def _parse_pdf_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse PDF date string to datetime object.

        PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
        Example: D:20231225143000+09'00'

        Args:
            date_str: PDF date string

        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None

        try:
            # Remove 'D:' prefix if present
            if date_str.startswith("D:"):
                date_str = date_str[2:]

            # Extract basic date components (YYYYMMDDHHmmSS)
            if len(date_str) >= 14:
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                hour = int(date_str[8:10])
                minute = int(date_str[10:12])
                second = int(date_str[12:14])

                return datetime(year, month, day, hour, minute, second)
            elif len(date_str) >= 8:
                # Only date available
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])

                return datetime(year, month, day)

        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse PDF date '{date_str}': {e}")
            return None

        return None

    def get_page_info(self, pdf_path: str, page_number: int) -> dict:
        """
        Get detailed information about a specific page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (1-indexed)

        Returns:
            Dictionary containing page information

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted or page doesn't exist
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)

            if page_number < 1 or page_number > doc.page_count:
                doc.close()
                raise PDFParseError(
                    f"Invalid page number: {page_number} (document has {doc.page_count} pages)"
                )

            page = doc[page_number - 1]  # Convert to 0-indexed

            page_info = {
                "page_number": page_number,
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
                "text_length": len(page.get_text()),
                "image_count": len(page.get_images()),
                "link_count": len(page.get_links()),
            }

            doc.close()

            return page_info

        except fitz.FileDataError as e:
            raise PDFParseError(f"Failed to parse PDF: {str(e)}")
        except Exception as e:
            raise PDFParseError(f"Error getting page info: {str(e)}")
