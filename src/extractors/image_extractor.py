"""Image extraction from PDF files."""

import os
import shutil
from typing import List
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
from ..types.models import ExtractedImage
from ..utils.logger import get_logger
from .exceptions import (
    FileNotFoundError,
    PDFParseError,
    ImageExtractionError,
    DiskSpaceError,
)

logger = get_logger(__name__)


class ImageExtractor:
    """Extract images from PDF files."""

    def __init__(self, output_dir: str = "./temp_images"):
        """
        Initialize ImageExtractor.

        Args:
            output_dir: Directory to save extracted images
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def extract_images(self, pdf_path: str) -> List[ExtractedImage]:
        """
        Extract all images from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of ExtractedImage objects

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted
            ImageExtractionError: If image extraction fails
            DiskSpaceError: If insufficient disk space
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Check disk space (require at least 100MB free)
        stat = shutil.disk_usage(self.output_dir)
        if stat.free < 100 * 1024 * 1024:  # 100MB in bytes
            raise DiskSpaceError(f"Insufficient disk space: {stat.free / (1024**3):.2f}GB free")

        extracted_images: List[ExtractedImage] = []

        try:
            doc = fitz.open(pdf_path)
            logger.info(f"Extracting images from {doc.page_count} pages...")

            for page_num in range(doc.page_count):
                page = doc[page_num]
                image_list = page.get_images(full=True)

                logger.info(f"Page {page_num + 1}: Found {len(image_list)} images")

                for img_index, img_info in enumerate(image_list):
                    try:
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # Save image
                        image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                        image_path = os.path.join(self.output_dir, image_filename)

                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)

                        # Get image dimensions
                        with Image.open(image_path) as img:
                            width, height = img.size

                        extracted_images.append(
                            ExtractedImage(
                                page_number=page_num + 1,
                                image_path=image_path,
                                width=width,
                                height=height,
                            )
                        )

                        logger.info(
                            f"Extracted image: {image_filename} ({width}x{height})"
                        )

                    except Exception as e:
                        logger.warning(
                            f"Failed to extract image {img_index + 1} from page {page_num + 1}: {e}"
                        )
                        continue

                logger.info(f"Processed page {page_num + 1}/{doc.page_count}")

            doc.close()
            logger.info(f"Successfully extracted {len(extracted_images)} images")

        except fitz.FileDataError as e:
            raise PDFParseError(f"Failed to parse PDF: {str(e)}")
        except Exception as e:
            raise ImageExtractionError(f"Error extracting images: {str(e)}")

        return extracted_images

    def extract_page_as_image(
        self, pdf_path: str, page_number: int, dpi: int = 150
    ) -> ExtractedImage:
        """
        Render a PDF page as an image.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (1-indexed)
            dpi: Resolution for rendering (default: 150)

        Returns:
            ExtractedImage object

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PDFParseError: If PDF is corrupted
            ImageExtractionError: If rendering fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)

            if page_number < 1 or page_number > doc.page_count:
                doc.close()
                raise ImageExtractionError(
                    f"Invalid page number: {page_number} (document has {doc.page_count} pages)"
                )

            page = doc[page_number - 1]  # Convert to 0-indexed

            # Render page to image
            zoom = dpi / 72  # Convert DPI to zoom factor
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Save image
            image_filename = f"page_{page_number}_rendered.png"
            image_path = os.path.join(self.output_dir, image_filename)
            pix.save(image_path)

            width = pix.width
            height = pix.height

            doc.close()

            logger.info(
                f"Rendered page {page_number} as image: {image_filename} ({width}x{height})"
            )

            return ExtractedImage(
                page_number=page_number,
                image_path=image_path,
                width=width,
                height=height,
            )

        except fitz.FileDataError as e:
            raise PDFParseError(f"Failed to parse PDF: {str(e)}")
        except Exception as e:
            raise ImageExtractionError(f"Error rendering page: {str(e)}")

    def cleanup(self) -> None:
        """Remove temporary image directory."""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
            logger.info(f"Cleaned up temporary directory: {self.output_dir}")
