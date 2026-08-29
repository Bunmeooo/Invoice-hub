import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import InvoiceDatabase

db = InvoiceDatabase() # runs _init_db and auto-migrates columns
conn = db._get_connection()
c = conn.cursor()
c.execute("PRAGMA table_info(invoices)")
cols = [r["name"] for r in c.fetchall()]
print("Existing columns in invoices table:", cols)

from validator import InvoiceValidator
c.execute("SELECT * FROM invoices")
for r in c.fetchall():
    inv = dict(r)
    val = InvoiceValidator.validate_invoice(inv)
    c.execute("""
        UPDATE invoices SET
            sig_status = ?, is_valid = ?, status_summary = ?, notes = ?,
            ma_cqt = COALESCE(ma_cqt, 'Có mã CQT'),
            web_tra_cuu = COALESCE(web_tra_cuu, 'https://sinvoice.viettel.vn/utilities/invoice-search'),
            ma_tra_cuu = COALESCE(ma_tra_cuu, so_hd)
        WHERE id = ?
    """, (val["sig_status"], 1 if val["is_valid"] else 0, val["status_summary"], val["notes"], inv["id"]))
conn.commit()

c.execute("SELECT id, so_hd, ten_nban, mst_nban, tong_tien, sig_status, ma_cqt, web_tra_cuu, status_summary FROM invoices")
for r in c.fetchall():
    print(f"ID: {r['id']} | Số: {r['so_hd']} | NCC: {r['ten_nban'][:35]} | Tổng: {r['tong_tien']:,.0f} đ | Trạng thái: {r['status_summary']} | Mã CQT: {r['ma_cqt']}")
