import os
import re
import sys
import pdfplumber
import pypdf
from typing import Dict, Any, Optional, List

sys.stdout.reconfigure(encoding='utf-8')

def parse_pdf_invoice(pdf_bytes: bytes, filename: str = "") -> Optional[Dict[str, Any]]:
    """Extract structured invoice fields from a PDF e-invoice"""
    text = ""
    try:
        # 1. Try reading with pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception:
        try:
            # Fallback to pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        except Exception as e:
            print(f"Error reading PDF {filename}: {e}")
            return None

    if not text.strip():
        # Scanned image PDF without text layer
        return {
            "filename": filename,
            "kh_mau": "",
            "kh_hd": "",
            "so_hd": os.path.splitext(filename)[0],
            "ngay_lap": "",
            "dv_tiente": "VND",
            "ty_gia": 1.0,
            "mst_nban": "",
            "ten_nban": "PDF Hóa đơn (Chưa OCR)",
            "dc_nban": "",
            "mst_nmua": "",
            "ten_nmua": "",
            "dc_nmua": "",
            "tien_chua_thue": 0.0,
            "tien_thue": 0.0,
            "tong_tien": 0.0,
            "items": []
        }

    # Normalize text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_text = " ".join(lines)

    # 1. Extract Số Hóa Đơn
    so_hd = ""
    # Look for "Số/No: 00001530" or "Số: 1530" or "Số HĐ: 1530"
    m_so = re.search(r"(?:Số|No|SHDon|Số\s*HĐ|Số\s*hóa\s*đơn)[\s\:\.\_]*([A-Za-z0-9\-]+)", full_text, re.IGNORECASE)
    if m_so:
        so_hd = m_so.group(1).strip()
    else:
        # Fallback extract digits from filename (e.g. 1.发票1530.pdf -> 1530)
        m_fn = re.search(r"(\d{3,8})", filename)
        if m_fn:
            so_hd = m_fn.group(1)

    # 2. Extract Ký hiệu Hóa đơn
    kh_hd = ""
    m_kh = re.search(r"(?:Ký\s*hiệu|KHHDon|Serial|Ký\s*hiệu\s*mẫu)[\s\:\.\_]*([A-Za-z0-9\/]+)", full_text, re.IGNORECASE)
    if m_kh:
        kh_hd = m_kh.group(1).strip()

    # 3. Extract Ngày lập
    ngay_lap = ""
    # "Ngày 15 tháng 03 năm 2024" or "15/03/2024" or "2024-03-15"
    m_ngay_vn = re.search(r"Ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})", full_text, re.IGNORECASE)
    if m_ngay_vn:
        d, m, y = m_ngay_vn.groups()
        ngay_lap = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        m_ngay_slash = re.search(r"(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})", full_text)
        if m_ngay_slash:
            d, m, y = m_ngay_slash.groups()
            ngay_lap = f"{y}-{int(m):02d}-{int(d):02d}"

    # 4. Extract Mã số thuế (MST)
    # Vietnam MST is either 10 digits or 10 digits - 3 digits (13 chars)
    msts = re.findall(r"(?:Mã\s*số\s*thuế|MST|Tax\s*code)[\s\:\.\_]*([0-9]{10}(?:-[0-9]{3})?)", full_text, re.IGNORECASE)
    mst_nban = msts[0] if len(msts) > 0 else ""
    mst_nmua = msts[1] if len(msts) > 1 else ""

    # 5. Extract Amounts
    # Helper to parse money numbers: 1.900.000.000 or 1,900,000,000 or 1900000000
    def parse_money(val_str: str) -> float:
        try:
            # remove spaces
            s = val_str.replace(" ", "").replace("VND", "").replace("đ", "").strip()
            if "," in s and "." in s:
                if s.rfind(",") > s.rfind("."):
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", "")
            elif "," in s:
                # check if comma is decimal or thousand separator
                parts = s.split(",")
                if len(parts[-1]) == 3:
                    s = s.replace(",", "")
                else:
                    s = s.replace(",", ".")
            elif "." in s:
                parts = s.split(".")
                if len(parts[-1]) == 3:
                    s = s.replace(".", "")
            return float(s)
        except Exception:
            return 0.0

    tien_chua_thue = 0.0
    tien_thue = 0.0
    tong_tien = 0.0

    # Search total payment
    m_tong = re.search(r"(?:Tổng\s*cộng\s*tiền\s*thanh\s*toán|Tổng\s*tiền\s*thanh\s*toán|Total\s*amount|Tổng\s*thanh\s*toán)[\s\:\.\_]*([0-9\.\,\s]+)", full_text, re.IGNORECASE)
    if m_tong:
        tong_tien = parse_money(m_tong.group(1))

    m_thue = re.search(r"(?:Tiền\s*thuế\s*GTGT|Thuế\s*GTGT|VAT\s*amount|Tiền\s*thuế)[\s\:\.\_]*([0-9\.\,\s]+)", full_text, re.IGNORECASE)
    if m_thue:
        tien_thue = parse_money(m_thue.group(1))

    m_chua_thue = re.search(r"(?:Cộng\s*tiền\s*hàng|Tiền\s*hàng|Tổng\s*tiền\s*chưa\s*thuế|Subtotal)[\s\:\.\_]*([0-9\.\,\s]+)", full_text, re.IGNORECASE)
    if m_chua_thue:
        tien_chua_thue = parse_money(m_chua_thue.group(1))

    if tong_tien == 0.0 and tien_chua_thue > 0:
        tong_tien = tien_chua_thue + tien_thue
    elif tien_chua_thue == 0.0 and tong_tien > 0:
        tien_chua_thue = tong_tien - tien_thue

    # 6. Extract Seller & Buyer names
    ten_nban = ""
    m_nban = re.search(r"(?:Đơn\s*vị\s*bán\s*hàng|Tên\s*người\s*bán|Seller|Công\s*ty\s*bán)[\s\:\.\_]*([^\n\r]+)", text, re.IGNORECASE)
    if m_nban:
        ten_nban = m_nban.group(1).strip()
    else:
        # Fallback: check first 5 lines for "CÔNG TY"
        for l in lines[:5]:
            if "CÔNG TY" in l.upper() or "COMPANY" in l.upper() or "LIMITED" in l.upper():
                ten_nban = l
                break

    ten_nmua = ""
    m_nmua = re.search(r"(?:Tên\s*đơn\s*vị|Người\s*mua\s*hàng|Buyer|Tên\s*người\s*mua)[\s\:\.\_]*([^\n\r]+)", text, re.IGNORECASE)
    if m_nmua:
        ten_nmua = m_nmua.group(1).strip()

    return {
        "filename": filename,
        "kh_mau": "1",
        "kh_hd": kh_hd if kh_hd else "PDF",
        "so_hd": so_hd if so_hd else os.path.splitext(filename)[0],
        "ngay_lap": ngay_lap,
        "dv_tiente": "VND",
        "ty_gia": 1.0,
        "mst_nban": mst_nban,
        "ten_nban": ten_nban if ten_nban else "Hóa đơn PDF",
        "dc_nban": "",
        "mst_nmua": mst_nmua,
        "ten_nmua": ten_nmua,
        "dc_nmua": "",
        "tien_chua_thue": tien_chua_thue,
        "tien_thue": tien_thue,
        "tong_tien": tong_tien,
        "items": []
    }

print("PDF parser test module initialized successfully.")
