import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

AUTH_DB_PATH = os.path.join(os.path.dirname(__file__), "auth.db")

def _get_auth_conn():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    with _get_auth_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                company TEXT DEFAULT '',
                registered_at TEXT NOT NULL,
                trial_start TEXT NOT NULL,
                trial_end TEXT NOT NULL,
                plan TEXT DEFAULT 'trial_pro',
                status TEXT DEFAULT 'active',
                last_login TEXT DEFAULT ''
            )
        """)
        conn.commit()

        # Tao tai khoan Admin mac dinh neu chua ton tai
        cursor.execute("SELECT id FROM users WHERE username = 'hznguyen1997'")
        if not cursor.fetchone():
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            forever_end = (now + timedelta(days=3650)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, phone, company, registered_at, trial_start, trial_end, plan, status)
                VALUES ('hznguyen1997', ?, 'Nguyễn Hoàng Giang (Quản Trị Viên)', 'hznguyen1993@gmail.com', '09727 858 67', 'Admin System', ?, ?, ?, 'pro_admin', 'active')
            """, (hash_password("Anthumatmeo020922"), now_str, now_str, forever_end))
            conn.commit()

        # Tao tai khoan Ke toan trai nghiem mau neu chua co
        cursor.execute("SELECT id FROM users WHERE username = 'ketoan_demo'")
        if not cursor.fetchone():
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            trial_end = (now + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, phone, company, registered_at, trial_start, trial_end, plan, status)
                VALUES ('ketoan_demo', ?, 'Kế Toán Trải Nghiệm Mẫu', 'demo@ketoan.vn', '0912345678', 'Công Ty Thử Nghiệm FDI', ?, ?, ?, 'trial_pro', 'active')
            """, (hash_password("123456"), now_str, now_str, trial_end))
            conn.commit()

def hash_password(password: str) -> str:
    """Bam mat khau bao mat chuan SHA-256 kem muoi co dinh."""
    salt = "CHECK_INVOICE_SALT_2026"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def register_user(username: str, password: str, full_name: str, email: str = "", phone: str = "", company: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Dang ky tai khoan moi va tu dong cap 30 ngay dung thu Full tinh nang tinh tu thoi diem dang ky.
    """
    init_auth_db()
    u = username.strip().lower()
    p = password.strip()
    fn = full_name.strip()
    
    if len(u) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự.", None
    if len(p) < 4:
        return False, "Mật khẩu phải có ít nhất 4 ký tự.", None
    if not fn:
        return False, "Vui lòng nhập Họ và tên hoặc Tên người sử dụng.", None

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    trial_end = (now + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

    try:
        with _get_auth_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, phone, company, registered_at, trial_start, trial_end, plan, status, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'trial_pro', 'active', ?)
            """, (u, hash_password(p), fn, email.strip(), phone.strip(), company.strip(), now_str, now_str, trial_end, now_str))
            conn.commit()
            
            cursor.execute("SELECT * FROM users WHERE username = ?", (u,))
            user_row = dict(cursor.fetchone())
            return True, "🎉 Đăng ký thành công! Bạn nhận được 30 ngày dùng thử trọn vẹn mọi tính năng cao cấp.", user_row
    except sqlite3.IntegrityError:
        return False, f"Tên đăng nhập '{u}' đã tồn tại. Vui lòng chọn tên khác hoặc đăng nhập.", None
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}", None

def login_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Dang nhap va kiem tra thong tin tai khoan cung thoi han dung thu.
    """
    init_auth_db()
    u = username.strip().lower()
    p = password.strip()
    
    with _get_auth_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (u,))
        row = cursor.fetchone()
        
        if not row:
            return False, "Tài khoản không tồn tại. Vui lòng đăng ký tài khoản mới!", None
            
        user = dict(row)
        if user["password_hash"] != hash_password(p):
            return False, "Mật khẩu không chính xác. Vui lòng thử lại!", None
            
        if user["status"] == "blocked":
            return False, "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Quản trị viên.", None
            
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user["id"]))
        conn.commit()
        user["last_login"] = now_str
        
        return True, f"Chào mừng {user['full_name']} quay trở lại!", user

def get_user_trial_info(username: str) -> Dict[str, Any]:
    """
    Tinh toan chi tiet so ngay dung thu con lai, trang thai het han va quyen han cua tai khoan.
    """
    init_auth_db()
    u = username.strip().lower()
    with _get_auth_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (u,))
        row = cursor.fetchone()
        
        if not row:
            return {
                "username": username,
                "full_name": username,
                "is_active": True,
                "is_pro": True,
                "plan": "pro",
                "days_remaining": 30,
                "trial_start_fmt": datetime.now().strftime("%d/%m/%Y"),
                "trial_end_fmt": (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"),
                "is_admin": (u == "hznguyen1997")
            }
            
        user = dict(row)
        is_admin = (user["username"] == "hznguyen1997" or user["plan"] == "pro_admin")
        
        try:
            trial_end_dt = datetime.strptime(user["trial_end"], "%Y-%m-%d %H:%M:%S")
            trial_start_dt = datetime.strptime(user["trial_start"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            trial_end_dt = datetime.now() + timedelta(days=30)
            trial_start_dt = datetime.now()
            
        now = datetime.now()
        days_left = (trial_end_dt.date() - now.date()).days
        
        if is_admin or user["plan"] == "pro_permanent":
            return {
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user.get("email", ""),
                "phone": user.get("phone", ""),
                "company": user.get("company", ""),
                "is_active": True,
                "is_pro": True,
                "plan": "pro",
                "days_remaining": 9999,
                "trial_start_fmt": trial_start_dt.strftime("%d/%m/%Y"),
                "trial_end_fmt": "Vĩnh Viễn (Admin)",
                "is_admin": is_admin
            }
            
        is_trial_valid = (days_left >= 0)
        return {
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user.get("email", ""),
            "phone": user.get("phone", ""),
            "company": user.get("company", ""),
            "is_active": is_trial_valid,
            "is_pro": is_trial_valid,
            "plan": "pro" if is_trial_valid else "basic",
            "days_remaining": max(0, days_left),
            "trial_start_fmt": trial_start_dt.strftime("%d/%m/%Y"),
            "trial_end_fmt": trial_end_dt.strftime("%d/%m/%Y"),
            "is_admin": is_admin
        }

def get_all_registered_users() -> List[Dict[str, Any]]:
    """Lay toan bo danh sach nguoi dung cho Quan tri vien theo doi."""
    init_auth_db()
    with _get_auth_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, email, phone, company, registered_at, trial_start, trial_end, plan, status, last_login FROM users ORDER BY id DESC")
        rows = cursor.fetchall()
        
        results = []
        now = datetime.now()
        for r in rows:
            u = dict(r)
            try:
                end_dt = datetime.strptime(u["trial_end"], "%Y-%m-%d %H:%M:%S")
                days_left = (end_dt.date() - now.date()).days
            except Exception:
                days_left = 30
            u["days_remaining"] = max(0, days_left) if u["username"] != "hznguyen1997" else 9999
            results.append(u)
        return results

def admin_extend_user_trial(username: str, extra_days: int = 30) -> bool:
    """Quan tri vien cong them ngay dung thu cho nguoi dung."""
    init_auth_db()
    with _get_auth_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT trial_end FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return False
            
        try:
            curr_end = datetime.strptime(row["trial_end"], "%Y-%m-%d %H:%M:%S")
            if curr_end < datetime.now():
                new_end = datetime.now() + timedelta(days=extra_days)
            else:
                new_end = curr_end + timedelta(days=extra_days)
        except Exception:
            new_end = datetime.now() + timedelta(days=extra_days)
            
        new_end_str = new_end.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET trial_end = ?, status = 'active' WHERE username = ?", (new_end_str, username))
        conn.commit()
        return True

def admin_reset_user_password(username: str, new_password: str = "123456") -> Tuple[bool, str]:
    """Quan tri vien dat lai mat khau cho nguoi dung (khi nguoi dung quen mat khau)."""
    init_auth_db()
    u = username.strip().lower()
    p = new_password.strip()
    if len(p) < 4:
        return False, "Mật khẩu mới phải có ít nhất 4 ký tự."
        
    with _get_auth_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name FROM users WHERE username = ?", (u,))
        row = cursor.fetchone()
        if not row:
            return False, f"Không tìm thấy tài khoản '{u}'."
            
        new_hash = hash_password(p)
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, u))
        conn.commit()
        return True, f"✅ Đã đặt lại mật khẩu cho '{u}' thành '{p}' thành công!"

def admin_delete_user(username: str) -> Tuple[bool, str]:
    """Quan tri vien xoa tai khoan nguoi dung va toan bo thu muc du lieu."""
    init_auth_db()
    u = username.strip().lower()
    if u == "hznguyen1997":
        return False, "Không thể xóa tài khoản Quản trị viên tối cao!"
        
    with _get_auth_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (u,))
        conn.commit()
        
    import shutil
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_dir = os.path.join(base_dir, "user_data", u)
    if os.path.exists(user_dir):
        try:
            shutil.rmtree(user_dir, ignore_errors=True)
        except Exception:
            pass
            
    return True, f"✅ Đã xóa hoàn toàn tài khoản '{u}' và dữ liệu liên quan khỏi hệ thống!"

def delete_my_account(username: str) -> Tuple[bool, str]:
    """Nguoi dung tu yeu cau xoa vinh vien tai khoan cua chinh minh."""
    return admin_delete_user(username)

def user_forgot_password(username: str, phone_or_email: str, new_password: str) -> Tuple[bool, str]:
    """Nguoi dung tu khoi phuc mat khau bang cach xac thuc qua SĐT hoac Email da dang ky."""
    init_auth_db()
    u = username.strip().lower()
    contact = phone_or_email.strip().lower()
    p = new_password.strip()
    
    if len(p) < 4:
        return False, "Mật khẩu mới phải có ít nhất 4 ký tự."
        
    with _get_auth_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, phone, email FROM users WHERE username = ?", (u,))
        row = cursor.fetchone()
        if not row:
            return False, "Tài khoản không tồn tại. Vui lòng kiểm tra lại Tên đăng nhập."
            
        u_phone = (row["phone"] or "").strip().lower()
        u_email = (row["email"] or "").strip().lower()
        
        if contact not in [u_phone, u_email] or not contact:
            return False, "Số điện thoại hoặc Email không khớp với thông tin đã đăng ký tài khoản này."
            
        new_hash = hash_password(p)
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, u))
        conn.commit()
        return True, "🎉 Đặt lại mật khẩu thành công! Bạn có thể đăng nhập ngay bằng mật khẩu mới."

