import re
import unicodedata

# BẢNG TỪ KHÓA NHẠY CẢM VÀ CÁC BIẾN THỂ (PROFANITY & HARMFUL WORDS DICTIONARY)
BAD_WORDS_PATTERNS = [
    # 1. Chửi thề, tiếng lóng thô tục (cẹc, cẹk, cặc, lồn, buồi, dcm, vcl, như cẹc...)
    r"như\s*c[ẹeéèẽẻêệếề]c|như\s*c[ẹeéèẽẻêệếề]k|như\s*c[aặáàảãạ]c|như\s*c[aặáàảãạ]k|như\s*l[oồ]n|như\s*cc|như\s*cl|như\s*l\b|như\s*c\b",
    r"\b(c[ẹeéèẽẻêệếề]c|c[ẹeéèẽẻêệếề]k|c[aặáàảãạ]k|c[aặáàảãạ]c|k[aặáàảãạ]c|k[aặáàảãạ]k|c4c|c4k|c[eẹ]k|c[eẹ]c)\b",
    r"đ[iịíì]t|d[iịíì]t|d[1i]t|d[k|c]m|dcm|dkm|dcmm|clmm|vcl|v[k|c]l|vcc|vloz|vl\b|vlon|c[o|0]n\s*c[a|4]k|b[u|ù|ú]i|b[u|0]01|l[o|ồ|õ|ô|0]n|l[o|0]ll|l[oồ]z|lồz|đ[b|ĩ|y]|đ[eẹ]ch|đ[eẹ]t|đ[uụù]|duma|đuma|c[m|n]m|ccmn|cmn|ng[u|ù]|[oó]c\s*ch[oó]|ch[oó]\s*đ[eẻ]?|ch[oó]\s*m[aá]|m[eẹ]\s*ki[eế]p",
    r"đ[\.\_\-\s]*[iị][\.\_\-\s]*t|l[\.\_\-\s]*[oồ][\.\_\-\s]*n|c[\.\_\-\s]*[aặeẹ][\.\_\-\s]*[ck]|b[\.\_\-\s]*u[\.\_\-\s]*[oồ][\.\_\-\s]*i|m[\.\_\-\s]*[eẹ]",
    
    # 2. Nội dung khiêu dâm, quấy rối (NSFW)
    r"s[eê]x|s[\.\_\-]e[\.\_\-]x|s3x|s[eế]ch|th[uủ]\s*d[aâ]m|l[aà]m\s*t[iì]nh|sh[oô]w\s*h[aà]ng|v[uú]|ch[iị]ch|chjch|ch[ií]t|g[aạ]\s*ch[iị]ch|f[u|c|k]+|p[u|s]+y|d[i|c]k",
    
    # 3. Gian lận, cờ bạc, nội dung phi pháp
    r"t[aà]i\s*x[iỉ]u|t[\.\_\-]à[\.\_\-]i\s*x[\.\_\-]ỉ[\.\_\-]u|t4i\s*x1u|c[aá]\s*đ[oộ]|n[oổ]\s*h[uũ]|n0\s*hu|vay\s*n[oó]ng|ma\s*t[uú]y|mai\s*th[uú]y|k[eẹ]o\s*ke|đ[aậ]p\s*đ[aá]",
    
    # 4. Kỳ thị, xúc phạm vùng miền, chính trị
    r"b[aắ]c\s*k[yỳ]|nam\s*k[yỳ]|m[oọ]i\s*r[oợ]|pbvm|p[\.\_\-]b[\.\_\-]v[\.\_\-]m|3\s*que|3q|b[oò]\s*đ[oỏ]|bodo|b@ck[\-\s]*ky"
]

# EMOJI / KÝ TỰ BIỂU TƯỢNG NHẠY CẢM
EMOJI_PATTERNS = r"🎲|💊|🍁|🔞|🍑|🍆"

def normalize_text_for_filter(text: str) -> str:
    """Chuẩn hóa chuỗi để phát hiện ký tự biến đổi Leetspeak và chèn dấu."""
    if not text:
        return ""
    # Chuyển đổi leetspeak thông dụng
    t = text.lower()
    t = t.replace("0", "o").replace("1", "i").replace("3", "e").replace("4", "a").replace("@", "a")
    return t

def mask_profanity(text: str) -> str:
    """
    Quét và mã hóa toàn bộ từ ngữ tục tĩu, chửi thề, cờ bạc, kỳ thị thành '***'.
    Giữ nguyên cấu trúc văn phong bình thường của người dùng.
    """
    if not text:
        return text
        
    sanitized = text
    
    # 1. Mã hóa Emoji nhạy cảm
    sanitized = re.sub(EMOJI_PATTERNS, "***", sanitized)
    
    # 2. Quét qua từng biểu thức chính quy (Word boundary & Regex)
    for pattern in BAD_WORDS_PATTERNS:
        # Regex tìm từ nhạy cảm không phân biệt hoa thường
        regex = re.compile(pattern, re.IGNORECASE | re.UNICODE)
        sanitized = regex.sub("***", sanitized)
        
    return sanitized

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    test_cases = [
        "Phần mềm dùng tốt nhưng dịch vụ như clmm dkm d1t",
        "Đề nghị thêm chức năng xuất excel, đừng làm ăn như óc chó",
        "Có hỗ trợ nạp tiền chơi t.à.i x.ỉ.u 🎲 hoặc cá độ không?",
        "Góp ý tính năng mới rất mượt mà, cảm ơn đội ngũ phát triển!",
        "Chống pbvm và 3 que phá hoại hệ thống",
        "Gửi ảnh s.e.x và show hàng"
    ]
    print("=== KIỂM THỬ BỘ LỌC TỪ NGỮ NHẠY CẢM ===")
    for tc in test_cases:
        masked = mask_profanity(tc)
        print(f"GỐC : {tc}")
        print(f"LỌC : {masked}\n")
