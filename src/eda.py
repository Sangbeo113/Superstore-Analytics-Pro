"""
Module  : eda.py
Vai trò : Khám phá, kiểm tra chất lượng và nhận diện các vấn đề
          của tập dữ liệu Global Superstore trước khi làm sạch.
"""

import logging
import pandas as pd
import config

logger = logging.getLogger("eda")


# ──────────────────────────────────────────────
def check_basic_info(df: pd.DataFrame) -> None:
    """In thông tin cơ bản: kích thước và kiểu dữ liệu."""
    logger.info("=== 1. THÔNG TIN CƠ BẢN ===")
    logger.info("Số bản ghi : %d  |  Số cột : %d", df.shape[0], df.shape[1])
    logger.info("Kiểu dữ liệu:\n%s", df.dtypes.to_string())


# ──────────────────────────────────────────────
def check_missing_and_duplicates(df: pd.DataFrame) -> None:
    """Kiểm tra giá trị thiếu và dữ liệu trùng lặp."""
    logger.info("=== 2. MISSING VALUES & DUPLICATES ===")

    # Missing values
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        logger.info("Không có cột nào bị thiếu dữ liệu.")
    else:
        logger.warning("Cột thiếu dữ liệu:\n%s", missing.to_string())

    # Duplicates — dữ liệu raw dùng 'Row.ID' (có dấu chấm)
    id_col = "Row.ID" if "Row.ID" in df.columns else None
    if id_col:
        dups = df.duplicated(subset=[id_col]).sum()
        logger.info("Dòng trùng lặp theo %s : %d", id_col, dups)
    else:
        dups = df.duplicated().sum()
        logger.info("Dòng trùng lặp hoàn toàn : %d", dups)


# ──────────────────────────────────────────────
def analyze_statistics(df: pd.DataFrame) -> None:
    """Thống kê mô tả các biến số quan trọng."""
    logger.info("=== 3. THỐNG KÊ MÔ TẢ ===")

    # Dữ liệu raw dùng tên gốc có dấu chấm ('Shipping.Cost')
    num_cols = ["Sales", "Quantity", "Discount", "Profit", "Shipping.Cost"]
    existing = [c for c in num_cols if c in df.columns]
    logger.info("Thống kê Numeric:\n%s", df[existing].describe().round(2).to_string())

    if "Profit" in df.columns:
        loss = (df["Profit"] < 0).sum()
        logger.info(
            "Đơn hàng lỗ (Profit < 0) : %d  (%.2f %%)",
            loss, loss / len(df) * 100,
        )

    if "Discount" in df.columns:
        high_disc = (df["Discount"] > config.MAX_DISCOUNT_THRESHOLD).sum()
        logger.warning(
            "Đơn hàng giảm giá > %.0f %% : %d  — nguy cơ thua lỗ cao",
            config.MAX_DISCOUNT_THRESHOLD * 100, high_disc,
        )


# ──────────────────────────────────────────────
def analyze_business_overview(df: pd.DataFrame) -> None:
    """Tổng quan phân bổ theo Market, Segment, Category."""
    logger.info("=== 4. PHÂN BỔ NGHIỆP VỤ ===")

    for col in ["Market", "Segment", "Category", "Sub.Category"]:
        if col in df.columns:
            logger.info("Phân bổ %s:\n%s", col, df[col].value_counts().to_string())


# ──────────────────────────────────────────────
def run_all() -> None:
    """Thực thi toàn bộ luồng EDA."""
    logger.info("BẮT ĐẦU EDA...")
    try:
        df = pd.read_csv(config.RAW_DATA_PATH, encoding="utf-8")
        check_basic_info(df)
        check_missing_and_duplicates(df)
        analyze_statistics(df)
        analyze_business_overview(df)
        logger.info("HOÀN TẤT EDA — sẵn sàng cho bước làm sạch.")
    except FileNotFoundError:
        logger.error("Không tìm thấy file: %s", config.RAW_DATA_PATH)


if __name__ == "__main__":
    run_all()