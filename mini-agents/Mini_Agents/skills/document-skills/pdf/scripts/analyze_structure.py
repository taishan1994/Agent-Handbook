"""
Analyze PDF Structure Script

Analyzes the structure and metadata of a PDF file
"""

import sys
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 is not installed. Install it with: pip install PyPDF2")
    sys.exit(1)


def analyze_pdf_structure(pdf_path):
    """Analyze PDF structure and metadata"""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return None
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            print("=== PDF Structure Analysis ===")
            print(f"File: {pdf_path}")
            print(f"File size: {pdf_path.stat().st_size} bytes")
            print("=" * 60)
            
            # Basic info
            num_pages = len(reader.pages)
            print(f"\n📄 Basic Information:")
            print(f"  Number of pages: {num_pages}")
            print(f"  Is encrypted: {reader.is_encrypted}")
            
            # Metadata
            print(f"\n📋 Metadata:")
            metadata = reader.metadata
            if metadata:
                for key, value in metadata.items():
                    if value:
                        print(f"  {key}: {value}")
            else:
                print("  No metadata available")
            
            # Page-by-page analysis
            print(f"\n📖 Page Analysis:")
            for page_num in range(min(num_pages, 5)):  # Analyze first 5 pages
                page = reader.pages[page_num]
                
                # Get page dimensions
                width = float(page.mediabox[2])
                height = float(page.mediabox[3])
                
                # Extract text to estimate content
                text = page.extract_text()
                text_length = len(text.strip())
                
                print(f"\n  Page {page_num + 1}:")
                print(f"    Dimensions: {width:.2f} x {height:.2f} points")
                print(f"    Text length: {text_length} characters")
                
                if text_length > 0:
                    preview = text[:100].replace('\n', ' ')
                    print(f"    Preview: {preview}...")
                else:
                    print(f"    Preview: (No text - might be an image)")
            
            if num_pages > 5:
                print(f"\n  ... and {num_pages - 5} more pages")
            
            return {
                'num_pages': num_pages,
                'is_encrypted': reader.is_encrypted,
                'metadata': metadata,
            }
            
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_structure.py <pdf_file>")
        print("Example: python analyze_structure.py /path/to/document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    analyze_pdf_structure(pdf_path)


if __name__ == "__main__":
    main()
