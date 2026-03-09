"""
Module: Aggregate.py
Vai trò: Tạo các Data Marts (bảng tổng hợp) để phục vụ trực tiếp cho BI Dashboard.
Bao gồm: RFM Segmentation, Cohort Retention Rate, Pareto Products.
"""

import pandas as pd
import config

def segment_customer(row):
    """Gán nhãn phân khúc khách hàng dựa trên điểm số R-F-M."""
    rfm_score = row['rfm_score']
    if rfm_score in ['555', '554', '544', '545', '454', '455', '445']:
        return 'Champions'
    elif rfm_score.startswith('5') or rfm_score.startswith('4'):
        return 'Loyal Customers'
    elif rfm_score.startswith('3'):
        return 'Potential Loyalist'
    elif rfm_score.startswith('1') and (row['f_score'] == 5 or row['m_score'] == 5):
        return 'Cant Lose Them'
    elif rfm_score in ['111', '112']:
        return 'Lost'
    else:
        return 'At Risk / Others'

def agg_rfm_segments():
    """Chấm điểm và phân nhóm RFM."""
    print("Đang xử lý phân khúc RFM...")
    rfm = pd.read_csv(config.CLEANED_DIR / "rfm_base.csv")
    
    # Sử dụng tên cột viết thường (recency, frequency, monetary)
    rfm['r_score'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
    
    rfm['f_rank'] = rfm['frequency'].rank(method='first')
    rfm['f_score'] = pd.qcut(rfm['f_rank'], 5, labels=[1, 2, 3, 4, 5])
    
    rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])
    
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    rfm['segment'] = rfm.apply(segment_customer, axis=1)
    
    rfm.drop(columns=['f_rank'], inplace=True)
    rfm.to_csv(config.AGG_DIR / "agg_rfm_segments.csv", index=False)
    print("-> Xong RFM Segmentation.")

def agg_cohort_retention():
    """Tính toán ma trận tỷ lệ giữ chân."""
    print("Đang xử lý phân tích Cohort...")
    df = pd.read_csv(config.CLEANED_DIR / "superstore_cleaned.csv")
    
    # Sử dụng tên cột viết thường
    cohort_data = df.groupby(['cohort_month', 'cohort_index'])['customer_id'].apply(pd.Series.nunique).reset_index()
    cohort_counts = cohort_data.pivot(index='cohort_month', columns='cohort_index', values='customer_id')
    
    cohort_sizes = cohort_counts.iloc[:, 0]
    retention = cohort_counts.divide(cohort_sizes, axis=0)
    
    retention.to_csv(config.AGG_DIR / "agg_cohort_retention.csv")
    print("-> Xong Cohort Retention.")

def agg_product_pareto():
    """Phân tích quy tắc 80/20 cho sản phẩm."""
    print("Đang xử lý phân tích Pareto...")
    df = pd.read_csv(config.CLEANED_DIR / "superstore_cleaned.csv")
    
    pareto = df.groupby('sub-category')['profit'].sum().reset_index()
    pareto = pareto.sort_values(by='profit', ascending=False)
    
    total_profit = pareto['profit'].sum()
    pareto['profit_contribution_pct'] = pareto['profit'] / total_profit
    pareto['cumulative_pct'] = pareto['profit_contribution_pct'].cumsum()
    
    pareto.to_csv(config.AGG_DIR / "agg_product_pareto.csv", index=False)
    print("-> Xong Product Pareto.")

def run_all():
    print("=== BẮT ĐẦU TẠO CÁC DATA MARTS ===")
    agg_rfm_segments()
    agg_cohort_retention()
    agg_product_pareto()
    print("=== HOÀN TẤT TỔNG HỢP DỮ LIỆU ===")

if __name__ == "__main__":
    run_all()