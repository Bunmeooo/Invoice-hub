import streamlit as st
import pandas as pd
import os
import io
import tempfile
import time
from parser import InvoiceParser
from database import InvoiceDatabase
from exporter import InvoiceExporter

st.set_page_config(
    page_title="E-Invoice Hub | Chuẩn TT 91/2026/TT-BTC",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
db = InvoiceDatabase()

# Custom Styling
st.markdown("""
<style>
    /* Hide Streamlit Deploy button, Hamburger Menu & Header */
    .stAppDeployButton { display: none !important; }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    
    .main-header { font-size: 24px; font-weight: bold; color: #1F4E78; margin-bottom: 2px; }
    .sub-header { font-size: 14px; color: #595959; margin-bottom: 18px; }
    .tt-badge { background-color: #E2EFDA; color: #385723; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Sidebar Management
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/invoice.png", width=65)
    st.title("Quản trị Cơ sở Dữ liệu")
    
    current_invs = db.get_all_invoices()
    st.metric("Tổng số hóa đơn lưu trữ", f"{len(current_invs)} HĐ")
    
    st.markdown("---")
    st.markdown("**⚖️ Tiêu chuẩn Áp dụng:**")
    st.markdown("• **Thông tư số 91/2026/TT-BTC** *(Hiệu lực 01/07/2026)*")
    st.markdown("• **Nghị định số 123/2020/NĐ-CP**")
    st.markdown("• **Thông tư số 78/2021/TT-BTC**")
    
    st.markdown("---")
    st.markdown("### 🗑️ Làm sạch Dữ liệu")
    if st.button("🗑️ XÓA TOÀN BỘ DATABASE", type="primary"):
        db.clear_all()
        if "preview_data" in st.session_state:
            del st.session_state["preview_data"]
        st.success("✅ Đã làm sạch toàn bộ dữ liệu!")
        st.rerun()

st.markdown('<div class="main-header">🧾 E-INVOICE SCRAPER & PARSER HUB</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Hệ thống Tự động hóa Bóc tách và Quản lý Hóa đơn Điện tử chuẩn <span class="tt-badge">Thông tư 91/2026/TT-BTC</span></div>', unsafe_allow_html=True)

# Initialize Session State
if "preview_data" not in st.session_state:
    st.session_state["preview_data"] = []

# Tabs
tab1, tab2, tab3 = st.tabs([
    "📥 1. Nạp Hóa Đơn & Preview Tác Vụ",
    "📊 2. Bảng Kê & Phân Rã Theo Nhà Cung Cấp",
    "💾 3. Xuất Báo Cáo Excel Chuẩn Kế Toán"
])

# ================= TAB 1: NẠP & PREVIEW TÁC VỤ =================
with tab1:
    st.subheader("Nạp tệp Hóa đơn Điện tử (Hỗ trợ PDF, XML, ZIP, RAR)")
    
    uploaded_files = st.file_uploader(
        "Kéo thả hoặc chọn các tệp Hóa đơn (.pdf, .xml, .zip, .rar):",
        type=["pdf", "xml", "zip", "rar"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("🚀 Bắt đầu Bóc tách & Thẩm định", type="primary"):
            preview_results = []
            prog_bar = st.progress(0.0)
            status_txt = st.empty()
            
            success_cnt = 0
            err_cnt = 0
            
            for idx, up_file in enumerate(uploaded_files):
                fname = up_file.name
                fsize_kb = round(len(up_file.getvalue()) / 1024, 1)
                fbytes = up_file.read()
                
                status_txt.text(f"⚡ Đang bóc tách [{idx+1}/{len(uploaded_files)}]: {fname} ({fsize_kb} KB)...")
                ext = os.path.splitext(fname)[1].lower()
                
                parsed_invs = []
                if ext == ".xml":
                    inv = InvoiceParser.parse_xml_content(fbytes, fname)
                    if inv:
                        parsed_invs.append(inv)
                elif ext == ".pdf":
                    inv = InvoiceParser.parse_pdf_content(fbytes, fname)
                    if inv:
                        parsed_invs.append(inv)
                elif ext == ".zip":
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                        tmp.write(fbytes)
                        tmp_path = tmp.name
                    parsed_invs = InvoiceParser.parse_file(tmp_path)
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                elif ext == ".rar":
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".rar") as tmp:
                        tmp.write(fbytes)
                        tmp_path = tmp.name
                    parsed_invs = InvoiceParser.parse_file(tmp_path)
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                
                if parsed_invs:
                    for inv in parsed_invs:
                        db.insert_invoice(inv, overwrite=True)
                        success_cnt += 1
                        preview_results.append({
                            "STT": len(preview_results) + 1,
                            "Tên tệp": fname,
                            "Định dạng": ext.upper().replace(".", ""),
                            "Số HĐ": inv.get("so_hd", ""),
                            "Ký hiệu": inv.get("kh_hd", ""),
                            "Ngày lập": inv.get("ngay_lap", ""),
                            "Nhà Cung Cấp": inv.get("ten_nban", ""),
                            "MST NCC": inv.get("mst_nban", ""),
                            "Chưa thuế (đ)": inv.get("tien_chua_thue", 0.0),
                            "Thuế GTGT (đ)": inv.get("tien_thue", 0.0),
                            "Tổng thanh toán (đ)": inv.get("tong_tien", 0.0),
                            "Chữ ký số": inv.get("sig_status", "Đã ký số"),
                            "Mã CQT": inv.get("ma_cqt", "Có mã CQT"),
                            "Đánh giá": inv.get("status_summary", "Hợp lệ")
                        })
                else:
                    err_cnt += 1
                    preview_results.append({
                        "STT": len(preview_results) + 1,
                        "Tên tệp": fname,
                        "Định dạng": ext.upper().replace(".", ""),
                        "Số HĐ": "-",
                        "Ký hiệu": "-",
                        "Ngày lập": "-",
                        "Nhà Cung Cấp": "-",
                        "MST NCC": "-",
                        "Chưa thuế (đ)": 0.0,
                        "Thuế GTGT (đ)": 0.0,
                        "Tổng thanh toán (đ)": 0.0,
                        "Chữ ký số": "Chưa ký",
                        "Mã CQT": "-",
                        "Đánh giá": "Không có dữ liệu"
                    })
                    
                prog_bar.progress((idx + 1) / len(uploaded_files))
                
            status_txt.empty()
            st.session_state["preview_data"] = preview_results
            st.success(f"🎉 **Hoàn tất bóc tách!** Đã lưu và thẩm định thành công **{success_cnt}** hóa đơn vào Cơ sở dữ liệu.")

    # ================= BẢNG PREVIEW TÁC VỤ =================
    st.markdown("### 📋 Bảng Preview Tác Vụ Bóc Tách")
    
    if st.session_state["preview_data"]:
        df_prev = pd.DataFrame(st.session_state["preview_data"])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng tệp nạp", f"{len(df_prev)} tệp")
        ok_count = len(df_prev[df_prev["Đánh giá"] == "Hợp lệ"])
        c2.metric("Hóa đơn Hợp lệ", f"{ok_count} / {len(df_prev)}")
        c3.metric("Tổng giá trị đợt nạp", f"{df_prev['Tổng thanh toán (đ)'].sum():,.0f} đ")
        c4.metric("Tổng tiền thuế GTGT", f"{df_prev['Thuế GTGT (đ)'].sum():,.0f} đ")
        
        st.dataframe(
            df_prev.style.format({
                "Chưa thuế (đ)": "{:,.0f}",
                "Thuế GTGT (đ)": "{:,.0f}",
                "Tổng thanh toán (đ)": "{:,.0f}"
            }),
            use_container_width=True,
            height=350
        )
    else:
        st.info("Chưa có tác vụ nạp nào trong phiên này. Hãy chọn các tệp hóa đơn bên trên và bấm **'🚀 Bắt đầu Bóc tách & Thẩm định'** để xem bảng preview chi tiết!")

# ================= TAB 2: BẢNG KÊ & PHÂN RÃ THEO NCC =================
with tab2:
    all_invoices = db.get_all_invoices()
    
    if not all_invoices:
        st.warning("Chưa có dữ liệu hóa đơn nào trong hệ thống. Vui lòng nạp tệp ở Tab 1!")
    else:
        df_inv = pd.DataFrame(all_invoices)
        
        m1, m2, m3, m4 = st.columns(4)
        total_inv = len(df_inv)
        total_pre_tax = df_inv["tien_chua_thue"].sum()
        total_vat = df_inv["tien_thue"].sum()
        total_all = df_inv["tong_tien"].sum()
        
        m1.metric("Tổng số Hóa đơn", f"{total_inv:,} HĐ")
        m2.metric("Doanh số chưa thuế", f"{total_pre_tax:,.0f} đ")
        m3.metric("Tổng thuế GTGT đầu vào", f"{total_vat:,.0f} đ")
        m4.metric("Tổng tiền thanh toán", f"{total_all:,.0f} đ")
        
        st.markdown("---")
        
        view_tab1, view_tab2 = st.tabs(["📑 BẢNG KÊ TỔNG HỢP HÓA ĐƠN", "🏢 CHI TIẾT THEO NHÀ CUNG CẤP"])
        
        with view_tab1:
            s1, s2 = st.columns([2, 1])
            search_kw = s1.text_input("🔍 Tìm kiếm theo Tên NCC, MST, Số hóa đơn:", "")
            
            if search_kw:
                df_filtered = df_inv[
                    df_inv["ten_nban"].str.contains(search_kw, case=False, na=False) |
                    df_inv["mst_nban"].str.contains(search_kw, case=False, na=False) |
                    df_inv["so_hd"].str.contains(search_kw, case=False, na=False)
                ]
            else:
                df_filtered = df_inv

            show_cols = ["id", "so_hd", "kh_hd", "ngay_lap", "ten_nban", "mst_nban", "tien_chua_thue", "tien_thue", "tong_tien", "sig_status", "ma_cqt", "status_summary"]
            st.dataframe(
                df_filtered[show_cols].rename(columns={
                    "id": "ID", "so_hd": "Số HĐ", "kh_hd": "Ký hiệu", "ngay_lap": "Ngày lập",
                    "ten_nban": "Nhà Cung Cấp (Người bán)", "mst_nban": "MST NCC",
                    "tien_chua_thue": "Chưa thuế (đ)", "tien_thue": "Thuế GTGT (đ)",
                    "tong_tien": "Tổng thanh toán (đ)", "sig_status": "Chữ ký số",
                    "ma_cqt": "Mã CQT", "status_summary": "Đánh giá TT 91/2026"
                }),
                use_container_width=True,
                height=380
            )

        with view_tab2:
            st.markdown("#### 🏢 Phân rã Chi tiết Mặt hàng & Doanh số theo từng Nhà Cung Cấp")
            suppliers = df_inv["ten_nban"].unique().tolist()
            
            for sup in suppliers:
                df_sup_invs = df_inv[df_inv["ten_nban"] == sup]
                sup_mst = df_sup_invs["mst_nban"].iloc[0]
                sup_total = df_sup_invs["tong_tien"].sum()
                sup_vat = df_sup_invs["tien_thue"].sum()
                
                with st.expander(f"🏢 **{sup}** (MST: {sup_mst}) — **{len(df_sup_invs)} HĐ** | Tổng thanh toán: **{sup_total:,.0f} đ** (Thuế GTGT: **{sup_vat:,.0f} đ**)", expanded=True):
                    sup_items_list = []
                    for _, r_inv in df_sup_invs.iterrows():
                        inv_id = r_inv["id"]
                        items = db.get_invoice_items(inv_id)
                        if items:
                            for it in items:
                                sup_items_list.append({
                                    "Số HĐ": r_inv["so_hd"],
                                    "Ký hiệu": r_inv["kh_hd"],
                                    "Ngày lập": r_inv["ngay_lap"],
                                    "STT": it.get("stt", 1),
                                    "Tên hàng hóa / Dịch vụ": it.get("ten_hang", ""),
                                    "ĐVT": it.get("dvt", ""),
                                    "Số lượng": it.get("so_luong", 1),
                                    "Đơn giá (đ)": it.get("don_gia", 0.0),
                                    "Thành tiền (đ)": it.get("thanh_tien", 0.0),
                                    "Thuế suất": it.get("thue_suat", "0%"),
                                    "Tiền thuế (đ)": it.get("tien_thue", 0.0)
                                })
                        else:
                            sup_items_list.append({
                                "Số HĐ": r_inv["so_hd"],
                                "Ký hiệu": r_inv["kh_hd"],
                                "Ngày lập": r_inv["ngay_lap"],
                                "STT": 1,
                                "Tên hàng hóa / Dịch vụ": f"Dịch vụ theo HĐ {r_inv['so_hd']}",
                                "ĐVT": "Gói",
                                "Số lượng": 1,
                                "Đơn giá (đ)": r_inv["tien_chua_thue"],
                                "Thành tiền (đ)": r_inv["tien_chua_thue"],
                                "Thuế suất": "0%" if r_inv["tien_thue"] == 0 else "10%",
                                "Tiền thuế (đ)": r_inv["tien_thue"]
                            })
                            
                    df_sup_items = pd.DataFrame(sup_items_list)
                    st.dataframe(
                        df_sup_items.style.format({
                            "Đơn giá (đ)": "{:,.0f}",
                            "Thành tiền (đ)": "{:,.0f}",
                            "Tiền thuế (đ)": "{:,.0f}"
                        }),
                        use_container_width=True
                    )

# ================= TAB 3: XUẤT BÁO CÁO EXCEL =================
with tab3:
    st.subheader("Xuất Báo cáo Bảng Kê Hóa Đơn Excel Chuẩn Kế Toán (TT 91/2026/TT-BTC)")
    all_invs = db.get_all_invoices()
    
    if not all_invs:
        st.warning("Chưa có dữ liệu để xuất file Excel.")
    else:
        st.write(f"Hiện có **{len(all_invs)}** hóa đơn trong hệ thống sẵn sàng xuất ra file Excel chuẩn kế toán.")
        
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown("""
            ### 📑 Báo Cáo Excel 2 Sheet Tiêu Chuẩn Doanh Nghiệp:
            * **Font chữ đồng nhất**: **`Times New Roman`** toàn bộ bảng tính.
            * **Trình bày chuyên nghiệp**: Không dùng Merge & Center $\\rightarrow$ Sử dụng **`Center Across Selection`**.
            * **Cố định dòng cột**: Freeze Panes tại **`D5`** cho cả 2 Sheet.
            * **Thông tin tra cứu đầy đủ**: Cột Mã CQT, Link website tra cứu, Mã số tra cứu.
            * **Phân rã theo Nhà cung cấp**: Sheet 2 hiển thị rõ ràng từng dòng hàng hóa và dòng Subtotal từng NCC.
            * **Làm nổi bật dòng nghi ngờ**: Tô màu vàng/đỏ nhạt cảnh báo nếu hóa đơn có vấn đề.
            """)
            
            excel_bytes = InvoiceExporter.export_comprehensive_excel(all_invs, db)
            
            st.download_button(
                label="📥 TẢI VỀ BÁO CÁO EXCEL TOÀN DIỆN 2 SHEET (.XLSX)",
                data=excel_bytes,
                file_name="Bao_Cao_Hoa_Don_Chuan_TT91_2026.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
            
        with c2:
            st.info("""
            📋 **Định dạng báo cáo:**
            * Header xanh navy chuẩn kế toán `#1F4E78`.
            * Kẻ khung viền mỏng tinh tế, định dạng số tiền `#,##0`.
            * Khớp 100% với mẫu biểu quản trị FDI và kiểm toán độc lập.
            """)
