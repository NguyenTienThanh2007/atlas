# Vietnamese UI glossary

The fixed Vietnamese terms used in the interface (WS2, P2-4.12). The source of truth is
`frontend/src/i18n/vi.ts`, and `en.ts` must contain the same keys (a test enforces this). Metric
names come from the versioned metric dictionary (`name_vi`) through the API and are not repeated
here.

**Status: needs review by a native speaker** (owner or delegate) before P2-4.12 can be marked
PASS. Proposed changes go into `vi.ts`, then this table.

## Statements and periods

| Concept | Tiếng Việt | English |
| --- | --- | --- |
| Income statement | Báo cáo kết quả kinh doanh | Income statement |
| Balance sheet | Bảng cân đối kế toán | Balance sheet |
| Cash flow statement | Báo cáo lưu chuyển tiền tệ | Cash flow statement |
| Consolidated / separate | Hợp nhất / Riêng | Consolidated / Separate |
| Fiscal year 2025 | Năm tài chính 2025 | FY2025 |
| Quarter 2 of 2025 | Quý 2/2025 | FY2025 Q2 |
| Restated (revision n) | đã điều chỉnh (lần n) | restated (revision n) |
| Financial statements (section) | Báo cáo tài chính | Financial statements |

## Listings and securities

| Concept | Tiếng Việt | English |
| --- | --- | --- |
| Ticker | Mã CK | Ticker |
| Exchange | Sàn | Exchange |
| Pending / listed / suspended / delisted | Chờ niêm yết / Đang niêm yết / Tạm ngừng giao dịch / Đã hủy niêm yết | Pending listing / Listed / Trading suspended / Delisted |
| Common / preferred stock | Cổ phiếu phổ thông / Cổ phiếu ưu đãi | Common / Preferred stock |
| Fund certificate, bond, covered warrant | Chứng chỉ quỹ, Trái phiếu, Chứng quyền có bảo đảm | Fund certificate, Bond, Covered warrant |
| Tax code | Mã số thuế | Tax code |

## Verification and sources

| Concept | Tiếng Việt | English |
| --- | --- | --- |
| unverified / verified | Chưa xác minh / Đã xác minh | Unverified / Verified |
| disputed / rejected / superseded | Đang xem xét lại / Bị loại / Đã được thay thế | Under review / Rejected / Superseded |
| sample (fictional) | Dữ liệu mẫu | Sample data |
| Sources (section) | Nguồn tài liệu | Sources |
| Retrieved (date) | truy xuất (ngày) | retrieved (date) |
| Usage rights: unknown / personal only / licensed / official disclosure / restricted | quyền sử dụng: Chưa rõ / Chỉ dùng cá nhân / Có giấy phép / Công bố chính thức / Hạn chế | usage rights: Unknown / Personal use only / Licensed / Official public disclosure / Restricted |

## Units and number format

| Concept | Tiếng Việt | English |
| --- | --- | --- |
| Currency amount | 1.234.567,89 đồng | 1,234,567.89 VND |
| Per share | 4.321 đồng/cổ phiếu | 4,321 VND/share |
| Share count | cổ phiếu | shares |
| Date | 28/06/2024 | 2024-06-28 |

Numbers are formatted from the exact decimal string, never through floating point. Timestamps
are shown in Vietnam time (UTC+7).

## Calculated ratios (WS4-2)

New terms, added for the same native-speaker review. "Kiểm chứng" here follows the owner-approved
label text (WS4-D7); the verification statuses above use "xác minh". The review should pick one.

| Concept | Tiếng Việt | English |
| --- | --- | --- |
| Calculated ratios (section) | Chỉ số tính toán (do ATLAS tính) | Calculated ratios (computed by ATLAS) |
| ROE | Tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE) | Return on equity (ROE) |
| ROA | Tỷ suất lợi nhuận trên tổng tài sản (ROA) | Return on assets (ROA) |
| How it's calculated | Cách tính | How it's calculated |
| Numerator / closing / opening | Tử số / Cuối kỳ / Đầu kỳ | Numerator / Closing / Opening |
| Average denominator | Bình quân mẫu số | Average denominator |
| Calculated from verified / unverified figures | Tính từ số liệu đã kiểm chứng / chưa kiểm chứng | Calculated from verified / unverified figures |
| Not calculable / not meaningful | Không tính được / Không có ý nghĩa | Not calculable / Not meaningful |
| Opening balance | Số dư đầu kỳ | Opening balance |
| Sample and real data mixed (audit AU-3) | Không tính được: dữ liệu mẫu và dữ liệu thật bị trộn lẫn | Not calculable: sample and real data are mixed |
| Page range (audit AU-5) | Đang hiển thị 1–20 / 85 | Showing 1–20 of 85 |
| Past the last page | Trang 9 không có mục nào (tổng cộng 85 mục) | Page 9 has no items (85 in total) |

## Navigation

Khám phá (Discover) · Ngành (Sectors) · Doanh nghiệp (Companies) · Danh sách theo dõi
(Watchlist) · Chọn ngôn ngữ (Choose language).
