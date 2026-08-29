import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect(r'C:\Users\VSUN\.gemini\antigravity\scratch\einvoice_app\invoices.db')
c = conn.cursor()

# Remove records with total = 0 or test data
c.execute("DELETE FROM invoices WHERE tong_tien = 0")
conn.commit()

c.execute("SELECT id, so_hd, kh_hd, ngay_lap, ten_nban, mst_nban, tong_tien, sig_status, status_summary FROM invoices ORDER BY id ASC")
rows = c.fetchall()
print(f"Total active invoices in DB: {len(rows)}")
for r in rows:
    print(f"  - ID: {r[0]} | Số HĐ: {r[1]} | Ký hiệu: {r[2]} | Ngày: {r[3]} | NCC: {r[4]} (MST: {r[5]}) | Tổng: {r[6]:,.0f} đ | Chữ ký: {r[7]} | {r[8]}")
