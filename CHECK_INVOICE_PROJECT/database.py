import sqlite3
import os
from typing import Dict, List, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "invoices.db")

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
