import os
import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')
from parser import InvoiceParser
from database import InvoiceDatabase
from exporter import InvoiceExporter

db = InvoiceDatabase()
db.clear_all()

# 1. Parse Madeown invoice
madeown_pdf = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2025\2025.07\MADEOWN\1C25TMD_Chuacapso.pdf"
if os.path.exists(madeown_pdf):
    invs_m = InvoiceParser.parse_file(madeown_pdf)
    for inv in invs_m:
        db.insert_invoice(inv, overwrite=True)

# 2. Parse Viettel invoices
viettel_dir = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2026\2026.08\SOLAR\VIETTEL"
if os.path.exists(viettel_dir):
    for f in sorted(glob.glob(os.path.join(viettel_dir, "1.发票*.pdf"))):
        invs_v = InvoiceParser.parse_file(f)
        for inv in invs_v:
            db.insert_invoice(inv, overwrite=True)

all_invs = db.get_all_invoices()
print(f"Total invoices in DB: {len(all_invs)}")
for inv in all_invs:
    print(f"- Số: {inv['so_hd']} | NCC: {inv['ten_nban']} (MST: {inv['mst_nban']}) | Tiền: {inv['tong_tien']:,.0f} đ | Chữ ký: {inv['sig_status']} | Mã CQT: {inv['ma_cqt']} | Mã TC: {inv['ma_tra_cuu']} | Đánh giá: {inv['status_summary']}")

# Generate Excel
excel_bytes = InvoiceExporter.export_comprehensive_excel(all_invs, db)
out_excel = os.path.join(os.path.dirname(__file__), "test_pipeline.xlsx")
with open(out_excel, "wb") as f:
    f.write(excel_bytes)
print(f"Generated test Excel file: {out_excel} ({len(excel_bytes)} bytes)")
