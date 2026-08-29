import re
from typing import Dict, Any, List

class InvoiceValidator:
    """
    Module Thẩm định Hóa đơn Điện tử theo chuẩn:
    - Thông tư số 91/2026/TT-BTC & Thông tư 78/2021/TT-BTC
    - Nghị định số 123/2020/NĐ-CP
    - Luật Quản lý Thuế & Luật Thuế GTGT
    """
    
    @staticmethod
    def validate_invoice(inv_data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        is_valid = True
        status_summary = "Hợp lệ"
        
        # 1. Kiểm tra Số hóa đơn
        so_hd = str(inv_data.get("so_hd", "")).strip()
        if not so_hd or so_hd == "<Chưa cấp số>" or "Chưa cấp số" in so_hd:
            is_valid = False
            issues.append("Hóa đơn nháp / Chưa được cấp số hóa đơn chính thức")
            
        # 2. Kiểm tra Ký hiệu mẫu số và Ký hiệu hóa đơn
        kh_hd = str(inv_data.get("kh_hd", "")).strip()
        if not kh_hd or kh_hd.lower() in ["xml", "no", "serial"]:
            is_valid = False
            issues.append("Ký hiệu hóa đơn không đúng chuẩn")
            
        # 3. Kiểm tra Mã số thuế Người bán (10 số hoặc 13 số chi nhánh)
        mst_seller = str(inv_data.get("mst_nban", "")).strip()
        if not mst_seller:
            is_valid = False
            issues.append("Thiếu mã số thuế người bán")
        else:
            clean_mst = mst_seller.replace("-", "").replace(" ", "")
            if not (len(clean_mst) in [10, 13] and clean_mst.isdigit()):
                is_valid = False
                issues.append(f"MST người bán ({mst_seller}) không đúng định dạng quy định")
                
        # 4. Kiểm tra Chữ ký số (QUY CHUẨN BẮT BUỘC THEO TT 91/2026/TT-BTC)
        has_sig = bool(inv_data.get("has_signature"))
        sig_status = str(inv_data.get("sig_status", "Chưa ký số"))
        if not has_sig or sig_status == "Chưa ký số":
            is_valid = False
            issues.append("Hóa đơn chưa ký số hoặc chữ ký điện tử không hợp lệ")

        # 5. Kiểm tra Dấu mờ / Trạng thái CHƯA THANH TOÁN (Hóa đơn viễn thông Viettel)
        is_unpaid = bool(inv_data.get("is_unpaid", False))
        if is_unpaid:
            is_valid = False
            issues.append("Bản thông báo cước mang dấu 'CHƯA THANH TOÁN' (Portal Viettel chưa đồng bộ dữ liệu hóa đơn chính thức)")

        # 6. Kiểm tra Tiền thanh toán
        tong_tien = float(inv_data.get("tong_tien", 0.0))
        tien_chua_thue = float(inv_data.get("tien_chua_thue", 0.0))
        tien_thue = float(inv_data.get("tien_thue", 0.0))
        
        if tong_tien <= 0 and tien_chua_thue <= 0:
            is_valid = False
            issues.append("Hóa đơn không có giá trị thanh toán")
            
        # 7. Tổng hợp trạng thái thẩm định
        if not is_valid:
            if not has_sig or sig_status == "Chưa ký số":
                status_summary = "Không hợp lệ / Chưa ký số"
            elif so_hd == "<Chưa cấp số>" or "Chưa cấp số" in so_hd:
                status_summary = "Không hợp lệ / Chưa cấp số"
            elif is_unpaid:
                status_summary = "Cần kiểm tra: Bản cước Chưa thanh toán"
            else:
                status_summary = "Không hợp lệ / Cần kiểm tra"
            notes = "; ".join(issues)
        else:
            status_summary = "Hợp lệ"
            notes = "Đầy đủ tiêu chuẩn pháp lý theo TT 91/2026/TT-BTC"

        return {
            "is_valid": 1 if is_valid else 0,
            "status_summary": status_summary,
            "notes": notes,
            "validation_issues": issues
        }
