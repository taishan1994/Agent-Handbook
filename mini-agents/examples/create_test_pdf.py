"""
Create a test PDF file for testing
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

def create_test_pdf(output_path):
    """Create a test PDF file"""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(inch, height - inch, "Test PDF Document")
    
    # Subtitle
    c.setFont("Helvetica", 14)
    c.drawString(inch, height - 1.5 * inch, "This is a test PDF for testing PDF processing skills")
    
    # Content
    c.setFont("Helvetica", 12)
    y = height - 2 * inch
    
    c.drawString(inch, y, "Introduction")
    y -= 0.5 * inch
    c.setFont("Helvetica", 10)
    text = "This is a test PDF document created for testing the PDF processing skill. "
    text += "It contains multiple pages with different types of content including text, "
    text += "tables, and various formatting."
    c.drawString(inch, y, text)
    
    y -= 0.75 * inch
    
    # Page 2
    c.showPage()
    c.setFont("Helvetica-Bold", 24)
    c.drawString(inch, height - inch, "Page 2: Data Table")
    
    c.setFont("Helvetica", 12)
    y = height - 1.5 * inch
    
    # Simple table
    c.drawString(inch, y, "ID")
    c.drawString(2 * inch, y, "Name")
    c.drawString(4 * inch, y, "Value")
    y -= 0.3 * inch
    
    c.line(inch, y, 6 * inch, y)
    y -= 0.3 * inch
    
    data = [
        ("1", "Item A", "100"),
        ("2", "Item B", "200"),
        ("3", "Item C", "300"),
        ("4", "Item D", "400"),
        ("5", "Item E", "500"),
    ]
    
    for item in data:
        c.drawString(inch, y, item[0])
        c.drawString(2 * inch, y, item[1])
        c.drawString(4 * inch, y, item[2])
        y -= 0.3 * inch
    
    # Page 3
    c.showPage()
    c.setFont("Helvetica-Bold", 24)
    c.drawString(inch, height - inch, "Page 3: Summary")
    
    c.setFont("Helvetica", 12)
    y = height - 1.5 * inch
    c.drawString(inch, y, "This PDF contains:")
    y -= 0.4 * inch
    c.drawString(inch, y, "• 3 pages")
    y -= 0.4 * inch
    c.drawString(inch, y, "• Text content")
    y -= 0.4 * inch
    c.drawString(inch, y, "• A data table")
    y -= 0.4 * inch
    c.drawString(inch, y, "• Various formatting")
    
    c.save()
    print(f"✓ Test PDF created: {output_path}")

if __name__ == "__main__":
    output_path = "/nfs/FM/gongoubo/new_project/Agent-Handbook/mini-agents/examples/test.pdf"
    create_test_pdf(output_path)
