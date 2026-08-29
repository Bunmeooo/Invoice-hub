import os
import glob
import pdfplumber
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
viettel_dir = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2026\2026.08\SOLAR\VIETTEL"
files = sorted(glob.glob(os.path.join(viettel_dir, "1.发票*.pdf")))

print(f"Found {len(files)} Viettel PDF files.")
for f in files:
    with pdfplumber.open(f) as pdf:
        txt = ""
        for page in pdf.pages:
            txt += page.extract_text() or ""
        
        # Regex for website
        m_web = re.search(r"Website\s*tra\s*cứu(?:\s*hóa\s*đơn)?[\s\:\.\_]*(https?://[^\s\,]+)", txt, re.IGNORECASE)
        web_val = m_web.group(1).strip().rstrip(".") if m_web else "NOT_FOUND"
        
        # Regex for lookup code
        m_code = re.search(r"Mã\s*số\s*tra\s*cứu[\s\:\.\_]*([A-Za-z0-9]+)", txt, re.IGNORECASE)
        code_val = m_code.group(1).strip() if m_code else "NOT_FOUND"
        
        # Regex for invoice number
        m_so = re.search(r"Số[\s\:\.\_]+(\d+)", txt)
        so_val = m_so.group(1) if m_so else "N/A"
        
        print(f"File: {os.path.basename(f)} | Số HĐ: {so_val} | Website: {web_val} | Mã tra cứu: {code_val}")
