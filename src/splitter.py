"""
Module  : splitter.py
Vai trò : Chuyển đổi cleaned data thành Star Schema (mô hình dữ liệu hình sao).

Output  : data/dim_fact/
    - dim_customer.csv
    - dim_product.csv
    - dim_location.csv
    - dim_time.csv
    - fact_sales.csv
"""

import logging

import pandas as pd
import config

logger = logging.getLogger("splitter")


# ──────────────────────────────────────────────────────────────
def create_dim_customer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo bảng Dimension Khách hàng.

    Cột: customer_id | customer_name | segment
    """
    dim = df[["customer_id", "customer_name", "segment"]].drop_duplicates()
    out = config.DIM_FACT_DIR / "dim_customer.csv"
    dim.to_csv(out, index=False)
    logger.info("dim_customer : %d bản ghi  →  %s", len(dim), out)
    return dim


# ──────────────────────────────────────────────────────────────
def create_dim_product(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo bảng Dimension Sản phẩm.

    Cột: product_id | category | sub_category | product_name
    Lưu ý: tên cột là 'sub_category' (gạch dưới) sau khi cleaner chuẩn hóa.
    """
    dim = df[["product_id", "category", "sub_category", "product_name"]].drop_duplicates()
    out = config.DIM_FACT_DIR / "dim_product.csv"
    dim.to_csv(out, index=False)
    logger.info("dim_product  : %d bản ghi  →  %s", len(dim), out)
    return dim


# ──────────────────────────────────────────────────────────────
def create_dim_location(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Tạo bảng Dimension Vị trí địa lý.

    Tạo khóa tổng hợp location_id = Country_State_City (bỏ khoảng trắng).
    Cột: location_id | market | region | country | state | city
    """
    df = df.copy()
    df["location_id"] = (
        df["country"].str.replace(" ", "", regex=False)
        + "_"
        + df["state"].str.replace(" ", "", regex=False)
        + "_"
        + df["city"].str.replace(" ", "", regex=False)
    )

    dim = df[["location_id", "market", "region", "country", "state", "city"]].drop_duplicates()
    out = config.DIM_FACT_DIR / "dim_location.csv"
    dim.to_csv(out, index=False)
    logger.info("dim_location : %d bản ghi  →  %s", len(dim), out)
    return df, dim


# ──────────────────────────────────────────────────────────────
def create_dim_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo bảng Dimension Thời gian từ order_date.

    Cột: date | year | quarter | month | month_name | day | weekday | is_weekend
    """
    dates = df["order_date"].drop_duplicates().sort_values()
    dim   = pd.DataFrame({"date": dates})

    dim["year"]       = dim["date"].dt.year
    dim["quarter"]    = dim["date"].dt.quarter
    dim["month"]      = dim["date"].dt.month
    dim["month_name"] = dim["date"].dt.strftime("%B")
    dim["day"]        = dim["date"].dt.day
    dim["weekday"]    = dim["date"].dt.day_name()
    dim["is_weekend"] = dim["date"].dt.dayofweek >= 5

    out = config.DIM_FACT_DIR / "dim_time.csv"
    dim.to_csv(out, index=False)
    logger.info("dim_time     : %d bản ghi  →  %s", len(dim), out)
    return dim


# ──────────────────────────────────────────────────────────────
def create_fact_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo bảng Fact Giao dịch.

    Cột chính: order_id | customer_id | product_id | location_id |
               order_date | ship_date | ship_mode | order_priority |
               sales | quantity | discount | profit | shipping_cost |
               profit_margin | ship_delay_days
    """
    fact_cols = [
        "order_id", "customer_id", "product_id", "location_id",
        "order_date", "ship_date", "ship_mode", "order_priority",
        "sales", "quantity", "discount", "profit", "shipping_cost",
        "profit_margin", "ship_delay_days",
    ]
    # Chỉ lấy cột thực sự tồn tại (an toàn)
    existing = [c for c in fact_cols if c in df.columns]
    fact = df[existing].copy()

    out = config.DIM_FACT_DIR / "fact_sales.csv"
    fact.to_csv(out, index=False)
    logger.info("fact_sales   : %d bản ghi  →  %s", len(fact), out)
    return fact


# ──────────────────────────────────────────────────────────────
def run_all() -> None:
    """Chạy toàn bộ pipeline xây dựng Star Schema."""
    logger.info("=== BẮT ĐẦU XÂY DỰNG STAR SCHEMA ===")
    try:
        df = pd.read_csv(
            config.CLEANED_DIR / "superstore_cleaned.csv",
            parse_dates=["order_date", "ship_date"],
        )
        logger.info("Đọc cleaned data: %d dòng", len(df))

        create_dim_customer(df)
        create_dim_product(df)
        df, _ = create_dim_location(df)   # df được bổ sung cột location_id
        create_dim_time(df)
        create_fact_sales(df)

        logger.info("=== HOÀN TẤT STAR SCHEMA ===")

    except FileNotFoundError:
        logger.error(
            "Không tìm thấy cleaned data. Hãy chạy cleaner.py trước."
        )
    except Exception as exc:
        logger.exception("Lỗi trong splitter: %s", exc)


if __name__ == "__main__":
    run_all()