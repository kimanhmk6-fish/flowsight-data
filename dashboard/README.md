# FlowSight — Lot-Level Incident Impact & Cause Intelligence

Mở `index.html` trực tiếp (không cần server, không cần mạng). Dữ liệu: repo `flowsight-data` đã đóng gói trong `data/bundle.js`.

## Cấu trúc
- `index.html` — khung giao diện, bộ lọc toàn cục
- `css/styles.css` — giao diện nền sáng, responsive desktop/tablet
- `data/bundle.js` — CSV/JSON của repo (tạo bằng `python tools/build_bundle.py <repo>/data`)
- `js/core/` — `csv.js` (đọc/ghi CSV), `store.js` (dữ liệu, cấu hình, workflow), `schema.js` (lược đồ, ánh xạ cột, kiểm tra chất lượng), `engine.js` (công thức tác động, đồ thị lan truyền, bằng chứng nguyên nhân), `ui.js` (KPI, bảng, biểu đồ SVG, modal), `router.js`
- `js/pages/` — mỗi chức năng một tệp: command (FR-01), incidents (FR-02), impact (FR-03), propagation (FR-04), genealogy (FR-05), import (FR-06), health (FR-07), rootcause (FR-08), priority (FR-09), validation (FR-10), reports (FR-11), architecture (FR-12 + 9 ca kiểm thử), guide (hướng dẫn), cause_dist (phân bổ nguyên nhân), materials (danh mục & vật tư)

## Nguyên tắc
Số liệu luôn gắn nhãn Đã xác nhận / Suy luận / Mô phỏng / Chưa đủ dữ liệu; ngưỡng rủi ro và trọng số ưu tiên là **demo, chưa xác nhận với DENSO**.
