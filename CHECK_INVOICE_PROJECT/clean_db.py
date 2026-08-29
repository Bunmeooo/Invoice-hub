import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect(r'C:\Users\VSUN\.gemini\antigravity\scratch\einvoice_app\invoices.db')
c = conn.cursor()

# Remove the sample test invoice
c.execute("DELETE FROM invoices WHERE filename = 'sample_invoice.xml'")
conn.commit()

# Check count
c.execute("SELECT COUNT(*) FROM invoices")
count = c.fetchone()[0]
print(f"Total real invoices in database: {count}")

c.execute("SELECT id, filename, so_hd, ngay_lap, ten_nban, tong_tien FROM invoices ORDER BY id ASC")
for row in c.fetchall():
    print(f"  - ID: {row[0]} | Tên file: {row[1]} | Số HĐ: {row[2]} | Ngày: {row[3]} | Tổng tiền: {row[5]:,.0f} đ")
