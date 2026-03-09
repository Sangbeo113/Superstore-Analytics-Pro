"""
Module  : cleaner.py
Vai trò : Làm sạch dữ liệu, xử lý ngoại lệ, chuẩn hóa cột,
          tạo đặc trưng Cohort và tính toán RFM base.
          
Output : data/cleaned/superstore_cleaned.csv
         data/cleaned/rfm_base.csv
"""

import logging
from datetime import timedelta
import pandas as pd
import config

logger = logging.getLogger("cleaner")


# ──────────────────────────────────────────────────────────────
def _validate_schema(df: pd.DataFrame, stage: str) -> None:
    """Kiểm tra schema sau mỗi bước — log cảnh báo nếu có vấn đề."""
    null_counts = df.isnull().sum()
    null_cols   = null_counts[null_counts > 0]
    if not null_cols.empty:
        logger.warning("[%s] Cột có null: %s", stage, null_cols.to_dict())
    logger.info("[%s] Shape: %s", stage, df.shape)


# ──────────────────────────────────────────────────────────────
def clean_basic_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hóa tên cột, xóa cột rác và lọc lỗi logic.

    1. Chuyển tên cột → chữ thường, khoảng trắng & dấu chấm → gạch dưới.
    2. Xóa các cột không có giá trị phân tích.
    3. Parse ngày tháng; lọc ship_date < order_date.
    4. Loại trùng lặp nghiệp vụ (Order ID + Product ID).
    5. Ép kiểu sales về float để tính toán chính xác.
    """
    logger.info("Bước 1 — Chuẩn hóa tên cột và xóa rác...")

    # Chuẩn hóa tên cột: chữ thường, thay khoảng trắng & dấu chấm bằng _
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(".", "_", regex=False)
    )

    # Xóa cột rác
    junk_cols = ["row_id", "记录数", "weeknum", "market2", "year"]
    df.drop(columns=[c for c in junk_cols if c in df.columns], inplace=True, errors="ignore")

    logger.info("Bước 2 — Parse ngày & lọc lỗi logic...")
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["ship_date"]  = pd.to_datetime(df["ship_date"])

    invalid = (df["ship_date"] < df["order_date"]).sum()
    if invalid > 0:
        logger.warning("Loại bỏ %d dòng Ship Date < Order Date.", invalid)
        df = df[df["ship_date"] >= df["order_date"]].copy()

    # Loại trùng lặp nghiệp vụ
    before = len(df)
    df = df.sort_values("order_date").drop_duplicates(
        subset=["order_id", "product_id"], keep="last"
    )
    removed = before - len(df)
    if removed > 0:
        logger.warning("Gộp/loại %d dòng trùng lặp (Order ID + Product ID).", removed)

    # Ép kiểu sales → float (ban đầu là int, cần float cho tính margin)
    df["sales"] = df["sales"].astype(float)

    _validate_schema(df, "clean_basic_anomalies")
    return df


# ──────────────────────────────────────────────────────────────
def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Xử lý giá trị bị thiếu theo từng cột."""
    logger.info("Bước 3 — Xử lý Missing Values...")

    if "postal_code" in df.columns:
        df["postal_code"] = df["postal_code"].fillna("00000")

    _validate_schema(df, "handle_missing")
    return df


# ──────────────────────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo các cột đặc trưng bổ sung phục vụ phân tích.

    Cột mới:
    - profit_margin   : tỷ suất lợi nhuận (profit / sales)
    - ship_delay_days : số ngày chờ giao hàng
    - order_year      : năm đặt hàng (dùng cho YoY)
    - order_quarter   : quý đặt hàng
    """
    logger.info("Bước 4 — Feature Engineering...")

    df["profit_margin"]   = df["profit"] / df["sales"].replace(0, float("nan"))
    df["ship_delay_days"] = (df["ship_date"] - df["order_date"]).dt.days
    df["order_year"]      = df["order_date"].dt.year
    df["order_quarter"]   = df["order_date"].dt.to_period("Q").astype(str)

    _validate_schema(df, "engineer_features")
    return df


# ──────────────────────────────────────────────────────────────
def create_cohort_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo các cột cần thiết cho Cohort Analysis.

    Cột mới:
    - order_month  : tháng đặt hàng (Period)
    - cohort_month : tháng đầu tiên khách hàng mua hàng
    - cohort_index : khoảng cách (tháng) từ cohort_month đến order_month
    """
    logger.info("Bước 5 — Tạo đặc trưng Cohort...")

    df["order_month"]  = df["order_date"].dt.to_period("M")
    df["cohort_month"] = (
        df.groupby("customer_id")["order_date"]
        .transform("min")
        .dt.to_period("M")
    )
    df["cohort_index"] = (df["order_month"] - df["cohort_month"]).apply(lambda x: x.n)

    _validate_schema(df, "create_cohort_features")
    return df


# ──────────────────────────────────────────────────────────────
def calculate_rfm_base(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính toán Recency, Frequency, Monetary cho từng khách hàng.

    - Recency  : số ngày kể từ lần mua cuối đến snapshot_date
    - Frequency: số đơn hàng duy nhất
    - Monetary : tổng doanh thu
    """
    logger.info("Bước 6 — Tính RFM base...")

    snapshot = df["order_date"].max() + timedelta(days=config.SNAPSHOT_DATE_OFFSET)

    rfm = df.groupby("customer_id").agg(
        recency   = ("order_date",  lambda x: (snapshot - x.max()).days),
        frequency = ("order_id",    "nunique"),
        monetary  = ("sales",       "sum"),
    ).reset_index()

    logger.info(
        "RFM: %d khách hàng  |  Recency trung bình %.0f ngày  |  "
        "Monetary trung bình %.0f $",
        len(rfm), rfm["recency"].mean(), rfm["monetary"].mean(),
    )
    return rfm


# ──────────────────────────────────────────────────────────────
def run_all() -> None:
    """Chạy toàn bộ pipeline làm sạch và lưu kết quả."""
    logger.info("=== BẮT ĐẦU LÀM SẠCH DỮ LIỆU ===")
    try:
        df = pd.read_csv(config.RAW_DATA_PATH, encoding="utf-8")
        logger.info("Đọc file thô: %d dòng, %d cột", *df.shape)

        df = clean_basic_anomalies(df)
        df = handle_missing(df)
        df = engineer_features(df)
        df = create_cohort_features(df)

        # Lưu cleaned data
        cleaned_path = config.CLEANED_DIR / "superstore_cleaned.csv"
        df.to_csv(cleaned_path, index=False)
        logger.info("Đã lưu cleaned data: %s  (%d dòng)", cleaned_path, len(df))

        # Lưu RFM base
        rfm = calculate_rfm_base(df)
        rfm_path = config.CLEANED_DIR / "rfm_base.csv"
        rfm.to_csv(rfm_path, index=False)
        logger.info("Đã lưu rfm_base: %s  (%d khách hàng)", rfm_path, len(rfm))

        logger.info("=== HOÀN TẤT LÀM SẠCH ===")

    except FileNotFoundError:
        logger.error("Không tìm thấy file: %s", config.RAW_DATA_PATH)
    except Exception as exc:
        logger.exception("Lỗi không mong đợi trong cleaner: %s", exc)


if __name__ == "__main__":
    run_all()