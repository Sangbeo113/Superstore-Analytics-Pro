```
Dự án Tối ưu hóa hiệu quả kinh doanh Global Superstore

Graduation_Project_Superstore/
│
├── data/
│   ├── raw/                 # Dữ liệu gốc (superstore.csv)
│   ├── processed/           # Dữ liệu sạch (superstore_final_v1.csv)
│
├── notebooks/
│   ├── 01_data_checker.ipynb    # Kiểm tra lỗi, thống kê mô tả
│   ├── 02_data_cleaner.ipynb    # Làm sạch & tạo cột mới (RFM, Cohort...)
│   └── 03_data_visualizer.ipynb # Phân tích nháp tìm Insight
│
├── dashboards/                  # SẢN PHẨM CUỐI CÙNG
│   ├── assets/                  # Tài nguyên thiết kế (Logo, màu sắc, background)
│   │   ├── color_palette.png
│   │   ├── logo_company.png
│   │   └── background_layout.png
│   ├── drafts/                  # Các bản Tableau nháp
│   └── Final_Superstore_Story.twbx # File nộp chính thức
│
├── docs/                        # TÀI LIỆU BÁO CÁO
│   ├── references/              # Các bài báo, nghiên cứu tham khảo
│   └── Report_Final_Thesis.pdf  # Bản báo cáo tốt nghiệp bản cứng
│
├── .gitignore                   # File cấu hình git bỏ qua file rác
├── README.md                    # Hướng dẫn đọc dự án
└── requirements.txt             # Các thư viện cần cài đặt