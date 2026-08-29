import sqlite3
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
print("All invoices validated and updated successfully.")
