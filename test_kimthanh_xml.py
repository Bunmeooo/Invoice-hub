import sys
sys.stdout.reconfigure(encoding='utf-8')
from parser import InvoiceParser

xml_path = r"C:\Users\VSUN\Desktop\TEST_CHECK_INVOICE\1C26TYY_00000578_2601084657.xml"
invs = InvoiceParser.parse_file(xml_path)

print(f"Parsed {len(invs)} invoice(s) from XML:")
for inv in invs:
    print(f"- Ký hiệu: {inv['kh_hd']}")
    print(f"- Số HĐ: {inv['so_hd']}")
    print(f"- Ngày lập: {inv['ngay_lap']}")
    print(f"- NCC: {inv['ten_nban']} (MST: {inv['mst_nban']})")
    print(f"- Tổng tiền: {inv['tong_tien']:,.0f} {inv['dv_tiente']}")
    print(f"- Chữ ký: {inv['sig_status']} ({inv['signer']})")
    print(f"- Mã CQT: {inv['ma_cqt']}")
    print(f"- Website tra cứu: {inv['web_tra_cuu']}")
    print(f"- Mã số tra cứu: {inv['ma_tra_cuu']}")
    print(f"- Đánh giá: {inv['status_summary']}")
