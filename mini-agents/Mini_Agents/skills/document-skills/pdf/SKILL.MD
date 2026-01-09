---
name: pdf-processing
description: Skill for processing and extracting content from PDF files
---

# PDF Processing Skill

This skill provides guidance and tools for processing PDF files, extracting text, and analyzing document content.

## Overview

This skill includes Python scripts for common PDF processing tasks:
- Extracting text from PDF files
- Analyzing PDF structure
- Extracting tables from PDFs
- Converting PDF pages to images

## Available Scripts

### 1. Extract Text from PDF

Use `execute_script` to run the text extraction script:
```python
python /nfs/FM/gongoubo/new_project/Agent-Handbook/mini-agents/Mini_Agents/skills/document-skills/pdf/scripts/extract_text.py /path/to/your/file.pdf
```

### 2. Analyze PDF Structure

Use `execute_script` to run the structure analysis script:
```python
python /nfs/FM/gongoubo/new_project/Agent-Handbook/mini-agents/Mini_Agents/skills/document-skills/pdf/scripts/analyze_structure.py /path/to/your/file.pdf
```

### 3. Extract Tables from PDF

Use `execute_script` to run the table extraction script:
```python
python /nfs/FM/gongoubo/new_project/Agent-Handbook/mini-agents/Mini_Agents/skills/document-skills/pdf/scripts/extract_tables.py /path/to/your/file.pdf
```

### 4. Quick Code Execution

For quick PDF processing, use `execute_code` with inline Python code:

```python
import PyPDF2

# Open PDF file
pdf_path = '/path/to/your/file.pdf'
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    
    # Get basic info
    num_pages = len(reader.pages)
    print(f"Number of pages: {num_pages}")
    
    # Extract text from first page
    first_page = reader.pages[0]
    text = first_page.extract_text()
    print(f"First page text preview: {text[:200]}...")
```

## Usage Examples

### Example 1: Extract All Text from PDF

Use `execute_code` tool:
```python
import PyPDF2

pdf_path = '/path/to/your/file.pdf'
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    
    all_text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        all_text += page.extract_text()
    
    print(all_text)
```

### Example 2: Extract Text from Specific Page

Use `execute_code` tool:
```python
import PyPDF2

pdf_path = '/path/to/your/file.pdf'
page_number = 2  # Extract from page 3 (0-indexed)

with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    
    if page_number < len(reader.pages):
        page = reader.pages[page_number]
        text = page.extract_text()
        print(f"Text from page {page_number + 1}:")
        print(text)
    else:
        print(f"Page {page_number + 1} does not exist. Total pages: {len(reader.pages)}")
```

### Example 3: Get PDF Metadata

Use `execute_code` tool:
```python
import PyPDF2

pdf_path = '/path/to/your/file.pdf'
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    
    metadata = reader.metadata
    print("PDF Metadata:")
    if metadata:
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    else:
        print("  No metadata available")
```

## Best Practices

1. Always check if the PDF file exists before processing
2. Handle encoding issues gracefully (some PDFs may have special characters)
3. Use `execute_code` for simple text extraction tasks
4. Use `execute_script` for complex PDF processing workflows
5. Be aware that some PDFs may be password-protected or scanned images
6. For scanned PDFs, you may need OCR (Optical Character Recognition)

## Required Libraries

- PyPDF2
- pdfplumber (for better text extraction and table extraction)
- tabula-py (for advanced table extraction)

Install with: `pip install PyPDF2 pdfplumber tabula-py`

## Troubleshooting

### Issue: Cannot extract text from PDF
- The PDF might be a scanned image. Use OCR tools like Tesseract.
- The PDF might be password-protected. Provide the password when opening.

### Issue: Text extraction is garbled
- Try different PDF libraries (PyPDF2, pdfplumber, pdftotext)
- Some PDFs have complex layouts that are hard to parse automatically

### Issue: Large PDF processing is slow
- Process pages in batches
- Consider using multiprocessing for parallel processing
