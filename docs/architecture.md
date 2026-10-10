Kiến trúc: Lớp phân tích độc lập (Independent Analytics Layer)
FlowSight được thiết kế như một lớp phần mềm phân tích độc lập, không can thiệp vào hệ thống vận hành hiện có (F-IoT, MES, DN7). Luồng dữ liệu đi một chiều: các hệ thống nguồn xuất dữ liệu qua API/Views hoặc file export → FlowSight ingest, liên kết và phân tích → kết quả hiển thị trên dashboard 12D.

Cách tiếp cận này có 3 lợi ích:

Không rủi ro vận hành: chỉ đọc dữ liệu, không ghi ngược vào hệ thống sản xuất.
Triển khai nhanh: chạy được on-premise hoặc trên WAN nội bộ, không đòi hỏi thay đổi hạ tầng.
Giải thích được: mọi kết luận đều kèm Evidence Card ghi rõ công thức, input và chuỗi bằng chứng — đúng ưu tiên mà DENSO đã xác nhận: khả năng giải thích chuỗi bằng chứng kỹ thuật và độ chính xác dự báo.