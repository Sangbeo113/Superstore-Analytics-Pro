# Dự án Tối ưu hóa hiệu quả kinh doanh Global Superstore 🛒

Đây là kho lưu trữ mã nguồn cho Đồ án tốt nghiệp Phân tích Dữ liệu Bán lẻ (Retail Data Analytics) dựa trên tập dữ liệu Global Superstore. Dự án tập trung vào việc áp dụng các kỹ thuật làm sạch dữ liệu, xây dựng Star Schema, phân tích RFM Segmentation và Cohort Analysis để tối ưu hóa chiến lược giữ chân khách hàng.

## Cấu trúc thư mục dự án 

```text
Superstore-Analytics-Pro/
│
├── data/
│   ├── raw/                 # Dữ liệu gốc (Global_Superstore.csv)
│   ├── cleaned/             # Dữ liệu sau khi làm sạch
│   ├── dim_fact/            # Dữ liệu mô hình Star Schema (dim_time, fact_sales...)
│   └── aggregates/          # Dữ liệu tổng hợp cho Tableau (agg_rfm_segments...)
│
├── src/                     # Source code chính của dự án
│   ├── config.py            # Cấu hình đường dẫn, tham số RFM, ngưỡng xử lý
│   ├── eda.py               # Module phân tích khám phá dữ liệu (EDA)
│   ├── cleaner.py           # Module làm sạch, xử lý missing và tạo đặc trưng
│   ├── Splitter.py          # Module tách dữ liệu thành Star Schema
│   └── Aggregate.py         # Module tạo các Data Marts (Cohort, RFM, Pareto)
│
├── notebooks/               # Thư mục chứa các bản nháp Jupyter Notebook
│
├── dashboards/              # Thư mục chứa file Tableau và tài nguyên BI
│   └── Final_Superstore_Story.twbx 
│
├── docs/                    # Tài liệu, báo cáo đồ án (Word, PDF)
│
├── README.md                # Tài liệu hướng dẫn (File này)
└── requirements.txt         # Các thư viện Python: pandas, numpy, seaborn...