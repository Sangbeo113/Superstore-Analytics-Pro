"""
Module: eda.py
Vai trò: Khám phá, kiểm tra chất lượng và nhận diện các vấn đề của tập dữ liệu Global Superstore.
"""

import pandas as pd
import config

def check_basic_info(df):
    """Kiểm tra thông tin cơ bản: kích thước, kiểu dữ liệu."""
    print("\n" + "="*40)
    print("1. THÔNG TIN CƠ BẢN (BASIC INFO)")
    print("="*40)
    print(f"Số lượng bản ghi (Rows): {df.shape[0]}")
    print(f"Số lượng cột (Columns): {df.shape[1]}")
    print("\nKiểu dữ liệu của các cột:")
    print(df.dtypes)

def check_missing_and_duplicates(df):
    """Kiểm tra giá trị thiếu (Null) và dữ liệu trùng lặp."""
    print("\n" + "="*40)
    print("2. MISSING VALUES & DUPLICATES")
    print("="*40)
    
    # Kiểm tra Missing Values
    missing_data = df.isnull().sum()
    missing_cols = missing_data[missing_data > 0]
    if not missing_cols.empty:
        print("Các cột có giá trị thiếu:")
        print(missing_cols)
    else:
        print("Tuyệt vời! Không có cột nào bị thiếu dữ liệu.")

    # Kiểm tra Duplicates
    if 'Row ID' in df.columns:
        duplicates = df.duplicated(subset=['Row ID']).sum()
        print(f"\nSố dòng trùng lặp theo Row ID: {duplicates}")
    else:
        duplicates = df.duplicated().sum()
        print(f"\nSố dòng trùng lặp hoàn toàn: {duplicates}")

def analyze_statistics(df):
    """Thống kê mô tả các biến số Numeric và Categorical quan trọng."""
    print("\n" + "="*40)
    print("3. THỐNG KÊ MÔ TẢ (STATISTICS)")
    print("="*40)
    
    print("Thống kê các biến số (Numeric):")
    # Lấy các cột số thực/nguyên, bỏ qua mã định danh như Row ID hay Postal Code
    num_cols = ['Sales', 'Quantity', 'Discount', 'Profit', 'Shipping Cost']
    existing_num_cols = [col for col in num_cols if col in df.columns]
    print(df[existing_num_cols].describe().round(2))
    
    print("\nPhân bổ lợi nhuận (Profit < 0):")
    if 'Profit' in df.columns:
        loss_orders = len(df[df['Profit'] < 0])
        print(f"Số lượng đơn hàng bị lỗ: {loss_orders} đơn ({loss_orders/len(df):.2%})")

def run_all():
    """Hàm thực thi toàn bộ luồng EDA."""
    print("BẮT ĐẦU QUÁ TRÌNH KHÁM PHÁ DỮ LIỆU (EDA)...")
    try:
        # Đọc dữ liệu từ file gốc
        df = pd.read_csv(config.RAW_DATA_PATH, encoding='utf-8')
        check_basic_info(df)
        check_missing_and_duplicates(df)
        analyze_statistics(df)
        print("\nHOÀN TẤT EDA! CHUẨN BỊ CHO BƯỚC LÀM SẠCH.")
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file dữ liệu tại {config.RAW_DATA_PATH}. Vui lòng kiểm tra lại.")

if __name__ == "__main__":
    run_all()