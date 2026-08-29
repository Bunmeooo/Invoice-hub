import os
import re
import zipfile
import shutil
import subprocess
import tempfile
import io
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import pdfplumber
import pypdf
import rarfile
from validator import InvoiceValidator

# Configure unrar/7z tool for rarfile
for p in [r"C:\Program Files\WinRAR\UnRAR.exe", r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\WinRAR\UnRAR.exe"]:
    if os.path.exists(p):
        rarfile.UNRAR_TOOL = p
        break

# Provider Tax Code (MSTTCGP) to Portal Mapping
SOLUTION_PROVIDERS_MAP = {
    "0101243150": ("MISA meInvoice", "https://www.meinvoice.vn/tra-cuu/"),
    "0100109106": ("Viettel S-Invoice", "https://sinvoice.viettel.vn/utilities/invoice-search"),
    "0101360697": ("BKAV eHoadon", "http://tracuu.ehoadon.vn"),
    "0100686209": ("VNPT Invoice", "https://portal.vnpt-invoice.com.vn"),
    "0301097491": ("FAST e-Invoice", "https://invoice.fast.com.vn"),
    "0100234479": ("BRAVO e-Invoice", "https://einvoice.bravo.com.vn"),
    "0313886561": ("CyberBill", "https://cyberbill.vn/tra-cuu/"),
    "0102604609": ("Thái Sơn E-Invoice", "https://einvoice.vn/tra-cuu"),
    "0303102146": ("Vina-CA / SmartSign", "https://smartsign.com.vn"),
    "0311226265": ("EasyInvoice (Softdreams)", "https://easyinvoice.vn/tra-cuu/")
}

def clean_tag(tag: str) -> str:
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

def get_text(element: Optional[ET.Element], default: str = "") -> str:
    if element is not None and element.text is not None:
        return element.text.strip()
    return default

def get_float(element: Optional[ET.Element], default: float = 0.0) -> float:
    val_str = get_text(element)
    if not val_str:
        return default
    try:
        val_str = val_str.replace(",", ".")
        return float(val_str)
    except ValueError:
        return default

def clean_num(s: str) -> float:
    if not s:
        return 0.0
    try:
        s = str(s).replace(" ", "").replace("VND", "").replace("đ", "").replace("USD", "").replace("$", "").strip()
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
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

def clean_supplier_name(name: str) -> str:
    if not name:
        return ""
    s = name.strip()
    s = re.sub(r"^(?:Đơn\s*vị\s*bán\s*hàng|Đơn\s*vị\s*bán|Tên\s*người\s*bán|Tên\s*đơn\s*vị)?\s*(?:\(Supplier\)|\(Seller\)|\(Issued\)|\(Issued\s*by\)|Supplier|Seller)?[\s\:\.\_\-]*", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"^[\:\.\_\-\s]+", "", s).strip()
    return s

def clean_buyer_name(name: str) -> str:
    if not name:
        return "CÔNG TY TNHH TOYO SOLAR"
    s = name.strip()
    s = re.sub(r"^(?:Họ\s*tên\s*người\s*mua\s*hàng|Tên\s*đơn\s*vị|Người\s*mua\s*hàng|Người\s*mua)?\s*(?:\(Buyer\)|\(Buyer\s*name\)|\(Co\.\s*name\)|\(Company\'s\s*name\)|Buyer)?[\s\:\.\_\-]*", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"^[\:\.\_\-\s]+", "", s).strip()
    return s if s else "CÔNG TY TNHH TOYO SOLAR"

def clean_address(addr: str) -> str:
    if not addr:
        return ""
    s = addr.strip()
    s = re.sub(r"^(?:Địa\s*chỉ\s*\(Address\)|Địa\s*chỉ|Address)[\s\:\.\_\-]*", "", s, flags=re.IGNORECASE).strip()
    for kw in ["(Buyer)", "(Buyer name)", "(Co. name)", "Họ tên người mua", "Tên đơn vị:", "Người mua hàng"]:
        if kw in s:
            s = s.split(kw)[0].strip()
    return s.rstrip(";").rstrip(",").strip()

class InvoiceParser:
    """Universal Parser for Vietnamese E-Invoices (XML, PDF, ZIP, RAR)"""
    
    @staticmethod
    def parse_xml_content(xml_bytes: bytes, filename: str = "") -> Optional[Dict[str, Any]]:
        """Parse XML E-Invoice (ND 123 / TT 78 / TT 91/2026/TT-BTC) extracting Lookups & Signatures"""
        try:
            root = ET.fromstring(xml_bytes)
        except Exception:
            return None
            
        def find_element(node: ET.Element, tag_name: str) -> Optional[ET.Element]:
            for elem in node.iter():
                if clean_tag(elem.tag).lower() == tag_name.lower():
                    return elem
            return None

        def find_all_elements(node: ET.Element, tag_name: str) -> List[ET.Element]:
            results = []
            for elem in node.iter():
                if clean_tag(elem.tag).lower() == tag_name.lower():
                    results.append(elem)
            return results

        # 1. Header
        kh_mau = get_text(find_element(root, "KHMSHDon") or find_element(root, "KHMHDon"), default="1")
        kh_hd = get_text(find_element(root, "KHHDon"))
        so_hd = get_text(find_element(root, "SHDon"))
        ngay_lap = get_text(find_element(root, "NLap"))
        dv_tiente = get_text(find_element(root, "DVTTe"), default="VND")
        ty_gia = get_float(find_element(root, "TGia"), default=1.0)
        ma_cqt_xml = get_text(find_element(root, "MCCQT"))
        mst_tcgp = get_text(find_element(root, "MSTTCGP"))
        
        # 2. Seller
        nban = find_element(root, "NBan")
        ten_nban = clean_supplier_name(get_text(find_element(nban, "Ten") if nban is not None else None))
        mst_nban = get_text(find_element(nban, "MST") if nban is not None else None)
        dc_nban = clean_address(get_text(find_element(nban, "DChi") if nban is not None else None))
        
        # 3. Buyer
        nmua = find_element(root, "NMua")
        ten_nmua = clean_buyer_name(get_text(find_element(nmua, "Ten") if nmua is not None else None))
        mst_nmua = get_text(find_element(nmua, "MST") if nmua is not None else None)
        dc_nmua = clean_address(get_text(find_element(nmua, "DChi") if nmua is not None else None))
        
        # 4. Digital Signature
        sig_elem = find_element(root, "Signature")
        has_signature = False
        sig_status = "Chưa ký số"
        signer = ""
        sign_time = ""
        
        if sig_elem is not None:
            has_signature = True
            sig_status = "Đã ký số"
            subj = find_element(sig_elem, "X509SubjectName")
            if subj is not None and subj.text:
                m_cn = re.search(r"CN=([^,]+)", subj.text)
                signer = m_cn.group(1).strip() if m_cn else subj.text[:60]
            if not signer:
                signer = ten_nban
            st_elem = find_element(sig_elem, "SigningTime")
            sign_time = get_text(st_elem)
        
        # 5. Totals
        ttoan = find_element(root, "TToan")
        tien_chua_thue = get_float(find_element(ttoan, "TgTCThue") if ttoan is not None else None)
        tien_thue = get_float(find_element(ttoan, "TgTThue") if ttoan is not None else None)
        tong_tien = get_float(find_element(ttoan, "TgTTToan") or find_element(ttoan, "TgTTTBSo") if ttoan is not None else None)
        
        if tong_tien == 0.0:
            tong_tien = tien_chua_thue + tien_thue
            
        # 6. Line items
        items = []
        dshh = find_element(root, "DSHHDVu") or find_element(root, "DSHangHoa")
        hh_elements = find_all_elements(dshh, "HHDVu") if dshh is not None else find_all_elements(root, "HHDVu")
        
        for idx, hh in enumerate(hh_elements, 1):
            ten_hh = get_text(find_element(hh, "THHDVu"))
            dvt = get_text(find_element(hh, "DVTinh"), default="Gói")
            so_luong = get_float(find_element(hh, "SLuong"), default=1.0)
            don_gia = get_float(find_element(hh, "DGia"))
            thanh_tien = get_float(find_element(hh, "ThTien"))
            thue_suat = get_text(find_element(hh, "TSuat"), default="0%")
            tien_thue_hh = get_float(find_element(hh, "TThue"))
            
            if ten_hh:
                items.append({
                    "stt": idx,
                    "ten_hang": ten_hh,
                    "dvt": dvt,
                    "so_luong": so_luong,
                    "don_gia": don_gia,
                    "thanh_tien": thanh_tien,
                    "thue_suat": thue_suat,
                    "tien_thue": tien_thue_hh
                })

        # 7. Extract Website tra cứu & Mã số tra cứu từ XML
        ma_tra_cuu = ""
        dlhdon_elem = find_element(root, "DLHDon")
        if dlhdon_elem is not None and "Id" in dlhdon_elem.attrib:
            ma_tra_cuu = dlhdon_elem.attrib["Id"]
            
        if not ma_tra_cuu:
            for ttin in find_all_elements(root, "TTin"):
                ttruong = get_text(find_element(ttin, "TTruong"))
                if ttruong in ["TransactionID", "LookupCode", "InvoiceCode", "MaTraCuu", "MaBiMat"]:
                    ma_tra_cuu = get_text(find_element(ttin, "DLieu"))
                    if ma_tra_cuu:
                        break
                        
        if not ma_tra_cuu:
            ma_tra_cuu = "Chưa có mã tra cứu"

        web_tra_cuu = ""
        if mst_tcgp in SOLUTION_PROVIDERS_MAP:
            provider_name, web_tra_cuu = SOLUTION_PROVIDERS_MAP[mst_tcgp]
        else:
            if "misa" in str(xml_bytes).lower():
                web_tra_cuu = "https://www.meinvoice.vn/tra-cuu/"
            elif "viettel" in str(xml_bytes).lower():
                web_tra_cuu = "https://sinvoice.viettel.vn/utilities/invoice-search"
            elif "bkav" in str(xml_bytes).lower() or "ehoadon" in str(xml_bytes).lower():
                web_tra_cuu = "http://tracuu.ehoadon.vn"
            elif "vnpt" in str(xml_bytes).lower():
                web_tra_cuu = "https://portal.vnpt-invoice.com.vn"
            else:
                web_tra_cuu = "https://hoadondientu.gdt.gov.vn"

        ma_cqt = ma_cqt_xml if ma_cqt_xml else ("Không có mã CQT (HĐ không mã)" if "viettel" in ten_nban.lower() else "Chưa có mã CQT")

        inv_data = {
            "filename": filename,
            "kh_mau": kh_mau,
            "kh_hd": kh_hd if kh_hd else "XML",
            "so_hd": so_hd if so_hd else os.path.splitext(filename)[0],
            "ngay_lap": ngay_lap,
            "dv_tiente": dv_tiente,
            "ty_gia": ty_gia,
            "mst_nban": mst_nban,
            "ten_nban": ten_nban,
            "dc_nban": dc_nban,
            "mst_nmua": mst_nmua if mst_nmua else "2601084657",
            "ten_nmua": ten_nmua,
            "dc_nmua": dc_nmua,
            "tien_chua_thue": tien_chua_thue,
            "tien_thue": tien_thue,
            "tong_tien": tong_tien,
            "ma_cqt": ma_cqt,
            "web_tra_cuu": web_tra_cuu,
            "ma_tra_cuu": ma_tra_cuu,
            "has_signature": has_signature,
            "sig_status": sig_status,
            "signer": signer,
            "sign_time": sign_time,
            "items": items
        }
        
        val_res = InvoiceValidator.validate_invoice(inv_data)
        inv_data.update(val_res)
        return inv_data

    @staticmethod
    def parse_pdf_content(pdf_bytes: bytes, filename: str = "") -> Optional[Dict[str, Any]]:
        """Parse PDF E-Invoice extracting Tax Authority Code, Lookups, Line items, Signatures"""
        text = ""
        has_unpaid_stamp = False
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
                    # Check for diagonal stamp / unpaid watermark
                    if len(page.images) >= 3:
                        has_unpaid_stamp = True
        except Exception:
            try:
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
                    if len(page.images) >= 3:
                        has_unpaid_stamp = True
            except Exception:
                pass

        if not text.strip():
            return None

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        full_text = "\n".join(lines)

        # 1. KÝ HIỆU HÓA ĐƠN & MẪU SỐ
        kh_hd = ""
        m_symbol = re.search(r"\b([1-6]?[C|K|M][0-9]{2}[A-Z0-9]{2,4})\b", full_text[:1200])
        if m_symbol:
            kh_hd = m_symbol.group(1).upper()
        else:
            m_kh = re.search(r"(?:Mẫu\s*số\s*[\-\/]\s*)?Ký\s*hiệu(?:\s*\(Serial(?:\s*No\.?)?\))?[\s\:\.\_\-]*([A-Za-z0-9\/]+)", full_text, re.IGNORECASE)
            if m_kh and m_kh.group(1).lower() not in ["no", "serial", "sign", "no."]:
                kh_hd = m_kh.group(1).strip().upper()

        # 2. Số hóa đơn
        so_hd = ""
        if "<Chưa cấp số>" in full_text or "Chưa cấp số" in full_text:
            so_hd = "<Chưa cấp số>"
        else:
            m_so = re.search(r"(?:Số\s*\(No\.\)|Số\s*\(No\)|Số|No|SHDon|Số\s*HĐ|Invoice\s*No\.?)[\s\:\.\_]+(\d{1,10})", full_text, re.IGNORECASE)
            if m_so:
                so_hd = m_so.group(1).strip()
                if len(so_hd) < 7:
                    so_hd = so_hd.zfill(7)
            else:
                m_fn = re.search(r"(\d{3,10})", filename)
                so_hd = m_fn.group(1).zfill(7) if m_fn else os.path.splitext(filename)[0]

        # 3. Ngày lập
        ngay_lap = ""
        m_ngay_vn = re.search(r"Ngày\s*(?:\(day\)|(?:\(Date\)))?\s*(\d{1,2})\s*tháng\s*(?:\(month\))?\s*(\d{1,2})\s*năm\s*(?:\(year\))?\s*(\d{4})", full_text, re.IGNORECASE)
        if m_ngay_vn:
            d, m, y = m_ngay_vn.groups()
            ngay_lap = f"{y}-{int(m):02d}-{int(d):02d}"
        else:
            m_nlap = re.search(r"(?:Ngày\s*lập|Ngày|Ký\s*ngày)[\s\:\.\_]*(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})", full_text, re.IGNORECASE)
            if m_nlap:
                d, m, y = m_nlap.groups()
                ngay_lap = f"{y}-{int(m):02d}-{int(d):02d}"

        # 4. Mã của cơ quan thuế (Mã CQT)
        ma_cqt = ""
        m_cqt = re.search(r"(?:Mã\s*của\s*Cơ\s*quan\s*thuế|Mã\s*CQT\s*\(Code\)|Mã\s*CQT)[\s\:\.\_]*([0-9A-F]{20,40})", full_text, re.IGNORECASE)
        if m_cqt:
            ma_cqt = m_cqt.group(1).strip()
        else:
            if "viettel" in full_text.lower() and "quân đội" in full_text.lower():
                ma_cqt = "Không có mã CQT (HĐ không mã)"
            else:
                ma_cqt = "Chưa có mã CQT"

        # 5. Website tra cứu & Mã bí mật tra cứu
        web_tra_cuu = ""
        m_web = re.search(r"(?:Website\s*tra\s*cứu(?:\s*hóa\s*đơn)?|Tra\s*cứu\s*tại\s*Website|trực\s*tuyến\s*tại|Website|trang\s*web)[\s\:\.\_\(Search\s*on\s*Website\)]*(https?://[^\s\,]+)", full_text, re.IGNORECASE)
        if m_web:
            web_tra_cuu = m_web.group(1).strip().rstrip(".")
        elif "vietteltelecom.vn" in full_text.lower():
            web_tra_cuu = "https://vietteltelecom.vn/hoadondientu/"
        elif "ehoadon" in full_text.lower():
            web_tra_cuu = "http://tracuu.ehoadon.vn"
        elif "viettel" in full_text.lower():
            web_tra_cuu = "https://vietteltelecom.vn/hoadondientu/"
        elif "meinvoice" in full_text.lower():
            web_tra_cuu = "https://www.meinvoice.vn/tra-cuu/"
        else:
            web_tra_cuu = "https://hoadondientu.gdt.gov.vn"

        ma_tra_cuu = ""
        m_matc1 = re.search(r"Mã\s*số\s*tra\s*cứu[\s\:\.\_]*([A-Za-z0-9]+)", full_text, re.IGNORECASE)
        if m_matc1 and m_matc1.group(1).lower() not in ["website", "http", "https"]:
            ma_tra_cuu = m_matc1.group(1).strip()
        else:
            m_matc2 = re.search(r"Mã\s*tra\s*cứu\s*HĐĐT(?:\s*này)?[\s\:\.\_]*([A-Za-z0-9]+)", full_text, re.IGNORECASE)
            if m_matc2:
                ma_tra_cuu = m_matc2.group(1).strip()
            else:
                m_matc3 = re.search(r"(?:Mã\s*tra\s*cứu\s*\(Invoice\s*code\)|Mã\s*số\s*bí\s*mật|Mã\s*bí\s*mật)[\s\:\.\_]*([A-Za-z0-9]+)", full_text, re.IGNORECASE)
                if m_matc3:
                    ma_tra_cuu = m_matc3.group(1).strip()
                else:
                    m_vtt_code = re.search(r"Mã\s*số\s*nhận\s*HĐ[\s\:\.\_]*(\d{5,8})", full_text, re.IGNORECASE)
                    if m_vtt_code:
                        ma_tra_cuu = m_vtt_code.group(1).strip()
                    else:
                        ma_tra_cuu = "Chưa có mã tra cứu"

        # 6. Người bán (Tên, MST, Địa chỉ)
        ten_nban = ""
        mst_nban = ""
        dc_nban = ""

        m_sell_name = re.search(r"(?:Đơn\s*vị\s*bán\s*(?:hàng)?\s*(?:\(Supplier\))?\s*(?:\(Seller\))?\s*(?:\(Issued\))?|Tên\s*người\s*bán)[\s\:\.\_]*([^\n\r]+)", full_text, re.IGNORECASE)
        if m_sell_name:
            ten_nban = clean_supplier_name(m_sell_name.group(1))
        else:
            for l in lines[:12]:
                up = l.upper()
                if any(k in up for k in ["TẬP ĐOÀN", "CÔNG TY", "DOANH NGHIỆP", "CHI NHÁNH"]) and "NGƯỜI MUA" not in up and "KÝ BỞI" not in up and "CUNG CẤP DỊCH VỤ" not in up and "MISA" not in up and "BKAV" not in up:
                    ten_nban = clean_supplier_name(l)
                    break

        m_mst_seller = re.search(r"(?:MST\s*\(Tax\s*Code\)|Mã\s*số\s*thuế\s*\(Tax\s*code\)|Mã\s*số\s*thuế|MST)[\s\:\.\_]*([0-9]{10}(?:-[0-9]{3})?)", full_text[:1200], re.IGNORECASE)
        if m_mst_seller:
            mst_nban = m_mst_seller.group(1).strip()
        else:
            msts = re.findall(r"([0-9]{10}(?:-[0-9]{3})?)", full_text)
            if msts:
                mst_nban = msts[0]

        m_dc_seller = re.search(r"(?:Địa\s*chỉ\s*\(Address\)|Địa\s*chỉ)[\s\:\.\_]*([^\n\r]+)", full_text[:1500], re.IGNORECASE)
        if m_dc_seller:
            dc_nban = clean_address(m_dc_seller.group(1))

        # 7. Người mua
        ten_nmua = "CÔNG TY TNHH TOYO SOLAR"
        mst_nmua = ""
        dc_nmua = ""
        
        m_buy_name = re.search(r"(?:Đơn\s*vị\s*\(Company\'s\s*name\)|Đơn\s*vị\s*\(Co\.\s*name\)|Tên\s*đơn\s*vị|Người\s*mua\s*hàng\s*\(Buyer\)|Họ\s*tên\s*người\s*mua\s*hàng)[\s\:\.\_]*([^\n\r]+)", full_text, re.IGNORECASE)
        if m_buy_name:
            ten_nmua = clean_buyer_name(m_buy_name.group(1))

        m_mst_buyer = re.search(r"(?:Mã\s*số\s*thuế\s*\(Tax\s*code\)|MST\s*\(Tax\s*Code\)|Mã\s*số\s*thuế)[\s\:\.\_]*([0-9]{10})", full_text[500:], re.IGNORECASE)
        if m_mst_buyer:
            mst_nmua = m_mst_buyer.group(1).strip()

        # 8. Digital Signature
        has_signature = False
        signer = ""
        sign_time = ""
        
        if "Đã được ký điện tử bởi" in full_text or "Signed digitally by" in full_text or "Signature valid" in full_text or "Ký bởi" in full_text:
            has_signature = True
            m_sig = re.search(r"(?:Đã\s*được\s*ký\s*điện\s*tử\s*bởi|Ký\s*bởi|Signed\s*digitally\s*by)[\s\:\.\_]*([^\n\r]+)", full_text, re.IGNORECASE)
            if m_sig:
                signer = clean_supplier_name(m_sig.group(1))
            else:
                signer = ten_nban
        elif "ĐÃ ĐƯỢC KÝ ĐIỆN TỬ" in full_text or ("BẢN THỂ HIỆN CỦA HÓA ĐƠN ĐIỆN TỬ" in full_text and "viettel" in ten_nban.lower()):
            has_signature = True
            signer = ten_nban
        else:
            if "(Ký, ghi rõ họ, tên)" in full_text and "Ký bởi" not in full_text and "Signature valid" not in full_text:
                has_signature = False
                signer = ""

        sig_status = "Đã ký số" if has_signature else "Chưa ký số"

        m_sig_date = re.search(r"(?:Ký\s*ngày|Ngày)[\s\:\.\_]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})", full_text[-500:], re.IGNORECASE)
        if m_sig_date:
            sign_time = m_sig_date.group(1).strip()

        # 9. Amounts & Line items
        tien_chua_thue = 0.0
        tien_thue = 0.0
        tong_tien = 0.0
        items = []

        m_tot = re.search(r"(?:Tổng\s*cộng\s*tiền\s*thanh\s*toán|Total\s*payment|Tổng\s*tiền\s*thanh\s*toán\s*\(Total\s*amount\)|Tổng\s*tiền\s*thanh\s*toán)[\s\:\.\_\(Total\s*amount\)\(Total\s*payment\)]*([0-9\.\,]+)", full_text, re.IGNORECASE)
        if m_tot:
            tong_tien = clean_num(m_tot.group(1))

        m_sub = re.search(r"(?:Cộng\s*tiền\s*hàng\s*\(Total\s*before\s*VAT\)|Cộng\s*tiền\s*hàng|Sub\s*total|Total\s*amount)[\s\:\.\_\(Sub\s*total\)\(Total\s*before\s*VAT\)]*([0-9\.\,]+)", full_text, re.IGNORECASE)
        if m_sub:
            tien_chua_thue = clean_num(m_sub.group(1))

        m_vat = re.search(r"(?:Tiền\s*thuế\s*GTGT\s*\(VAT\s*amount\)|Cộng\s*tiền\s*thuế\s*GTGT|Tiền\s*thuế\s*GTGT|VAT\s*amount)[\s\:\.\_\(VAT\s*amount\)]*([0-9\.\,]+)", full_text, re.IGNORECASE)
        if m_vat:
            tien_thue = clean_num(m_vat.group(1))

        if tong_tien == 0.0:
            m_cong = re.search(r"CỘNG\s+([0-9\.\,]+)\s+([0-9\.\,]+)\s+([0-9\.\,]+)", full_text, re.IGNORECASE)
            if m_cong:
                tien_chua_thue = clean_num(m_cong.group(1))
                tien_thue = clean_num(m_cong.group(2))
                tong_tien = clean_num(m_cong.group(3))

        if tong_tien == 0.0 and tien_chua_thue > 0:
            tong_tien = tien_chua_thue + tien_thue
        elif tien_chua_thue == 0.0 and tong_tien > 0:
            tien_chua_thue = tong_tien - tien_thue

        item_matches = re.findall(r"(\d+)\s+([^\n\r]+?)\s+(Gói|Giờ|Tháng|Bộ|Chiếc|Kg|m|Lần|Cái|Khẩu)\s+([0-9\.\,]+)\s+([0-9\.\,]+)\s+([0-9\.\,]+)(?:\s+([0-9]+%|KCT|KKKNT)\s+([0-9\.\,]+))?", full_text)
        
        if item_matches:
            for itm in item_matches:
                stt_i, name_i, dvt_i, sl_i, dg_i, tt_i, ts_i, tv_i = itm
                items.append({
                    "stt": int(stt_i),
                    "ten_hang": name_i.strip(),
                    "dvt": dvt_i.strip(),
                    "so_luong": clean_num(sl_i),
                    "don_gia": clean_num(dg_i),
                    "thanh_tien": clean_num(tt_i),
                    "thue_suat": ts_i if ts_i else "0%",
                    "tien_thue": clean_num(tv_i) if tv_i else 0.0
                })
        else:
            if tien_chua_thue > 0 or tong_tien > 0:
                items.append({
                    "stt": 1,
                    "ten_hang": f"Dịch vụ / Hàng hóa theo HĐ {so_hd}",
                    "dvt": "Gói",
                    "so_luong": 1.0,
                    "don_gia": tien_chua_thue if tien_chua_thue > 0 else tong_tien,
                    "thanh_tien": tien_chua_thue if tien_chua_thue > 0 else tong_tien,
                    "thue_suat": "0%" if tien_thue == 0 else f"{round((tien_thue/tien_chua_thue)*100)}%",
                    "tien_thue": tien_thue
                })

        inv_data = {
            "filename": filename,
            "kh_mau": "1",
            "kh_hd": kh_hd if kh_hd else "1C25TMT",
            "so_hd": so_hd,
            "ngay_lap": ngay_lap,
            "dv_tiente": "VND",
            "ty_gia": 1.0,
            "mst_nban": mst_nban,
            "ten_nban": ten_nban if ten_nban else "Nhà cung cấp",
            "dc_nban": dc_nban,
            "mst_nmua": mst_nmua if mst_nmua else ("2601084657" if "toyo" in ten_nmua.lower() else ""),
            "ten_nmua": ten_nmua,
            "dc_nmua": dc_nmua,
            "tien_chua_thue": tien_chua_thue,
            "tien_thue": tien_thue,
            "tong_tien": tong_tien,
            "ma_cqt": ma_cqt,
            "web_tra_cuu": web_tra_cuu,
            "ma_tra_cuu": ma_tra_cuu,
            "has_signature": has_signature,
            "sig_status": sig_status,
            "signer": signer,
            "sign_time": sign_time,
            "is_unpaid": has_unpaid_stamp and ("viettel" in ten_nban.lower()),
            "items": items
        }

        val_res = InvoiceValidator.validate_invoice(inv_data)
        inv_data.update(val_res)
        return inv_data

    @classmethod
    def _extract_and_parse_rar(cls, rar_path: str) -> List[Dict[str, Any]]:
        results = []
        temp_dir = tempfile.mkdtemp(prefix="rar_extract_")
        
        extracted = False
        try:
            with rarfile.RarFile(rar_path) as rf:
                rf.extractall(path=temp_dir)
                extracted = True
        except Exception:
            pass

        if not extracted and os.path.exists(r"C:\Program Files\7-Zip\7z.exe"):
            try:
                subprocess.run([r"C:\Program Files\7-Zip\7z.exe", "x", "-y", f"-o{temp_dir}", rar_path], capture_output=True, check=True)
                extracted = True
            except Exception:
                pass

        if not extracted and os.path.exists(r"C:\Program Files\WinRAR\UnRAR.exe"):
            try:
                subprocess.run([r"C:\Program Files\WinRAR\UnRAR.exe", "x", "-y", rar_path, temp_dir], capture_output=True, check=True)
                extracted = True
            except Exception:
                pass

        if extracted:
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    full_fpath = os.path.join(root, f)
                    if ext in [".xml", ".pdf"]:
                        sub_invs = cls.parse_file(full_fpath)
                        results.extend(sub_invs)

        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

        return results

    @classmethod
    def parse_file(cls, file_path: str) -> List[Dict[str, Any]]:
        results = []
        if not os.path.exists(file_path):
            return results
            
        ext = os.path.splitext(file_path)[1].lower()
        base_name = os.path.basename(file_path)
        
        if ext == ".xml":
            try:
                with open(file_path, "rb") as f:
                    inv = cls.parse_xml_content(f.read(), base_name)
                    if inv:
                        results.append(inv)
            except Exception:
                pass
        elif ext == ".pdf":
            try:
                with open(file_path, "rb") as f:
                    inv = cls.parse_pdf_content(f.read(), base_name)
                    if inv:
                        results.append(inv)
            except Exception:
                pass
        elif ext == ".zip":
            try:
                with zipfile.ZipFile(file_path, 'r') as z:
                    for zname in z.namelist():
                        zext = os.path.splitext(zname)[1].lower()
                        if zext == ".xml":
                            with z.open(zname) as f:
                                inv = cls.parse_xml_content(f.read(), zname)
                                if inv:
                                    results.append(inv)
                        elif zext == ".pdf":
                            with z.open(zname) as f:
                                inv = cls.parse_pdf_content(f.read(), zname)
                                if inv:
                                    results.append(inv)
            except Exception:
                pass
        elif ext == ".rar":
            results = cls._extract_and_parse_rar(file_path)
            
        return results
