"""
Module: splitter.py
Vai trò: Chuyển đổi tập dữ liệu làm sạch thành Mô hình dữ liệu hình sao (Star Schema).
Bao gồm: dim_customer, dim_product, dim_location, dim_time và fact_sales.
"""

import pandas as pd
import config

def create_dim_customer(df):
    """Tạo bảng Dimension Khách hàng."""
    dim_customer = df[['customer_id', 'customer_name', 'segment']].drop_duplicates()
    dim_customer.to_csv(config.DIM_FACT_DIR / "dim_customer.csv", index=False)
    print(f"Đã tạo dim_customer: {len(dim_customer)} bản ghi.")
    return dim_customer

def create_dim_product(df):
    """Tạo bảng Dimension Sản phẩm."""
    # Lưu ý: 'Sub-Category' chuyển thành 'sub-category' do không thay thế dấu gạch ngang ở Cleaner
    dim_product = df[['product_id', 'category', 'sub-category', 'product_name']].drop_duplicates()
    dim_product.to_csv(config.DIM_FACT_DIR / "dim_product.csv", index=False)
    print(f"Đã tạo dim_product: {len(dim_product)} bản ghi.")
    return dim_product

def create_dim_location(df):
    """Tạo bảng Dimension Vị trí địa lý."""
    # Tạo location_id duy nhất từ sự kết hợp của Country, State và City
    df['location_id'] = df['country'] + "_" + df['state'] + "_" + df['city']
    df['location_id'] = df['location_id'].str.replace(" ", "")
    
    dim_location = df[['location_id', 'market', 'region', 'country', 'state', 'city']].drop_duplicates()
    dim_location.to_csv(config.DIM_FACT_DIR / "dim_location.csv", index=False)
    print(f"Đã tạo dim_location: {len(dim_location)} bản ghi.")
    return df, dim_location

def create_dim_time(df):
    """Tạo bảng Dimension Thời gian."""
    dim_time = pd.DataFrame({'date': df['order_date'].drop_duplicates()})
    dim_time['year'] = dim_time['date'].dt.year
    dim_time['quarter'] = dim_time['date'].dt.quarter
    dim_time['month'] = dim_time['date'].dt.month
    dim_time['day'] = dim_time['date'].dt.day
    dim_time['weekday'] = dim_time['date'].dt.day_name()
    
    dim_time.to_csv(config.DIM_FACT_DIR / "dim_time.csv", index=False)
    print(f"Đã tạo dim_time: {len(dim_time)} bản ghi.")
    return dim_time

def create_fact_sales(df):
    """Tạo bảng Fact chi tiết Giao dịch."""
    columns_for_fact = [
        'order_id', 'customer_id', 'product_id', 'location_id', 
        'order_date', 'sales', 'quantity', 'discount', 'profit', 'shipping_cost'
    ]
    fact_cols = [col for col in columns_for_fact if col in df.columns]
    
    fact_sales = df[fact_cols]
    fact_sales.to_csv(config.DIM_FACT_DIR / "fact_sales.csv", index=False)
    print(f"Đã tạo fact_sales: {len(fact_sales)} bản ghi.")
    return fact_sales

def run_all():
    print("=== BẮT ĐẦU XÂY DỰNG STAR SCHEMA ===")
    # Đã đổi 'Order Date' thành 'order_date'
    df = pd.read_csv(config.CLEANED_DIR / "superstore_cleaned.csv", parse_dates=['order_date'])
    
    create_dim_customer(df)
    create_dim_product(df)
    df, dim_loc = create_dim_location(df) 
    create_dim_time(df)
    create_fact_sales(df)
    
    print("=== HOÀN TẤT MÔ HÌNH DỮ LIỆU ===")

if __name__ == "__main__":
    run_all()