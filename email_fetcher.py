import imaplib
import email
from email.header import decode_header
import os
import zipfile
from typing import List, Dict, Any

class EmailInvoiceFetcher:
    @staticmethod
    def decode_str(s) -> str:
        if s is None:
            return ""
        decoded, encoding = decode_header(s)[0]
        if isinstance(decoded, bytes):
            return decoded.decode(encoding if encoding else "utf-8", errors="ignore")
        return str(decoded)

    @classmethod
    def fetch_invoices_from_email(
        cls, 
        imap_server: str, 
        email_user: str, 
        email_password: str, 
        folder: str = "INBOX", 
        days_limit: int = 7,
        download_dir: str = "downloaded_invoices"
    ) -> List[str]:
        """Connect to IMAP email, find invoice emails, download XML/ZIP attachments and return file paths"""
        os.makedirs(download_dir, exist_ok=True)
        downloaded_files = []
        
        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_user, email_password)
            mail.select(folder)
            
            # Search for emails containing invoice keywords
            status, messages = mail.search(None, '(OR (SUBJECT "hoa don") (SUBJECT "invoice"))')
            
            if status != "OK":
                print("No invoice emails found.")
                return []
                
            email_ids = messages[0].split()
            # Check latest emails
            for e_id in email_ids[-30:]:
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                if res != "OK":
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = cls.decode_str(msg["Subject"])
                        
                        for part in msg.walk():
                            if part.get_content_maintype() == 'multipart':
                                continue
                            if part.get('Content-Disposition') is None:
                                continue
                                
                            filename = part.get_filename()
                            if filename:
                                filename = cls.decode_str(filename)
                                ext = os.path.splitext(filename)[1].lower()
                                
                                if ext in [".xml", ".zip"]:
                                    file_path = os.path.join(download_dir, filename)
                                    with open(file_path, "wb") as f:
                                        f.write(part.get_payload(decode=True))
                                    downloaded_files.append(file_path)
            mail.logout()
        except Exception as e:
            print(f"Error fetching from email: {e}")
            
        return downloaded_files
