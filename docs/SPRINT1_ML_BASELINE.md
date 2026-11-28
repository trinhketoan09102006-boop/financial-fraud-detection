## Sprint 1 – Baseline Machine Learning

### 1. Mục tiêu

Xây dựng và đánh giá ba mô hình phân loại giao dịch gian lận gồm Logistic Regression, Random Forest và LightGBM trên bộ dữ liệu Sparkov, sử dụng các đặc trưng giao dịch cơ bản và chưa áp dụng phương pháp xử lý mất cân bằng.

### 2. Dữ liệu và tiền xử lý

Dữ liệu được chia theo thời gian thành 1.037.340 giao dịch train, 259.335 giao dịch validation và 555.719 giao dịch test. Trong Sprint 1, chỉ sử dụng train và validation, giữ nguyên test cho giai đoạn đánh giá cuối.

Bộ đặc trưng baseline gồm 7 biến số và 2 biến phân loại: `amt`, `hour`, `day_of_week`, `month`, `is_weekend`, `age_at_transaction`, `merchant_distance_km`, `merchant`, `category`.

Pipeline sử dụng SimpleImputer, StandardScaler và OneHotEncoder. Các phép biến đổi được fit trên train để hạn chế Data Leakage.

### 3. Kết quả thực nghiệm

| Mô hình | Average Precision | Thời gian huấn luyện |
|---|---:|---:|
| Logistic Regression | 0.240788 | 3,00 giây |
| Random Forest | 0.855569 | 179,27 giây |
| LightGBM | **0.880187** | **3,69 giây** |

Ba mô hình sử dụng chung seed 42, feature set `baseline_v1` và không áp dụng chiến lược cân bằng dữ liệu.

### 4. Nhận xét

LightGBM đạt Average Precision cao nhất trên validation (0,880187), đồng thời có thời gian huấn luyện thấp hơn đáng kể so với Random Forest.

Random Forest cũng đạt hiệu quả cao nhưng có chi phí huấn luyện lớn. Logistic Regression là mô hình baseline tuyến tính đơn giản, có kết quả thấp hơn hai mô hình cây.

Các kết quả đã được đối chiếu với prediction CSV theo `trans_num`. Cả ba mô hình có đủ 259.335 dự đoán validation, không trùng ID và Average Precision tính lại khớp `metrics.csv`.

### 5. Giới hạn và hướng phát triển

Kết quả mới được đánh giá trên tập validation của Sparkov, chưa đánh giá trên tập test khóa. Các thử nghiệm chưa kết hợp đặc trưng hành vi khách hàng và chưa áp dụng phương pháp xử lý mất cân bằng.

Trong Sprint 2, nhóm sẽ so sánh tác động của đặc trưng hành vi và các chiến lược xử lý mất cân bằng, chọn ngưỡng trên validation và đánh giá M1–M4 trên test.

Do Sparkov là dữ liệu mô phỏng, kết quả không được xem là bằng chứng hiệu quả tương đương trên giao dịch ngân hàng thực tế.