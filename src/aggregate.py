"""
Module  : aggregate.py
Vai trò : Tạo toàn bộ Data Marts phục vụ trực tiếp Tableau Dashboard.

Output  : data/aggregates/
    - agg_rfm_segments.csv          — RFM Segmentation
    - agg_cohort_retention.csv      — Cohort Retention Matrix
    - agg_product_pareto.csv        — Pareto 80/20 sản phẩm
    - agg_yoy_growth.csv            — Tăng trưởng theo năm / market
    - agg_discount_impact.csv       — Tác động discount lên lợi nhuận
    - agg_shipping_analysis.csv     — Phân tích giao hàng
    - agg_market_performance.csv    — Hiệu suất từng market
    - agg_segment_performance.csv   — Hiệu suất từng customer segment
"""

import logging

import pandas as pd
import config

logger = logging.getLogger("aggregate")


# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════
def _save(df: pd.DataFrame, filename: str) -> None:
    path = config.AGG_DIR / filename
    df.to_csv(path, index=False)
    logger.info("Đã lưu %-40s  (%d dòng)", filename, len(df))


def _load_cleaned(parse_dates: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(
        config.CLEANED_DIR / "superstore_cleaned.csv",
        parse_dates=parse_dates or [],
    )


# ══════════════════════════════════════════════════════════════
# 1. RFM SEGMENTATION
# ══════════════════════════════════════════════════════════════
def _segment_label(row: pd.Series) -> str:
    """Gán nhãn phân khúc dựa trên điểm RFM tổng hợp."""
    score = row["rfm_score"]
    r, f, m = int(score[0]), int(score[1]), int(score[2])

    if score in {"555", "554", "544", "545", "454", "455", "445"}:
        return "Champions"
    if r >= 4 and f >= 4:
        return "Loyal Customers"
    if r >= 3 and f >= 3:
        return "Potential Loyalist"
    if r <= 2 and (f >= 4 or m >= 4):
        return "Can't Lose Them"
    if r == 1 and f <= 2 and m <= 2:
        return "Lost"
    if r <= 2:
        return "At Risk"
    return "Others"


def agg_rfm_segments() -> None:
    """
    Chấm điểm R-F-M và phân nhóm khách hàng.

    Điểm 1–5 (cao = tốt) theo phương pháp quintile:
    - R (Recency)   : ngày càng gần càng tốt → điểm 5
    - F (Frequency) : mua càng nhiều lần càng tốt → điểm 5
    - M (Monetary)  : chi tiêu càng cao càng tốt → điểm 5
    """
    logger.info("-- RFM Segmentation...")
    rfm = pd.read_csv(config.CLEANED_DIR / "rfm_base.csv")

    rfm["r_score"] = pd.qcut(rfm["recency"],  config.RFM_BINS, labels=[5, 4, 3, 2, 1])
    rfm["f_rank"]  = rfm["frequency"].rank(method="first")
    rfm["f_score"] = pd.qcut(rfm["f_rank"],   config.RFM_BINS, labels=[1, 2, 3, 4, 5])
    rfm["m_score"] = pd.qcut(rfm["monetary"], config.RFM_BINS, labels=[1, 2, 3, 4, 5])

    rfm["rfm_score"] = (
        rfm["r_score"].astype(str)
        + rfm["f_score"].astype(str)
        + rfm["m_score"].astype(str)
    )
    rfm["segment"] = rfm.apply(_segment_label, axis=1)
    rfm.drop(columns=["f_rank"], inplace=True)

    # Thống kê tóm tắt theo segment
    summary = rfm.groupby("segment").agg(
        customers  = ("customer_id", "count"),
        avg_recency   = ("recency",   "mean"),
        avg_frequency = ("frequency", "mean"),
        avg_monetary  = ("monetary",  "mean"),
    ).round(1).reset_index()
    logger.info("Phân bổ segment:\n%s", summary.to_string(index=False))

    _save(rfm, "agg_rfm_segments.csv")


# ══════════════════════════════════════════════════════════════
# 2. COHORT RETENTION
# ══════════════════════════════════════════════════════════════
def agg_cohort_retention() -> None:
    """
    Tính ma trận tỷ lệ giữ chân khách hàng theo tháng.

    Kết quả: pivot table  rows = cohort_month, cols = cohort_index (0,1,2,...)
             giá trị = tỷ lệ % so với cohort size tháng đầu.
    """
    logger.info("-- Cohort Retention...")
    df = _load_cleaned(parse_dates=["order_date"])

    cohort_data = (
        df.groupby(["cohort_month", "cohort_index"])["customer_id"]
        .nunique()
        .reset_index()
    )
    pivot = cohort_data.pivot(
        index="cohort_month", columns="cohort_index", values="customer_id"
    )
    retention = pivot.divide(pivot[0], axis=0).round(4)

    # Lưu dạng long format (dễ dùng hơn trong Tableau)
    retention_long = retention.reset_index().melt(
        id_vars="cohort_month",
        var_name="cohort_index",
        value_name="retention_rate",
    )
    retention_long["retention_pct"] = (retention_long["retention_rate"] * 100).round(2)

    _save(retention_long, "agg_cohort_retention.csv")


# ══════════════════════════════════════════════════════════════
# 3. PRODUCT PARETO (80/20)
# ══════════════════════════════════════════════════════════════
def agg_product_pareto() -> None:
    """
    Phân tích quy tắc 80/20: sub-category nào đóng góp 80 % lợi nhuận?

    Cột quan trọng:
    - profit_contribution_pct : % đóng góp từng sub-category
    - cumulative_pct          : % tích lũy
    - is_top80                : True nếu nằm trong nhóm tạo ra 80 % lợi nhuận
    """
    logger.info("-- Product Pareto...")
    df = _load_cleaned()

    pareto = (
        df.groupby("sub_category")
        .agg(
            total_profit  = ("profit", "sum"),
            total_sales   = ("sales",  "sum"),
            total_orders  = ("order_id", "count"),
        )
        .reset_index()
        .sort_values("total_profit", ascending=False)
    )

    total = pareto["total_profit"].sum()
    pareto["profit_contribution_pct"] = (pareto["total_profit"] / total * 100).round(2)
    pareto["cumulative_pct"]          = pareto["profit_contribution_pct"].cumsum().round(2)
    pareto["is_top80"]                = pareto["cumulative_pct"] <= 80
    pareto["profit_margin_pct"]       = (pareto["total_profit"] / pareto["total_sales"] * 100).round(2)

    logger.info(
        "Top 80 %% lợi nhuận gồm %d / %d sub-categories",
        pareto["is_top80"].sum(), len(pareto),
    )
    _save(pareto, "agg_product_pareto.csv")


# ══════════════════════════════════════════════════════════════
# 4. YoY GROWTH  
# ══════════════════════════════════════════════════════════════
def agg_yoy_growth() -> None:
    """
    Phân tích tăng trưởng Doanh thu & Lợi nhuận theo Năm và Market.
    Cột:
    - sales_growth_pct   : % tăng trưởng doanh thu so với năm trước
    - profit_growth_pct  : % tăng trưởng lợi nhuận so với năm trước
    """
    logger.info("-- YoY Growth Analysis...")
    df = _load_cleaned(parse_dates=["order_date"])
    df["order_year"] = df["order_date"].dt.year

    # Tổng hợp theo năm + market
    yoy = (
        df.groupby(["order_year", "market"])
        .agg(
            total_sales   = ("sales",  "sum"),
            total_profit  = ("profit", "sum"),
            total_orders  = ("order_id", "count"),
            unique_customers = ("customer_id", "nunique"),
        )
        .reset_index()
    )

    yoy = yoy.sort_values(["market", "order_year"])
    yoy["sales_growth_pct"]  = (
        yoy.groupby("market")["total_sales"].pct_change() * 100
    ).round(2)
    yoy["profit_growth_pct"] = (
        yoy.groupby("market")["total_profit"].pct_change() * 100
    ).round(2)
    yoy["profit_margin_pct"] = (yoy["total_profit"] / yoy["total_sales"] * 100).round(2)

    # Tổng toàn cầu mỗi năm (để vẽ trend line trong Tableau)
    global_yoy = (
        df.groupby("order_year")
        .agg(
            total_sales      = ("sales",  "sum"),
            total_profit     = ("profit", "sum"),
            total_orders     = ("order_id", "count"),
            unique_customers = ("customer_id", "nunique"),
        )
        .reset_index()
    )
    global_yoy["market"]             = "ALL"
    global_yoy["sales_growth_pct"]   = (global_yoy["total_sales"].pct_change() * 100).round(2)
    global_yoy["profit_growth_pct"]  = (global_yoy["total_profit"].pct_change() * 100).round(2)
    global_yoy["profit_margin_pct"]  = (global_yoy["total_profit"] / global_yoy["total_sales"] * 100).round(2)

    result = pd.concat([yoy, global_yoy], ignore_index=True)
    _save(result, "agg_yoy_growth.csv")


# ══════════════════════════════════════════════════════════════
# 5. DISCOUNT IMPACT  
# ══════════════════════════════════════════════════════════════
def agg_discount_impact() -> None:
    """
    Phân tích tác động của mức giảm giá lên lợi nhuận.

    Insight từ dữ liệu thực:
    - Discount 0–10 %  → lợi nhuận trung bình  +62.56 $ / đơn
    - Discount 10–30 % → lợi nhuận trung bình  +21.00 $ / đơn
    - Discount 30–50 % → lợi nhuận trung bình  -61.56 $ / đơn  ← CẢNH BÁO
    - Discount 50 %+   → lợi nhuận trung bình  -98.89 $ / đơn  ← NGHIÊM TRỌNG
    - Tỷ lệ đơn lỗ khi discount > 30 %: 87–100 %

    Cột:
    - discount_band      : nhóm giảm giá
    - avg_profit         : lợi nhuận trung bình
    - loss_rate_pct      : % đơn hàng bị lỗ
    - revenue_at_risk    : tổng doanh thu của nhóm đơn hàng lỗ
    """
    logger.info("-- Discount Impact Analysis...")
    df = _load_cleaned()

    df["discount_band"] = pd.cut(
        df["discount"],
        bins=config.DISCOUNT_BINS,
        labels=config.DISCOUNT_LABELS,
        include_lowest=True,
    )

    impact = (
        df.groupby("discount_band", observed=True)
        .agg(
            total_orders     = ("order_id",  "count"),
            avg_profit       = ("profit",    "mean"),
            total_profit     = ("profit",    "sum"),
            avg_sales        = ("sales",     "mean"),
            total_sales      = ("sales",     "sum"),
            loss_orders      = ("profit",    lambda x: (x < 0).sum()),
        )
        .reset_index()
    )

    impact["loss_rate_pct"]   = (impact["loss_orders"] / impact["total_orders"] * 100).round(1)
    impact["revenue_at_risk"] = (
        df[df["profit"] < 0]
        .groupby("discount_band", observed=True)["sales"]
        .sum()
        .values
    )
    impact["avg_profit"]  = impact["avg_profit"].round(2)
    impact["avg_sales"]   = impact["avg_sales"].round(2)

    # Phân tích thêm theo category × discount_band (cho Tableau heatmap)
    cat_impact = (
        df.groupby(["category", "discount_band"], observed=True)
        .agg(
            avg_profit   = ("profit", "mean"),
            loss_rate_pct = ("profit", lambda x: round((x < 0).mean() * 100, 1)),
        )
        .reset_index()
    )

    _save(impact,     "agg_discount_impact.csv")
    _save(cat_impact, "agg_discount_impact_by_category.csv")


# ══════════════════════════════════════════════════════════════
# 6. SHIPPING ANALYSIS  
# ══════════════════════════════════════════════════════════════
def agg_shipping_analysis() -> None:
    """
    Phân tích hiệu suất giao hàng theo Ship Mode, Market và Order Priority.

    Khuyến nghị: Ưu tiên nâng Ship Mode cho nhóm Champions (RFM) lên First Class.
    """
    logger.info("-- Shipping Analysis...")
    df = _load_cleaned(parse_dates=["order_date", "ship_date"])

    df["ship_delay_days"] = (df["ship_date"] - df["order_date"]).dt.days

    # Tổng hợp theo ship_mode × market
    ship_agg = (
        df.groupby(["ship_mode", "market"])
        .agg(
            total_orders      = ("order_id",       "count"),
            avg_delay_days    = ("ship_delay_days", "mean"),
            max_delay_days    = ("ship_delay_days", "max"),
            avg_shipping_cost = ("shipping_cost",   "mean"),
            total_shipping_cost = ("shipping_cost", "sum"),
        )
        .reset_index()
    )
    ship_agg["avg_delay_days"]    = ship_agg["avg_delay_days"].round(2)
    ship_agg["avg_shipping_cost"] = ship_agg["avg_shipping_cost"].round(2)

    # Tổng hợp theo ship_mode × order_priority (Late delivery risk)
    priority_ship = (
        df.groupby(["order_priority", "ship_mode"])
        .agg(
            total_orders   = ("order_id",       "count"),
            avg_delay_days = ("ship_delay_days", "mean"),
        )
        .reset_index()
    )
    priority_ship["avg_delay_days"] = priority_ship["avg_delay_days"].round(2)

    _save(ship_agg,      "agg_shipping_analysis.csv")
    _save(priority_ship, "agg_shipping_by_priority.csv")


# ══════════════════════════════════════════════════════════════
# 7.HIỆU SUẤT THỊ TRƯỜNG
# ══════════════════════════════════════════════════════════════
def agg_market_performance() -> None:
    """
    So sánh hiệu suất kinh doanh toàn diện giữa 7 Markets.
    Cột thêm:
    - sales_share_pct   : % thị phần doanh thu toàn cầu
    - profit_share_pct  : % đóng góp lợi nhuận toàn cầu
    """
    logger.info("-- Market Performance...")
    df = _load_cleaned(parse_dates=["order_date"])
    df["order_year"] = df["order_date"].dt.year

    market = (
        df.groupby(["market", "order_year"])
        .agg(
            total_sales      = ("sales",       "sum"),
            total_profit     = ("profit",      "sum"),
            total_orders     = ("order_id",    "count"),
            unique_customers = ("customer_id", "nunique"),
            avg_order_value  = ("sales",       "mean"),
            avg_discount     = ("discount",    "mean"),
        )
        .reset_index()
    )

    market["profit_margin_pct"] = (market["total_profit"] / market["total_sales"] * 100).round(2)
    market["avg_order_value"]   = market["avg_order_value"].round(2)
    market["avg_discount"]      = (market["avg_discount"] * 100).round(2)

    # Thêm % thị phần theo năm
    year_totals = df.groupby("order_year")["sales"].sum().rename("year_total_sales")
    market = market.merge(year_totals, on="order_year")
    market["sales_share_pct"] = (market["total_sales"] / market["year_total_sales"] * 100).round(2)
    market.drop(columns=["year_total_sales"], inplace=True)

    _save(market, "agg_market_performance.csv")


# ══════════════════════════════════════════════════════════════
# 8. HIỆU SUẤT PHÂN KHÚC  
# ══════════════════════════════════════════════════════════════
def agg_segment_performance() -> None:
    """
    Phân tích hiệu suất theo Customer Segment (Consumer / Corporate / Home Office).

    Phân tích theo 3 chiều:
    1. Doanh thu & lợi nhuận theo segment × year
    2. Hành vi mua hàng: tần suất, giá trị đơn hàng trung bình
    3. Sản phẩm ưa thích theo segment (top categories)
    """
    logger.info("-- Segment Performance...")
    df = _load_cleaned(parse_dates=["order_date"])
    df["order_year"] = df["order_date"].dt.year

    # Theo năm
    seg_year = (
        df.groupby(["segment", "order_year"])
        .agg(
            total_sales      = ("sales",       "sum"),
            total_profit     = ("profit",      "sum"),
            total_orders     = ("order_id",    "count"),
            unique_customers = ("customer_id", "nunique"),
            avg_order_value  = ("sales",       "mean"),
        )
        .reset_index()
    )
    seg_year["profit_margin_pct"] = (seg_year["total_profit"] / seg_year["total_sales"] * 100).round(2)
    seg_year["avg_order_value"]   = seg_year["avg_order_value"].round(2)

    # Category ưa thích theo segment
    seg_cat = (
        df.groupby(["segment", "category"])
        .agg(
            total_sales  = ("sales",  "sum"),
            total_profit = ("profit", "sum"),
            order_count  = ("order_id", "count"),
        )
        .reset_index()
    )
    seg_cat["profit_margin_pct"] = (seg_cat["total_profit"] / seg_cat["total_sales"] * 100).round(2)

    _save(seg_year, "agg_segment_performance.csv")
    _save(seg_cat,  "agg_segment_by_category.csv")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def run_all() -> None:
    """Chạy toàn bộ pipeline tạo Data Marts."""
    logger.info("=== BẮT ĐẦU TẠO DATA MARTS ===")
    try:
        agg_rfm_segments()
        agg_cohort_retention()
        agg_product_pareto()
        agg_yoy_growth()
        agg_discount_impact()
        agg_shipping_analysis()
        agg_market_performance()
        agg_segment_performance()
        logger.info("=== HOÀN TẤT — %d file đã được tạo trong %s ===", 10, config.AGG_DIR)
    except FileNotFoundError:
        logger.error("Không tìm thấy cleaned data. Hãy chạy cleaner.py trước.")
    except Exception as exc:
        logger.exception("Lỗi trong aggregate: %s", exc)


if __name__ == "__main__":
    run_all()