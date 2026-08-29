import pypdf
import os

pdf_path = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2026\2026.08\SOLAR\VIETTEL\1.发票1718.pdf"
reader = pypdf.PdfReader(pdf_path)
page = reader.pages[0]

out_dir = r"C:\Users\VSUN\.gemini\antigravity\scratch\einvoice_app\extracted_imgs"
os.makedirs(out_dir, exist_ok=True)

for idx, img in enumerate(page.images):
    img_path = os.path.join(out_dir, f"{idx}_{img.name}")
    with open(img_path, "wb") as f:
        f.write(img.data)
    print(f"Saved {img_path} ({len(img.data)} bytes)")
