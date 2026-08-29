import pdfplumber
import sys

sys.stdout.reconfigure(encoding='utf-8')
pdf_path = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2025\2025.07\MADEOWN\1C25TMD_Chuacapso.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"--- PAGE {i+1} ---")
        print(page.extract_text())
