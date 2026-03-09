### 2. Nội dung file `config.py`

"""
Module: config.py
Vai trò: Trung tâm cấu hình đường dẫn dữ liệu, tham số thời gian, ngưỡng phát hiện ngoại lệ 
và các tham số tính toán RFM cho dự án Global Superstore.
"""
from pathlib import Path

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN DỮ LIỆU (PATHS)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "superstore.csv"

# Các thư mục đầu ra
CLEANED_DIR = DATA_DIR / "cleaned"
DIM_FACT_DIR = DATA_DIR / "dim_fact"
AGG_DIR = DATA_DIR / "aggregates"

# Tạo thư mục nếu chưa tồn tại
for folder in [DATA_DIR, RAW_DATA_PATH.parent, CLEANED_DIR, DIM_FACT_DIR, AGG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. THAM SỐ THỜI GIAN (TEMPORAL PARAMETERS)
# ==========================================
# Giới hạn phạm vi thời gian phân tích của đồ án
START_DATE = '2012-01-01'
END_DATE = '2015-12-31'


# ==========================================
# 3. THAM SỐ MÔ HÌNH RFM & COHORT
# ==========================================
# Bù trừ ngày đối chiếu (Snapshot Date) để tránh Recency = 0
SNAPSHOT_DATE_OFFSET = 1  

# Số lượng nhóm chia (Binning) cho điểm RFM
RFM_BINS = 5  


# ==========================================
# 4. NGƯỠNG NGOẠI LỆ (DOMAIN KNOWLEDGE THRESHOLDS)
# ==========================================
# Giới hạn mức giảm giá tối đa cho phép (ví dụ: không vượt quá 80%)
MAX_DISCOUNT_THRESHOLD = 0.8

# Biên lợi nhuận tối thiểu cần cảnh báo (Profit Margin)
MIN_PROFIT_MARGIN_WARNING = -0.5