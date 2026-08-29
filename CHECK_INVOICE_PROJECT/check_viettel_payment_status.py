import os
import glob
import pdfplumber
import sys

sys.stdout.reconfigure(encoding='utf-8')
viettel_dir = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2026\2026.08\SOLAR\VIETTEL"
files = sorted(glob.glob(os.path.join(viettel_dir, "1.发票*.pdf")))

print(f"Checking payment and issue status for {len(files)} Viettel files:")
for f in files:
    with pdfplumber.open(f) as pdf:
        txt = ""
        for page in pdf.pages:
            txt += page.extract_text() or ""
        
        has_chua_tt = "CHƯA THANH TOÁN" in txt or "Chua thanh toan" in txt or "chưa thanh toán" in txt
        has_da_tt = "ĐÃ THANH TOÁN" in txt or "Da thanh toan" in txt or "đã thanh toán" in txt
        
        print(f"- File: {os.path.basename(f)} | 'CHƯA THANH TOÁN': {has_chua_tt} | 'ĐÃ THANH TOÁN': {has_da_tt}")
