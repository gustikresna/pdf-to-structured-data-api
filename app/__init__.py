"""
PDF-to-Structured-Data API Package
"""

from .main import app
from .pdf_extractor import PDFExtractor, TableExporter
from .models import (
    ExtractionOptions,
    ExtractionResponse,
    PageText,
    TableData,
    ImageInfo,
    PDFMetadata,
    ErrorResponse,
    HealthResponse
)

__version__ = "1.0.0"
__all__ = [
    "app",
    "PDFExtractor",
    "TableExporter",
    "ExtractionOptions",
    "ExtractionResponse",
    "PageText",
    "TableData",
    "ImageInfo",
    "PDFMetadata",
    "ErrorResponse",
    "HealthResponse",
]
