"""
Module: config.py
Vai trò: Trung tâm cấu hình đọc trực tiếp từ file .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env vào hệ thống
load_dotenv()

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN DỮ LIỆU (PATHS)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "Global_Superstore.csv"

CLEANED_DIR = DATA_DIR / "cleaned"
DIM_FACT_DIR = DATA_DIR / "dim_fact"
AGG_DIR = DATA_DIR / "aggregates"

# Tạo thư mục nếu chưa tồn tại
for folder in [DATA_DIR, RAW_DATA_PATH.parent, CLEANED_DIR, DIM_FACT_DIR, AGG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. ĐỌC THAM SỐ TỪ .ENV (Có giá trị mặc định nếu quên cấu hình)
# ==========================================
START_DATE = os.getenv('START_DATE', '2012-01-01')
END_DATE = os.getenv('END_DATE', '2015-12-31')

# Lưu ý: os.getenv luôn trả về kiểu String, cần ép kiểu về int/float để tính toán
SNAPSHOT_DATE_OFFSET = int(os.getenv('SNAPSHOT_DATE_OFFSET', 1))
RFM_BINS = int(os.getenv('RFM_BINS', 5))

MAX_DISCOUNT_THRESHOLD = float(os.getenv('MAX_DISCOUNT_THRESHOLD', 0.8))
MIN_PROFIT_MARGIN_WARNING = float(os.getenv('MIN_PROFIT_MARGIN_WARNING', -0.5))

# ==========================================
# CẤU HÌNH CHO PHÂN TÍCH DISCOUNT IMPACT
# ==========================================
DISCOUNT_BINS = [0.0, 0.1, 0.3, 0.5, 1.0]
DISCOUNT_LABELS = ["0-10%", "10-30%", "30-50%", "50%+"]