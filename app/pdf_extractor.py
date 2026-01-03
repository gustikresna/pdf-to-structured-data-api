"""
PDF Extractor - Core extraction logic for the API
"""

import os
from typing import Optional, Any
from datetime import datetime

import pdfplumber
from pypdf import PdfReader
import pandas as pd

from .models import (
    ExtractionOptions,
    ExtractionResponse,
    PageText,
    TableData,
    ImageInfo,
    PDFMetadata
)


class PDFExtractor:
    """
    Extracts structured data from PDF files.
    Uses pdfplumber for text/tables and pypdf for metadata.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        
    def extract(self, options: ExtractionOptions) -> ExtractionResponse:
        """
        Main extraction method - extracts all requested data types.
        """
        response = ExtractionResponse(
            success=True,
            filename=os.path.basename(self.file_path),
            extraction_timestamp=datetime.utcnow().isoformat()
        )
        
        try:
            # Extract metadata (always useful for context)
            if options.extract_metadata:
                response.metadata = self.extract_metadata()
            
            # Extract text
            if options.extract_text:
                text_data = self.extract_text(options.pages)
                response.text = text_data
                response.full_text = "\n\n".join([p.text for p in text_data])
            
            # Extract tables
            if options.extract_tables:
                response.tables = self.extract_tables(options.pages, options.output_format)
            
            # Extract image info
            if options.extract_images:
                response.images = self.extract_image_info(options.pages)
            
            # Add statistics
            response.statistics = self._compute_statistics(response)
            
            return response
            
        except Exception as e:
            response.success = False
            raise e
    
    def extract_metadata(self) -> PDFMetadata:
        """Extract PDF metadata using pypdf."""
        reader = PdfReader(self.file_path)
        meta = reader.metadata or {}
        
        # Parse dates if available
        creation_date = None
        mod_date = None
        
        if meta.get("/CreationDate"):
            creation_date = self._parse_pdf_date(meta["/CreationDate"])
        if meta.get("/ModDate"):
            mod_date = self._parse_pdf_date(meta["/ModDate"])
        
        return PDFMetadata(
            title=meta.get("/Title"),
            author=meta.get("/Author"),
            subject=meta.get("/Subject"),
            creator=meta.get("/Creator"),
            producer=meta.get("/Producer"),
            creation_date=creation_date,
            modification_date=mod_date,
            page_count=len(reader.pages),
            file_size_bytes=self.file_size,
            is_encrypted=reader.is_encrypted,
            pdf_version=reader.pdf_header if hasattr(reader, 'pdf_header') else None
        )
    
    def extract_text(self, pages: Optional[list[int]] = None) -> list[PageText]:
        """
        Extract text from PDF pages using pdfplumber.
        Returns structured text with per-page statistics.
        """
        text_results = []
        
        with pdfplumber.open(self.file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                
                # Skip if specific pages requested and this isn't one
                if pages and page_num not in pages:
                    continue
                
                text = page.extract_text() or ""
                
                text_results.append(PageText(
                    page_number=page_num,
                    text=text,
                    char_count=len(text),
                    word_count=len(text.split()) if text else 0
                ))
        
        return text_results
    
    def extract_tables(
        self, 
        pages: Optional[list[int]] = None,
        output_format: str = "json"
    ) -> list[TableData]:
        """
        Extract tables from PDF pages using pdfplumber.
        """
        tables_results = []
        
        with pdfplumber.open(self.file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                
                # Skip if specific pages requested
                if pages and page_num not in pages:
                    continue
                
                tables = page.extract_tables()
                
                for j, table in enumerate(tables):
                    if not table or len(table) == 0:
                        continue
                    
                    # First row as headers if it looks like headers
                    headers = None
                    data_rows = table
                    
                    if self._looks_like_header(table[0]):
                        headers = [str(cell) if cell else "" for cell in table[0]]
                        data_rows = table[1:]
                    
                    # Clean the rows
                    cleaned_rows = [
                        [str(cell) if cell is not None else "" for cell in row]
                        for row in data_rows
                    ]
                    
                    tables_results.append(TableData(
                        page_number=page_num,
                        table_index=j,
                        headers=headers,
                        rows=cleaned_rows,
                        row_count=len(cleaned_rows),
                        column_count=len(table[0]) if table else 0
                    ))
        
        return tables_results
    
    def extract_image_info(self, pages: Optional[list[int]] = None) -> list[ImageInfo]:
        """
        Extract information about images in the PDF.
        Note: This extracts metadata, not the actual image data.
        """
        images_info = []
        
        reader = PdfReader(self.file_path)
        
        for i, page in enumerate(reader.pages):
            page_num = i + 1
            
            if pages and page_num not in pages:
                continue
            
            if "/Resources" in page and "/XObject" in page["/Resources"]:
                x_objects = page["/Resources"]["/XObject"].get_object()
                
                img_index = 0
                for obj_name in x_objects:
                    obj = x_objects[obj_name]
                    if obj["/Subtype"] == "/Image":
                        images_info.append(ImageInfo(
                            page_number=page_num,
                            image_index=img_index,
                            width=int(obj.get("/Width", 0)),
                            height=int(obj.get("/Height", 0)),
                            color_space=str(obj.get("/ColorSpace", "")),
                            bits_per_component=int(obj.get("/BitsPerComponent", 0)) if obj.get("/BitsPerComponent") else None
                        ))
                        img_index += 1
        
        return images_info
    
    def _looks_like_header(self, row: list) -> bool:
        """
        Heuristic to determine if a row looks like a table header.
        """
        if not row:
            return False
        
        # Check if all cells are non-empty strings
        non_empty = sum(1 for cell in row if cell and str(cell).strip())
        if non_empty < len(row) * 0.5:
            return False
        
        # Check if cells don't look like numbers
        numeric_count = 0
        for cell in row:
            if cell:
                try:
                    float(str(cell).replace(",", "").replace("$", ""))
                    numeric_count += 1
                except ValueError:
                    pass
        
        # If more than half are numeric, probably not headers
        return numeric_count < len(row) * 0.5
    
    def _parse_pdf_date(self, date_str: str) -> Optional[str]:
        """Parse PDF date format (D:YYYYMMDDHHmmss) to ISO format."""
        try:
            if date_str.startswith("D:"):
                date_str = date_str[2:]
            # Handle various PDF date formats
            date_str = date_str.replace("'", "").replace("Z", "")
            if len(date_str) >= 14:
                dt = datetime.strptime(date_str[:14], "%Y%m%d%H%M%S")
                return dt.isoformat()
            elif len(date_str) >= 8:
                dt = datetime.strptime(date_str[:8], "%Y%m%d")
                return dt.isoformat()
        except Exception:
            pass
        return None
    
    def _compute_statistics(self, response: ExtractionResponse) -> dict:
        """Compute overall statistics for the extraction."""
        stats = {
            "extraction_timestamp": response.extraction_timestamp,
        }
        
        if response.text:
            stats["total_pages_extracted"] = len(response.text)
            stats["total_characters"] = sum(p.char_count for p in response.text)
            stats["total_words"] = sum(p.word_count for p in response.text)
        
        if response.tables:
            stats["total_tables"] = len(response.tables)
            stats["total_table_rows"] = sum(t.row_count for t in response.tables)
        
        if response.images:
            stats["total_images"] = len(response.images)
        
        if response.metadata:
            stats["total_pages_in_document"] = response.metadata.page_count
        
        return stats


class TableExporter:
    """Export tables to different formats."""
    
    @staticmethod
    def to_dataframe(table: TableData) -> pd.DataFrame:
        """Convert TableData to pandas DataFrame."""
        if table.headers:
            return pd.DataFrame(table.rows, columns=table.headers)
        return pd.DataFrame(table.rows)
    
    @staticmethod
    def to_csv(table: TableData) -> str:
        """Convert TableData to CSV string."""
        df = TableExporter.to_dataframe(table)
        return df.to_csv(index=False)
    
    @staticmethod
    def to_markdown(table: TableData) -> str:
        """Convert TableData to Markdown table."""
        df = TableExporter.to_dataframe(table)
        return df.to_markdown(index=False)
    
    @staticmethod
    def to_dict(table: TableData) -> dict:
        """Convert TableData to dictionary."""
        df = TableExporter.to_dataframe(table)
        return df.to_dict(orient='records')
