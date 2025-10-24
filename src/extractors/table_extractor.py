"""Table extraction from PDF files."""

import os
from typing import List
import pdfplumber
from ..types.models import ExtractedTable, Position
from ..utils.logger import get_logger
from .exceptions import FileNotFoundError, PDFParseError

logger = get_logger(__name__)


class TableExtractor:
    """Extract tables from PDF files."""

    def extract_tables(self, pdf_path: str) -> List[ExtractedTable]:
        """
        Extract all tables from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of ExtractedTable objects

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        extracted_tables: List[ExtractedTable] = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"Extracting tables from {len(pdf.pages)} pages...")

                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract tables from the page
                    tables = page.extract_tables()

                    if tables:
                        logger.info(f"Page {page_num}: Found {len(tables)} tables")

                    for table_index, table in enumerate(tables):
                        try:
                            # Convert None values to empty strings
                            cleaned_table = [
                                [str(cell) if cell is not None else "" for cell in row]
                                for row in table
                            ]

                            # Get table bounding box (approximate)
                            # Note: pdfplumber doesn't provide exact table positions,
                            # so we use page dimensions as fallback
                            position = Position(
                                x=0.0,
                                y=0.0,
                                width=float(page.width),
                                height=float(page.height),
                            )

                            extracted_tables.append(
                                ExtractedTable(
                                    page_number=page_num,
                                    rows=cleaned_table,
                                    position=position,
                                )
                            )

                            logger.info(
                                f"Extracted table {table_index + 1} from page {page_num}: "
                                f"{len(cleaned_table)} rows, {len(cleaned_table[0]) if cleaned_table else 0} columns"
                            )

                        except Exception as e:
                            logger.warning(
                                f"Failed to process table {table_index + 1} on page {page_num}: {e}"
                            )
                            continue

                    logger.info(f"Processed page {page_num}/{len(pdf.pages)}")

            logger.info(f"Successfully extracted {len(extracted_tables)} tables")

        except Exception as e:
            raise PDFParseError(f"Error extracting tables: {str(e)}")

        return extracted_tables

    def extract_tables_from_page(self, pdf_path: str, page_number: int) -> List[ExtractedTable]:
        """
        Extract tables from a specific page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (1-indexed)

        Returns:
            List of ExtractedTable objects from the specified page

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted or page doesn't exist
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        extracted_tables: List[ExtractedTable] = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    raise PDFParseError(
                        f"Invalid page number: {page_number} (document has {len(pdf.pages)} pages)"
                    )

                page = pdf.pages[page_number - 1]  # Convert to 0-indexed
                tables = page.extract_tables()

                logger.info(f"Page {page_number}: Found {len(tables)} tables")

                for table_index, table in enumerate(tables):
                    try:
                        cleaned_table = [
                            [str(cell) if cell is not None else "" for cell in row]
                            for row in table
                        ]

                        position = Position(
                            x=0.0,
                            y=0.0,
                            width=float(page.width),
                            height=float(page.height),
                        )

                        extracted_tables.append(
                            ExtractedTable(
                                page_number=page_number,
                                rows=cleaned_table,
                                position=position,
                            )
                        )

                        logger.info(
                            f"Extracted table {table_index + 1}: "
                            f"{len(cleaned_table)} rows, {len(cleaned_table[0]) if cleaned_table else 0} columns"
                        )

                    except Exception as e:
                        logger.warning(
                            f"Failed to process table {table_index + 1}: {e}"
                        )
                        continue

        except Exception as e:
            raise PDFParseError(f"Error extracting tables from page {page_number}: {str(e)}")

        return extracted_tables

    def extract_tables_with_settings(
        self,
        pdf_path: str,
        table_settings: dict = None,
    ) -> List[ExtractedTable]:
        """
        Extract tables with custom pdfplumber settings.

        Args:
            pdf_path: Path to the PDF file
            table_settings: Custom settings for table extraction
                           (see pdfplumber documentation for options)

        Returns:
            List of ExtractedTable objects

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if table_settings is None:
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 3,
            }

        extracted_tables: List[ExtractedTable] = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(
                    f"Extracting tables with custom settings from {len(pdf.pages)} pages..."
                )

                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables(table_settings=table_settings)

                    if tables:
                        logger.info(f"Page {page_num}: Found {len(tables)} tables")

                    for table_index, table in enumerate(tables):
                        try:
                            cleaned_table = [
                                [str(cell) if cell is not None else "" for cell in row]
                                for row in table
                            ]

                            position = Position(
                                x=0.0,
                                y=0.0,
                                width=float(page.width),
                                height=float(page.height),
                            )

                            extracted_tables.append(
                                ExtractedTable(
                                    page_number=page_num,
                                    rows=cleaned_table,
                                    position=position,
                                )
                            )

                            logger.info(
                                f"Extracted table {table_index + 1} from page {page_num}: "
                                f"{len(cleaned_table)} rows"
                            )

                        except Exception as e:
                            logger.warning(
                                f"Failed to process table {table_index + 1} on page {page_num}: {e}"
                            )
                            continue

                    logger.info(f"Processed page {page_num}/{len(pdf.pages)}")

            logger.info(f"Successfully extracted {len(extracted_tables)} tables")

        except Exception as e:
            raise PDFParseError(f"Error extracting tables: {str(e)}")

        return extracted_tables
