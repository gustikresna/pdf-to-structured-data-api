"""
Pydantic models for the PDF-to-Structured-Data API
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ExtractionOptions(BaseModel):
    """Options for PDF extraction"""
    extract_text: bool = True
    extract_tables: bool = True
    extract_metadata: bool = True
    extract_images: bool = False
    pages: Optional[list[int]] = None
    output_format: str = "json"


class PageText(BaseModel):
    """Text content from a single page"""
    page_number: int
    text: str
    char_count: int
    word_count: int


class TableData(BaseModel):
    """Extracted table data"""
    page_number: int
    table_index: int
    headers: Optional[list[str]] = None
    rows: list[list[Any]]
    row_count: int
    column_count: int


class ImageInfo(BaseModel):
    """Information about an image in the PDF"""
    page_number: int
    image_index: int
    width: int
    height: int
    color_space: Optional[str] = None
    bits_per_component: Optional[int] = None


class PDFMetadata(BaseModel):
    """PDF document metadata"""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int
    file_size_bytes: Optional[int] = None
    is_encrypted: bool = False
    pdf_version: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Complete extraction response"""
    success: bool = True
    filename: Optional[str] = None
    extraction_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Optional[PDFMetadata] = None
    text: Optional[list[PageText]] = None
    full_text: Optional[str] = None
    tables: Optional[list[TableData]] = None
    images: Optional[list[ImageInfo]] = None
    statistics: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "filename": "document.pdf",
                "extraction_timestamp": "2024-01-15T10:30:00",
                "metadata": {
                    "title": "Sample Document",
                    "author": "John Doe",
                    "page_count": 5
                },
                "text": [
                    {
                        "page_number": 1,
                        "text": "Sample text content...",
                        "char_count": 1500,
                        "word_count": 250
                    }
                ],
                "tables": [
                    {
                        "page_number": 1,
                        "table_index": 0,
                        "headers": ["Name", "Value"],
                        "rows": [["Item 1", "100"]],
                        "row_count": 1,
                        "column_count": 2
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid file type",
                "detail": "Only PDF files are accepted"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str
