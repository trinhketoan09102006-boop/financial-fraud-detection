# Open-source feature review — T01

Nguồn được đọc là trang README/tài liệu và issue công khai, không phải audit source code.

- [Featuretools issue về cutoff time](https://github.com/alteryx/featuretools/issues/1692): ví dụ phân biệt giao dịch trước và sau cutoff, liên quan cửa sổ F01–F03 và lịch sử F04–F10. Việc đặt cutoff phải loại cả anchor và sự kiện cùng thời điểm; không thể mặc định mọi API thư viện đáp ứng chính xác quy tắc này.
- [NVTabular README](https://github.com/NVIDIA-Merlin/NVTabular): thư viện xử lý dữ liệu bảng và hỗ trợ thống nhất transform giữa training và inference, liên quan việc triển khai các thống kê và categorical. Tài liệu README không chứng minh API của thư viện áp dụng temporal isolation theo contract dự án này.
- [Transactional ML feature pipeline README](https://github.com/NiharikaKomaragiri/transactional-ml-feature-pipeline): mô tả point-in-time correctness và tách target khỏi feature; nguyên tắc áp dụng cho tất cả F01–F10. Chưa audit mã nguồn hoặc xác minh hiệu năng dự án đó.

Kỹ thuật phù hợp: hàng đợi cửa sổ, thống kê online, trạng thái riêng theo thẻ và cập nhật theo nhóm timestamp. Các aggregate toàn bộ dữ liệu, lấy target, join tương lai hoặc cập nhật tuần tự các dòng cùng timestamp đều có nguy cơ leakage.

Ứng viên **chỉ đề xuất cho Sprint 2**, chưa triển khai: `amt_zscore`, `amt_sum_24h`, `unique_merchants_24h`, các đặc trưng thời gian bổ sung và đặc trưng địa lý sau khi xác minh ý nghĩa tọa độ. V1 giữ đúng 10 feature đã phê duyệt để duy trì contract, kiểm thử và so sánh nhất quán.
