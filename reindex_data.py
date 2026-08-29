import os
import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')
from parser import InvoiceParser
from database import InvoiceDatabase

db = InvoiceDatabase()
fld = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2026\2026.08\SOLAR\VIETTEL"

files = sorted(glob.glob(os.path.join(fld, "1.发票*.pdf")))
print(f"Re-indexing {len(files)} invoices...")
for f in files:
    invs = InvoiceParser.parse_file(f)
    for inv in invs:
        db.insert_invoice(inv, overwrite=True)

all_invs = db.get_all_invoices()
print(f"Database successfully updated with {len(all_invs)} invoices:")
for inv in all_invs:
    print(f"  - Số HĐ: {inv['so_hd']} | NCC: {inv['ten_nban']} (MST: {inv['mst_nban']}) | Tổng: {inv['tong_tien']:,.0f} đ | Chữ ký: {inv['sig_status']} | Đánh giá: {inv['status_summary']}")
