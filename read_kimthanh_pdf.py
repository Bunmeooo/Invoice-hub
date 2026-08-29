import pdfplumber
import sys

sys.stdout.reconfigure(encoding='utf-8')
pdf_path = r"C:\Users\VSUN\Desktop\1C26TYY_00000578_2601084657.pdf"

try:
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"--- PDF PAGE {i+1} ---")
            print(page.extract_text())
except Exception as e:
    print(f"PDF Read error: {e}")
