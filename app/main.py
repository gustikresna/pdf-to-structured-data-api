"""
PDF-to-Structured-Data API
Extracts text, tables, metadata, and structured information from PDF files.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
import os

from .pdf_extractor import PDFExtractor
from .models import (
    ExtractionResponse,
    ExtractionOptions,
    ErrorResponse,
    HealthResponse
)

app = FastAPI(
    title="PDF-to-Structured-Data API",
    description="Extract text, tables, metadata, and structured data from PDF files",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="PDF-to-Structured-Data API is running",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Service is operational",
        version="1.0.0"
    )


@app.post("/extract", response_model=ExtractionResponse)
async def extract_pdf(
    file: UploadFile = File(..., description="PDF file to process"),
    extract_text: bool = Query(True, description="Extract text content"),
    extract_tables: bool = Query(True, description="Extract tables as structured data"),
    extract_metadata: bool = Query(True, description="Extract PDF metadata"),
    extract_images: bool = Query(False, description="Extract image information"),
    page_numbers: Optional[str] = Query(None, description="Specific pages to extract (e.g., '1,2,5-10')"),
    output_format: str = Query("json", description="Output format: json, markdown, or csv")
):
    """
    Extract structured data from a PDF file.
    
    - **file**: The PDF file to process
    - **extract_text**: Whether to extract text content (default: True)
    - **extract_tables**: Whether to extract tables (default: True)
    - **extract_metadata**: Whether to extract PDF metadata (default: True)
    - **extract_images**: Whether to extract image information (default: False)
    - **page_numbers**: Specific pages to process (e.g., "1,2,5-10")
    - **output_format**: Output format - json, markdown, or csv
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are accepted."
        )
    
    # Validate output format
    if output_format not in ["json", "markdown", "csv"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid output format. Use 'json', 'markdown', or 'csv'."
        )
    
    # Parse page numbers if provided
    pages_to_extract = None
    if page_numbers:
        try:
            pages_to_extract = parse_page_numbers(page_numbers)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Create extraction options
    options = ExtractionOptions(
        extract_text=extract_text,
        extract_tables=extract_tables,
        extract_metadata=extract_metadata,
        extract_images=extract_images,
        pages=pages_to_extract,
        output_format=output_format
    )
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Process the PDF
        extractor = PDFExtractor(tmp_path)
        result = extractor.extract(options)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/extract/text")
async def extract_text_only(
    file: UploadFile = File(...),
    page_numbers: Optional[str] = Query(None)
):
    """Extract only text content from a PDF file."""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    pages = parse_page_numbers(page_numbers) if page_numbers else None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        extractor = PDFExtractor(tmp_path)
        text_data = extractor.extract_text(pages)
        
        return {"text": text_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/extract/tables")
async def extract_tables_only(
    file: UploadFile = File(...),
    page_numbers: Optional[str] = Query(None),
    output_format: str = Query("json", description="Output: json, csv, or excel")
):
    """Extract only tables from a PDF file."""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    pages = parse_page_numbers(page_numbers) if page_numbers else None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        extractor = PDFExtractor(tmp_path)
        tables_data = extractor.extract_tables(pages, output_format)
        
        return {"tables": tables_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/extract/metadata")
async def extract_metadata_only(file: UploadFile = File(...)):
    """Extract only metadata from a PDF file."""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        extractor = PDFExtractor(tmp_path)
        metadata = extractor.extract_metadata()
        
        return {"metadata": metadata}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def parse_page_numbers(page_str: str) -> list[int]:
    """
    Parse page number string into a list of page numbers.
    Supports formats: "1,2,3" or "1-5" or "1,3,5-10"
    """
    pages = set()
    parts = page_str.replace(" ", "").split(",")
    
    for part in parts:
        if "-" in part:
            try:
                start, end = part.split("-")
                start, end = int(start), int(end)
                if start > end:
                    raise ValueError(f"Invalid range: {part}")
                pages.update(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Invalid page range: {part}")
        else:
            try:
                pages.add(int(part))
            except ValueError:
                raise ValueError(f"Invalid page number: {part}")
    
    return sorted(list(pages))
