import sys
sys.stdout.reconfigure(encoding='utf-8')
from parser import InvoiceParser

sample_tcs_text = """
HÓA ĐƠN GIÁ TRỊ GIA TĂNG
(VAT INVOICE)
Ngày (day) 25 tháng (month) 11 năm (year) 2025
Mẫu số - Ký hiệu (Serial No.): 1C25TMT
Số (Invoice No.): 00000374
Mã của Cơ quan thuế: 00182618D4B07744D892C544EBD78E15EC
Đơn vị bán (Seller): CHI NHÁNH HÀ NỘI - CÔNG TY TNHH TCS - KỸ THUẬT MÔI TRƯỜNG
MST (Tax Code): 3702653397-002
Địa chỉ (Address): Số 45A, ngõ 167 Tây Sơn, Phường Kim Liên, Thành phố Hà Nội, Việt Nam
Người mua (Buyer):
Đơn vị (Co. name): CÔNG TY TNHH TOYO SOLAR
MST (Tax Code): 2601084657
Địa chỉ (Address): Khu công nghiệp Cẩm Khê, Xã Cẩm Khê, Tỉnh Phú Thọ, Việt Nam
STT Tên hàng hóa, dịch vụ ĐVT SL Đơn giá Thành tiền Thuế suất Tiền thuế
1 Quan trắc môi trường lao động theo Hợp đồng số 2808/2025/HĐKT/TOYO-TCS Gói 1 20.480.000 20.480.000 0% 0
Cộng tiền hàng (Sub total): 20.480.000
Cộng tiền thuế GTGT (VAT amount): 0
Tổng cộng tiền thanh toán (Total payment): 20.480.000
Đã được ký điện tử bởi
CHI NHÁNH HÀ NỘI - CÔNG TY TNHH TCS - KỸ THUẬT MÔI TRƯỜNG
Ngày: 25/11/2025
Hóa đơn Điện tử (HĐĐT) được tra cứu trực tuyến tại http://tracuu.ehoadon.vn. Mã tra cứu HĐĐT này: ONAYLJ4PYEB
"""

# Test regex parsing
import re
from parser import clean_supplier_name, clean_address

m_symbol = re.search(r"\b([1-6]?[C|K|M][0-9]{2}[A-Z0-9]{2,4})\b", sample_tcs_text[:1200])
symbol_val = m_symbol.group(1).upper() if m_symbol else "NOT_FOUND"

m_matc = re.search(r"(?:Mã\s*tra\s*cứu\s*HĐĐT\s*này|Mã\s*số\s*bí\s*mật|Mã\s*bí\s*mật)[\s\:\.\_]*([A-Za-z0-9]{4,20})", sample_tcs_text, re.IGNORECASE)
matc_val = m_matc.group(1).strip() if m_matc else "NOT_FOUND"

m_cqt = re.search(r"(?:Mã\s*của\s*Cơ\s*quan\s*thuế|Mã\s*CQT\s*\(Code\)|Mã\s*CQT)[\s\:\.\_]*([0-9A-F]{20,40})", sample_tcs_text, re.IGNORECASE)
cqt_val = m_cqt.group(1).strip() if m_cqt else "NOT_FOUND"

print("--- TEST TCS EXTRACTION ---")
print("Ký hiệu hóa đơn:", symbol_val)
print("Mã tra cứu:", matc_val)
print("Mã CQT:", cqt_val)
