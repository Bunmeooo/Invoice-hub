import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
from validator import InvoiceValidator

conn = sqlite3.connect(r'C:\Users\VSUN\.gemini\antigravity\scratch\einvoice_app\invoices.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT * FROM invoices")
rows = c.fetchall()

for r in rows:
    inv = dict(r)
    val = InvoiceValidator.validate_invoice(inv)
    c.execute("""
        UPDATE invoices SET
            sig_status = ?, is_valid = ?, status_summary = ?, notes = ?
        WHERE id = ?
    """, (val["sig_status"], 1 if val["is_valid"] else 0, val["status_summary"], val["notes"], inv["id"]))
    
conn.commit()

c.execute("SELECT id, so_hd, ten_nban, mst_nban, tong_tien, sig_status, ma_cqt, web_tra_cuu, ma_tra_cuu, status_summary FROM invoices")
for r in c.fetchall():
    print(f"ID: {r['id']} | Số: {r['so_hd']} | NCC: {r['ten_nban']} (MST: {r['mst_nban']}) | Tiền: {r['tong_tien']:,.0f} đ | Trạng thái: {r['status_summary']} | Mã CQT: {r['ma_cqt']} | Web: {r['web_tra_cuu']}")
