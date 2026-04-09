"""
Module  : main.py
Vai trò : Điều phối toàn bộ pipeline — chạy 1 lệnh duy nhất để xử lý
          từ raw data → Star Schema → Data Marts sẵn sàng cho Tableau.

Chạy   : python main.py
         python main.py --skip-eda       (bỏ qua EDA, chạy nhanh hơn)
         python main.py --only-agg       (chỉ chạy lại aggregate)
"""

import argparse
import logging
import time

import config   # noqa: F401 — kích hoạt logging + tạo thư mục

logger = logging.getLogger("main")


def run_pipeline(skip_eda: bool = False, only_agg: bool = False) -> None:
    start = time.time()
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║   SUPERSTORE ANALYTICS PRO — PIPELINE   ║")
    logger.info("╚══════════════════════════════════════════╝")

    if not only_agg:
        # ── Bước 0: EDA (tuỳ chọn) ──────────────────
        if not skip_eda:
            logger.info("▶ Bước 0 — EDA")
            import eda
            eda.run_all()

        # ── Bước 1: Làm sạch ────────────────────────
        logger.info("▶ Bước 1 — Làm sạch dữ liệu (cleaner)")
        import cleaner
        cleaner.run_all()

        # ── Bước 2: Star Schema ──────────────────────
        logger.info("▶ Bước 2 — Xây dựng Star Schema (splitter)")
        import splitter
        splitter.run_all()

    # ── Bước 3: Data Marts ──────────────────────────
    logger.info("▶ Bước 3 — Tạo Data Marts (aggregate)")
    import aggregate
    aggregate.run_all()

    elapsed = time.time() - start
    logger.info("══════════════════════════════════════════")
    logger.info(" PIPELINE HOÀN TẤT trong %.1f giây", elapsed)
    logger.info(" Kiểm tra kết quả tại:")
    logger.info("   • Cleaned data : %s", config.CLEANED_DIR)
    logger.info("   • Star Schema  : %s", config.DIM_FACT_DIR)
    logger.info("   • Data Marts   : %s", config.AGG_DIR)
    logger.info("══════════════════════════════════════════")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Superstore Analytics Pipeline")
    parser.add_argument(
        "--skip-eda",
        action="store_true",
        help="Bỏ qua bước EDA để chạy nhanh hơn",
    )
    parser.add_argument(
        "--only-agg",
        action="store_true",
        help="Chỉ chạy lại bước tạo Data Marts (aggregate)",
    )
    args = parser.parse_args()
    run_pipeline(skip_eda=args.skip_eda, only_agg=args.only_agg)