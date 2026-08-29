import os
import sys
from database import get_user_database
from exporter import InvoiceExporter

def run_test():
    print("==================================================================")
    print("🧪 BẮT ĐẦU KIỂM THỬ PHÂN LẬP DỮ LIỆU ĐA NGƯỜI DÙNG (DATA ISOLATION TEST)")
    print("==================================================================")
    
    # 1. Khởi tạo 2 database độc lập cho 2 người dùng khác nhau
    db_user_a = get_user_database(user_id="Ketoan_A")
    db_user_b = get_user_database(user_id="Ketoan_B")
    db_temp = get_user_database(user_id="Ketoan_Temp", is_temp=True)
    
    # Làm sạch trước khi test
    db_user_a.clear_all()
    db_user_b.clear_all()
    db_temp.clear_all()
    
    print(f"✅ DB User A path: {db_user_a.db_path}")
    print(f"✅ DB User B path: {db_user_b.db_path}")
    print(f"✅ DB User Temp path: {db_temp.db_path}")
    
    # 2. User A nạp hóa đơn Viettel
    inv_a = {
        "filename": "Viettel_Test.pdf",
        "kh_mau": "1",
        "kh_hd": "1C25TMT",
        "so_hd": "00000123",
        "ngay_lap": "2026-08-26",
        "ten_nban": "TẬP ĐOÀN CÔNG NGHIỆP - VIỄN THÔNG QUÂN ĐỘI",
        "mst_nban": "0100109106",
        "dc_nban": "Hà Nội",
        "mst_nmua": "2601084657",
        "ten_nmua": "CÔNG TY TNHH TOYO SOLAR",
        "dc_nmua": "Phú Thọ",
        "tien_chua_thue": 180000.0,
        "tien_thue": 18000.0,
        "tong_tien": 198000.0,
        "has_signature": 1,
        "sig_status": "Đã ký số",
        "ma_cqt": "Không có mã CQT (HĐ không mã)",
        "web_tra_cuu": "https://vietteltelecom.vn/hoadondientu/",
        "ma_tra_cuu": "513719",
        "is_valid": 1,
        "status_summary": "Hợp lệ",
        "notes": "HĐ Viettel Cước viễn thông",
        "items": [
            {
                "stt": 1,
                "ten_hang": "Cước FTTH Internet tháng 07/2026",
                "dvt": "Tháng",
                "so_luong": 1,
                "don_gia": 180000.0,
                "thanh_tien": 180000.0,
                "thue_suat": "10%",
                "tien_thue": 18000.0
            }
        ]
    }
    db_user_a.insert_invoice(inv_a)
    
    # 3. User B nạp hóa đơn Madeown
    inv_b = {
        "filename": "Madeown_Test.pdf",
        "kh_mau": "1",
        "kh_hd": "1C25TMD",
        "so_hd": "00000999",
        "ngay_lap": "2026-08-25",
        "ten_nban": "CÔNG TY TNHH MADEOWN VIỆT NAM",
        "mst_nban": "0107610008",
        "dc_nban": "Bắc Ninh",
        "mst_nmua": "2601084657",
        "ten_nmua": "CÔNG TY TNHH TOYO SOLAR",
        "dc_nmua": "Phú Thọ",
        "tien_chua_thue": 85000000.0,
        "tien_thue": 0.0,
        "tong_tien": 85000000.0,
        "has_signature": 0,
        "sig_status": "Chưa ký số",
        "ma_cqt": "Chưa có mã CQT",
        "web_tra_cuu": "https://hoadondientu.gdt.gov.vn",
        "ma_tra_cuu": "Chưa có mã tra cứu",
        "is_valid": 0,
        "status_summary": "Không hợp lệ / Chưa ký số",
        "notes": "Chưa ký số điện tử",
        "items": [
            {
                "stt": 1,
                "ten_hang": "Gói Gia công cơ khí theo đơn đặt hàng",
                "dvt": "Gói",
                "so_luong": 1,
                "don_gia": 85000000.0,
                "thanh_tien": 85000000.0,
                "thue_suat": "0%",
                "tien_thue": 0.0
            }
        ]
    }
    db_user_b.insert_invoice(inv_b)
    
    # 4. Kiểm tra cách ly dữ liệu
    invs_a = db_user_a.get_all_invoices()
    invs_b = db_user_b.get_all_invoices()
    invs_temp = db_temp.get_all_invoices()
    
    print(f"\n📊 KẾT QUẢ ĐỌC DỮ LIỆU:")
    print(f"- Số HĐ của User A: {len(invs_a)} (NCC: {invs_a[0]['ten_nban']})")
    print(f"- Số HĐ của User B: {len(invs_b)} (NCC: {invs_b[0]['ten_nban']})")
    print(f"- Số HĐ của User Temp: {len(invs_temp)} (Trống)")
    
    assert len(invs_a) == 1, "User A phải có đúng 1 HĐ"
    assert len(invs_b) == 1, "User B phải có đúng 1 HĐ"
    assert len(invs_temp) == 0, "User Temp phải có 0 HĐ"
    assert invs_a[0]['mst_nban'] == "0100109106", "User A chỉ thấy HĐ Viettel"
    assert invs_b[0]['mst_nban'] == "0107610008", "User B chỉ thấy HĐ Madeown"
    
    # 5. Kiểm tra xuất Excel riêng biệt
    excel_a = InvoiceExporter.export_comprehensive_excel(invs_a, db_user_a)
    excel_b = InvoiceExporter.export_comprehensive_excel(invs_b, db_user_b)
    
    print(f"✅ Xuất Excel User A thành công ({len(excel_a)} bytes)")
    print(f"✅ Xuất Excel User B thành công ({len(excel_b)} bytes)")
    
    # 6. Kiểm tra xóa dữ liệu User A
    print("\n🗑️ Thực hiện XÓA DATABASE User A...")
    db_user_a.clear_all()
    
    assert len(db_user_a.get_all_invoices()) == 0, "User A phải về 0 HĐ sau khi xóa"
    assert len(db_user_b.get_all_invoices()) == 1, "User B VẪN PHẢI GIỮ NGUYÊN 1 HĐ (Không bị ảnh hưởng)"
    
    print(f"✅ Sau khi xóa User A:")
    print(f"   - User A còn lại: {len(db_user_a.get_all_invoices())} HĐ")
    print(f"   - User B còn lại: {len(db_user_b.get_all_invoices())} HĐ (Bảo toàn 100%)")
    
    print("\n🎉 KIỂM THỬ PHÂN LẬP DỮ LIỆU & BẢO MẬT RIÊNG TƯ HOÀN TẤT THÀNH CÔNG 100%!")

if __name__ == "__main__":
    run_test()
