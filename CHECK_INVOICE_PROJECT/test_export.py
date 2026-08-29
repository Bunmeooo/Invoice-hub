import os
from database import InvoiceDatabase
from exporter import InvoiceExporter

db = InvoiceDatabase()
all_invs = db.get_all_invoices()
print(f"Exporting {len(all_invs)} invoices to Excel...")

excel_data = InvoiceExporter.export_comprehensive_excel(all_invs, db)
out_path = os.path.join(os.path.dirname(__file__), "test_export.xlsx")
with open(out_path, "wb") as f:
    f.write(excel_data)

print(f"Successfully generated {out_path} ({len(excel_data)} bytes).")
