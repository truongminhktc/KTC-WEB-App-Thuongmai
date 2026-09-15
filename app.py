import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import unicodedata
import io

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG & DESIGN SYSTEM CHUẨN C-SUITE
# ---------------------------------------------------------
st.set_page_config(
    page_title="KTC C-Suite Strategic Executive Analytics",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Master Executive Dark Theme (Obsidian Glassmorphism)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Canvas Background */
    .stApp {
        background-color: #080c14;
        color: #f3f4f6;
    }

    /* Executive Header Banner */
    .csuite-header {
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.25);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
    }
    .csuite-header h2 {
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0 0 6px 0;
        font-size: 1.65rem;
    }
    .csuite-header p {
        color: #94a3b8;
        margin: 0;
        font-size: 0.9rem;
        font-weight: 500;
    }

    /* Executive Insight Glass Box */
    .ceo-box {
        background: linear-gradient(135deg, rgba(19, 28, 49, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
        border-left: 4px solid #38bdf8;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 28px;
        box-shadow: 0 12px 32px -10px rgba(0,0,0,0.5);
    }
    .ceo-title {
        color: #38bdf8;
        font-weight: 700;
        font-size: 0.98rem;
        margin-bottom: 10px;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }
    .ceo-content {
        color: #cbd5e1;
        font-size: 0.92rem;
        line-height: 1.65;
    }

    /* KPI Glass Cards with Hover Elevation */
    .kpi-card {
        background: rgba(17, 24, 39, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 12px 28px -5px rgba(56, 189, 248, 0.15);
    }
    .kpi-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        font-weight: 700;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #f8fafc;
        margin: 6px 0;
        letter-spacing: -0.02em;
    }
    .kpi-sub {
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Redesigned Streamlit Tab Bar */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.7);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 600;
        font-size: 0.88rem;
        border: none !important;
        padding: 0 18px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    /* Quadrant Strategic Cards */
    .quad-card {
        background: rgba(30, 41, 59, 0.7);
        border-radius: 10px;
        padding: 14px 16px;
        border-top: 3px solid #64748b;
        margin-bottom: 12px;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #0d1322;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MASTER DESIGN SYSTEM PLOTLY
# ---------------------------------------------------------
EXECUTIVE_PALETTE = ['#38bdf8', '#34d399', '#fbbf24', '#818cf8', '#f87171', '#a78bfa', '#f472b6']

DARK_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#cbd5e1', family="Plus Jakarta Sans, sans-serif", size=12),
    xaxis=dict(
        showgrid=False, 
        zeroline=False, 
        color='#94a3b8', 
        tickfont=dict(size=11, color='#94a3b8')
    ),
    yaxis=dict(
        showgrid=True, 
        gridcolor='rgba(255,255,255,0.06)', 
        zeroline=False, 
        color='#94a3b8', 
        tickfont=dict(size=11, color='#94a3b8')
    ),
    hoverlabel=dict(
        bgcolor='#0f172a',
        font_size=12,
        font_family="Plus Jakarta Sans, sans-serif",
        font_color="#f8fafc",
        bordercolor='#38bdf8'
    ),
    margin=dict(l=20, r=20, t=40, b=30)
)

def normalize_text(text):
    if not isinstance(text, str): return ""
    text = text.replace('_', ' ')
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    return text.lower().strip()

# ---------------------------------------------------------
# 2. XỬ LÝ DỮ LIỆU CHUẨN HÓA
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
    df_merged['Thuyet_Minh_NPP'] = "[" + df_merged['Ma_KH'] + "] " + df_merged['Ten_NPP_Khai_Bao']
    df_merged['Dia_Ban_Tieu_Thu'] = df_merged['Dia_Ban_Master'].fillna('Chưa phân vùng')
    
    return df_merged

# ---------------------------------------------------------
# 3. SIDEBAR CONTROLS
# ---------------------------------------------------------
st.sidebar.markdown("<h3 style='color:#38bdf8; font-weight:700;'>🏛️ C-SUITE CONTROLS</h3>", unsafe_allow_html=True)
file_dm = st.sidebar.file_uploader("1. File Danh mục Master (.xlsx)", type=["xlsx"])
files_sl = st.sidebar.file_uploader("2. File Sản lượng Tháng (.xlsx)", type=["xlsx"], accept_multiple_files=True)

if file_dm and files_sl:
    dm_bytes = io.BytesIO(file_dm.read())
    sl_tuples = [(f.name, io.BytesIO(f.read())) for f in files_sl]
    
    with st.spinner("⚡ Đang đồng bộ hệ thống biểu đồ C-Suite..."):
        df = process_data(dm_bytes, sl_tuples)

    st.sidebar.markdown("---")
    st.sidebar.markdown("<h4 style='color:#e2e8f0; font-size:0.95rem; font-weight:700;'>🎯 BỘ LỌC TẦM NHÌN CHIẾN LƯỢC</h4>", unsafe_allow_html=True)
    
    selected_months = st.sidebar.multiselect("Chu kỳ Tháng", options=sorted(df['Thang'].unique()), default=sorted(df['Thang'].unique()))
    selected_regions = st.sidebar.multiselect("Địa Bàn / Tỉnh", options=sorted(df['Dia_Ban_Tieu_Thu'].unique()), default=sorted(df['Dia_Ban_Tieu_Thu'].unique()))

    df_filtered = df[(df['Thang'].isin(selected_months)) & (df['Dia_Ban_Tieu_Thu'].isin(selected_regions))]

    unit_choice = st.sidebar.radio("Đơn vị đo lường:", ["Doanh_Thu", "San_Luong"], format_func=lambda x: "Doanh Thu (VNĐ)" if x == "Doanh_Thu" else "Sản Lượng (Bao)")

    # ---------------------------------------------------------
    # 4. DASHBOARD HEADER & EXECUTIVE KPI CARDS
    # ---------------------------------------------------------
    st.markdown("""
    <div class="csuite-header">
        <h2>🏛️ BÁO CÁO QUẢN TRỊ CHIẾN LƯỢC C-SUITE</h2>
        <p>Hệ thống hỗ trợ ra quyết định: Thị trường x Sản phẩm x Năng lực Nhà Phân Phối</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    total_rev = df_filtered['Doanh_Thu'].sum()
    total_vol = df_filtered['San_Luong'].sum()
    active_npp = df_filtered['Ma_KH'].nunique()
    active_sku = df_filtered['Ten_SP'].nunique()

    c1.markdown(f"""<div class="kpi-card"><div class="kpi-title">TỔNG DOANH THU</div><div class="kpi-value">{total_rev/1e9:,.2f} Tỷ</div><div class="kpi-sub" style="color:#10b981;">VNĐ</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="kpi-card"><div class="kpi-title">TỔNG SẢN LƯỢNG</div><div class="kpi-value">{total_vol:,.0f}</div><div class="kpi-sub" style="color:#38bdf8;">Bao</div></div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="kpi-card"><div class="kpi-title">SỐ NPP ACTIVE</div><div class="kpi-value">{active_npp}</div><div class="kpi-sub" style="color:#94a3b8;">Khách hàng</div></div>""", unsafe_allow_html=True)
    c4.markdown(f"""<div class="kpi-card"><div class="kpi-title">DANH MỤC SKU ACTIVE</div><div class="kpi-value">{active_sku}</div><div class="kpi-sub" style="color:#f59e0b;">SKU</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 5. KHỐI NHẬN ĐỊNH CEO
    # ---------------------------------------------------------
    top_region = df_filtered.groupby('Dia_Ban_Tieu_Thu')['Doanh_Thu'].sum().idxmax() if not df_filtered.empty else "N/A"
    top_region_rev = df_filtered.groupby('Dia_Ban_Tieu_Thu')['Doanh_Thu'].sum().max() if not df_filtered.empty else 0
    top_region_pct = (top_region_rev / total_rev * 100) if total_rev > 0 else 0

    top3_npp_rev = df_filtered.groupby('Thuyet_Minh_NPP')['Doanh_Thu'].sum().nlargest(3).sum() if not df_filtered.empty else 0
    top3_npp_pct = (top3_npp_rev / total_rev * 100) if total_rev > 0 else 0

    st.markdown(f"""
    <div class="ceo-box">
        <div class="ceo-title">💡 NHẬN ĐỊNH ĐIỀU HÀNH CẤP CAO (EXECUTIVE SUMMARY & CEO DIRECTIVES)</div>
        <div class="ceo-content">
            • <b>Tập trung thị trường:</b> Địa bàn <b>{top_region}</b> đang đóng góp lớn nhất với <b>{top_region_rev/1e9:,.2f} tỷ VNĐ</b> (chiếm <b>{top_region_pct:.1f}%</b> tổng doanh số).<br>
            • <b>Rủi ro kênh phân phối:</b> Top 3 Nhà Phân Phối nắm giữ <b>{top3_npp_pct:.1f}%</b> tổng doanh thu. Cần có chính sách quản trị công nợ linh hoạt.<br>
            • <b>Định hướng danh mục:</b> Tập trung Marketing nhóm <b>Ngôi Sao</b> và kiểm soát dòng tiền ở nhóm <b>Bò Sữa</b>. Rà soát loại bỏ SKU <b>Yếu Kém</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 6. THẺ TABS CHIẾN LƯỢC
    # ---------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 1. Ma Trận BCG & Chỉ Đạo Sản Phẩm",
        "🗺️ 2. Phân Bổ Thị Trường & Địa Bàn",
        "📈 3. Xu Hướng Tăng Trưởng SKU",
        "🏆 4. Năng Lực & Rủi Ro Kênh NPP",
        "📋 5. Lộ Trình CEO & Dữ Liệu Chi Tiết"
    ])

    # ---------------------------------------------------------
    # TAB 1: MA TRẬN BCG
    # ---------------------------------------------------------
    with tab1:
        st.markdown("##### 🎯 Ma Trận Tăng Trưởng BCG")
        st.caption("💡 *Rê chuột vào từng điểm để xem Tên sản phẩm & Thị trường.*")

        bcg_df = df_filtered.groupby(['Dia_Ban_Tieu_Thu', 'Ten_SP']).agg(
            Revenue=('Doanh_Thu', 'sum'),
            Volume=('San_Luong', 'sum')
        ).reset_index()

        if not bcg_df.empty:
            avg_rev = bcg_df['Revenue'].mean()
            avg_vol = bcg_df['Volume'].mean()

            def classify(row):
                if row['Revenue'] >= avg_rev and row['Volume'] >= avg_vol: return '🌟 Ngôi Sao'
                elif row['Revenue'] >= avg_rev: return '🐄 Bò Sữa'
                elif row['Volume'] >= avg_vol: return '❓ Dấu Hỏi'
                else: return '⚠️ Yếu Kém'

            bcg_df['Phan_Loai'] = bcg_df.apply(classify, axis=1)

            fig_bcg = px.scatter(
                bcg_df, x='Volume', y='Revenue', color='Phan_Loai',
                hover_name='Ten_SP', hover_data={'Dia_Ban_Tieu_Thu': True, 'Revenue': ':,', 'Volume': ':,'},
                color_discrete_map={
                    '🌟 Ngôi Sao': '#38bdf8',
                    '🐄 Bò Sữa': '#34d399',
                    '❓ Dấu Hỏi': '#fbbf24',
                    '⚠️ Yếu Kém': '#f87171'
                }
            )
            fig_bcg.add_hline(y=avg_rev, line_dash="dash", line_color="#64748b", annotation_text="TB Doanh Thu")
            fig_bcg.add_vline(x=avg_vol, line_dash="dash", line_color="#64748b", annotation_text="TB Sản Lượng")
            fig_bcg.update_traces(marker=dict(size=14, opacity=0.88, line=dict(width=1.5, color='#ffffff')))
            fig_bcg.update_layout(**DARK_LAYOUT, height=430, legend_title_text="Phân Loại BCG")
            st.plotly_chart(fig_bcg, use_container_width=True)

            st.markdown("---")
            st.markdown("##### 📌 Bảng Báo Cáo Phân Lớp & Chỉ Đạo Từ CEO")
            
            col_s, col_m, col_q, col_d = st.columns(4)
            with col_s:
                st.markdown("<div class='quad-card' style='border-color:#38bdf8;'><b style='color:#38bdf8;'>🌟 NGUỒN LỰC TĂNG TRƯỞNG (NGÔI SAO)</b></div>", unsafe_allow_html=True)
                st.dataframe(bcg_df[bcg_df['Phan_Loai'] == '🌟 Ngôi Sao'][['Ten_SP', 'Revenue']], hide_index=True, use_container_width=True)

            with col_m:
                st.markdown("<div class='quad-card' style='border-color:#34d399;'><b style='color:#34d399;'>🐄 DÒNG TIỀN CHỦ LỰC (BÒ SỮA)</b></div>", unsafe_allow_html=True)
                st.dataframe(bcg_df[bcg_df['Phan_Loai'] == '🐄 Bò Sữa'][['Ten_SP', 'Revenue']], hide_index=True, use_container_width=True)

            with col_q:
                st.markdown("<div class='quad-card' style='border-color:#fbbf24;'><b style='color:#fbbf24;'>❓ CƠ HỘI ĐỘT PHÁ (DẤU HỎI)</b></div>", unsafe_allow_html=True)
                st.dataframe(bcg_df[bcg_df['Phan_Loai'] == '❓ Dấu Hỏi'][['Ten_SP', 'Revenue']], hide_index=True, use_container_width=True)

            with col_d:
                st.markdown("<div class='quad-card' style='border-color:#f87171;'><b style='color:#f87171;'>⚠️ NGUY CƠ LÃNG PHÍ (YẾU KÉM)</b></div>", unsafe_allow_html=True)
                st.dataframe(bcg_df[bcg_df['Phan_Loai'] == '⚠️ Yếu Kém'][['Ten_SP', 'Revenue']], hide_index=True, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 2: PHÂN BỔ THỊ TRƯỜNG
    # ---------------------------------------------------------
    with tab2:
        st.markdown("##### 🗺️ Biểu Đồ Cây Phân Cấp Thị Trường (Treemap)")
        
        tree_df = df_filtered.groupby(['Dia_Ban_Tieu_Thu', 'Ten_SP'])[unit_choice].sum().reset_index()
        tree_df = tree_df[tree_df[unit_choice] > 0]

        if not tree_df.empty:
            fig_tree = px.treemap(
                tree_df, path=['Dia_Ban_Tieu_Thu', 'Ten_SP'], values=unit_choice,
                color=unit_choice, 
                color_continuous_scale=[[0, '#0f172a'], [0.5, '#1e3a8a'], [1, '#0284c7']]
            )
            fig_tree.update_traces(textinfo="label+value+percent parent", marker=dict(cornerradius=4))
            fig_tree.update_layout(**DARK_LAYOUT, height=480, coloraxis_showscale=False)
            st.plotly_chart(fig_tree, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 3: XU HƯỚNG TĂNG TRƯỜNG (SỬA LỖI ĐÈ CHỮ TRỤC X)
    # ---------------------------------------------------------
    with tab3:
        st.markdown("##### 📈 Biến Động Chu Kỳ Tăng Trưởng - Top Sản Phẩm Chủ Lực")
        
        top5_skus = df_filtered.groupby('Ten_SP')[unit_choice].sum().nlargest(5).index.tolist()
        selected_display_skus = st.multiselect("Tùy chọn danh mục sản phẩm theo dõi:", options=df_filtered['Ten_SP'].unique(), default=top5_skus)

        trend_df = df_filtered[df_filtered['Ten_SP'].isin(selected_display_skus)].groupby(['Thang', 'Ten_SP'])[unit_choice].sum().reset_index()

        if not trend_df.empty:
            fig_line = px.line(
                trend_df, x='Thang', y=unit_choice, color='Ten_SP', markers=True,
                color_discrete_sequence=EXECUTIVE_PALETTE
            )
            fig_line.update_traces(line=dict(width=3), marker=dict(size=8, symbol='circle'))
            
            # Khắc phục triệt để đè chữ: Chuyển Legend lên vị trí trên cùng biểu đồ (y=1.12)
            layout_trend = DARK_LAYOUT.copy()
            layout_trend['margin'] = dict(l=20, r=20, t=60, b=50)
            fig_line.update_layout(
                **layout_trend, 
                height=450, 
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.12, 
                    xanchor="left", 
                    x=0, 
                    title_text=""
                ),
                xaxis_title="",
                yaxis_title="Doanh Thu (VNĐ)" if unit_choice == "Doanh_Thu" else "Sản Lượng (Bao)"
            )
            st.plotly_chart(fig_line, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 4: NĂNG LỰC & RỦI RO NPP (SỬA LỖI 140G & VỠ NHÃN)
    # ---------------------------------------------------------
    with tab4:
        st.markdown("##### 🏆 Top 15 Nhà Phân Phối Đóng Góp Lớn Nhất")
        
        npp_df = df_filtered.groupby('Thuyet_Minh_NPP')[unit_choice].sum().reset_index()
        npp_df = npp_df.sort_values(by=unit_choice, ascending=True).tail(15)

        # Định dạng nhãn thuần Việt chuẩn C-Suite (Thay thế '140G' thành '140.0 Tỷ')
        if unit_choice == 'Doanh_Thu':
            npp_df['Val_Label'] = npp_df[unit_choice].apply(lambda x: f"{x/1e9:,.1f} Tỷ")
        else:
            npp_df['Val_Label'] = npp_df[unit_choice].apply(lambda x: f"{x:,.0f} Bao")

        npp_df['Short_Name'] = npp_df['Thuyet_Minh_NPP'].apply(lambda x: x[:38] + '...' if len(x) > 38 else x)

        if not npp_df.empty:
            fig_npp = px.bar(
                npp_df, x=unit_choice, y='Short_Name', orientation='h',
                text='Val_Label',
                hover_name='Thuyet_Minh_NPP'
            )
            fig_npp.update_traces(
                marker_color='#38bdf8', 
                marker_line=dict(width=1, color='rgba(255,255,255,0.2)'),
                textposition='outside',
                textfont=dict(color='#cbd5e1', size=11, family="Plus Jakarta Sans")
            )
            layout_npp = DARK_LAYOUT.copy()
            layout_npp['margin'] = dict(l=20, r=80, t=20, b=30)
            fig_npp.update_layout(**layout_npp, height=480, yaxis_title="", xaxis_title="")
            st.plotly_chart(fig_npp, use_container_width=True)

            st.markdown("##### ⚠️ Phân Tích Mức Độ Tập Trung & Rủi Ro Phụ Thuộc (Pareto NPP):")
            st.info(f"Top 3 NPP đóng góp {top3_npp_pct:.1f}% tổng doanh số. Cần đảm bảo hạn mức tín dụng công nợ trong tầm kiểm soát.")

    # ---------------------------------------------------------
    # TAB 5: LỘ TRÌNH CEO & EXPORT (ĐÃ SỬA LỖI TYPEERROR)
    # ---------------------------------------------------------
    with tab5:
        st.markdown("##### 🚀 Lộ Trình Hành Động Chiến Lược CEO (Executive Roadmap)")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.markdown("""
            **GIAI ĐOẠN 1: TỐI ƯU HÓA (1 - 3 Tháng)**
            * Cut-off toàn bộ SKU nhóm Yếu Kém không tạo ra biên lợi nhuận.
            * Áp dụng chính sách kiểm soát hạn mức công nợ với Top 3 NPP lớn nhất.
            * Tối ưu tồn kho tại các thị trường trọng điểm.
            """, unsafe_allow_html=True)
            
        with col_r2:
            st.markdown("""
            **GIAI ĐOẠN 2: BỨC PHÁ (3 - 6 Tháng)**
            * Đẩy mạnh ngân sách Marketing cho nhóm Sản phẩm Ngôi Sao.
            * Mở rộng thêm 15-20% số lượng NPP tại các Tỉnh tiềm năng.
            * Thử nghiệm điều chỉnh giá bán với nhóm Dấu Hỏi.
            """, unsafe_allow_html=True)

        with col_r3:
            st.markdown("""
            **GIAI ĐOẠN 3: BỀN VỮNG (6 - 12 Tháng)**
            * Số hóa 100% quản trị chuỗi cung ứng và Sell-out từ NPP.
            * Xây dựng chương trình đối tác chiến lược cho Top 20% NPP xuất sắc.
            * Định hình lại toàn bộ danh mục SKU thế hệ mới.
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 📊 Bảng Tra Cứu Dữ Liệu Chi Tiết & Export CSV")
        
        search_kw = st.text_input("🔍 Tìm kiếm nhanh (Mã KH, Tên NPP, Sản phẩm, Tỉnh...):")
        df_export = df_filtered.copy()
        
        if search_kw:
            mask = df_export.astype(str).apply(lambda x: x.str.contains(search_kw, case=False)).any(axis=1)
            df_export = df_export[mask]
            
        st.dataframe(df_export, use_container_width=True, height=300)
        
        csv_bytes = df_export.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Tải Dữ Liệu Hiện Tại Về File CSV",
            data=csv_bytes,
            file_name="CSuite_Strategic_Data_Export.csv",
            mime="text/csv"
        )

else:
    st.info("👋 Vui lòng tải lên **Master Danh Mục** và **Dữ liệu Sản Lượng** ở thanh bên trái để khởi tạo Báo Cáo.")
