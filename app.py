import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import unicodedata
import io

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG & C-SUITE EXECUTIVE STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="KTC C-Suite Global Strategy & Analytics",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Executive UI Style Sheet
st.markdown("""
<style>
    /* Global Base */
    .main { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Header Container */
    .csuite-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 24px 30px;
        border-radius: 14px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    }
    .csuite-header h2 { color: #38bdf8; margin: 0 0 8px 0; font-weight: 700; font-size: 1.6rem; }
    .csuite-header p { color: #94a3b8; margin: 0; font-size: 0.95rem; }
    
    /* Executive Metric Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .kpi-title { font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; font-weight: 600; }
    .kpi-value { font-size: 1.6rem; font-weight: 800; color: #0f172a; margin: 6px 0; }
    .kpi-sub { font-size: 0.8rem; font-weight: 500; }
    
    /* Badges & Tags */
    .badge-star { background-color: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.75rem; }
    .badge-cash { background-color: #d1fae5; color: #065f46; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.75rem; }
    .badge-quest { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.75rem; }
    .badge-dog { background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.replace('_', ' ')
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    return text.lower().strip()

# ---------------------------------------------------------
# 2. XỬ LÝ DỮ LIỆU TỐI ƯU HIỆU NĂNG
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def process_data(file_dm_bytes, files_sl_tuples):
    df_dm_raw = pd.read_excel(file_dm_bytes, header=None)
    
    dm_hdr = 0
    for idx, row in df_dm_raw.iterrows():
        row_str = " ".join([str(x) for x in row.values if pd.notna(x)])
        if 'stt' in normalize_text(row_str) and 'ma kh' in normalize_text(row_str):
            dm_hdr = idx
            break
            
    df_dm = df_dm_raw.iloc[dm_hdr + 1:].copy()
    df_dm.columns = [str(x).strip() for x in df_dm_raw.iloc[dm_hdr].values]
    
    c_dm_code = next(c for c in df_dm.columns if 'ma kh' in normalize_text(c))
    c_dm_name = next(c for c in df_dm.columns if 'ten nha phan phoi' in normalize_text(c) or 'dai ly' in normalize_text(c))
    c_dm_region = next(c for c in df_dm.columns if 'dia ban' in normalize_text(c) or 'tinh' in normalize_text(c))
    
    df_dm_clean = df_dm[[c_dm_code, c_dm_name, c_dm_region]].copy()
    df_dm_clean.columns = ['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban_Master']
    df_dm_clean['Ma_KH'] = df_dm_clean['Ma_KH'].astype(str).str.strip()
    df_dm_clean = df_dm_clean.dropna(subset=['Ma_KH']).drop_duplicates(subset=['Ma_KH'])
    
    sales_frames = []
    for f_name, f_bytes in files_sl_tuples:
        df_raw = pd.read_excel(f_bytes, header=None)
        
        hdr_idx = 0
        for idx, row in df_raw.iterrows():
            row_str = " ".join([str(x) for x in row.values if pd.notna(x)])
            if 'stt' in normalize_text(row_str) and ('ma kh' in normalize_text(row_str) or 'san pham' in normalize_text(row_str)):
                hdr_idx = idx
                break
                
        df = df_raw.iloc[hdr_idx + 1:].copy()
        df.columns = [str(x).strip() for x in df_raw.iloc[hdr_idx].values]
        
        c_code = next((c for c in df.columns if 'ma kh' in normalize_text(c)), None)
        c_name = next((c for c in df.columns if 'ten nha phan phoi' in normalize_text(c) or 'dai ly' in normalize_text(c)), None)
        c_sp = next((c for c in df.columns if 'san pham' in normalize_text(c)), None)
        c_sl = next((c for c in df.columns if 'so luong' in normalize_text(c) or 'san luong' in normalize_text(c)), None)
        c_dt = next((c for c in df.columns if 'doanh thu' in normalize_text(c)), None)
        
        if c_code: df[c_code] = df[c_code].ffill()
        if c_name: df[c_name] = df[c_name].ffill()
        
        df_prod = df[df[c_sp].notna()].copy()
        df_prod[c_sp] = df_prod[c_sp].astype(str).str.strip()
        df_prod = df_prod[~df_prod[c_sp].str.lower().str.contains('sản phẩm|tổng cộng|cộng')]
        
        m_match = re.search(r'T(\d{1,2})', f_name, re.IGNORECASE)
        thang_label = f"Tháng {int(m_match.group(1)):02d}" if m_match else f_name
        
        temp_df = pd.DataFrame({
            'Ma_KH': df_prod[c_code].astype(str).str.strip(),
            'Ten_NPP_File': df_prod[c_name].astype(str).str.strip() if c_name else "",
            'Ten_SP': df_prod[c_sp],
            'San_Luong': pd.to_numeric(df_prod[c_sl], errors='coerce').fillna(0),
            'Doanh_Thu': pd.to_numeric(df_prod[c_dt], errors='coerce').fillna(0),
            'Thang': thang_label
        })
        sales_frames.append(temp_df)
        
    df_all_sales = pd.concat(sales_frames, ignore_index=True)
    
    df_merged = pd.merge(df_all_sales, df_dm_clean, on='Ma_KH', how='left')
    df_merged['Ten_NPP_Khai_Bao'] = df_merged['Ten_NPP_Master'].fillna(df_merged['Ten_NPP_File'])
    df_merged['Thuyet_Minh_NPP'] = "[" + df_merged['Ma_KH'] + "] - " + df_merged['Ten_NPP_Khai_Bao']
    df_merged['Dia_Ban_Tieu_Thu'] = df_merged['Dia_Ban_Master'].fillna('Chưa phân vùng')
    
    return df_merged

# ---------------------------------------------------------
# 3. SIDEBAR CONTROLS
# ---------------------------------------------------------
st.sidebar.title("🏛️ C-SUITE CONTROL CENTER")
file_dm = st.sidebar.file_uploader("1. Master File Danh mục (.xlsx)", type=["xlsx"])
files_sl = st.sidebar.file_uploader("2. Dữ liệu Sản lượng (.xlsx)", type=["xlsx"], accept_multiple_files=True)

if file_dm and files_sl:
    dm_bytes = io.BytesIO(file_dm.read())
    sl_tuples = [(f.name, io.BytesIO(f.read())) for f in files_sl]
    
    with st.spinner("⚡ Ứng dụng AI Analytics & C-Suite Matrix..."):
        df = process_data(dm_bytes, sl_tuples)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Bộ Lọc Báo Cáo")
    
    all_months = sorted(df['Thang'].unique())
    selected_months = st.sidebar.multiselect("Chu kỳ Tháng", options=all_months, default=all_months)
    
    all_regions = sorted(df['Dia_Ban_Tieu_Thu'].unique())
    selected_regions = st.sidebar.multiselect("Địa Bàn / Tỉnh", options=all_regions, default=all_regions)

    all_prods = sorted(df['Ten_SP'].unique())
    selected_prods = st.sidebar.multiselect("Dòng Sản Phẩm", options=all_prods, default=all_prods)

    df_filtered = df[
        (df['Thang'].isin(selected_months)) & 
        (df['Dia_Ban_Tieu_Thu'].isin(selected_regions)) &
        (df['Ten_SP'].isin(selected_prods))
    ]

    unit_choice = st.sidebar.radio("Chỉ số hiển thị:", ["Doanh_Thu", "San_Luong"], 
                                   format_func=lambda x: "Doanh Thu (VNĐ)" if x == "Doanh_Thu" else "Sản Lượng (Bao)")
    unit_label = "VNĐ" if unit_choice == "Doanh_Thu" else "Bao"

    # ---------------------------------------------------------
    # 4. EXECUTIVE BRIEFING (TÓM TẮT DÀNH CHO CEO)
    # ---------------------------------------------------------
    st.markdown("""
    <div class="csuite-header">
        <h2>🏛️ TẬP ĐOÀN KTC - EXECUTIVE STRATEGY DASHBOARD</h2>
        <p>Hệ thống hỗ trợ ra quyết định chiến lược: Sản phẩm x Địa bàn tiêu thụ x Tối ưu hóa Nhà Phân Phối</p>
    </div>
    """, unsafe_allow_html=True)

    total_rev = df_filtered['Doanh_Thu'].sum()
    total_vol = df_filtered['San_Luong'].sum()
    total_npp = df_filtered['Ma_KH'].nunique()
    total_sku = df_filtered['Ten_SP'].nunique()

    # Dynamic KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Doanh Thu Toàn Hệ Thống</div>
            <div class="kpi-value">{total_rev/1e9:,.2f} Tỷ</div>
            <div class="kpi-sub" style="color:#10b981;">▲ Chu kỳ báo cáo</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Tổng Sản Lượng Tiêu Thụ</div>
            <div class="kpi-value">{total_vol:,.0f}</div>
            <div class="kpi-sub" style="color:#0284c7;">Đơn vị: Bao</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Mạng Lưới NPP Hoạt Động</div>
            <div class="kpi-value">{total_npp} KH</div>
            <div class="kpi-sub" style="color:#64748b;">Khách hàng phát sinh doanh số</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Danh Mục Sản Phẩm Active</div>
            <div class="kpi-value">{total_sku} SKU</div>
            <div class="kpi-sub" style="color:#f59e0b;">Độ phủ sản phẩm</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 5. CÁC MODULE CHIẾN LƯỢC CAO CẤP
    # ---------------------------------------------------------
    st.subheader("📊 NĂNG LỰC PHÂN TÍCH CHIẾN LƯỢC C-SUITE")
    
    t_opt, t_fit, t_trend, t_pareto = st.tabs([
        "🎯 1. Tối Ưu Ưu Tiên SP - Địa Bàn (BCG Matrix)",
        "🤝 2. Khung Chọn & Đánh Giá Tương Thích NPP",
        "📈 3. Biến Động Chu Kỳ & Đốm Trắng Thị Trường",
        "⚖️ 4. Phân Hạng Pareto 3D & Cảnh Báo CEO"
    ])

    # ---------------------------------------------------------
    # TAB 1: BCG MATRIX & PRODUCT-TERRITORY PRIORITY
    # ---------------------------------------------------------
    with t_opt:
        st.markdown("##### 🚀 Ma Trận Tối Ưu Ưu Tiên Phát Triển Sản Phẩm x Địa Bàn Tiêu Thụ")
        st.caption("Xác định chính xác cặp (Sản phẩm - Tỉnh) nào là Ngôi sao cần bơm vốn, Bò sữa cần khai thác, hoặc Yếu kém cần cắt giảm.")

        # Aggregate Product x Region
        pr_df = df_filtered.groupby(['Dia_Ban_Tieu_Thu', 'Ten_SP']).agg(
            Revenue=('Doanh_Thu', 'sum'),
            Volume=('San_Luong', 'sum'),
            NPP_Count=('Ma_KH', 'nunique')
        ).reset_index()

        if not pr_df.empty:
            # Calculate metrics for classification
            avg_rev = pr_df['Revenue'].mean()
            avg_vol = pr_df['Volume'].mean()

            def classify_bcg(row):
                if row['Revenue'] >= avg_rev and row['Volume'] >= avg_vol:
                    return '🌟 Ngôi Sao (Đẩy mạnh mở rộng)'
                elif row['Revenue'] >= avg_rev and row['Volume'] < avg_vol:
                    return '🐄 Bò Sữa (Tối ưu lợi nhuận)'
                elif row['Revenue'] < avg_rev and row['Volume'] >= avg_vol:
                    return '❓ Dấu Hỏi (Thử nghiệm tăng giá)'
                else:
                    return '⚠️ Yếu Kém (Tái cấu trúc/Rút lui)'

            pr_df['Nhom_Chien_Luoc'] = pr_df.apply(classify_bcg, axis=1)

            # Scatter Plot BCG Matrix
            fig_bcg = px.scatter(
                pr_df,
                x='Volume',
                y='Revenue',
                size='NPP_Count',
                color='Nhom_Chien_Luoc',
                hover_name='Ten_SP',
                hover_data=['Dia_Ban_Tieu_Thu'],
                text='Ten_SP',
                color_discrete_map={
                    '🌟 Ngôi Sao (Đẩy mạnh mở rộng)': '#0284c7',
                    '🐄 Bò Sữa (Tối ưu lợi nhuận)': '#10b981',
                    '❓ Dấu Hỏi (Thử nghiệm tăng giá)': '#f59e0b',
                    '⚠️ Yếu Kém (Tái cấu trúc/Rút lui)': '#ef4444'
                },
                title="Ma Trận Phân Bổ Tiềm Năng Sản Phẩm Theo Địa Bàn"
            )
            fig_bcg.add_hline(y=avg_rev, line_dash="dash", line_color="#94a3b8", annotation_text="Trung bình Doanh thu")
            fig_bcg.add_vline(x=avg_vol, line_dash="dash", line_color="#94a3b8", annotation_text="Trung bình Sản lượng")
            fig_bcg.update_traces(textposition='top center')
            fig_bcg.update_layout(height=480, plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig_bcg, use_container_width=True)

            # Detail Priority Table
            st.markdown("**Bảng Chỉ Số Ưu Tiên Phát Triển (Product Priority Index):**")
            st.dataframe(
                pr_df.sort_values(by='Revenue', ascending=False).style.format({
                    'Revenue': '{:,.0f}',
                    'Volume': '{:,.0f}'
                }),
                use_container_width=True
            )

    # ---------------------------------------------------------
    # TAB 2: DISTRIBUTOR FIT SCORE & SELECTION FRAMEWORK
    # ---------------------------------------------------------
    with t_fit:
        st.markdown("##### 🤝 Khung Đánh Giá & Thuật Toán Chọn Nhà Phân Phối Tương Thích Địa Bàn")
        st.caption("Chấm điểm NPP theo 3 chiều: Tỷ trọng đóng góp địa bàn, Độ rộng SKU tiêu thụ, và Tốc độ tăng trưởng.")

        npp_eval = df_filtered.groupby(['Thuyet_Minh_NPP', 'Dia_Ban_Tieu_Thu']).agg(
            NPP_Rev=('Doanh_Thu', 'sum'),
            NPP_Vol=('San_Luong', 'sum'),
            SKU_Count=('Ten_SP', 'nunique')
        ).reset_index()

        reg_tot = df_filtered.groupby('Dia_Ban_Tieu_Thu')['Doanh_Thu'].sum().to_dict()
        max_skus = df_filtered['Ten_SP'].nunique()

        if not npp_eval.empty:
            npp_eval['Region_Total'] = npp_eval['Dia_Ban_Tieu_Thu'].map(reg_tot)
            npp_eval['Market_Share_Pct'] = (npp_eval['NPP_Rev'] / npp_eval['Region_Total']) * 100
            npp_eval['SKU_Coverage_Pct'] = (npp_eval['SKU_Count'] / max_skus) * 100

            # Composite Fit Score Formula (0-100)
            npp_eval['Fit_Score'] = (npp_eval['Market_Share_Pct'] * 0.6) + (npp_eval['SKU_Coverage_Pct'] * 0.4)

            def fit_recommendation(score):
                if score >= 40: return "🟢 NPP Chi Lược (Phù hợp giao độc quyền/mở rộng)"
                elif score >= 20: return "🟡 NPP Tiềm Năng (Cần giao thêm chỉ tiêu SKU)"
                else: return "🔴 NPP Phụ (Rủi ro phân tán nguồn lực)"

            npp_eval['Danh_Gia'] = npp_eval['Fit_Score'].apply(fit_recommendation)

            # Visual Distribution of Scores
            fig_fit = px.bar(
                npp_eval.sort_values(by='Fit_Score', ascending=False).head(15),
                x='Fit_Score',
                y='Thuyet_Minh_NPP',
                color='Fit_Score',
                orientation='h',
                color_continuous_scale='Blues',
                title="Top 15 Nhà Phân Phối Có Điểm Tương Thích Cao Nhất"
            )
            fig_fit.update_layout(height=450, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_fit, use_container_width=True)

            # Executive Selection Criteria Guide
            st.markdown("""
            > 💡 **KHUYÊN NGHỊ TỪ CEO TOP 10 DÀNH CHO TIÊU CHUẨN CHỌN NPP:**
            > 1. **NPP Chiến Lược (Điểm > 40):** Ưu tiên hỗ trợ chính sách thưởng quý, hỗ trợ nhân sự Sales thị trường (PG/SS).
            > 2. **NPP Tiềm Năng (Điểm 20-40):** Bắt buộc ký hợp đồng Combi-Sell (bán kèm 2 SKU mới nếu muốn giữ chiết khấu dòng chủ lực).
            > 3. **NPP Phụ (Điểm < 20):** Không tốn chi phí Marketing riêng, chỉ áp dụng chính sách mua đứt bán đoạn.
            """)

            st.dataframe(
                npp_eval[['Thuyet_Minh_NPP', 'Dia_Ban_Tieu_Thu', 'Market_Share_Pct', 'SKU_Coverage_Pct', 'Fit_Score', 'Danh_Gia']]
                .sort_values(by='Fit_Score', ascending=False)
                .style.format({
                    'Market_Share_Pct': '{:.1f}%',
                    'SKU_Coverage_Pct': '{:.1f}%',
                    'Fit_Score': '{:.1f}'
                }),
                use_container_width=True
            )

    # ---------------------------------------------------------
    # TAB 3: MONTHLY TRENDS & HEATMAP MATRIX
    # ---------------------------------------------------------
    with t_trend:
        st.markdown("##### 🗺️ Ma Trận Đốm Trắng Thị Trường (Territory x Product Heatmap)")
        
        matrix_df = df_filtered.pivot_table(
            index='Dia_Ban_Tieu_Thu', 
            columns='Ten_SP', 
            values=unit_choice, 
            aggfunc='sum'
        ).fillna(0)

        if not matrix_df.empty:
            fig_matrix = px.imshow(
                matrix_df,
                text_auto='.2s' if unit_choice == 'Doanh_Thu' else ',.0f',
                aspect="auto",
                color_continuous_scale="Viridis",
                labels=dict(x="Dòng Sản Phẩm", y="Địa Bàn / Tỉnh", color=unit_label),
                title="Độ Phủ Doanh Số Sản Phẩm Tại Các Địa Bàn"
            )
            fig_matrix.update_layout(height=420)
            st.plotly_chart(fig_matrix, use_container_width=True)

        st.markdown("##### 📈 Biến Động Tăng Trưởng Theo Tháng")
        trend_df = df_filtered.groupby(['Thang', 'Ten_SP'])[unit_choice].sum().reset_index()
        fig_line = px.line(
            trend_df, x='Thang', y=unit_choice, color='Ten_SP', markers=True,
            color_discrete_sequence=px.colors.qualitative.Bold,
            title=f"Xu Hướng {unit_label} Từng Dòng Sản Phẩm"
        )
        fig_line.update_layout(height=400, plot_bgcolor='white')
        st.plotly_chart(fig_line, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 4: PARETO 3D & AUTOMATED ALERTS
    # ---------------------------------------------------------
    with t_pareto:
        st.markdown("##### ⚖️ Phân Hạng Pareto 80/20 & Cảnh Báo Rủi Ro Tự Động")

        # Risk Alerts Engine
        npp_revs = df_filtered.groupby('Thuyet_Minh_NPP')['Doanh_Thu'].sum().sort_values(ascending=False)
        top3_pct = (npp_revs.head(3).sum() / total_rev * 100) if total_rev > 0 else 0

        c_a1, c_a2 = st.columns(2)
        with c_a1:
            if top3_pct > 50:
                st.error(f"🚨 **RỦI RO TẬP TRUNG CAO:** Top 3 NPP chiếm tới **{top3_pct:.1f}%** tổng doanh thu toàn công ty. Cần mở rộng kênh phân phối ngay!")
            else:
                st.success(f"✅ **MỨC TẬP TRUNG AN TOÀN:** Top 3 NPP chiếm **{top3_pct:.1f}%** doanh thu.")

        with c_a2:
            single_sku_cnt = (df_filtered.groupby('Thuyet_Minh_NPP')['Ten_SP'].nunique() == 1).sum()
            if single_sku_cnt > 0:
                st.warning(f"⚠️ **RỦI RO ĐƠN ĐỘC DÒNG SP:** Phát hiện **{single_sku_cnt} NPP** chỉ bán duy nhất 1 sản phẩm. Nguy cơ mất khách hàng cao nếu đối thủ hạ giá.")

        # Pareto Chart
        pareto_df = df_filtered.groupby('Thuyet_Minh_NPP').agg(Total_Val=('Doanh_Thu', 'sum')).reset_index()
        pareto_df = pareto_df.sort_values(by='Total_Val', ascending=False)
        pareto_df['Cum_Val'] = pareto_df['Total_Val'].cumsum()
        pareto_df['Cum_Pct'] = (pareto_df['Cum_Val'] / total_rev * 100) if total_rev > 0 else 0

        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=pareto_df['Thuyet_Minh_NPP'], y=pareto_df['Total_Val'], name="Doanh Thu", marker_color='#1e3a8a'))
        fig_pareto.add_trace(go.Scatter(x=pareto_df['Thuyet_Minh_NPP'], y=pareto_df['Cum_Pct'], name="Tích Luỹ %", yaxis="y2", line=dict(color='#ef4444', width=3)))
        fig_pareto.update_layout(
            title="Đường Cong Tích Luỹ Pareto (Xác Định Nhóm Khách Hàng Core)",
            yaxis=dict(title="Doanh Thu (VNĐ)"),
            yaxis2=dict(title="Tích Luỹ (%)", overlaying="y", side="right", range=[0, 105]),
            height=420,
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

    # ---------------------------------------------------------
    # EXPORT DATA
    # ---------------------------------------------------------
    st.markdown("---")
    output_buffer = io.BytesIO()
    with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Sales_Data')
        if 'pr_df' in locals():
            pr_df.to_excel(writer, index=False, sheet_name='BCG_Priority_Matrix')

    st.download_button(
        label="📥 Tải Xuất Báo Cáo Chiến Lược C-Suite (.xlsx)",
        data=output_buffer.getvalue(),
        file_name="KTC_CSuite_Strategic_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👋 Vui lòng tải lên file **Master Danh Mục** và **Dữ liệu Sản Lượng** ở thanh bên trái để khởi tạo Báo Cáo Chiến Lược C-Suite.")
