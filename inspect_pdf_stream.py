import pypdf
import sys

sys.stdout.reconfigure(encoding='utf-8')
pdf_path = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2026\2026.08\SOLAR\VIETTEL\1.发票1718.pdf"

reader = pypdf.PdfReader(pdf_path)
page = reader.pages[0]

print("--- RAW TEXT FROM PYPDF ---")
print(page.extract_text())

print("\n--- IMAGES IN PAGE ---")
for count, img in enumerate(page.images):
    print(f"Image {count}: {img.name}")
