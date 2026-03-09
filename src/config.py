"""
Module  : config.py
Vai trò : Trung tâm cấu hình toàn bộ dự án — đường dẫn, tham số RFM,
          ngưỡng phát hiện ngoại lệ và các hằng số nghiệp vụ.
"""

import logging
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# 1. LOGGING — dùng chung cho toàn bộ pipeline
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("config")


# ══════════════════════════════════════════════════════════════
# 2. ĐƯỜNG DẪN (PATHS)
# ══════════════════════════════════════════════════════════════
BASE_DIR      = Path(__file__).resolve().parent.parent

DATA_DIR      = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "superstore.csv"

CLEANED_DIR   = DATA_DIR / "cleaned"
DIM_FACT_DIR  = DATA_DIR / "dim_fact"
AGG_DIR       = DATA_DIR / "aggregates"

# Tạo thư mục nếu chưa tồn tại
for _folder in [RAW_DATA_PATH.parent, CLEANED_DIR, DIM_FACT_DIR, AGG_DIR]:
    _folder.mkdir(parents=True, exist_ok=True)

# Cảnh báo sớm nếu thiếu file — tránh crash giữa pipeline
if not RAW_DATA_PATH.exists():
    logger.warning(
        "Không tìm thấy file dữ liệu tại: %s  —  "
        "Hãy đặt superstore.csv vào data/raw/ trước khi chạy.",
        RAW_DATA_PATH,
    )


# ══════════════════════════════════════════════════════════════
# 3. THAM SỐ THỜI GIAN
# ══════════════════════════════════════════════════════════════
START_DATE = "2011-01-01"
END_DATE   = "2014-12-31"


# ══════════════════════════════════════════════════════════════
# 4. THAM SỐ RFM & COHORT
# ══════════════════════════════════════════════════════════════
SNAPSHOT_DATE_OFFSET = 1   # bù +1 ngày để tránh Recency = 0
RFM_BINS             = 5   # số nhóm qcut (điểm 1–5)


# ══════════════════════════════════════════════════════════════
# 5. NGƯỠNG NGHIỆP VỤ (DOMAIN THRESHOLDS)
# ══════════════════════════════════════════════════════════════
# Từ phân tích thực tế: discount > 30 % → lỗ trung bình -61 $ / đơn
MAX_DISCOUNT_THRESHOLD    = 0.30

# Profit margin < -50 % → cảnh báo sản phẩm thua lỗ nặng
MIN_PROFIT_MARGIN_WARNING = -0.50

# Phân dải discount — dùng cho agg_discount_impact()
DISCOUNT_BINS   = [0.00, 0.10, 0.30, 0.50, 1.01]
DISCOUNT_LABELS = ["0-10%", "10-30%", "30-50%", "50%+"]