import os
import re
import sys
import glob
import pdfplumber
from typing import Dict, Any, Optional, List

sys.stdout.reconfigure(encoding='utf-8')

def parse_vietnam_pdf(pdf_bytes: bytes, filename: str = "") -> Optional[Dict[str, Any]]:
    import io
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"Error reading PDF {filename}: {e}")
        return None

    if not text.strip():
        # Scanned or empty PDF (like contract scan)
        return None

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    full_text = "\n".join(lines)

    # 1. Ký hiệu (kh_hd)
    kh_hd = ""
    m_kh = re.search(r"Ký\s*hiệu[\s\:\.\_]*([A-Za-z0-9\/]+)", full_text, re.IGNORECASE)
    if m_kh:
        kh_hd = m_kh.group(1).strip()
    else:
        m_kh2 = re.search(r"(?:KHHDon|Serial|Ký\s*hiệu\s*mẫu)[\s\:\.\_]*([A-Za-z0-9\/]+)", full_text, re.IGNORECASE)
        if m_kh2:
            kh_hd = m_kh2.group(1).strip()

    # 2. Số hóa đơn (so_hd)
    so_hd = ""
    m_so = re.search(r"(?:Số|No|SHDon|Số\s*HĐ)[\s\:\.\_]+(\d{1,10})", full_text, re.IGNORECASE)
    if m_so:
        so_hd = m_so.group(1).strip().zfill(7) if len(m_so.group(1)) <= 7 else m_so.group(1).strip()
    else:
        m_fn = re.search(r"(\d{4,10})", filename)
        if m_fn:
            so_hd = m_fn.group(1)

    # 3. Ngày lập (ngay_lap)
    ngay_lap = ""
    m_nlap = re.search(r"(?:Ngày\s*lập|Ngày)[\s\:\.\_]*(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})", full_text, re.IGNORECASE)
    if m_nlap:
        d, m, y = m_nlap.groups()
        ngay_lap = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        m_ngay_vn = re.search(r"Ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})", full_text, re.IGNORECASE)
        if m_ngay_vn:
            d, m, y = m_ngay_vn.groups()
            ngay_lap = f"{y}-{int(m):02d}-{int(d):02d}"

    # 4. Mã số thuế (MST)
    # Search all MST patterns: "Mã số thuế:0100109106" or "MST: 0100109106"
    msts = re.findall(r"(?:Mã\s*số\s*thuế|MST|Tax\s*code)[\s\:\.\_]*([0-9]{10}(?:-[0-9]{3})?)", full_text, re.IGNORECASE)
    mst_nban = msts[0] if len(msts) > 0 else ""
    mst_nmua = msts[1] if len(msts) > 1 else ""

    # 5. Tên người bán
    ten_nban = ""
    # In Viettel/VNPT: line with TẬP ĐOÀN... or CÔNG TY...
    for line in lines[:12]:
        up = line.upper()
        if ("TẬP ĐOÀN" in up or "CÔNG TY" in up or "DOANH NGHIỆP" in up) and "NGƯỜI MUA" not in up:
            ten_nban = line
            break
    if not ten_nban:
        m_nban = re.search(r"(?:Đơn\s*vị\s*bán\s*hàng|Tên\s*người\s*bán)[\s\:\.\_]*([^\n\r]+)", full_text, re.IGNORECASE)
        if m_nban:
            ten_nban = m_nban.group(1).strip()

    # 6. Tên người mua
    ten_nmua = ""
    m_nmua = re.search(r"(?:Họ\s*tên\s*người\s*mua\s*hàng|Tên\s*đơn\s*vị|Người\s*mua\s*hàng)[\s\:\.\_]*([^\n\r]+)", full_text, re.IGNORECASE)
    if m_nmua:
        ten_nmua = m_nmua.group(1).strip()

    # 7. Parsing Amounts (Chưa thuế, Tiền thuế, Tổng tiền)
    def clean_num(s: str) -> float:
        try:
            s = s.replace(".", "").replace(",", ".")
            return float(s)
        except Exception:
            return 0.0

    tien_chua_thue = 0.0
    tien_thue = 0.0
    tong_tien = 0.0
    items = []

    # Check for Viettel / Standard "CỘNG 163.636 16.364 180.000"
    m_cong = re.search(r"CỘNG\s+([0-9\.\,]+)\s+([0-9\.\,]+)\s+([0-9\.\,]+)", full_text, re.IGNORECASE)
    if m_cong:
        tien_chua_thue = clean_num(m_cong.group(1))
        tien_thue = clean_num(m_cong.group(2))
        tong_tien = clean_num(m_cong.group(3))
    else:
        # Check standard Total Payment
        m_tong = re.search(r"(?:TỔNG\s*CỘNG\s*TIỀN\s*THANH\s*TOÁN|Tổng\s*tiền\s*thanh\s*toán|Total\s*amount)[\s\:\.\_]*([0-9\.\,]+)", full_text, re.IGNORECASE)
        if m_tong:
            tong_tien = clean_num(m_tong.group(1))
            
        m_thue = re.search(r"(?:Tiền\s*thuế\s*GTGT|Thuế\s*GTGT|VAT\s*amount|Tiền\s*thuế)[\s\:\.\_]*([0-9\.\,]+)", full_text, re.IGNORECASE)
        if m_thue:
            tien_thue = clean_num(m_thue.group(1))
            
        m_chua = re.search(r"(?:Cộng\s*tiền\s*hàng|Tiền\s*hàng|Tổng\s*tiền\s*chưa\s*thuế)[\s\:\.\_]*([0-9\.\,]+)", full_text, re.IGNORECASE)
        if m_chua:
            tien_chua_thue = clean_num(m_chua.group(1))

    if tong_tien == 0.0 and tien_chua_thue > 0:
        tong_tien = tien_chua_thue + tien_thue

    # Check line item: "1 Dịch vụ FTTH 01 163.636 10% 16.364 180.000"
    m_item = re.search(r"(\d+)\s+([A-Za-z0-9\s\_\-]+?)\s+(\d+)\s+([0-9\.\,]+)\s+([0-9]+%)\s+([0-9\.\,]+)\s+([0-9\.\,]+)", full_text)
    if m_item:
        stt, ten_h, sl, tien_dv, vat_pct, tien_v, tt = m_item.groups()
        items.append({
            "stt": int(stt),
            "ten_hang": ten_h.strip(),
            "dvt": "Gói",
            "so_luong": clean_num(sl),
            "don_gia": clean_num(tien_dv),
            "thanh_tien": clean_num(tien_dv),
            "thue_suat": vat_pct,
            "tien_thue": clean_num(tien_v)
        })

    return {
        "filename": filename,
        "kh_mau": "1",
        "kh_hd": kh_hd if kh_hd else "PDF",
        "so_hd": so_hd,
        "ngay_lap": ngay_lap,
        "dv_tiente": "VND",
        "ty_gia": 1.0,
        "mst_nban": mst_nban,
        "ten_nban": ten_nban if ten_nban else "Tập đoàn Viễn thông",
        "dc_nban": "",
        "mst_nmua": mst_nmua,
        "ten_nmua": ten_nmua,
        "dc_nmua": "",
        "tien_chua_thue": tien_chua_thue,
        "tien_thue": tien_thue,
        "tong_tien": tong_tien,
        "items": items
    }

# Test on all 12 Viettel files
fld = r"\\10.102.8.250\财务部\13 TOYO SOLAR COMPANY LIMITED（越南）\1. O DIA CHUNG\2. GIANG\5. Invoice for expensive\2026\2026.08\SOLAR\VIETTEL"
print("--- TESTING REFINED PDF PARSER ON 12 INVOICES ---")
for f in sorted(glob.glob(os.path.join(fld, "1.发票*.pdf"))):
    with open(f, "rb") as fp:
        res = parse_vietnam_pdf(fp.read(), os.path.basename(f))
        if res:
            print(f"[{res['filename']}] Ký hiệu: {res['kh_hd']} | Số HĐ: {res['so_hd']} | Ngày: {res['ngay_lap']} | Người bán: {res['ten_nban']} (MST: {res['mst_nban']}) | Chưa thuế: {res['tien_chua_thue']:,.0f} | Thuế: {res['tien_thue']:,.0f} | Tổng: {res['tong_tien']:,.0f} VND")
