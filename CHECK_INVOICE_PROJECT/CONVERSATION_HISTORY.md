# HỒ SƠ LỊCH SỬ DỰ ÁN & TOÀN BỘ YÊU CẦU NGƯỜI DÙNG
## PROJECT: CHECK_INVOICE_PROJECT (E-Invoice Scraper, Parser & TT 91/2026/TT-BTC Hub)

---

### 📌 MỤC TIÊU DỰ ÁN
Xây dựng một hệ thống phần mềm kế toán tự động hóa hoàn chỉnh nhằm:
1. **Nạp & Quét Đa Định Dạng**: Tự động đọc và bóc tách dữ liệu từ các tệp hóa đơn điện tử định dạng `.xml`, `.pdf`, `.zip`, và kho lưu trữ nén `.rar` (sử dụng WinRAR/7-Zip).
2. **Thẩm định Pháp lý Kế toán Chuẩn Thông tư 91/2026/TT-BTC & Nghị định 123/2020/NĐ-CP**:
   - Kiểm tra tính đầy đủ của chữ ký số điện tử (`Đã ký số` vs `Chưa ký số`).
   - Kiểm tra sự tồn tại và tính toàn vẹn của Mã cơ quan thuế (MCCQT).
   - Xác định và bóc tách chính xác Ký hiệu mẫu số, Ký hiệu hóa đơn (`1C25TMT`, `1C26TYY`, `1K26DAB`...).
   - Bóc tách Website tra cứu và Mã số bí mật tra cứu cho từng loại hóa đơn (BKAV eHoadon, MISA meInvoice, Viettel S-Invoice, VNPT, FAST, v.v.).
   - Phân biệt rõ ràng các bản thể hiện tạm tính/chưa thanh toán, bản nháp chưa cấp số, hóa đơn hợp lệ.
3. **Báo cáo Kế toán Đạt Chuẩn Forensic Excel**:
   - Sử dụng font chữ thống nhất: **`Times New Roman`** trên toàn bộ workbook.
   - **Tuyệt đối không dùng gộp ô (Merge & Center)** $\rightarrow$ Bắt buộc sử dụng **`Center Across Selection` (`centerContinuous`)** cho các tiêu đề bảng và dòng tổng cộng.
   - **Cố định dòng và cột (Freeze Panes)** chính xác tại ô **`D5`** cho cả 2 Sheet.
   - Độ rộng các cột được thiết lập vừa vặn chính xác theo độ dài dữ liệu thực tế bên trong.
   - Phân cách giữa các ô và cột bằng đường viền nét mảnh màu xám nhẹ (`#BFBFBF`).
   - Tự động **tô màu nổi bật cảnh báo (`#FFF2CC` / `#FCE4D6`)** với chữ màu đỏ đậm đối với các dòng hóa đơn chưa ký số, chưa cấp số, hoặc nghi ngờ/chưa đủ điều kiện pháp lý.
4. **Chia sẻ & Khởi động Dễ dàng**: Cho phép mọi người trong mạng LAN/Wi-Fi công ty cùng truy cập qua trình duyệt mà không cần cài đặt.

---

### 📜 TOÀN BỘ LỊCH SỬ TRAO ĐỔI & YÊU CẦU CỦA NGƯỜI DÙNG (CHRONOLOGICAL RECORD)

#### 🔹 GIAI ĐOẠN 1: Khởi tạo & Sửa lỗi Nạp Tệp / Cache
* **Yêu cầu 1**: *"2 chức năng nạp tệp và quét đường dẫn đều đang bị lỗi, hãy kiểm tra và fix chúng"*
  * *Xử lý*: Khắc phục lỗi đọc dữ liệu từ đường dẫn mạng LAN và tải tệp lên qua giao diện Streamlit.
* **Yêu cầu 2**: *"Tôi đã thử lại các chức năng trên vẫn không được"*
  * *Xử lý*: Sửa triệt để hàm xử lý luồng byte dữ liệu tạm (`tempfile`), tối ưu hóa kết nối SQLite database.
* **Yêu cầu 3**: *"xử lý tiếp lỗi này"*
  * *Xử lý*: Khắc phục lỗi xử lý xung đột khóa chính và lưu trữ danh sách hàng hóa chi tiết (`invoice_items`).
* **Yêu cầu 4**: *"tại sao lại có 13 dòng hóa đơn trong khi tôi kiểm tra tại thư mục chỉ có 12 hóa đơn, và khi tôi xóa cache vẫn hiện lên báo cáo cũ, hãy xử lý vấn đề này"*
  * *Xử lý*:
    - Điều tra nguyên nhân 13 dòng: Thư mục chứa 12 file Viettel cước viễn thông (`1.发票1530.pdf` đến `1.发票2624.pdf`) cộng với 1 file nháp của Madeown (`1C25TMD_Chuacapso.pdf`) tồn đọng trong DB.
    - Bổ sung nút **"🗑️ XÓA TOÀN BỘ DATABASE"** trên Sidebar giúp làm sạch dữ liệu triệt để, xóa bỏ hoàn toàn cache bộ nhớ đệm và reset bảng tính.

---

#### 🔹 GIAI ĐOẠN 2: Tinh gọn Giao diện & Thiết lập Tiêu chuẩn Thông tư Mới nhất
* **Yêu cầu 5**: *"Bỏ phần Quét Thư mục (Máy tính & Ổ mạng LAN) đi, thay vào đó làm 1 bảng preview tác vụ"*
  * *Xử lý*: Loại bỏ ô nhập đường dẫn thư mục quét trên Tab 1; thay thế bằng Bảng Preview Tác vụ Trực quan hiển thị trạng thái xử lý từng file ngay sau khi nạp.
* **Yêu cầu 6**: *"Bỏ phần 3. Tự động quét email đi"*
  * *Xử lý*: Loại bỏ hoàn toàn tính năng quét email IMAP, tinh gọn ứng dụng thành 3 Tab cốt lõi:
    - **Tab 1**: Nạp & Quét Tệp (PDF, XML, ZIP, RAR).
    - **Tab 2**: Cơ sở Dữ liệu & Quản lý Hóa đơn.
    - **Tab 3**: Xuất Báo Cáo Excel Chuẩn Kế Toán (2 Sheet).
* **Yêu cầu 7**: *"Hiện tại thì thông tin quét tệp tin pdf và xml vẫn chưa đúng và đầy đủ, cần trình bày gọn gàng sạch sẽ dữ liệu cào ra, chứ không phải cào cho qua loa, hãy tự căn chỉnh lại. Sheet tổng hợp là tổng hợp các hóa đơn, sheet chi tiết thì phải định được chi tiết theo nhà cung cấp. Xác định hóa đơn đã đầy đủ chữ ký, hóa đơn hợp lý, hợp lệ theo chuẩn thông tư mới nhất hiện tại (Thông tư mới nhất về hóa đơn điện tử là Thông tư số 91/2026/TT-BTC do Bộ Tài chính ban hành ngày 30/06/2026, có hiệu lực từ ngày 01/07/2026)."*
  * *Xử lý*:
    - Xây dựng cấu trúc Báo cáo 2 Sheet:
      * **Sheet 1 (`Bảng_Kê_Tổng_Hợp`)**: Danh sách tổng hợp toàn bộ hóa đơn với 19 cột nghiệp vụ chi tiết.
      * **Sheet 2 (`Chi_Tiết_Theo_Nhà_Cung_Cấp`)**: Phân nhóm (Group) theo từng Nhà Cung Cấp và phân rã chi tiết từng dòng mặt hàng, đơn giá, thuế suất, thành tiền và dòng Subtotal cho từng NCC.
    - Cập nhật bộ luật thẩm định chuẩn **Thông tư 91/2026/TT-BTC** và **Nghị định 123/2020/NĐ-CP**.

---

#### 🔹 GIAI ĐOẠN 3: Thẩm định Tự động, Cố định Định dạng Báo cáo & Hỗ trợ RAR
* **Yêu cầu 8**: *"Mọi quy trình thẩm định tự động đều được phải căn cứ theo thông tư mới nhất, không cần thiết phải show ra các bước so sánh hay làm gì đối với hóa đơn. 2 hóa đơn này đều đã được ký số, có chữ ký của nhà cung cấp và có mã của cơ quan thuế, tại sao lại coi là hóa đơn không hợp lệ/ cần kiểm tra? Tìm và xác định lại nguyên nhân. Đọc thêm quy tắc hợp lý hợp lệ đối với hóa đơn. Khi trình bày báo cáo thì không được sử dụng gộp ô, merge & center hãy sử dụng center across selection cho các trường hợp muốn trình bày nội dung tiêu đề cho cả bảng. Hãy cố định dòng cột với tiêu đề ở bảng kê tổng hợp và chi tiết đều là cột D5. Sử dụng font chữ Times New Roman cho toàn bộ bảng báo cáo. Dòng hóa đơn nghi ngờ không hợp lý hợp lệ hãy làm nổi bật lên với màu sắc. Thêm dòng tra cứu hóa đơn địa chỉ như tại website: ... và mã số tra cứu với từng dòng hóa đơn bên sheet tổng hợp."*
  * *Xử lý*:
    - Loại bỏ hiển thị các bước giải thích so sánh thừa trên giao diện.
    - Cập nhật quy tắc thuế: Cho phép chi nhánh MST 13 số (`3702653397-002` của TCS), chấp nhận thuế suất 0% cho quan trắc môi trường và an ninh bảo vệ theo hợp đồng/xuất khẩu/chế xuất.
    - **Triệt tiêu toàn bộ `merge_cells`**: Áp dụng `Alignment(horizontal='centerContinuous')` cho tất cả tiêu đề và dòng Tổng cộng.
    - **Cố định Freeze Panes**: `ws.freeze_panes = "D5"` trên cả 2 sheet.
    - **Font chữ đồng nhất**: `Times New Roman` cho 100% các ô.
    - Bổ sung Cột O (Mã CQT), Cột P (Website tra cứu), Cột Q (Mã số tra cứu).
* **Yêu cầu 9**: *"Đối với file nén đuôi .rar hiện tại có thể upload nhưng chưa thể tự động đọc, hãy bổ sung thêm khả năng nay cho chức năng xử lý"*
  * *Xử lý*: Tích hợp thư viện `rarfile` kết hợp với backend `UnRAR.exe` (WinRAR) và `7z.exe` (7-Zip) để tự động giải nén và bóc tách đệ quy toàn bộ file `.xml` và `.pdf` nằm trong tệp `.rar`.

---

#### 🔹 GIAI ĐOẠN 4: Chuẩn hóa Độ Rộng Cột, Làm Sạch Tên NCC & Trích xuất Ký hiệu/Tra cứu
* **Yêu cầu 10**: *"chú ý đối với độ rộng của các cột thì cần để vừa đủ thể hiện dữ liệu nằm bên trong cột. Phần tên nhà cung cấp vẫn bóc tách sai chỗ Madeown, phần cột N sheet tổng hợp, cần phải quét và xác định 'Đã ký số/ chưa ký số'. Cột O có mã và chưa có chưa có hãy ghi nhận rõ, cột Q mã số tra cứu hiện tại cũng đang có vấn đề. Phần đánh giá cũng chưa chính xác vì trong số hóa đơn kiểm tra đó có hóa đơn chưa ký số nên không thể kết luận đầy đủ tiêu chuẩn -> điều này hoàn toàn sai và ảnh hưởng tới kết quả của báo cáo."*
  * *Xử lý*:
    - Sửa lỗi thuật toán độ rộng cột: Bỏ qua ô A1 khi tính độ rộng $\rightarrow$ Cột A (STT) rộng chuẩn 8, các cột khác vừa khít dữ liệu.
    - Làm sạch tiền tố tên NCC: Cắt bỏ `(Supplier) :`, `(Seller) :`, `Đơn vị bán hàng(Supplier) :` $\rightarrow$ Tên sạch: `CÔNG TY TNHH MADEOWN VIỆT NAM`.
    - Cột N: Ghi rõ `Đã ký số` vs `Chưa ký số`.
    - Cột O: Ghi rõ `Có mã CQT: <mã>`, `Không có mã CQT (HĐ không mã)`, hoặc `Chưa có mã CQT`.
    - Cột Q: Ghi đúng mã số bí mật tra cứu, nếu không có ghi `Chưa có mã tra cứu`.
    - Cột R: Hóa đơn Madeown chưa ký số $\rightarrow$ Đánh giá ngay là `Không hợp lệ / Chưa ký số` và tô nền vàng `#FFF2CC` nổi bật.
* **Yêu cầu 11**: *"phần này không phải ký hiệu hóa đơn thì là gì? vì sao không bóc tách được thông tin này trên hóa đơn, hãy kiểm tra lại và lưu vào quy tắc xử lý thông tin"* (Đính kèm ảnh HĐ TCS có Ký hiệu `1C25TMT`)
  * *Xử lý*:
    - Tìm ra nguyên nhân: Regex trước đó bắt chữ `No` trong cụm `(Serial No.): 1C25TMT`.
    - Sửa regex nhận diện cấu trúc chuẩn quốc gia `[1-6][C|K|M][0-9]{2}[A-Z]{2,4}` $\rightarrow$ Bóc tách chính xác `1C25TMT`.
    - Lưu vĩnh viễn quy tắc vào Bộ nhớ dài hạn `mem0` (Mục 9).
* **Yêu cầu 12**: *"đây là website tra cứu và mã số tra cứu mà, hãy rà soát thông tin 1 cách thật cẩn thận lại trước khi làm lên báo cáo, ngăn cách trong báo cáo cũng nên sử dụng line màu xám nhẹ để phân biệt các ô và cột."* (Đính kèm ảnh HĐ Viettel có Website `https://vietteltelecom.vn/hoadondientu/` và Mã tra cứu `513719`)
  * *Xử lý*:
    - Hoàn thiện regex trích xuất Website và Mã số bí mật cho 12 file Viettel (`513719`, `600444`...).
    - Áp dụng đường viền nét mảnh màu xám nhẹ (`Border(color='BFBFBF')`) cho tất cả các ô trên cả 2 sheet.
* **Yêu cầu 13**: *"C:\Users\VSUN\Desktop\TEST_CHECK_INVOICE\1C26TYY_00000578_2601084657 có thể xác định được website tra cứu và mã tra cứu từ file có đuôi .xml như thế này không?"*
  * *Xử lý*:
    - Phân tích cấu trúc XML: Bóc tách `Id` trong `<DLHDon>` (`PKF7I2124GEM`) làm Mã tra cứu.
    - Nhận diện `<MSTTCGP>0101243150</MSTTCGP>` (MISA) $\rightarrow$ Tự động map sang `https://www.meinvoice.vn/tra-cuu/`.
* **Yêu cầu 14 & 15**: *"Thử truy cập vào website tra cứu và tra cứu thử các hóa đơn hợp lý, hợp lệ trên xem kết quả trả về như thế nào"* & *"không được trả lời lung tung, rõ ràng là bạn không tra được thông tin hóa đơn. Hãy tìm hiểu nguyên nhân và khắc phục lỗi này, không thể vì lý do không tra cứu được mà đưa ra kết luận bừa. Bạn căn cứ vào đâu để nói rằng hóa đơn của viettel có dấu chéo 'chưa thanh toán' không thể tra cứu được?? hãy tìm những dẫn chứng cụ thể hay thông báo của chính chủ viettel về vấn đề này."*
  * *Xử lý*:
    - Truy cập thực tế các cổng: BKAV eHoadon (Tìm thấy HĐ `1C25TMT-00000374-ĐPH`), MISA meInvoice (Tìm thấy HĐ `PKF7I2124GEM`).
    - Khảo sát sâu cơ chế Viettel Telecom: Làm rõ sự khác biệt giữa *Hóa đơn bán lẻ đơn lẻ* (tra cứu qua số HĐ + mã bí mật) và *Hóa đơn cước viễn thông định kỳ FTTH* (tra cứu qua số thuê bao + mã OTP gửi về chính chủ hoặc My Viettel). Phân tích cấu trúc lớp ảnh chìm `CHƯA THANH TOÁN` trên file PDF gốc.
* **Yêu cầu 16**: *"Tạm thời ẩn phần deploy đi. Tôi muốn chia sẻ cái này cho mọi người sử dụng thì cần làm như thế nào?"*
  * *Xử lý*:
    - Ẩn hoàn toàn nút Deploy và Menu hệ thống trên web.
    - Cung cấp link chia sẻ mạng LAN `http://10.102.36.146:8501`.
    - Tạo file khởi động 1-Click `CHAY_HE_THONG_HOA_DON.bat` ngoài Desktop.
* **Yêu cầu 17**: *"Chuyển toàn bộ dự án chiều hôm qua tôi đã nói chuyện với bạn lên project work để tạo thành 1 phiên trò chuyện riêng có tên là CHECK_INVOICE_PROJECT. Yêu cầu giữ nguyên toàn bộ câu chuyện, không lược bỏ đi yêu cầu hay thay đổi nào của tôi."*
  * *Xử lý*: Đóng gói toàn bộ source code, database, tests, và tài liệu lịch sử này vào thư mục dự án độc lập `CHECK_INVOICE_PROJECT`.

---

### 📂 DANH MỤC CÁC TỆP NGUỒN CỐT LÕI (CORE FILES)

| Tên Tệp | Đường Dẫn Tuyệt Đối | Chức Năng Chính |
| :--- | :--- | :--- |
| **`app.py`** | `C:\Users\VSUN\.gemini\antigravity\scratch\CHECK_INVOICE_PROJECT\app.py` | Giao diện Dashboard Web Streamlit đa tác vụ (Đã ẩn nút Deploy). |
| **`parser.py`** | `C:\Users\VSUN\.gemini\antigravity\scratch\CHECK_INVOICE_PROJECT\parser.py` | Bộ bóc tách thông minh đa định dạng (PDF, XML, ZIP, RAR, làm sạch tên NCC, bắt ký hiệu chuẩn, mã CQT, website & mã tra cứu). |
| **`validator.py`** | `C:\Users\VSUN\.gemini\antigravity\scratch\CHECK_INVOICE_PROJECT\validator.py` | Module thẩm định tự động theo chuẩn **TT 91/2026/TT-BTC** & **NĐ 123/2020/NĐ-CP**. |
| **`exporter.py`** | `C:\Users\VSUN\.gemini\antigravity\scratch\CHECK_INVOICE_PROJECT\exporter.py` | Trình tạo Báo cáo Excel 2 Sheet chuẩn Forensic (Times New Roman, Freeze Panes D5, Center Continuous, viền xám nhẹ `#BFBFBF`, tô màu cảnh báo `#FFF2CC`). |
| **`database.py`** | `C:\Users\VSUN\.gemini\antigravity\scratch\CHECK_INVOICE_PROJECT\database.py` | Quản lý Cơ sở dữ liệu SQLite cục bộ, tự động migrate cột và lưu trữ phân cấp Hóa đơn - Dòng hàng hóa. |
| **`CHAY_HE_THONG_HOA_DON.bat`** | `C:\Users\VSUN\Desktop\CHAY_HE_THONG_HOA_DON.bat` | Phím tắt khởi động 1-Click trên Desktop cho người dùng. |
