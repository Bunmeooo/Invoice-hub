import os
import glob
import sqlite3
import random
import datetime
from typing import Dict, Any, List

ADMIN_BANK_NAME = "MBBank (Ngân hàng Quân Đội)"
ADMIN_BANK_CODE = "MB"
ADMIN_ACC_NUM = "0972785867"
ADMIN_ACC_NAME = "NGUYEN HOANG GIANG"
PRO_PRICE_VND = 99000

def generate_payment_order(user_id: str, amount: int = PRO_PRICE_VND) -> Dict[str, Any]:
    """Tạo thông tin giao dịch VietQR Napas 247 và cú pháp chuyển khoản định danh."""
    rand_code = f"{random.randint(1000, 9999)}"
    clean_user = user_id.replace(" ", "").upper()
    order_code = f"ORD_{clean_user}_{rand_code}"
    transfer_syntax = f"PRO {clean_user} {rand_code}"
    
    encoded_syntax = transfer_syntax.replace(" ", "%20")
    qr_url = f"https://img.vietqr.io/image/{ADMIN_BANK_CODE}-{ADMIN_ACC_NUM}-compact2.png?amount={amount}&addInfo={encoded_syntax}&accountName={ADMIN_ACC_NAME.replace(' ', '%20')}"
    
    return {
        "order_code": order_code,
        "bank_name": ADMIN_BANK_NAME,
        "bank_code": ADMIN_BANK_CODE,
        "account_num": ADMIN_ACC_NUM,
        "account_name": ADMIN_ACC_NAME,
        "amount": amount,
        "amount_formatted": f"{amount:,.0f} VND",
        "syntax": transfer_syntax,
        "code": rand_code,
        "qr_url": qr_url,
        "created_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

def submit_payment_order(db, order_code: str, user_id: str, device_id: str,
                         customer_name: str, contact_info: str, amount: float,
                         syntax: str, bank_tx_ref: str, auto_activate: bool = True) -> bool:
    """Ghi nhận giao dịch chuyển khoản vào cơ sở dữ liệu và kích hoạt quyền truy cập."""
    db.record_payment_transaction(
        order_code=order_code,
        user_id=user_id,
        device_id=device_id,
        customer_name=customer_name,
        contact_info=contact_info,
        amount=amount,
        syntax=syntax,
        bank_tx_ref=bank_tx_ref,
        status="approved" if auto_activate else "pending"
    )
    if auto_activate:
        db.activate_pro_plan(user_id=user_id, transaction_ref=bank_tx_ref or order_code, amount=amount)
    return True

def get_all_cross_payment_transactions() -> List[Dict[str, Any]]:
    """Tổng hợp tất cả giao dịch thanh toán từ toàn bộ các database người dùng để Quản trị viên kiểm soát."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_paths = glob.glob(os.path.join(base_dir, "user_data", "*", "invoices.db"))
    default_db = os.path.join(base_dir, "invoices.db")
    if os.path.exists(default_db):
        db_paths.append(default_db)
        
    all_txs = []
    seen_codes = set()
    
    for db_file in db_paths:
        try:
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Ensure payment_transactions table exists
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
            
            cursor.execute("SELECT * FROM payment_transactions ORDER BY id DESC")
            rows = cursor.fetchall()
            for r in rows:
                item = dict(r)
                item["db_path"] = db_file
                code = item.get("order_code")
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    all_txs.append(item)
            conn.close()
        except Exception:
            continue
            
    return sorted(all_txs, key=lambda x: x.get("id", 0), reverse=True)
