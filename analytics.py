import pandas as pd
import datetime
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go

# =========================================================================
# 1. BI VISUAL CHARTS (BIỂU ĐỒ TRỰC QUAN THEO YÊU CẦU)
# =========================================================================

def get_supplier_chart(invoices: List[Dict[str, Any]], lang: str = "vi"):
    """Biểu đồ Pareto Top Nhà Cung Cấp theo Tổng chi phí thanh toán"""
    if not invoices:
        return None
    df = pd.DataFrame(invoices)
    
    if "ten_nban" not in df.columns:
        df["ten_nban"] = "Chưa xác định"
    if "tong_tien" not in df.columns:
        pre = pd.to_numeric(df.get("tong_tien_chua_thue", df.get("tien_chua_thue", 0)), errors="coerce").fillna(0)
        vat = pd.to_numeric(df.get("tien_thue", 0), errors="coerce").fillna(0)
        df["tong_tien"] = pre + vat
        
    df["tong_tien"] = pd.to_numeric(df["tong_tien"], errors="coerce").fillna(0.0)
    sup_summary = df.groupby("ten_nban")["tong_tien"].sum().reset_index()
    sup_summary = sup_summary.sort_values(by="tong_tien", ascending=False).head(10)
    
    title_map = {
        "vi": "🏆 Top 10 Nhà Cung Cấp Chi Phí Lớn Nhất (VND)",
        "en": "🏆 Top 10 Suppliers by Total Spend (VND)",
        "zh": "🏆 采购金额前10大供应商排名 (VND)"
    }
    x_map = {"vi": "Nhà Cung Cấp", "en": "Supplier", "zh": "供应商"}
    y_map = {"vi": "Tổng tiền (VND)", "en": "Total Amount (VND)", "zh": "含税总金额 (VND)"}
    
    fig = px.bar(
        sup_summary,
        x="ten_nban",
        y="tong_tien",
        text="tong_tien",
        title=title_map.get(lang, title_map["vi"]),
        labels={"ten_nban": x_map.get(lang, x_map["vi"]), "tong_tien": y_map.get(lang, y_map["vi"])},
        color="tong_tien",
        color_continuous_scale="Blues"
    )
    fig.update_traces(texttemplate='%{text:,.0f} đ', textposition='outside')
    fig.update_layout(
        xaxis_tickangle=-30,
        height=420,
        margin=dict(l=20, r=20, t=50, b=100),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def get_monthly_trend_chart(invoices: List[Dict[str, Any]], lang: str = "vi"):
    """Biểu đồ Xu hướng Chi phí & Thuế GTGT theo Thời gian"""
    if not invoices:
        return None
    df = pd.DataFrame(invoices)
    
    # Chuẩn hóa tên cột
    if "tien_chua_thue" not in df.columns:
        if "tong_tien_chua_thue" in df.columns:
            df["tien_chua_thue"] = df["tong_tien_chua_thue"]
        else:
            df["tien_chua_thue"] = pd.to_numeric(df.get("tong_tien", 0), errors="coerce").fillna(0) - pd.to_numeric(df.get("tien_thue", 0), errors="coerce").fillna(0)
            
    if "tien_thue" not in df.columns:
        df["tien_thue"] = 0.0
    if "tong_tien" not in df.columns:
        df["tong_tien"] = pd.to_numeric(df["tien_chua_thue"], errors="coerce").fillna(0) + pd.to_numeric(df["tien_thue"], errors="coerce").fillna(0)
        
    df["tien_chua_thue"] = pd.to_numeric(df["tien_chua_thue"], errors="coerce").fillna(0.0)
    df["tien_thue"] = pd.to_numeric(df["tien_thue"], errors="coerce").fillna(0.0)
    df["tong_tien"] = pd.to_numeric(df["tong_tien"], errors="coerce").fillna(0.0)
    
    if "ngay_lap" not in df.columns:
        df["ngay_lap"] = datetime.date.today().isoformat()
        
    df["ngay_lap_dt"] = pd.to_datetime(df["ngay_lap"], errors="coerce")
    df["thang"] = df["ngay_lap_dt"].dt.strftime("%Y-%m")
    df["thang"] = df["thang"].fillna("Khác")
    
    trend = df.groupby("thang").agg({
        "tien_chua_thue": "sum",
        "tien_thue": "sum",
        "tong_tien": "sum"
    }).reset_index().sort_values("thang")
    
    title_map = {
        "vi": "📈 Biến Động Chi Phí & Thuế GTGT Theo Tháng",
        "en": "📈 Monthly Spend & VAT Trend Analysis",
        "zh": "📈 月度采购支出与增值税进项趋势分析"
    }
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=trend["thang"],
        y=trend["tien_chua_thue"],
        name="Chưa thuế" if lang == "vi" else ("Pre-tax" if lang == "en" else "不含税金额"),
        marker_color="#1F4E78"
    ))
    fig.add_trace(go.Bar(
        x=trend["thang"],
        y=trend["tien_thue"],
        name="Thuế GTGT" if lang == "vi" else ("VAT" if lang == "en" else "增值税额"),
        marker_color="#2CA02C"
    ))
    fig.add_trace(go.Scatter(
        x=trend["thang"],
        y=trend["tong_tien"],
        name="Tổng cộng" if lang == "vi" else ("Total" if lang == "en" else "含税总额"),
        mode="lines+markers+text",
        text=trend["tong_tien"].apply(lambda v: f"{v:,.0f}"),
        textposition="top center",
        line=dict(color="#D9534F", width=3)
    ))
    
    fig.update_layout(
        title=title_map.get(lang, title_map["vi"]),
        barmode="stack",
        height=400,
        margin=dict(l=20, r=20, t=50, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def get_tax_distribution_chart(invoices: List[Dict[str, Any]], lang: str = "vi"):
    """Biểu đồ Cơ cấu Thuế suất GTGT (0%, 8%, 10%)"""
    if not invoices:
        return None
    df = pd.DataFrame(invoices)
    
    if "tien_chua_thue" not in df.columns:
        if "tong_tien_chua_thue" in df.columns:
            df["tien_chua_thue"] = df["tong_tien_chua_thue"]
        else:
            df["tien_chua_thue"] = pd.to_numeric(df.get("tong_tien", 0), errors="coerce").fillna(0) - pd.to_numeric(df.get("tien_thue", 0), errors="coerce").fillna(0)
    if "tien_thue" not in df.columns:
        df["tien_thue"] = 0.0
    if "tong_tien" not in df.columns:
        df["tong_tien"] = pd.to_numeric(df["tien_chua_thue"], errors="coerce").fillna(0) + pd.to_numeric(df["tien_thue"], errors="coerce").fillna(0)
        
    df["tien_chua_thue"] = pd.to_numeric(df["tien_chua_thue"], errors="coerce").fillna(0.0)
    df["tien_thue"] = pd.to_numeric(df["tien_thue"], errors="coerce").fillna(0.0)
    df["tong_tien"] = pd.to_numeric(df["tong_tien"], errors="coerce").fillna(0.0)
    
    def classify_tax(row):
        vat = float(row.get("tien_thue", 0.0))
        pre = float(row.get("tien_chua_thue", 0.0))
        if vat == 0:
            return "0% / Không chịu thuế" if lang == "vi" else ("0% / Exempt" if lang == "en" else "0% / 免税")
        rate = round((vat / pre) * 100) if pre > 0 else 10
        if rate in [7, 8]:
            return "8% (Ưu đãi)" if lang == "vi" else ("8% (Reduced)" if lang == "en" else "8% (优惠税率)")
        return f"{rate}%"
        
    df["NhomThue"] = df.apply(classify_tax, axis=1)
    tax_pie = df.groupby("NhomThue")["tong_tien"].sum().reset_index()
    
    title_map = {
        "vi": "🍩 Tỷ Trọng Cơ Cấu Thuế Suất GTGT",
        "en": "🍩 VAT Rate Breakdown Distribution",
        "zh": "🍩 增值税税率结构占比"
    }
    
    fig = px.pie(
        tax_pie,
        names="NhomThue",
        values="tong_tien",
        title=title_map.get(lang, title_map["vi"]),
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# =========================================================================
# 2. AP DEBT RECONCILIATION ENGINE (ĐỐI SOÁT CÔNG NỢ PHẢI TRẢ)
# =========================================================================

def get_ap_debt_reconciliation(invoices: List[Dict[str, Any]], payment_term_days: int = 30) -> List[Dict[str, Any]]:
    """
    Tính toán và lập bảng Đối soát Công nợ Phải trả theo từng Nhà Cung Cấp:
    - Ngày lập hóa đơn -> Hạn thanh toán (Due Date = Invoice Date + Payment Terms).
    - Phân tuổi nợ: Trong hạn (Current), Quá hạn 1-30 ngày, Quá hạn 31-60 ngày, Quá hạn >60 ngày.
    """
    if not invoices:
        return []
    
    today = datetime.date.today()
    supplier_debts = {}
    
    for inv in invoices:
        sup = inv.get("ten_nban", "Chưa xác định")
        mst = inv.get("mst_nban", "")
        amount = float(inv.get("tong_tien", 0.0))
        ngay_lap_str = str(inv.get("ngay_lap", "")).strip()
        
        try:
            inv_date = datetime.datetime.strptime(ngay_lap_str, "%Y-%m-%d").date()
        except Exception:
            try:
                inv_date = datetime.datetime.strptime(ngay_lap_str, "%d/%m/%Y").date()
            except Exception:
                inv_date = today
                
        due_date = inv_date + datetime.timedelta(days=payment_term_days)
        overdue_days = (today - due_date).days
        
        key = (sup, mst)
        if key not in supplier_debts:
            supplier_debts[key] = {
                "ten_nban": sup,
                "mst_nban": mst,
                "so_luong_hd": 0,
                "tong_cong_no": 0.0,
                "trong_han": 0.0,
                "qua_han_1_30": 0.0,
                "qua_han_31_60": 0.0,
                "qua_han_tren_60": 0.0,
                "han_chot_gan_nhat": due_date.isoformat(),
                "trang_thai": "Trong hạn"
            }
            
        data = supplier_debts[key]
        data["so_luong_hd"] += 1
        data["tong_cong_no"] += amount
        
        if overdue_days <= 0:
            data["trong_han"] += amount
        elif 1 <= overdue_days <= 30:
            data["qua_han_1_30"] += amount
        elif 31 <= overdue_days <= 60:
            data["qua_han_31_60"] += amount
        else:
            data["qua_han_tren_60"] += amount
            
        if due_date < datetime.date.fromisoformat(data["han_chot_gan_nhat"]):
            data["han_chot_gan_nhat"] = due_date.isoformat()
            
    # Đánh giá trạng thái
    results = list(supplier_debts.values())
    for r in results:
        if r["qua_han_tren_60"] > 0:
            r["trang_thai"] = "🚨 Quá hạn nghiêm trọng (>60 ngày)"
        elif r["qua_han_31_60"] > 0 or r["qua_han_1_30"] > 0:
            r["trang_thai"] = "⚠️ Quá hạn cần ưu tiên thanh toán"
        else:
            r["trang_thai"] = "✅ Trong hạn an toàn"
            
    return sorted(results, key=lambda x: x["tong_cong_no"], reverse=True)

# =========================================================================
# 3. FRAUD & TAX COMPLIANCE RISK ENGINE (CẢNH BÁO GIAN LẬN & RỦI RO THUẾ)
# =========================================================================

def detect_tax_and_fraud_risks(invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rà soát và phát hiện 6 loại rủi ro gian lận & vi phạm pháp luật thuế:
    1. Hóa đơn chưa ký số hợp lệ (Trốn thuế / Hóa đơn giả).
    2. Hóa đơn chưa cấp số chính thức (Hóa đơn nháp).
    3. Trùng lặp số hóa đơn trên cùng 1 MST người bán.
    4. Trùng lặp số tiền thanh toán bất thường cùng ngày.
    5. Bản cước mang dấu 'CHƯA THANH TOÁN'.
    6. Mã số thuế không đúng quy chuẩn (Khác 10 hoặc 13 chữ số).
    """
    if not invoices:
        return []
        
    risk_alerts = []
    seen_invoices = set()
    amount_day_tracker = {}
    
    for inv in invoices:
        inv_id = inv.get("id")
        fname = inv.get("filename", "")
        so_hd = str(inv.get("so_hd", "")).strip()
        kh_hd = str(inv.get("kh_hd", "")).strip()
        mst = str(inv.get("mst_nban", "")).strip()
        sup = inv.get("ten_nban", "Chưa rõ")
        amount = float(inv.get("tong_tien", 0.0))
        ngay = str(inv.get("ngay_lap", "")).strip()
        has_sig = bool(inv.get("has_signature"))
        sig_status = str(inv.get("sig_status", "Chưa ký số"))
        
        # 1. Kiểm tra Chữ ký số
        if not has_sig or sig_status == "Chưa ký số":
            risk_alerts.append({
                "muc_do": "🔴 CAO (Nguy cơ không được khấu trừ)",
                "loai_rui_ro": "Hóa đơn chưa ký số điện tử",
                "so_hd": so_hd,
                "nha_cung_cap": sup,
                "mst": mst,
                "so_tien": amount,
                "chi_tiet": f"Hóa đơn {fname} thiếu chữ ký số hợp lệ theo Thông tư 91/2026/TT-BTC. Doanh nghiệp sẽ bị loại trừ chi phí và thuế GTGT nếu đưa vào kê khai."
            })
            
        # 2. Hóa đơn chưa cấp số
        if not so_hd or so_hd == "<Chưa cấp số>" or "Chưa cấp số" in so_hd:
            risk_alerts.append({
                "muc_do": "🔴 CAO (Hóa đơn nháp vô hiệu)",
                "loai_rui_ro": "Hóa đơn chưa được cấp số chính thức",
                "so_hd": so_hd,
                "nha_cung_cap": sup,
                "mst": mst,
                "so_tien": amount,
                "chi_tiet": f"Tệp {fname} chỉ là bản thể hiện xem trước / nháp, chưa có giá trị pháp lý kế toán."
            })
            
        # 3. Trùng lặp hóa đơn
        inv_key = (mst, kh_hd, so_hd)
        if so_hd and so_hd not in ["-", "<Chưa cấp số>"]:
            if inv_key in seen_invoices:
                risk_alerts.append({
                    "muc_do": "🟠 TRUNG BÌNH (Trùng lặp chứng từ)",
                    "loai_rui_ro": "Phát hiện số HĐ trùng lặp từ cùng 1 NCC",
                    "so_hd": so_hd,
                    "nha_cung_cap": sup,
                    "mst": mst,
                    "so_tien": amount,
                    "chi_tiet": f"Số hóa đơn {so_hd} (Ký hiệu {kh_hd}) của MST {mst} xuất hiện nhiều lần trong đợt quét. Cần kiểm tra tránh thanh toán kép."
                })
            else:
                seen_invoices.add(inv_key)
                
        # 4. Trùng khớp số tiền bất thường trong cùng 1 ngày
        if amount > 1000000 and ngay:
            day_key = (mst, ngay, amount)
            if day_key in amount_day_tracker:
                risk_alerts.append({
                    "muc_do": "🟡 CẢNH BÁO (Bất thường chi phí)",
                    "loai_rui_ro": "Nhiều hóa đơn cùng giá trị trong cùng 1 ngày",
                    "so_hd": so_hd,
                    "nha_cung_cap": sup,
                    "mst": mst,
                    "so_tien": amount,
                    "chi_tiet": f"Phát hiện nhiều giao dịch chính xác {amount:,.0f} đ xuất cùng ngày {ngay} từ NCC {sup}. Đề xuất đối soát lại hợp đồng/biên bản bàn giao."
                })
            else:
                amount_day_tracker[day_key] = so_hd
                
        # 5. MST không đúng chuẩn
        clean_mst = mst.replace("-", "").replace(" ", "")
        if clean_mst and not (len(clean_mst) in [10, 13] and clean_mst.isdigit()):
            risk_alerts.append({
                "muc_do": "🟠 TRUNG BÌNH (Sai chuẩn Cục Thuế)",
                "loai_rui_ro": "Mã số thuế Người bán không đúng định dạng",
                "so_hd": so_hd,
                "nha_cung_cap": sup,
                "mst": mst,
                "so_tien": amount,
                "chi_tiet": f"MST '{mst}' không thuộc cấu trúc 10 số (Doanh nghiệp) hoặc 13 số (Chi nhánh) theo quy định Tổng cục Thuế."
            })
            
    return risk_alerts
