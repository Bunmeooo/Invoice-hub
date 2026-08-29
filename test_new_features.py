import os
import sys
from i18n import t, TRANSLATIONS
from database import get_user_database
from exporter import InvoiceExporter
import analytics

def test_all_features():
    print("==================================================================")
    print("🧪 BẮT ĐẦU KIỂM THỬ TOÀN DIỆN CÁC TÍNH NĂNG MỚI")
    print("==================================================================")

    # 1. Test i18n
    for lang in ["vi", "en", "zh"]:
        title = t("app_title", lang)
        btn = t("btn_start_parse", lang)
        assert len(title) > 0 and len(btn) > 0, f"i18n missing for {lang}"
        print(f"✅ i18n ({lang}): App Title = '{title}' | Button = '{btn}'")
        
    # 2. Test Quota (Basic vs Pro)
    db = get_user_database("test_user_quota")
    db.clear_all()
    
    # Check Basic Quota
    allowed, used, remaining = db.check_quota("test_user_quota", plan_type="basic", new_files_count=5)
    assert allowed == True and remaining == 10, "Basic should allow 5 files when 0 used"
    
    db.increment_daily_usage("test_user_quota", count=8)
    allowed, used, remaining = db.check_quota("test_user_quota", plan_type="basic", new_files_count=3)
    assert allowed == False, "Basic should block 3 files when 8 used (8+3=11 > 10)"
    
    # Check Pro Quota
    allowed_pro, used_pro, remaining_pro = db.check_quota("test_user_quota", plan_type="pro", new_files_count=50)
    assert allowed_pro == True, "Pro should allow unlimited files"
    print("✅ Quota Engine: Basic (10/day limit) & Pro (Unlimited) verified!")
    
    # 3. Test Feedback System
    saved = db.save_feedback("test_user_quota", rating=5, category="✨ Đề xuất tính năng mới", comment="Hệ thống bóc tách rất nhanh và chính xác!")
    assert saved == True, "Feedback should save successfully"
    feedbacks = db.get_feedback_list("test_user_quota")
    assert len(feedbacks) >= 1, "Should retrieve saved feedback"
    print(f"✅ Feedback System: Saved and retrieved feedback (Rating: {feedbacks[0]['rating']} stars)")

    # 4. Test Analytics & AP Debt & Tax Risk
    # Insert test invoice
    inv_test = {
        "filename": "Madeown_Draft.pdf",
        "kh_mau": "1",
        "kh_hd": "1C25TMD",
        "so_hd": "<Chưa cấp số>",
        "ngay_lap": "2026-08-20",
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
        "notes": "Chưa ký số",
        "items": []
    }
    db.insert_invoice(inv_test)
    all_invs = db.get_all_invoices()
    
    # Charts
    fig_sup = analytics.get_supplier_chart(all_invs, "vi")
    fig_tax = analytics.get_tax_distribution_chart(all_invs, "vi")
    fig_trend = analytics.get_monthly_trend_chart(all_invs, "vi")
    assert fig_sup is not None and fig_tax is not None and fig_trend is not None, "Charts must generate"
    print("✅ BI Charts: Pareto Top Supplier, VAT Breakdown & Monthly Trend generated successfully!")
    
    # AP Debt
    debts = analytics.get_ap_debt_reconciliation(all_invs, payment_term_days=30)
    assert len(debts) == 1, "AP Debt should have 1 supplier"
    print(f"✅ AP Debt Reconciliation: Supplier = {debts[0]['ten_nban']}, Total Debt = {debts[0]['tong_cong_no']:,.0f} VND, Status = {debts[0]['trang_thai']}")
    
    # Tax Risks
    risks = analytics.detect_tax_and_fraud_risks(all_invs)
    assert len(risks) >= 2, "Should detect unsigned and unnumbered invoice risks"
    print(f"✅ Tax & Fraud Risk Engine: Detected {len(risks)} risk points (Unsigned, Unnumbered)")

    # 5. Multilingual Excel Export
    for l in ["vi", "en", "zh", "bilingual_zh"]:
        x_bytes = InvoiceExporter.export_comprehensive_excel(all_invs, db, lang=l)
        assert len(x_bytes) > 5000, f"Excel for {l} should be valid"
        print(f"✅ Excel Export ({l}): Generated {len(x_bytes)} bytes")
        
    print("\n🎉 TOÀN BỘ CÁC TÍNH NĂNG MỚI ĐÃ VƯỢT QUA KIỂM THỬ THÀNH CÔNG 100%!")

if __name__ == "__main__":
    test_all_features()
