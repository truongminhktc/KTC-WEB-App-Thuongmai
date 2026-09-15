import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import unicodedata
import io

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG & CUSTOM STYLING (GLOBAL TOP 10 ENTERPRISE LOOK)
# ---------------------------------------------------------
st.set_page_config(
    page_title="KTC Global Executive Dashboard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling cho C-Suite UI
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .exec-summary-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 22px 28px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 6px solid #3b82f6;
    }
    .exec-summary-box h4 { color: #38bdf8; margin-top: 0; font-size: 1.25rem; }
    .exec-summary-box ul { margin-bottom: 0; padding-left: 20px; color: #e2e8f0; }
    
    .alert-card-danger {
        background-color: #fef2f2; border: 1px solid #fecaca;
        border-left: 5px solid #ef4444; padding: 15px; border-radius: 8px; margin-bottom: 12px;
    }
    .alert-card-warning {
        background-color: #fffbeb; border: 1px solid #fde68a;
        border-left: 5px solid #f59e0b; padding: 15px; border-radius: 8px; margin-bottom: 12px;
    }
    .alert-card-info {
        background-color: #f0f9ff; border: 1px solid #bae6fd;
        border-left: 5px solid #0284c7; padding: 15px; border-radius: 8px; margin-bottom: 12px;
    }
    .metric-container {
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); text-align: center;
    }
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
# 2. CACHING & XỬ LÝ DỮ LIỆU
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
# 3. SIDEBAR & BO BỘ LỌC TOÀN CỤC
# ---------------------------------------------------------
st.sidebar.title("🏛️ C-SUITE EXECUTIVE PORTAL")
file_dm = st.sidebar.file_uploader("1. Master File Danh mục (.xlsx)", type=["xlsx"])
files_sl = st.sidebar.file_uploader("2. Dữ liệu Sản lượng các tháng (.xlsx)", type=["xlsx"], accept_multiple_files=True)

if file_dm and files_sl:
    dm_bytes = io.BytesIO(file_dm.read())
    sl_tuples = [(f.name, io.BytesIO(f.read())) for f in files_sl]
    
    with st.spinner("🔄 Đang xử lý & phân tích dữ liệu đa chiều..."):
        df = process_data(dm_bytes, sl_tuples)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Bộ Lọc Quản Trị")
    
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

    # Đơn vị hiển thị
    unit_choice = st.sidebar.radio("Đơn vị hiển thị:", ["Doanh_Thu", "San_Luong"], 
                                   format_func=lambda x: "Doanh Thu (VNĐ)" if x == "Doanh_Thu" else "Sản Lượng (Bao)")
    unit_label = "Doanh Thu (VNĐ)" if unit_choice == "Doanh_Thu" else "Sản Lượng (Bao)"

    # ---------------------------------------------------------
    # 4. TÓM TẮT ĐIỀU HÀNH CEO 30 GIÂY
    # ---------------------------------------------------------
    st.title("🌐 KTC EXECUTIVE DASHBOARD - TOP 10 GLOBAL STANDARD")
    
    total_rev = df_filtered['Doanh_Thu'].sum()
    total_vol = df_filtered['San_Luong'].sum()
    total_npp = df_filtered['Ma_KH'].nunique()
    total_sku = df_filtered['Ten_SP'].nunique()

    top_region = df_filtered.groupby('Dia_Ban_Tieu_Thu')['Doanh_Thu'].sum().idxmax() if len(df_filtered) > 0 else "N/A"
    top_npp = df_filtered.groupby('Thuyet_Minh_NPP')['Doanh_Thu'].sum().idxmax() if len(df_filtered) > 0 else "N/A"
    
    # Tính biến động MoM
    m_list = sorted(df_filtered['Thang'].unique())
    if len(m_list) >= 2:
        m_curr, m_prev = m_list[-1], m_list[-2]
        rev_c = df_filtered[df_filtered['Thang'] == m_curr]['Doanh_Thu'].sum()
        rev_p = df_filtered[df_filtered['Thang'] == m_prev]['Doanh_Thu'].sum()
        mom_pct = ((rev_c - rev_p) / rev_p * 100) if rev_p > 0 else 0
        mom_str = f"Tháng gần nhất ({m_curr}) tăng trưởng **{mom_pct:+.1f}%** so với {m_prev}."
    else:
        mom_str = "Cần tối thiểu 2 tháng dữ liệu để đánh giá tốc độ tăng trưởng MoM."

    st.markdown(f"""
    <div class="exec-summary-box">
        <h4>💡 BÁO CÁO NHANH DÀNH CHO CEO / HỘI ĐỒNG QUẢN TRỊ (30 SECONDS BRIEF)</h4>
        <ul>
            <li><b>Quy mô báo cáo:</b> Tổng Doanh Thu <b>{total_rev/1e9:,.2f} Tỷ VNĐ</b> | Tổng Sản Lượng <b>{total_vol:,.0f} Bao</b> trên <b>{total_npp} NPP</b> & <b>{total_sku} Dòng Sản Phẩm</b>.</li>
            <li><b>Địa bàn & Đối tác Cốt lõi:</b> Địa bàn tăng trưởng lớn nhất là <b>{top_region}</b>; NPP đóng góp doanh thu kỷ lục là <b>{top_npp}</b>.</li>
            <li><b>Biến động Chu kỳ:</b> {mom_str}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # KPIS METRICS BAR
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Doanh Thu Tổng", f"{total_rev/1e9:,.2f} Tỷ VNĐ")
    k2.metric("Sản Lượng Tổng", f"{total_vol:,.0f} Bao")
    k3.metric("Số Nhà Phân Phối Active", f"{total_npp} KH")
    k4.metric("Danh Mục SKU Tiêu Thụ", f"{total_sku} Dòng SP")

    st.markdown("---")

    # ---------------------------------------------------------
    # 5. HỆ THỐNG 4 GÓC NHÌN BỔ SUNG DÀNH CHO CEO & CẢNH BÁO
    # ---------------------------------------------------------
    st.subheader("🎯 4 GÓC NHÌN QUẢN TRỊ CHIẾN LƯỢC DÀNH CHO BAN GIÁM ĐỐC")
    
    v_tab1, v_tab2, v_tab3, v_tab4 = st.tabs([
        "1️⃣ Ma Trận SP - Địa Bàn", 
        "2️⃣ Cơ Cấu Portfolio / Mã_KH", 
        "3️⃣ Phân Hạng Pareto 3D (ABC)", 
        "4️⃣ Cảnh Báo Rủi Ro & Ghi Chú CEO"
    ])

    # GÓC NHÌN 1: MA TRẬN SẢN PHẨM - ĐỊA BÀN TIÊU THỤ (HEATMAP MATRIX)
    with v_tab1:
        st.markdown("##### 🗺️ Ma Trận Phủ Sản Phẩm x Địa Bàn Tiêu Thụ (Territory x SKU Matrix)")
        st.caption("Giúp CEO phát hiện ngay 'đốm trắng' thị trường (vùng đất trống) và các địa bàn đang bị lệch cơ cấu sản phẩm.")
        
        matrix_df = df_filtered.pivot_table(
            index='Dia_Ban_Tieu_Thu', 
            columns='Ten_SP', 
            values=unit_choice, 
            aggfunc='sum'
        ).fillna(0)

        if not matrix_df.empty:
            # Heatmap Plotly
            fig_matrix = px.imshow(
                matrix_df,
                text_auto='.2s' if unit_choice == 'Doanh_Thu' else ',.0f',
                aspect="auto",
                color_continuous_scale="YlGnBu",
                labels=dict(x="Dòng Sản Phẩm", y="Địa Bàn / Tỉnh", color=unit_label)
            )
            fig_matrix.update_layout(height=450)
            st.plotly_chart(fig_matrix, use_container_width=True)

            # Bảng ma trận chi tiết
            st.markdown("**Bảng Chi Tiết Giá Trị Ma Trận:**")
            st.dataframe(matrix_df.style.format("{:,.0f}").background_gradient(cmap="Blues", axis=None), use_container_width=True)
        else:
            st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại.")

    # GÓC NHÌN 2: CƠ CẤU DÒNG SẢN PHẨM THEO MÃ_KH (PORTFOLIO DIVERSIFICATION)
    with v_tab2:
        st.markdown("##### 🧩 Cơ Cấu Portfolio Dòng Sản Phẩm Của Từng Nhà Phân Phối")
        st.caption("Đánh giá mức độ đa dạng hóa mặt hàng của các KH. Tránh tình trạng NPP chỉ bán 1 sản phẩm truyền thống mà bỏ qua sản phẩm chiến lược.")
        
        # Chọn top bao nhiêu NPP để hiển thị
        top_n_npp = st.slider("Hiển thị Top Nhà Phân Phối lớn nhất:", min_value=5, max_value=30, value=10)
        
        top_npp_list = df_filtered.groupby('Thuyet_Minh_NPP')[unit_choice].sum().nlargest(top_n_npp).index
        df_top_npp = df_filtered[df_filtered['Thuyet_Minh_NPP'].isin(top_npp_list)]
        
        # Stacked Bar Chart 100%
        npp_prod_pivot = df_top_npp.pivot_table(index='Thuyet_Minh_NPP', columns='Ten_SP', values=unit_choice, aggfunc='sum').fillna(0)
        
        fig_stack = px.bar(
            df_top_npp, 
            y='Thuyet_Minh_NPP', 
            x=unit_choice, 
            color='Ten_SP', 
            orientation='h',
            title=f"Tỷ Trọng Dòng Sản Phẩm Của Top {top_n_npp} NPP",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_stack.update_layout(height=500, barmode='stack', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_stack, use_container_width=True)

    # GÓC NHÌN 3: PHÂN HẠNG PARETO 3D (ABC ANALYSIS)
    with v_tab3:
        st.markdown("##### ⚖️ Phân Hạng Pareto ABC (Tỷ Trọng Doanh Thu, Sản Lượng & Độ Phủ SKU)")
        st.caption("Phân hạng khách hàng theo nguyên lý 80/20: Nhóm A (Đóng góp ~80%), Nhóm B (~15%), Nhóm C (~5%).")

        pareto_df = df_filtered.groupby('Thuyet_Minh_NPP').agg(
            Total_Val=('Doanh_Thu', 'sum'),
            Total_Vol=('San_Luong', 'sum'),
            SKU_Coverage=('Ten_SP', 'nunique')
        ).reset_index()

        if not pareto_df.empty:
            pareto_df = pareto_df.sort_values(by='Total_Val', ascending=False)
            pareto_df['Cum_Val'] = pareto_df['Total_Val'].cumsum()
            total_sum = pareto_df['Total_Val'].sum()
            pareto_df['Cum_Pct'] = (pareto_df['Cum_Val'] / total_sum * 100) if total_sum > 0 else 0

            def assign_abc(pct):
                if pct <= 80: return 'A (Core - Top 80%)'
                elif pct <= 95: return 'B (Potential - Next 15%)'
                else: return 'C (Long Tail - Last 5%)'

            pareto_df['Phan_Hang'] = pareto_df['Cum_Pct'].apply(assign_abc)

            # Dual Axis Pareto Chart
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(
                x=pareto_df['Thuyet_Minh_NPP'], 
                y=pareto_df['Total_Val'], 
                name="Doanh Thu",
                marker_color='#1e3a8a'
            ))
            fig_pareto.add_trace(go.Scatter(
                x=pareto_df['Thuyet_Minh_NPP'], 
                y=pareto_df['Cum_Pct'], 
                name="Tích Luỹ %",
                yaxis="y2",
                line=dict(color='#ef4444', width=3)
            ))
            fig_pareto.update_layout(
                title="Biểu Đồ Đường Tích Luỹ Pareto 80/20",
                yaxis=dict(title="Doanh Thu (VNĐ)"),
                yaxis2=dict(title="Tích Luỹ (%)", overlaying="y", side="right", range=[0, 105]),
                height=450,
                showlegend=True
            )
            st.plotly_chart(fig_pareto, use_container_width=True)

            # Summary phân hạng
            abc_summary = pareto_df.groupby('Phan_Hang').agg(
                So_NPP=('Thuyet_Minh_NPP', 'count'),
                Tong_Doanh_Thu=('Total_Val', 'sum'),
                SKU_Phu_Trung_Binh=('SKU_Coverage', 'mean')
            ).reset_index()
            
            st.markdown("**Bảng Tổng Hợp Phân Hạng Nhóm Khách Hàng (ABC):**")
            st.dataframe(abc_summary.style.format({
                'Tong_Doanh_Thu': '{:,.0f}',
                'SKU_Phu_Trung_Binh': '{:.1f}'
            }), use_container_width=True)

    # GÓC NHÌN 4: CẢNH BÁO RỦI RO & GHI CHÚ CHO CEO
    with v_tab4:
        st.markdown("##### 🚨 ĐỘNG CƠ CẢNH BÁO RỦI RO TỰ ĐỘNG (AUTOMATED EXECUTIVE ALERT ENGINE)")
        st.caption("Các cảnh báo được hệ thống tính toán tự động dựa trên thuật toán quản trị rủi ro tập đoàn.")

        # Compute Risk Indices
        npp_sales = df_filtered.groupby('Thuyet_Minh_NPP')['Doanh_Thu'].sum().sort_values(ascending=False)
        top3_share = (npp_sales.head(3).sum() / total_rev * 100) if total_rev > 0 else 0
        
        # Single SKU NPPs
        npp_sku_cnt = df_filtered.groupby('Thuyet_Minh_NPP')['Ten_SP'].nunique()
        single_sku_npps = npp_sku_cnt[npp_sku_cnt == 1]

        # MoM Decline NPPs
        decline_npps = []
        if len(m_list) >= 2:
            m_latest, m_prev = m_list[-1], m_list[-2]
            piv_m = df_filtered.pivot_table(index='Thuyet_Minh_NPP', columns='Thang', values='Doanh_Thu', aggfunc='sum').fillna(0)
            if m_latest in piv_m.columns and m_prev in piv_m.columns:
                piv_m['Growth'] = (piv_m[m_latest] - piv_m[m_prev]) / piv_m[m_prev].replace(0, np.nan) * 100
                decline_npps = piv_m[piv_m['Growth'] < -20].index.tolist()

        # Alert 1: Concentration Risk
        if top3_share > 50:
            st.markdown(f"""
            <div class="alert-card-danger">
                <b>🚨 CẢNH BÁO 1: MỨC ĐỘ TẬP TRUNG DOANH THU CAO BÁO ĐỘNG (Concentration Risk)</b><br>
                Top 3 Nhà Phân Phối lớn nhất đang chiếm tới <b>{top3_share:.1f}%</b> tổng doanh thu tập đoàn. 
                <i>Khuyến nghị CEO:</i> Cần có chính sách mở rộng kênh phân phối nhóm B/C để giảm thiểu rủi ro khi một trong các NPP lớn dừng hợp tác.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-card-info">
                <b>✅ AN TOÀN TẬP TRUNG:</b> Top 3 NPP chiếm <b>{top3_share:.1f}%</b> doanh thu (Mức an toàn < 50%).
            </div>
            """, unsafe_allow_html=True)

        # Alert 2: MoM Drop
        if len(decline_npps) > 0:
            st.markdown(f"""
            <div class="alert-card-warning">
                <b>⚠️ CẢNH BÁO 2: NGUY CƠ SỤT GIẢM DOANH SỐ NẶNG (>20% MoM)</b><br>
                Phát hiện <b>{len(decline_npps)} Nhà Phân Phối</b> có mức sụt giảm doanh số trên 20% ở tháng gần nhất:
                <br><code>{", ".join(decline_npps[:5])}</code> {'...' if len(decline_npps) > 5 else ''}<br>
                <i>Hành động ngay:</i> Yêu cầu Giám đốc Bán hàng (RSM) làm việc trực tiếp để tìm nguyên nhân (chiết khấu, tồn kho, đối thủ cạnh tranh).
            </div>
            """, unsafe_allow_html=True)

        # Alert 3: Single SKU Reliance
        if len(single_sku_npps) > 0:
            st.markdown(f"""
            <div class="alert-card-warning">
                <b>⚠️ CẢNH BÁO 3: RỦI RO LỆCH DÒNG SẢN PHẨM (Single-Product Vulnerability)</b><br>
                Có <b>{len(single_sku_npps)} NPP</b> chỉ tiêu thụ duy nhất 1 mặt hàng (không phát sinh mặt hàng thứ 2).
                <br><i>Hành động ngay:</i> Áp dụng chương trình Combi-sell (bán kèm sản phẩm mới) với chính sách thưởng bổ sung.
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # 6. PHÂN TÍCH TỔNG THỂ & CHI TIẾT THEO CÁC THÁNG (MONTHLY TRENDS)
    # ---------------------------------------------------------
    st.subheader("📈 PHÂN TÍCH DIỄN BIẾN & BIẾN ĐỘNG THEO THÁNG")
    
    trend_type = st.radio("Góc nhìn biến động chu kỳ theo:", ["Dòng Sản Phẩm", "Địa Bàn / Tỉnh", "Top 5 Nhà Phân Phối"], horizontal=True)
    
    if trend_type == "Dòng Sản Phẩm":
        trend_df = df_filtered.groupby(['Thang', 'Ten_SP'])[unit_choice].sum().reset_index()
        fig_trend = px.line(trend_df, x='Thang', y=unit_choice, color='Ten_SP', markers=True, 
                            title=f"Xu Hướng {unit_label} Các Dòng Sản Phẩm Qua Các Tháng")
    elif trend_type == "Địa Bàn / Tỉnh":
        trend_df = df_filtered.groupby(['Thang', 'Dia_Ban_Tieu_Thu'])[unit_choice].sum().reset_index()
        fig_trend = px.line(trend_df, x='Thang', y=unit_choice, color='Dia_Ban_Tieu_Thu', markers=True,
                            title=f"Xu Hướng {unit_label} Các Địa Bàn Tiêu Thụ Qua Các Tháng")
    else:
        top5_npps = df_filtered.groupby('Thuyet_Minh_NPP')[unit_choice].sum().nlargest(5).index
        df_top5 = df_filtered[df_filtered['Thuyet_Minh_NPP'].isin(top5_npps)]
        trend_df = df_top5.groupby(['Thang', 'Thuyet_Minh_NPP'])[unit_choice].sum().reset_index()
        fig_trend = px.line(trend_df, x='Thang', y=unit_choice, color='Thuyet_Minh_NPP', markers=True,
                            title=f"Xu Hướng {unit_label} Top 5 NPP Qua Các Tháng")

    fig_trend.update_layout(height=450)
    st.plotly_chart(fig_trend, use_container_width=True)

    # ---------------------------------------------------------
    # 7. CHI TIẾT DỮ LIỆU & TRÍCH XUẤT FILE EXCEL
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 BẢNG DỮ LIỆU CHI TIẾT & XUẤT BÁO CÁO")
    
    st.dataframe(df_filtered[['Thang', 'Ma_KH', 'Thuyet_Minh_NPP', 'Dia_Ban_Tieu_Thu', 'Ten_SP', 'San_Luong', 'Doanh_Thu']], use_container_width=True)
    
    output_buffer = io.BytesIO()
    with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Sales_Executive_Report')
        if 'pareto_df' in locals():
            pareto_df.to_excel(writer, index=False, sheet_name='Pareto_ABC_Analysis')
        if 'matrix_df' in locals() and not matrix_df.empty:
            matrix_df.to_excel(writer, sheet_name='Product_Region_Matrix')

    st.download_button(
        label="📥 Tải Xuất Toàn Bộ Báo Cáo Excel Nâng Cao (.xlsx)",
        data=output_buffer.getvalue(),
        file_name="KTC_Executive_Sales_Analytics_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👋 Vui lòng tải lên file **Master Danh Mục** và **Các File Sản Lượng Tháng** ở bảng điều khiển bên trái để kích hoạt Báo cáo C-Suite Executive.")
