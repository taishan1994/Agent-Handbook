"""
Extract Text from PDF Script

Extracts all text from a PDF file
"""

import sys
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 is not installed. Install it with: pip install PyPDF2")
    sys.exit(1)


def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file"""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return None
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            num_pages = len(reader.pages)
            print(f"=== PDF Text Extraction ===")
            print(f"File: {pdf_path}")
            print(f"Number of pages: {num_pages}")
            print("=" * 60)
            
            all_text = ""
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                if text.strip():
                    all_text += text
                    print(f"\n--- Page {page_num + 1} ---")
                    print(text)
                else:
                    print(f"\n--- Page {page_num + 1} ---")
                    print("(No text found - might be an image or empty page)")
            
            return all_text
            
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python extract_text.py <pdf_file>")
        print("Example: python extract_text.py /path/to/document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    extract_text_from_pdf(pdf_path)


if __name__ == "__main__":
    main()
