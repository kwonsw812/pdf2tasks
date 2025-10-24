"""Text extraction from PDF files."""

import os
from typing import List
import fitz  # PyMuPDF
from ..types.models import ExtractedText, TextMetadata, Position
from ..utils.logger import get_logger
from .exceptions import FileNotFoundError, PDFParseError, EncryptedPDFError

logger = get_logger(__name__)


class TextExtractor:
    """Extract text from PDF files."""

    def extract_text(self, pdf_path: str) -> List[ExtractedText]:
        """
        Extract text from all pages of a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of ExtractedText objects containing text and metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted
            EncryptedPDFError: If PDF is encrypted
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        extracted_texts: List[ExtractedText] = []

        try:
            doc = fitz.open(pdf_path)

            # Check if PDF is encrypted
            if doc.is_encrypted:
                doc.close()
                raise EncryptedPDFError(f"PDF is encrypted: {pdf_path}")

            logger.info(f"Extracting text from {doc.page_count} pages...")

            for page_num in range(doc.page_count):
                page = doc[page_num]

                # Extract text with detailed information
                text_dict = page.get_text("dict")
                blocks = text_dict.get("blocks", [])

                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            line_text = ""
                            font_size = None
                            font_name = None
                            position = None

                            for span in line.get("spans", []):
                                line_text += span.get("text", "")
                                if font_size is None:
                                    font_size = span.get("size")
                                if font_name is None:
                                    font_name = span.get("font")

                            # Get position from line bbox
                            bbox = line.get("bbox")
                            if bbox:
                                position = Position(
                                    x=bbox[0],
                                    y=bbox[1],
                                    width=bbox[2] - bbox[0],
                                    height=bbox[3] - bbox[1],
                                )

                            if line_text.strip():
                                metadata = TextMetadata(
                                    font_size=font_size,
                                    font_name=font_name,
                                    position=position,
                                )

                                extracted_texts.append(
                                    ExtractedText(
                                        page_number=page_num + 1,  # 1-indexed
                                        text=line_text,
                                        metadata=metadata,
                                    )
                                )

                logger.info(f"Processed page {page_num + 1}/{doc.page_count}")

            doc.close()
            logger.info(f"Successfully extracted text from {len(extracted_texts)} text blocks")

        except fitz.FileDataError as e:
            raise PDFParseError(f"Failed to parse PDF: {str(e)}")
        except Exception as e:
            if "encrypted" in str(e).lower():
                raise EncryptedPDFError(f"PDF is encrypted: {pdf_path}")
            raise PDFParseError(f"Error extracting text: {str(e)}")

        return extracted_texts

    def extract_simple_text(self, pdf_path: str) -> str:
        """
        Extract plain text from PDF without metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Plain text content

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted
            EncryptedPDFError: If PDF is encrypted
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)

            if doc.is_encrypted:
                doc.close()
                raise EncryptedPDFError(f"PDF is encrypted: {pdf_path}")

            full_text = ""
            for page in doc:
                full_text += page.get_text()

            doc.close()
            return full_text

        except fitz.FileDataError as e:
            raise PDFParseError(f"Failed to parse PDF: {str(e)}")
        except Exception as e:
            if "encrypted" in str(e).lower():
                raise EncryptedPDFError(f"PDF is encrypted: {pdf_path}")
            raise PDFParseError(f"Error extracting text: {str(e)}")
