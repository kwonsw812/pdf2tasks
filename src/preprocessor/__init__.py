"""Preprocessor module for PDF text normalization and structuring."""

from .preprocessor import Preprocessor
from .text_normalizer import TextNormalizer
from .header_footer_remover import HeaderFooterRemover
from .section_segmenter import SectionSegmenter
from .functional_grouper import FunctionalGrouper
from .exceptions import (
    PreprocessorError,
    NormalizationError,
    SegmentationError,
    GroupingError,
)

__all__ = [
    "Preprocessor",
    "TextNormalizer",
    "HeaderFooterRemover",
    "SectionSegmenter",
    "FunctionalGrouper",
    "PreprocessorError",
    "NormalizationError",
    "SegmentationError",
    "GroupingError",
]
