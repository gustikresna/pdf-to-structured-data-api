# PDF-to-Structured-Data API

A FastAPI-based REST API that extracts text, tables, metadata, and structured information from PDF files.

## Features

- **Text Extraction**: Extract text content with per-page statistics (character count, word count)
- **Table Extraction**: Automatically detect and extract tables with header detection
- **Metadata Extraction**: Get PDF metadata (title, author, creation date, etc.)
- **Image Information**: Extract metadata about embedded images
- **Flexible Output**: JSON, Markdown, or CSV formats
- **Page Selection**: Extract from specific pages or page ranges
- **API Documentation**: Interactive Swagger UI and ReDoc documentation

## Quick Start

### Option 1: Run with Docker (Recommended)

```bash
# Clone and navigate to the project
cd pdf_to_structured_data_api

# Build and run with Docker Compose
docker-compose up --build

# API available at http://localhost:8000
```

### Option 2: Run Locally

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
```
GET /health
```

### Full Extraction
```
POST /extract
```
Extract all data types from a PDF with customizable options.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| file | File | required | PDF file to process |
| extract_text | bool | true | Extract text content |
| extract_tables | bool | true | Extract tables |
| extract_metadata | bool | true | Extract PDF metadata |
| extract_images | bool | false | Extract image info |
| page_numbers | string | null | Pages to extract (e.g., "1,2,5-10") |
| output_format | string | "json" | Output format: json, markdown, csv |

### Text Only
```
POST /extract/text
```
Extract only text content from a PDF.

### Tables Only
```
POST /extract/tables
```
Extract only tables from a PDF.

### Metadata Only
```
POST /extract/metadata
```
Extract only PDF metadata.

## Usage Examples

### Python with requests

```python
import requests

# Full extraction
url = "http://localhost:8000/extract"
files = {"file": open("document.pdf", "rb")}
params = {
    "extract_text": True,
    "extract_tables": True,
    "extract_metadata": True,
    "page_numbers": "1-5"
}

response = requests.post(url, files=files, params=params)
data = response.json()

# Access extracted data
print(f"Title: {data['metadata']['title']}")
print(f"Total pages: {data['metadata']['page_count']}")
print(f"Full text: {data['full_text'][:500]}...")

# Process tables
for table in data['tables']:
    print(f"Table on page {table['page_number']}: {table['row_count']} rows")
```

### cURL

```bash
# Full extraction
curl -X POST "http://localhost:8000/extract" \
  -F "file=@document.pdf" \
  -F "extract_text=true" \
  -F "extract_tables=true"

# Extract only text from pages 1-3
curl -X POST "http://localhost:8000/extract/text?page_numbers=1-3" \
  -F "file=@document.pdf"

# Extract tables as CSV
curl -X POST "http://localhost:8000/extract/tables?output_format=csv" \
  -F "file=@document.pdf"
```

### JavaScript/TypeScript

```typescript
async function extractPDF(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('http://localhost:8000/extract', {
    method: 'POST',
    body: formData,
  });

  return await response.json();
}
```

## Response Format

### Full Extraction Response

```json
{
  "success": true,
  "filename": "document.pdf",
  "extraction_timestamp": "2024-01-15T10:30:00.000000",
  "metadata": {
    "title": "Sample Document",
    "author": "John Doe",
    "subject": null,
    "creator": "Microsoft Word",
    "producer": "Adobe PDF Library",
    "creation_date": "2024-01-10T09:00:00",
    "modification_date": "2024-01-12T14:30:00",
    "page_count": 10,
    "file_size_bytes": 1048576,
    "is_encrypted": false,
    "pdf_version": "1.7"
  },
  "text": [
    {
      "page_number": 1,
      "text": "Introduction\n\nThis document covers...",
      "char_count": 2500,
      "word_count": 420
    }
  ],
  "full_text": "Introduction\n\nThis document covers...",
  "tables": [
    {
      "page_number": 2,
      "table_index": 0,
      "headers": ["Name", "Value", "Description"],
      "rows": [
        ["Item A", "100", "First item"],
        ["Item B", "200", "Second item"]
      ],
      "row_count": 2,
      "column_count": 3
    }
  ],
  "images": [
    {
      "page_number": 1,
      "image_index": 0,
      "width": 800,
      "height": 600,
      "color_space": "DeviceRGB",
      "bits_per_component": 8
    }
  ],
  "statistics": {
    "extraction_timestamp": "2024-01-15T10:30:00.000000",
    "total_pages_extracted": 10,
    "total_characters": 25000,
    "total_words": 4200,
    "total_tables": 3,
    "total_table_rows": 45,
    "total_images": 5,
    "total_pages_in_document": 10
  }
}
```

## API Documentation

Once the server is running, access interactive documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
pdf_to_structured_data_api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application and routes
│   ├── models.py         # Pydantic models
│   └── pdf_extractor.py  # Core extraction logic
├── tests/
│   └── test_api.py       # API tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| MAX_UPLOAD_SIZE | 50MB | Maximum file upload size |
| LOG_LEVEL | INFO | Logging level |

## Extending the API

### Adding OCR Support

For scanned PDFs, install OCR dependencies:

```bash
# Install system packages
apt-get install tesseract-ocr

# Install Python packages
pip install pytesseract pdf2image
```

Then extend `pdf_extractor.py` with OCR capabilities.

### Custom Table Detection

Modify `PDFExtractor.extract_tables()` to use custom table settings:

```python
table_settings = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "explicit_vertical_lines": [],
    "explicit_horizontal_lines": [],
    "snap_tolerance": 3,
    "join_tolerance": 3,
}
tables = page.extract_tables(table_settings)
```

## License

MIT License - see LICENSE file for details.
