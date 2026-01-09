"""
Extract Tables from PDF Script

Extracts tables from a PDF file using pdfplumber
"""

import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is not installed. Install it with: pip install pdfplumber")
    sys.exit(1)


def extract_tables_from_pdf(pdf_path):
    """Extract tables from a PDF file"""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print("=== PDF Table Extraction ===")
            print(f"File: {pdf_path}")
            print(f"Number of pages: {len(pdf.pages)}")
            print("=" * 60)
            
            all_tables = []
            
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                
                if tables:
                    print(f"\n📊 Page {page_num + 1}: Found {len(tables)} table(s)")
                    
                    for table_num, table in enumerate(tables):
                        print(f"\n  Table {table_num + 1}:")
                        print(f"    Rows: {len(table)}")
                        if len(table) > 0:
                            print(f"    Columns: {len(table[0])}")
                            
                            # Print first few rows as preview
                            print(f"    Preview (first 3 rows):")
                            for row_num, row in enumerate(table[:3]):
                                print(f"      Row {row_num + 1}: {row}")
                            
                            if len(table) > 3:
                                print(f"      ... and {len(table) - 3} more rows")
                        
                        all_tables.append({
                            'page': page_num + 1,
                            'table_num': table_num + 1,
                            'data': table
                        })
            
            if not all_tables:
                print("\nNo tables found in the PDF")
            
            return all_tables
            
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python extract_tables.py <pdf_file>")
        print("Example: python extract_tables.py /path/to/document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    extract_tables_from_pdf(pdf_path)


if __name__ == "__main__":
    main()
