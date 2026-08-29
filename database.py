import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "invoices.db")
USER_DATA_ROOT = os.path.join(os.path.dirname(__file__), "user_data")

def get_user_database(user_id: str = "default_user", is_temp: bool = False, base_dir: str = USER_DATA_ROOT) -> "InvoiceDatabase":
    """
    Tạo hoặc kết nối tới Cơ sở dữ liệu SQLite riêng biệt, độc lập cho từng người dùng / phiên làm việc.
    Đảm bảo 100% dữ liệu của người dùng A không bao giờ bị lẫn với người dùng B.
    """
    import re
    clean_user_id = re.sub(r'[^a-zA-Z0-9_\-\u00C0-\u1EF9]', '_', str(user_id).strip())
    if not clean_user_id:
        clean_user_id = "default_user"
        
    if is_temp:
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix=f"inv_sess_{clean_user_id}_")
        db_file = os.path.join(temp_dir, "invoices.db")
    else:
        user_folder = os.path.join(base_dir, clean_user_id)
        os.makedirs(user_folder, exist_ok=True)
        db_file = os.path.join(user_folder, "invoices.db")
        
    return InvoiceDatabase(db_path=db_file)

class InvoiceDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    kh_mau TEXT,
                    kh_hd TEXT,
                    so_hd TEXT,
                    ngay_lap TEXT,
                    dv_tiente TEXT,
                    ty_gia REAL,
                    mst_nban TEXT,
                    ten_nban TEXT,
                    dc_nban TEXT,
                    mst_nmua TEXT,
                    ten_nmua TEXT,
                    dc_nmua TEXT,
                    tien_chua_thue REAL,
                    tien_thue REAL,
                    tong_tien REAL,
                    ma_cqt TEXT,
                    web_tra_cuu TEXT,
                    ma_tra_cuu TEXT,
                    has_signature INTEGER DEFAULT 0,
                    signer TEXT,
                    sign_time TEXT,
                    sig_status TEXT,
                    is_valid INTEGER DEFAULT 1,
                    status_summary TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(mst_nban, kh_hd, so_hd)
                )
            """)
            
            # Migration check
            cursor.execute("PRAGMA table_info(invoices)")
            existing_cols = [c["name"] for c in cursor.fetchall()]
            
            all_cols = {
                "ma_cqt": "TEXT",
                "web_tra_cuu": "TEXT",
                "ma_tra_cuu": "TEXT",
                "has_signature": "INTEGER DEFAULT 0",
                "signer": "TEXT",
                "sign_time": "TEXT",
                "sig_status": "TEXT",
                "is_valid": "INTEGER DEFAULT 1",
                "status_summary": "TEXT",
                "notes": "TEXT"
            }
            for col_name, col_type in all_cols.items():
                if col_name not in existing_cols:
                    cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER,
                    stt INTEGER,
                    ten_hang TEXT,
                    dvt TEXT,
                    so_luong REAL,
                    don_gia REAL,
                    thanh_tien REAL,
                    thue_suat TEXT,
                    tien_thue REAL,
                    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    rating INTEGER,
                    category TEXT,
                    comment TEXT,
                    created_at TEXT,
                    status TEXT DEFAULT 'Chờ xử lý',
                    admin_note TEXT DEFAULT ''
                )
            """)
            cursor.execute("PRAGMA table_info(user_feedback)")
            existing_fb_cols = [col[1] for col in cursor.fetchall()]
            if "status" not in existing_fb_cols:
                cursor.execute("ALTER TABLE user_feedback ADD COLUMN status TEXT DEFAULT 'Chờ xử lý'")
            if "admin_note" not in existing_fb_cols:
                cursor.execute("ALTER TABLE user_feedback ADD COLUMN admin_note TEXT DEFAULT ''")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    usage_date TEXT,
                    file_count INTEGER DEFAULT 0,
                    UNIQUE(user_id, usage_date)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    user_id TEXT PRIMARY KEY,
                    plan TEXT DEFAULT 'basic',
                    activated_at TEXT,
                    expires_at TEXT,
                    transaction_ref TEXT,
                    amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weekly_archive_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    year_week TEXT,
                    file_count INTEGER DEFAULT 0,
                    UNIQUE(user_id, year_week)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_code TEXT UNIQUE,
                    user_id TEXT,
                    device_id TEXT,
                    customer_name TEXT,
                    contact_info TEXT,
                    amount REAL DEFAULT 99000,
                    syntax TEXT,
                    bank_tx_ref TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    approved_at TEXT,
                    notes TEXT DEFAULT ''
                )
            """)
            conn.commit()
            
    def insert_invoice(self, invoice_data: Dict[str, Any], overwrite: bool = True) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT id FROM invoices WHERE mst_nban = ? AND kh_hd = ? AND so_hd = ?",
                    (invoice_data.get("mst_nban", ""), invoice_data.get("kh_hd", ""), invoice_data.get("so_hd", ""))
                )
                existing = cursor.fetchone()
                
                if existing:
                    if not overwrite:
                        return False
                    inv_id = existing["id"]
                    cursor.execute("""
                        UPDATE invoices SET
                            filename = ?, kh_mau = ?, ngay_lap = ?, dv_tiente = ?, ty_gia = ?,
                            ten_nban = ?, dc_nban = ?, mst_nmua = ?, ten_nmua = ?, dc_nmua = ?,
                            tien_chua_thue = ?, tien_thue = ?, tong_tien = ?,
                            ma_cqt = ?, web_tra_cuu = ?, ma_tra_cuu = ?,
                            has_signature = ?, signer = ?, sign_time = ?, sig_status = ?,
                            is_valid = ?, status_summary = ?, notes = ?
                        WHERE id = ?
                    """, (
                        invoice_data.get("filename", ""),
                        invoice_data.get("kh_mau", "1"),
                        invoice_data.get("ngay_lap", ""),
                        invoice_data.get("dv_tiente", "VND"),
                        invoice_data.get("ty_gia", 1.0),
                        invoice_data.get("ten_nban", ""),
                        invoice_data.get("dc_nban", ""),
                        invoice_data.get("mst_nmua", ""),
                        invoice_data.get("ten_nmua", ""),
                        invoice_data.get("dc_nmua", ""),
                        invoice_data.get("tien_chua_thue", 0.0),
                        invoice_data.get("tien_thue", 0.0),
                        invoice_data.get("tong_tien", 0.0),
                        invoice_data.get("ma_cqt", ""),
                        invoice_data.get("web_tra_cuu", ""),
                        invoice_data.get("ma_tra_cuu", ""),
                        1 if invoice_data.get("has_signature") else 0,
                        invoice_data.get("signer", ""),
                        invoice_data.get("sign_time", ""),
                        invoice_data.get("sig_status", "Đã ký số"),
                        1 if invoice_data.get("is_valid", True) else 0,
                        invoice_data.get("status_summary", "Hợp lệ"),
                        invoice_data.get("notes", ""),
                        inv_id
                    ))
                    cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (inv_id,))
                else:
                    cursor.execute("""
                        INSERT INTO invoices (
                            filename, kh_mau, kh_hd, so_hd, ngay_lap, dv_tiente, ty_gia,
                            mst_nban, ten_nban, dc_nban, mst_nmua, ten_nmua, dc_nmua,
                            tien_chua_thue, tien_thue, tong_tien,
                            ma_cqt, web_tra_cuu, ma_tra_cuu,
                            has_signature, signer, sign_time, sig_status,
                            is_valid, status_summary, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        invoice_data.get("filename", ""),
                        invoice_data.get("kh_mau", "1"),
                        invoice_data.get("kh_hd", ""),
                        invoice_data.get("so_hd", ""),
                        invoice_data.get("ngay_lap", ""),
                        invoice_data.get("dv_tiente", "VND"),
                        invoice_data.get("ty_gia", 1.0),
                        invoice_data.get("mst_nban", ""),
                        invoice_data.get("ten_nban", ""),
                        invoice_data.get("dc_nban", ""),
                        invoice_data.get("mst_nmua", ""),
                        invoice_data.get("ten_nmua", ""),
                        invoice_data.get("dc_nmua", ""),
                        invoice_data.get("tien_chua_thue", 0.0),
                        invoice_data.get("tien_thue", 0.0),
                        invoice_data.get("tong_tien", 0.0),
                        invoice_data.get("ma_cqt", ""),
                        invoice_data.get("web_tra_cuu", ""),
                        invoice_data.get("ma_tra_cuu", ""),
                        1 if invoice_data.get("has_signature") else 0,
                        invoice_data.get("signer", ""),
                        invoice_data.get("sign_time", ""),
                        invoice_data.get("sig_status", "Đã ký số"),
                        1 if invoice_data.get("is_valid", True) else 0,
                        invoice_data.get("status_summary", "Hợp lệ"),
                        invoice_data.get("notes", ""),
                    ))
                    inv_id = cursor.lastrowid
                
                # Insert items
                items = invoice_data.get("items", [])
                for it in items:
                    cursor.execute("""
                        INSERT INTO invoice_items (
                            invoice_id, stt, ten_hang, dvt, so_luong, don_gia,
                            thanh_tien, thue_suat, tien_thue
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        inv_id,
                        it.get("stt", 1),
                        it.get("ten_hang", ""),
                        it.get("dvt", ""),
                        it.get("so_luong", 0.0),
                        it.get("don_gia", 0.0),
                        it.get("thanh_tien", 0.0),
                        it.get("thue_suat", ""),
                        it.get("tien_thue", 0.0),
                    ))
                    
                conn.commit()
                return True
            except Exception as e:
                print(f"DB Error: {e}")
                return False

    def get_all_invoices(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices ORDER BY ten_nban ASC, ngay_lap DESC, id DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
    def get_invoice_items(self, invoice_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY stt ASC", (invoice_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_all(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoice_items")
            cursor.execute("DELETE FROM invoices")
            conn.commit()

    # ================= QUẢN TRỊ HẠN MỨC GÓI BASIC / PRO =================
    def get_daily_usage(self, user_id: str, date_str: str = None) -> int:
        import datetime
        if not date_str:
            date_str = datetime.date.today().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_count FROM daily_usage WHERE user_id = ? AND usage_date = ?", (user_id, date_str))
            row = cursor.fetchone()
            return row["file_count"] if row else 0

    def increment_daily_usage(self, user_id: str, count: int = 1, date_str: str = None) -> int:
        import datetime
        if not date_str:
            date_str = datetime.date.today().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_usage (user_id, usage_date, file_count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, usage_date) DO UPDATE SET file_count = file_count + ?
            """, (user_id, date_str, count, count))
            conn.commit()
            return self.get_daily_usage(user_id, date_str)

    def get_user_plan(self, user_id: str) -> str:
        """
        Lấy trạng thái gói dịch vụ của người dùng dựa trên thời hạn 30 ngày dùng thử tính từ lúc đăng ký.
        """
        try:
            from auth import get_user_trial_info
            t_info = get_user_trial_info(user_id)
            return t_info.get("plan", "pro")
        except Exception:
            return "pro"

    def activate_pro_plan(self, user_id: str, transaction_ref: str, amount: float = 99000.0, days: int = 365) -> bool:
        """Kích hoạt gói Pro tự động và lưu vào cơ sở dữ liệu."""
        try:
            now = datetime.now()
            activated_at = now.strftime("%d/%m/%Y - %H:%M")
            expires_at = (now + timedelta(days=days)).strftime("%d/%m/%Y - %H:%M")
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_subscriptions (user_id, plan, activated_at, expires_at, transaction_ref, amount, status)
                    VALUES (?, 'pro', ?, ?, ?, ?, 'active')
                    ON CONFLICT(user_id) DO UPDATE SET
                        plan = 'pro',
                        activated_at = excluded.activated_at,
                        expires_at = excluded.expires_at,
                        transaction_ref = excluded.transaction_ref,
                        amount = excluded.amount,
                        status = 'active'
                """, (user_id, activated_at, expires_at, transaction_ref, amount))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error activating pro plan for {user_id}: {e}")
            return False

    def deactivate_pro_plan(self, user_id: str) -> bool:
        """Hủy kích hoạt gói Pro của người dùng."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE user_subscriptions SET plan = 'basic', status = 'expired' WHERE user_id = ?", (user_id,))
                conn.commit()
                return True
        except Exception as e:
            return False

    def get_weekly_archive_usage(self, user_id: str, week_str: str = None) -> int:
        """Lấy số lượng tệp nén (ZIP/RAR) đã xử lý trong tuần hiện tại."""
        import datetime
        if not week_str:
            week_str = datetime.date.today().strftime("%Y-W%W")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_count FROM weekly_archive_usage WHERE user_id = ? AND year_week = ?", (user_id, week_str))
            row = cursor.fetchone()
            return row["file_count"] if row else 0

    def increment_weekly_archive_usage(self, user_id: str, count: int = 1, week_str: str = None) -> int:
        """Tăng số lượng tệp nén đã xử lý trong tuần."""
        import datetime
        if not week_str:
            week_str = datetime.date.today().strftime("%Y-W%W")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weekly_archive_usage (user_id, year_week, file_count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, year_week) DO UPDATE SET file_count = file_count + ?
            """, (user_id, week_str, count, count))
            conn.commit()
            return self.get_weekly_archive_usage(user_id, week_str)

    def check_quota(self, user_id: str, plan_type: str = "pro", new_files_count: int = 1) -> Tuple[bool, int, int]:
        """
        Kiểm tra người dùng có được phép nạp thêm tệp hay không.
        - Trong thời gian 30 ngày dùng thử (Pro): Không giới hạn.
        - Khi hết hạn 30 ngày (Basic): 20 tệp PDF/XML mỗi ngày.
        """
        actual_plan = self.get_user_plan(user_id)
        if actual_plan == "pro" or plan_type.lower() == "pro":
            used_today = self.get_daily_usage(user_id)
            return True, used_today, 999999
            
        used_today = self.get_daily_usage(user_id)
        limit = 20
        if used_today + new_files_count > limit:
            return False, used_today, max(0, limit - used_today)
        return True, used_today, max(0, limit - used_today)

    def check_fine_grained_quota(self, user_id: str, plan_type: str = "pro", new_std_count: int = 0, new_arc_count: int = 0) -> Dict[str, Any]:
        """
        Kiểm tra hạn mức chi tiết theo trạng thái tài khoản:
        - Trong 30 ngày dùng thử: Mở 100% không giới hạn.
        - Khi hết hạn dùng thử: Áp dụng 20 PDF/XML/ngày và 3 ZIP/RAR/tuần.
        """
        actual_plan = self.get_user_plan(user_id)
        if actual_plan == "pro" or plan_type.lower() == "pro":
            std_used = self.get_daily_usage(user_id)
            arc_used = self.get_weekly_archive_usage(user_id)
            return {
                "allowed": True,
                "reason": "",
                "std_used": std_used,
                "std_limit": 999999,
                "std_rem": 999999,
                "arc_used": arc_used,
                "arc_limit": 999999,
                "arc_rem": 999999
            }
            
        std_used = self.get_daily_usage(user_id)
        arc_used = self.get_weekly_archive_usage(user_id)
        
        std_limit = 20
        arc_limit = 3
        
        std_ok = (std_used + new_std_count) <= std_limit
        arc_ok = (arc_used + new_arc_count) <= arc_limit
        
        reasons = []
        if not std_ok:
            reasons.append(f"Hạn mức PDF/XML đã đạt {std_used}/{std_limit} tệp hôm nay (nạp thêm: {new_std_count})")
        if not arc_ok:
            reasons.append(f"Hạn mức ZIP/RAR đã đạt {arc_used}/{arc_limit} tệp tuần này (nạp thêm: {new_arc_count})")
            
        return {
            "allowed": (std_ok and arc_ok),
            "reason": " | ".join(reasons),
            "std_used": std_used,
            "std_limit": std_limit,
            "std_rem": max(0, std_limit - std_used),
            "arc_used": arc_used,
            "arc_limit": arc_limit,
            "arc_rem": max(0, arc_limit - arc_used)
        }

    # ================= QUẢN LÝ GIAO DỊCH THANH TOÁN (PAYMENT TRANSACTIONS) =================
    def record_payment_transaction(self, order_code: str, user_id: str, device_id: str,
                                   customer_name: str, contact_info: str, amount: float,
                                   syntax: str, bank_tx_ref: str, status: str = "pending") -> bool:
        """Ghi nhận yêu cầu thanh toán / chuyển khoản nâng cấp Pro."""
        try:
            now_str = datetime.now().strftime("%d/%m/%Y - %H:%M")
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO payment_transactions (order_code, user_id, device_id, customer_name, contact_info, amount, syntax, bank_tx_ref, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_code) DO UPDATE SET
                        bank_tx_ref = excluded.bank_tx_ref,
                        contact_info = excluded.contact_info,
                        customer_name = excluded.customer_name
                """, (order_code, user_id, device_id, customer_name, contact_info, amount, syntax, bank_tx_ref, status, now_str))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording transaction {order_code}: {e}")
            return False

    def get_all_payment_transactions(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách giao dịch nâng cấp Pro để Quản trị viên kiểm soát."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM payment_transactions ORDER BY id DESC")
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"Error getting payment transactions: {e}")
            return []

    def approve_payment_transaction(self, order_code: str, admin_note: str = "") -> Tuple[bool, str]:
        """Quản trị viên phê duyệt giao dịch và tự động kích hoạt Pro cho người dùng."""
        try:
            now_str = datetime.now().strftime("%d/%m/%Y - %H:%M")
            user_id = ""
            amount = 99000.0
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, amount, bank_tx_ref FROM payment_transactions WHERE order_code = ?", (order_code,))
                row = cursor.fetchone()
                if not row:
                    return False, ""
                user_id = row["user_id"]
                amount = row["amount"]
                
                cursor.execute("""
                    UPDATE payment_transactions 
                    SET status = 'approved', approved_at = ?, notes = ?
                    WHERE order_code = ?
                """, (now_str, admin_note, order_code))
                conn.commit()
            
            # Kích hoạt gói Pro vào user_subscriptions
            self.activate_pro_plan(user_id=user_id, transaction_ref=f"APPROVED_{order_code}", amount=amount)
            return True, user_id
        except Exception as e:
            print(f"Error approving transaction {order_code}: {e}")
            return False, ""

    def reject_payment_transaction(self, order_code: str, admin_note: str = "") -> bool:
        """Quản trị viên từ chối / hủy giao dịch."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE payment_transactions SET status = 'rejected', notes = ? WHERE order_code = ?", (admin_note, order_code))
                conn.commit()
                return True
        except Exception as e:
            return False

    # ================= HỆ THỐNG ĐÓNG GÓP Ý KIẾN (FEEDBACK) =================
    def save_feedback(self, user_id: str, rating: int, category: str, comment: str) -> bool:
        try:
            from content_moderator import mask_profanity
            sanitized_comment = mask_profanity(comment)
            now_str = datetime.now().strftime("%d/%m/%Y - %H:%M")
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_feedback (user_id, rating, category, comment, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, rating, category, sanitized_comment, now_str))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False

    def get_feedback_list(self, user_id: str = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM user_feedback WHERE user_id = ? ORDER BY id DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM user_feedback ORDER BY id DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_feedback(self, feedback_id: int) -> bool:
        """Xóa bình luận theo ID dành cho Quản trị viên."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_feedback WHERE id = ?", (feedback_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting feedback {feedback_id}: {e}")
            return False

    def update_feedback_status(self, feedback_id: int, status: str, admin_note: str = "") -> bool:
        """Cập nhật trạng thái xử lý bình luận (Đã xử lý / Đang xử lý / Chờ xử lý)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_feedback 
                    SET status = ?, admin_note = ?
                    WHERE id = ?
                """, (status, admin_note, feedback_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating feedback {feedback_id}: {e}")
            return False

    def delete_all_feedback(self) -> bool:
        """Xóa toàn bộ bình luận trong database hiện tại."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_feedback")
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting all feedback: {e}")
            return False

