"""Tesseract OCR configuration and initialization."""

import os
import subprocess
from typing import Dict, Optional
from ..utils.logger import get_logger
from .exceptions import TesseractNotFoundError, LanguageDataNotFoundError

logger = get_logger(__name__)


class TesseractConfig:
    """Tesseract OCR configuration."""

    # OCR Engine Mode (OEM)
    OEM_LEGACY = 0  # Legacy engine only
    OEM_LSTM = 1  # Neural nets LSTM engine only (default)
    OEM_LEGACY_LSTM = 2  # Legacy + LSTM engines
    OEM_DEFAULT = 3  # Default, based on what is available

    # Page Segmentation Mode (PSM)
    PSM_OSD_ONLY = 0  # Orientation and script detection (OSD) only
    PSM_AUTO_OSD = 1  # Automatic page segmentation with OSD
    PSM_AUTO_ONLY = 2  # Automatic page segmentation, but no OSD, or OCR
    PSM_AUTO = 3  # Fully automatic page segmentation, but no OSD (default)
    PSM_SINGLE_COLUMN = 4  # Assume a single column of text of variable sizes
    PSM_SINGLE_BLOCK_VERT = 5  # Assume a single uniform block of vertically aligned text
    PSM_SINGLE_BLOCK = 6  # Assume a single uniform block of text
    PSM_SINGLE_LINE = 7  # Treat the image as a single text line
    PSM_SINGLE_WORD = 8  # Treat the image as a single word
    PSM_CIRCLE_WORD = 9  # Treat the image as a single word in a circle
    PSM_SINGLE_CHAR = 10  # Treat the image as a single character
    PSM_SPARSE = 11  # Sparse text. Find as much text as possible in no particular order
    PSM_SPARSE_OSD = 12  # Sparse text with OSD
    PSM_RAW_LINE = 13  # Raw line. Treat the image as a single text line

    def __init__(
        self,
        lang: str = "kor+eng",
        oem: int = OEM_LSTM,
        psm: int = PSM_AUTO,
        tesseract_cmd: Optional[str] = None,
    ):
        """
        Initialize Tesseract configuration.

        Args:
            lang: Language code (default: 'kor+eng' for Korean + English)
            oem: OCR Engine Mode (default: 1 for LSTM)
            psm: Page Segmentation Mode (default: 3 for auto)
            tesseract_cmd: Custom path to tesseract executable

        Raises:
            TesseractNotFoundError: If Tesseract is not installed
            LanguageDataNotFoundError: If required language data is missing
        """
        self.lang = lang
        self.oem = oem
        self.psm = psm
        self.tesseract_cmd = tesseract_cmd or self._find_tesseract()

        # Validate Tesseract installation
        self._validate_installation()

        logger.info(
            f"Tesseract configured: lang={lang}, oem={oem}, psm={psm}, cmd={self.tesseract_cmd}"
        )

    def _find_tesseract(self) -> str:
        """
        Find Tesseract executable in system PATH.

        Returns:
            Path to tesseract executable

        Raises:
            TesseractNotFoundError: If Tesseract is not found
        """
        # Try common locations
        common_paths = [
            "tesseract",  # System PATH
            "/usr/bin/tesseract",  # Linux
            "/usr/local/bin/tesseract",  # macOS (Homebrew)
            "/opt/homebrew/bin/tesseract",  # macOS (Apple Silicon Homebrew)
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",  # Windows
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",  # Windows
        ]

        for path in common_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    logger.info(f"Found Tesseract at: {path}")
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        raise TesseractNotFoundError(
            "Tesseract OCR not found. Please install Tesseract:\n"
            "  - macOS: brew install tesseract tesseract-lang\n"
            "  - Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-kor\n"
            "  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
        )

    def _validate_installation(self) -> None:
        """
        Validate Tesseract installation and language data.

        Raises:
            TesseractNotFoundError: If Tesseract is not working
            LanguageDataNotFoundError: If required language data is missing
        """
        try:
            # Check Tesseract version
            result = subprocess.run(
                [self.tesseract_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise TesseractNotFoundError(
                    f"Tesseract command failed: {result.stderr}"
                )

            version_info = result.stdout
            logger.info(f"Tesseract version info:\n{version_info}")

            # Check available languages
            result = subprocess.run(
                [self.tesseract_cmd, "--list-langs"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                raise TesseractNotFoundError(
                    f"Failed to list languages: {result.stderr}"
                )

            available_langs = result.stdout.split("\n")[1:]  # Skip header line
            available_langs = [lang.strip() for lang in available_langs if lang.strip()]

            logger.info(f"Available languages: {', '.join(available_langs)}")

            # Verify required languages
            required_langs = self.lang.split("+")
            missing_langs = [lang for lang in required_langs if lang not in available_langs]

            if missing_langs:
                raise LanguageDataNotFoundError(
                    f"Missing language data for: {', '.join(missing_langs)}\n"
                    f"Available languages: {', '.join(available_langs)}\n"
                    "Install missing languages:\n"
                    "  - macOS: brew install tesseract-lang\n"
                    "  - Ubuntu: sudo apt-get install tesseract-ocr-kor tesseract-ocr-eng"
                )

        except subprocess.TimeoutExpired:
            raise TesseractNotFoundError("Tesseract command timed out")
        except FileNotFoundError:
            raise TesseractNotFoundError(
                f"Tesseract executable not found at: {self.tesseract_cmd}"
            )

    def get_config_dict(self) -> Dict[str, any]:
        """
        Get configuration as dictionary for pytesseract.

        Returns:
            Dictionary with Tesseract configuration
        """
        config = f"--oem {self.oem} --psm {self.psm}"
        return {"lang": self.lang, "config": config}

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"TesseractConfig(lang='{self.lang}', oem={self.oem}, psm={self.psm}, "
            f"cmd='{self.tesseract_cmd}')"
        )


# Default configuration instance
_default_config: Optional[TesseractConfig] = None


def get_default_config() -> TesseractConfig:
    """
    Get or create default Tesseract configuration.

    Returns:
        Default TesseractConfig instance
    """
    global _default_config
    if _default_config is None:
        _default_config = TesseractConfig()
    return _default_config


def set_tesseract_cmd(cmd: str) -> None:
    """
    Set custom Tesseract command path.

    Args:
        cmd: Path to tesseract executable
    """
    global _default_config
    _default_config = TesseractConfig(tesseract_cmd=cmd)
    logger.info(f"Tesseract command set to: {cmd}")
