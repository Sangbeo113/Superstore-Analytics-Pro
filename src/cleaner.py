"""
Module: cleaner.py
Vai trò: Làm sạch dữ liệu, xử lý rác, xử lý lỗi logic nghiệp vụ, 
chuẩn hóa đặc trưng Cohort và tính toán giá trị gốc cho RFM.
"""

import pandas as pd
from datetime import timedelta
import config

def clean_basic_anomalies(df):
    """Chuẩn hóa cột, xóa rác và xử lý lỗi logic nghiệp vụ."""
    print("- Đang chuẩn hóa tên cột và xóa cột rác...")
    
    # Chuẩn hóa tên cột: Chuyển thành chữ thường, thay khoảng trắng và dấu chấm bằng dấu gạch dưới
    df.columns = df.columns.str.replace('.', '_', regex=False).str.replace(' ', '_').str.lower()
    
    # Xóa các cột rác không có giá trị phân tích
    junk_cols = ['row_id', '记录数', 'weeknum', 'market2']
    df.drop(columns=[c for c in junk_cols if c in df.columns], inplace=True, errors='ignore')
    
    print("- Đang chuẩn hóa định dạng thời gian và lọc lỗi logic...")
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['ship_date'] = pd.to_datetime(df['ship_date'])
    
    # Lọc bỏ các ngày logic sai (Ship Date < Order Date)
    invalid_dates = len(df[df['ship_date'] < df['order_date']])
    if invalid_dates > 0:
        print(f"  -> CẢNH BÁO: Đã loại bỏ {invalid_dates} dòng có lỗi logic (Ship Date < Order Date).")
        df = df[df['ship_date'] >= df['order_date']]
        
    # Xử lý trùng lặp nghiệp vụ (Order ID + Product ID)
    initial_len = len(df)
    df = df.sort_values('order_date').drop_duplicates(subset=['order_id', 'product_id'], keep='last')
    dup_count = initial_len - len(df)
    if dup_count > 0:
        print(f"  -> CẢNH BÁO: Đã gộp/loại bỏ {dup_count} dòng trùng lặp (cùng Order ID & Product ID).")
        
    return df

def handle_missing(df):
    """Xử lý dữ liệu bị thiếu."""
    print("- Đang xử lý Missing Values...")
    if 'postal_code' in df.columns:
        df['postal_code'] = df['postal_code'].fillna('00000')
    return df

def create_cohort_features(df):
    """Tạo các cột dữ liệu cần thiết cho Cohort Analysis."""
    print("- Đang tạo các đặc trưng Cohort...")
    df['order_month'] = df['order_date'].dt.to_period('M')
    df['cohort_month'] = df.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
    df['cohort_index'] = (df['order_month'] - df['cohort_month']).apply(lambda x: x.n)
    return df

def calculate_rfm_base(df):
    """Tính toán Recency, Frequency, Monetary gốc."""
    print("- Đang tính toán giá trị RFM gốc...")
    max_date = df['order_date'].max()
    snapshot_date = max_date + timedelta(days=config.SNAPSHOT_DATE_OFFSET)
    
    rfm_base = df.groupby('customer_id').agg({
        'order_date': lambda x: (snapshot_date - x.max()).days,
        'order_id': 'nunique',
        'sales': 'sum'
    }).reset_index()
    
    rfm_base.rename(columns={
        'order_date': 'recency',
        'order_id': 'frequency',
        'sales': 'monetary'
    }, inplace=True)
    
    return rfm_base

def run_all():
    print("=== BẮT ĐẦU QUÁ TRÌNH LÀM SẠCH VÀ CHUYỂN ĐỔI DỮ LIỆU ===")
    try:
        df = pd.read_csv(config.RAW_DATA_PATH, encoding='utf-8')
        
        # Chạy pipeline với các hàm đã cập nhật
        df = clean_basic_anomalies(df)
        df = handle_missing(df)
        df = create_cohort_features(df)
        
        # Lưu dữ liệu
        cleaned_path = config.CLEANED_DIR / "superstore_cleaned.csv"
        df.to_csv(cleaned_path, index=False)
        print(f"-> Đã lưu tập dữ liệu sạch tại: {cleaned_path}")
        
        rfm_base = calculate_rfm_base(df)
        rfm_base_path = config.CLEANED_DIR / "rfm_base.csv"
        rfm_base.to_csv(rfm_base_path, index=False)
        print(f"-> Đã lưu dữ liệu RFM gốc tại: {rfm_base_path}")
        
        print("=== HOÀN TẤT LÀM SẠCH DỮ LIỆU ===")
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file dữ liệu tại {config.RAW_DATA_PATH}.")

if __name__ == "__main__":
    run_all()