"""Image preprocessing for improved OCR accuracy."""

import os
import tempfile
from typing import Tuple
from PIL import Image, ImageEnhance, ImageFilter
from ..utils.logger import get_logger
from .exceptions import PreprocessingError, ImageLoadError

logger = get_logger(__name__)


class ImagePreprocessor:
    """Preprocess images to improve OCR accuracy."""

    def __init__(
        self,
        grayscale: bool = True,
        enhance_contrast: bool = True,
        contrast_factor: float = 1.5,
        denoise: bool = True,
        resize: bool = False,
        target_dpi: int = 300,
        sharpen: bool = False,
    ):
        """
        Initialize ImagePreprocessor.

        Args:
            grayscale: Convert to grayscale (default: True)
            enhance_contrast: Enhance contrast (default: True)
            contrast_factor: Contrast enhancement factor (default: 1.5)
            denoise: Apply noise reduction (default: True)
            resize: Resize image to target DPI (default: False)
            target_dpi: Target DPI for resizing (default: 300)
            sharpen: Apply sharpening filter (default: False)
        """
        self.grayscale = grayscale
        self.enhance_contrast = enhance_contrast
        self.contrast_factor = contrast_factor
        self.denoise = denoise
        self.resize = resize
        self.target_dpi = target_dpi
        self.sharpen = sharpen

        logger.info(
            f"ImagePreprocessor initialized: grayscale={grayscale}, "
            f"contrast={enhance_contrast}({contrast_factor}), "
            f"denoise={denoise}, resize={resize}({target_dpi}), sharpen={sharpen}"
        )

    def preprocess(self, image_path: str, output_path: str = None) -> str:
        """
        Preprocess an image for OCR.

        Args:
            image_path: Path to input image
            output_path: Path to save preprocessed image (optional)

        Returns:
            Path to preprocessed image

        Raises:
            ImageLoadError: If image cannot be loaded
            PreprocessingError: If preprocessing fails
        """
        if not os.path.exists(image_path):
            raise ImageLoadError(f"Image file not found: {image_path}")

        try:
            # Load image
            logger.info(f"Loading image: {image_path}")
            img = Image.open(image_path)

            # Get original size
            original_size = img.size
            logger.info(f"Original size: {original_size[0]}x{original_size[1]}")

            # Convert to RGB if necessary
            if img.mode not in ("RGB", "L"):
                logger.info(f"Converting from {img.mode} to RGB")
                img = img.convert("RGB")

            # 1. Convert to grayscale
            if self.grayscale:
                logger.info("Converting to grayscale")
                img = img.convert("L")

            # 2. Resize if needed
            if self.resize:
                img = self._resize_image(img)

            # 3. Enhance contrast
            if self.enhance_contrast:
                img = self._enhance_contrast(img)

            # 4. Denoise
            if self.denoise:
                img = self._denoise(img)

            # 5. Sharpen
            if self.sharpen:
                img = self._sharpen(img)

            # Save preprocessed image
            if output_path is None:
                # Create temporary file
                fd, output_path = tempfile.mkstemp(suffix=".png", prefix="preprocessed_")
                os.close(fd)

            img.save(output_path, "PNG")
            logger.info(f"Preprocessed image saved: {output_path}")

            # Log final size
            final_size = img.size
            logger.info(f"Final size: {final_size[0]}x{final_size[1]}")

            return output_path

        except IOError as e:
            raise ImageLoadError(f"Failed to load image: {str(e)}")
        except Exception as e:
            raise PreprocessingError(f"Image preprocessing failed: {str(e)}")

    def _resize_image(self, img: Image.Image) -> Image.Image:
        """
        Resize image to target DPI.

        Args:
            img: Input image

        Returns:
            Resized image
        """
        width, height = img.size

        # Get current DPI (default to 72 if not specified)
        info = img.info
        current_dpi = info.get("dpi", (72, 72))
        if isinstance(current_dpi, tuple):
            current_dpi = current_dpi[0]

        # Calculate scale factor
        scale = self.target_dpi / current_dpi

        if scale != 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            logger.info(
                f"Resizing from {width}x{height} to {new_width}x{new_height} "
                f"(DPI: {current_dpi} -> {self.target_dpi})"
            )
            img = img.resize((new_width, new_height), Image.LANCZOS)

        return img

    def _enhance_contrast(self, img: Image.Image) -> Image.Image:
        """
        Enhance image contrast.

        Args:
            img: Input image

        Returns:
            Contrast-enhanced image
        """
        logger.info(f"Enhancing contrast (factor={self.contrast_factor})")
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(self.contrast_factor)

    def _denoise(self, img: Image.Image) -> Image.Image:
        """
        Apply noise reduction filter.

        Args:
            img: Input image

        Returns:
            Denoised image
        """
        logger.info("Applying noise reduction filter")
        # Use median filter for noise reduction
        return img.filter(ImageFilter.MedianFilter(size=3))

    def _sharpen(self, img: Image.Image) -> Image.Image:
        """
        Apply sharpening filter.

        Args:
            img: Input image

        Returns:
            Sharpened image
        """
        logger.info("Applying sharpening filter")
        return img.filter(ImageFilter.SHARPEN)

    def preprocess_batch(
        self, image_paths: list[str], output_dir: str = None
    ) -> list[str]:
        """
        Preprocess multiple images.

        Args:
            image_paths: List of input image paths
            output_dir: Directory to save preprocessed images (optional)

        Returns:
            List of preprocessed image paths

        Raises:
            PreprocessingError: If any preprocessing fails
        """
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)

        preprocessed_paths = []
        failed_count = 0

        logger.info(f"Preprocessing {len(image_paths)} images...")

        for i, image_path in enumerate(image_paths, 1):
            try:
                if output_dir is not None:
                    # Generate output filename
                    basename = os.path.basename(image_path)
                    name, _ = os.path.splitext(basename)
                    output_path = os.path.join(output_dir, f"{name}_preprocessed.png")
                else:
                    output_path = None

                preprocessed_path = self.preprocess(image_path, output_path)
                preprocessed_paths.append(preprocessed_path)

                logger.info(f"Preprocessed {i}/{len(image_paths)}: {image_path}")

            except Exception as e:
                logger.error(f"Failed to preprocess {image_path}: {e}")
                failed_count += 1
                # Continue processing remaining images

        logger.info(
            f"Batch preprocessing complete: "
            f"{len(preprocessed_paths)} succeeded, {failed_count} failed"
        )

        if failed_count > 0 and len(preprocessed_paths) == 0:
            raise PreprocessingError("All images failed to preprocess")

        return preprocessed_paths

    def get_image_info(self, image_path: str) -> dict:
        """
        Get image information.

        Args:
            image_path: Path to image

        Returns:
            Dictionary with image info (size, mode, format, dpi)

        Raises:
            ImageLoadError: If image cannot be loaded
        """
        if not os.path.exists(image_path):
            raise ImageLoadError(f"Image file not found: {image_path}")

        try:
            with Image.open(image_path) as img:
                info = {
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format,
                    "dpi": img.info.get("dpi", (72, 72)),
                }
                return info
        except IOError as e:
            raise ImageLoadError(f"Failed to load image: {str(e)}")


def create_default_preprocessor() -> ImagePreprocessor:
    """
    Create a default ImagePreprocessor with optimal settings.

    Returns:
        ImagePreprocessor instance with default settings
    """
    return ImagePreprocessor(
        grayscale=True,
        enhance_contrast=True,
        contrast_factor=1.5,
        denoise=True,
        resize=False,
        sharpen=False,
    )
