import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as io_plotly
import re
import unicodedata
import io

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG & CUSTOM CSS (SCROLLABLE DASHBOARD)
# ---------------------------------------------------------
st.set_page_config(
    page_title="KTC Executive Sales Dashboard",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho thẻ Khối (Card Container) & Box Tóm tắt 30s
st.markdown("""
<style>
    .exec-summary-box {
        background-color: #f8f9fa;
        border-left: 5px solid #1e3a8a;
        padding: 18px 22px;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .risk-warning {
        color: #dc2626;
        font-weight: bold;
    }
    .risk-safe {
        color: #16a34a;
        font-weight: bold;
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
# 2. XỬ LÝ DỮ LIỆU & CACHING (@st.cache_data)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def process_data(file_dm_bytes, files_sl_tuples):
    # Đọc file Danh mục Master
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
    
    # Tổng hợp các File Sản lượng
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
    
    # Merge theo Mã_KH & Tạo cột thuyết minh
    df_merged = pd.merge(df_all_sales, df_dm_clean, on='Ma_KH', how='left')
    df_merged['Ten_NPP_Khai_Bao'] = df_merged['Ten_NPP_Master'].fillna(df_merged['Ten_NPP_File'])
    df_merged['Thuyet_Minh_NPP'] = "[" + df_merged['Ma_KH'] + "] - " + df_merged['Ten_NPP_Khai_Bao']
    df_merged['Dia_Ban_Tieu_Thu'] = df_merged['Dia_Ban_Master'].fillna('Chưa phân vùng')
    
    return df_merged

# ---------------------------------------------------------
# 3. SIDEBAR - UPLOAD & FILTERS
# ---------------------------------------------------------
st.sidebar.title("🏢 KTC EXECUTIVE PORTAL")
file_dm = st.sidebar.file_uploader("1. File Danh mục Master (.xlsx)", type=["xlsx"])
files_sl = st.sidebar.file_uploader("2. Các File Sản lượng (.xlsx)", type=["xlsx"], accept_multiple_files=True)

if file_dm and files_sl:
    # Convert file objects to bytes for st.cache_data compatibility
    dm_bytes = io.BytesIO(file_dm.read())
    sl_tuples = [(f.name, io.BytesIO(f.read())) for f in files_sl]
    
    with st.spinner("⚡ Caching & Processing Executive Dashboard..."):
        df = process_data(dm_bytes, sl_tuples)

    # Global Filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Bộ Lọc Quản Trị")
    all_months = sorted(df['Thang'].unique())
    selected_months = st.sidebar.multiselect("Tháng Báo Cáo", options=all_months, default=all_months)
    
    all_regions = sorted(df['Dia_Ban_Tieu_Thu'].unique())
    selected_regions = st.sidebar.multiselect("Địa Bàn / Tỉnh", options=all_regions, default=all_regions)

    # Filtered dataset
    df_filtered = df[(df['Thang'].isin(selected_months)) & (df['Dia_Ban_Tieu_Thu'].isin(selected_regions))]

    # ---------------------------------------------------------
    # 4. TÓM TẮT ĐIỀU HÀNH 30 GIÂY (EXECUTIVE SUMMARY BOX)
    # ---------------------------------------------------------
    st.title("📈 BÁO CÁO QUẢN TRỊ KINH DOANH & SẢN LƯỢNG")
    
    # Tính toán thông số cho Box 30s
    top_region = df_filtered.groupby('Dia_Ban_Tieu_Thu')['Doanh_Thu'].sum().idxmax()
    top_npp = df_filtered.groupby('Thuyet_Minh_NPP')['Doanh_Thu'].sum().idxmax()
    
    # Tăng trưởng / Sụt giảm theo tháng gần nhất
    months_list = sorted(df_filtered['Thang'].unique())
    if len(months_list) >= 2:
        m_curr, m_prev = months_list[-1], months_list[-2]
        rev_curr = df_filtered[df_filtered['Thang'] == m_curr]['Doanh_Thu'].sum()
        rev_prev = df_filtered[df_filtered['Thang'] == m_prev]['Doanh_Thu'].sum()
        mom_growth = ((rev_curr - rev_prev) / rev_prev) * 100 if rev_prev > 0 else 0
        mom_text = f"Doanh thu **{m_curr}** biến động **{mom_growth:+.1f}%** so với {m_prev}."
    else:
        mom_text = "Cần tối thiểu 2 tháng dữ liệu để phân tích biến động MoM."

    st.markdown(f"""
    <div class="exec-summary-box">
        <h4>💡 TÓM TẮT ĐIỀU HÀNH 30 GIÂY (EXECUTIVE SUMMARY)</h4>
        <ul>
            <li><b>Địa bàn trọng điểm:</b> <b>{top_region}</b> dẫn đầu doanh số trong kỳ phân tích.</li>
            <li><b>Đối tác lớn nhất:</b> <b>{top_npp}</b> đóng góp doanh thu cao nhất.</li>
            <li><b>Xu hướng tăng trưởng:</b> {mom_text}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 5. CHỈ SỐ CỐT LÕI (KPIS & CONCENTRATION RISK)
    # ---------------------------------------------------------
    total_rev = df_filtered['Doanh_Thu'].sum()
    total_vol = df_filtered['San_Luong'].sum()
    
    # Concentration Risk Index (Top 3 / Top 5)
    npp_rev_series = df_filtered.groupby('Thuyet_Minh_NPP')['Doanh_Thu'].sum().sort_values(ascending=False)
    top3_pct = (npp_rev_series.head(3).sum() / total_rev * 100) if total_rev > 0 else 0
    top5_pct = (npp_rev_series.head(5).sum() / total_rev * 100) if total_rev > 0 else 0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Doanh Thu Tổng", f"{total_rev/1e9:,.2f} Tỷ VNĐ")
    kpi2.metric("Sản Lượng Tổng", f"{total_vol:,.0f} Bao")
    
    risk_color = "risk-warning" if top3_pct > 60 else "risk-safe"
    kpi3.markdown(f"""
    <div class="metric-card">
        <small>Mức Độ Tập Trung (Top 3 NPP)</small>
        <h3 class="{risk_color}">{top3_pct:.1f}%</h3>
        <small>{'⚠️ Rủi ro phụ thuộc lớn' if top3_pct > 60 else '✅ Phân bổ an toàn'}</small>
    </div>
    """, unsafe_allow_html=True)

    kpi4.markdown(f"""
    <div class="metric-card">
        <small>Đóng Góp Top 5 NPP</small>
        <h3>{top5_pct:.1f}%</h3>
        <small>Tổng cộng {len(npp_rev_series)} Nhà phân phối</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # 6. ĐỔI ĐƠN VỊ & BIỂU ĐỒ TƯƠNG TÁC (DYNAMIC CONTROLS)
    # ---------------------------------------------------------
    st.subheader("📊 PHÂN TÍCH TƯƠNG TÁC ĐA TẦNG")
    
    unit_choice = st.radio("Đơn vị hiển thị trên Biểu đồ:", ["Doanh_Thu", "San_Luong"], horizontal=True, format_func=lambda x: "Doanh Thu (VNĐ)" if x == "Doanh_Thu" else "Sản Lượng (Bao)")
    
    c_left, c_right = st.columns(2)
    
    with c_left:
        st.markdown("**Top 10 Nhà Phân Phối Lớn Nhất**")
        top_10_df = df_filtered.groupby('Thuyet_Minh_NPP')[unit_choice].sum().nlargest(10).reset_index()
        fig_top10 = px.bar(top_10_df, x=unit_choice, y='Thuyet_Minh_NPP', orientation='h', text_auto=',.0f', color=unit_choice, color_continuous_scale='Blues')
        fig_top10.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=400)
        st.plotly_chart(fig_top10, use_container_width=True)
        
    with c_right:
        st.markdown("**Cơ Cấu Doanh Số Theo Địa Bàn / Tỉnh**")
        region_df = df_filtered.groupby('Dia_Ban_Tieu_Thu')[unit_choice].sum().reset_index()
        fig_region = px.pie(region_df, values=unit_choice, names='Dia_Ban_Tieu_Thu', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_region.update_layout(height=400)
        st.plotly_chart(fig_region, use_container_width=True)

    # ---------------------------------------------------------
    # 7. PHÂN TÍCH CHUYÊN SÂU (TABS)
    # ---------------------------------------------------------
    tab_health, tab_drill, tab_export = st.tabs(["🩺 Sức Khỏe NPP & Rủi Ro", "🔍 Soi Sâu 360° (Drill-down)", "📋 Bảng Dữ Liệu & Xuất File"])

    # TAB 1: SỨC KHỎE NPP
    with tab_health:
        st.subheader("Phân Loại Sức Khỏe Nhà Phân Phối (MoM)")
        if len(months_list) >= 2:
            m_latest, m_prev = months_list[-1], months_list[-2]
            piv = df_filtered.pivot_table(index='Thuyet_Minh_NPP', columns='Thang', values=unit_choice, aggfunc='sum').fillna(0)
            piv['Tăng_Trưởng_%'] = ((piv[m_latest] - piv[m_prev]) / piv[m_prev].replace(0, np.nan)) * 100
            
            def get_health(row):
                if row[m_latest] == 0:
                    return '🔴 Ngừng phát sinh'
                elif row['Tăng_Trưởng_%'] < -15:
                    return '⚠️ Suy giảm nặng (>15%)'
                elif row['Tăng_Trưởng_%'] < 0:
                    return '🟡 Suy giảm nhẹ'
                else:
                    return '🟢 Tăng trưởng tốt'
                    
            piv['Trạng_Thái'] = piv.apply(get_health, axis=1)
            st.dataframe(piv[[m_prev, m_latest, 'Tăng_Trưởng_%', 'Trạng_Thái']].sort_values(by='Tăng_Trưởng_%'), use_container_width=True)
        else:
            st.warning("Cần ít nhất 2 tháng dữ liệu để lập bảng theo dõi sức khỏe NPP.")

    # TAB 2: DRILL-DOWN 360°
    with tab_drill:
        st.subheader("Soi Sâu Chi Tiết Từng Đối Tác")
        selected_npp_single = st.selectbox("Chọn Nhà Phân Phối Cần Kiểm Tra:", options=sorted(df_filtered['Thuyet_Minh_NPP'].unique()))
        
        df_single = df_filtered[df_filtered['Thuyet_Minh_NPP'] == selected_npp_single]
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.markdown(f"**Diễn biến Doanh số theo Tháng của `{selected_npp_single}`**")
            trend_df = df_single.groupby('Thang')[unit_choice].sum().reset_index()
            fig_trend = px.line(trend_df, x='Thang', y=unit_choice, markers=True, text=unit_choice)
            fig_trend.update_traces(textposition="top center")
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with d_col2:
            st.markdown(f"**Cơ cấu Sản phẩm Tiêu thụ**")
            prod_df = df_single.groupby('Ten_SP')[unit_choice].sum().reset_index()
            fig_prod = px.bar(prod_df, x=unit_choice, y='Ten_SP', orientation='h', color='Ten_SP')
            st.plotly_chart(fig_prod, use_container_width=True)

    # TAB 3: TRÍCH XUẤT DỮ LIỆU
    with tab_export:
        st.subheader("Dữ Liệu Thô Đã Thuyết Minh")
        st.dataframe(df_filtered[['Thang', 'Ma_KH', 'Thuyet_Minh_NPP', 'Dia_Ban_Tieu_Thu', 'Ten_SP', 'San_Luong', 'Doanh_Thu']], use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Data_Thuong_Mai')
            
        st.download_button(
            label="📥 Tải Báo Cáo Xuất Excel (.xlsx)",
            data=output.getvalue(),
            file_name="Bao_Cao_Sot_Sieu_NPP_KTC.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("👋 Vui lòng tải lên file **Danh mục Master** và **File Sản lượng** tại thanh bên trái để khởi tạo Báo cáo Quản trị.")
