import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import unicodedata
import io

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG & DARK THEME C-SUITE UI/UX
# ---------------------------------------------------------
st.set_page_config(
    page_title="KTC C-Suite Strategic Analytics",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive Dark Style Sheet
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp { background-color: #0b0f19; color: #f1f5f9; }
    
    /* Executive Header */
    .csuite-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #312e81;
        color: #ffffff;
        padding: 20px 25px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .csuite-header h2 { color: #38bdf8; margin: 0 0 6px 0; font-weight: 700; font-size: 1.5rem; }
    .csuite-header p { color: #94a3b8; margin: 0; font-size: 0.9rem; }
    
    /* KPI Cards Dark Mode */
    .kpi-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
    }
    .kpi-title { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: 600; }
    .kpi-value { font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin: 4px 0; }
    .kpi-sub { font-size: 0.75rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# Chuẩn hóa Plotly Theme cho đồng bộ Dark Mode
DARK_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#e2e8f0', family="Inter, sans-serif"),
    xaxis=dict(showgrid=False, zeroline=False, color='#94a3b8'),
    yaxis=dict(showgrid=True, gridcolor='#1e293b', zeroline=False, color='#94a3b8'),
    margin=dict(l=20, r=20, t=40, b=20)
)

def normalize_text(text):
    if not isinstance(text, str): return ""
    text = text.replace('_', ' ')
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    return text.lower().strip()

# ---------------------------------------------------------
# 2. XỬ LÝ DỮ LIỆU
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
st.sidebar.title("🏛️ BẢNG DIỀU HÀNH C-SUITE")
file_dm = st.sidebar.file_uploader("1. File Danh mục Master (.xlsx)", type=["xlsx"])
files_sl = st.sidebar.file_uploader("2. File Sản lượng Tháng (.xlsx)", type=["xlsx"], accept_multiple_files=True)

if file_dm and files_sl:
    dm_bytes = io.BytesIO(file_dm.read())
    sl_tuples = [(f.name, io.BytesIO(f.read())) for f in files_sl]
    
    with st.spinner("⚡ Đang tối ưu hóa giao diện và dữ liệu..."):
        df = process_data(dm_bytes, sl_tuples)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Bộ Lọc Tối Ưu Tầm Nhìn")
    
    selected_months = st.sidebar.multiselect("Chu kỳ Tháng", options=sorted(df['Thang'].unique()), default=sorted(df['Thang'].unique()))
    selected_regions = st.sidebar.multiselect("Địa Bàn / Tỉnh", options=sorted(df['Dia_Ban_Tieu_Thu'].unique()), default=sorted(df['Dia_Ban_Tieu_Thu'].unique()))

    df_filtered = df[(df['Thang'].isin(selected_months)) & (df['Dia_Ban_Tieu_Thu'].isin(selected_regions))]

    unit_choice = st.sidebar.radio("Đơn vị hiển thị:", ["Doanh_Thu", "San_Luong"], format_func=lambda x: "Doanh Thu (VNĐ)" if x == "Doanh_Thu" else "Sản Lượng (Bao)")
    unit_label = "VNĐ" if unit_choice == "Doanh_Thu" else "Bao"

    # ---------------------------------------------------------
    # 4. DASHBOARD HEADER & KPI CARDS
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
    c1.markdown(f"""<div class="kpi-card"><div class="kpi-title">Tổng Doanh Thu</div><div class="kpi-value">{total_rev/1e9:,.2f} Tỷ</div><div class="kpi-sub" style="color:#10b981;">VNĐ</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="kpi-card"><div class="kpi-title">Tổng Sản Lượng</div><div class="kpi-value">{total_vol:,.0f}</div><div class="kpi-sub" style="color:#38bdf8;">Bao</div></div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="kpi-card"><div class="kpi-title">Số Lượng NPP Active</div><div class="kpi-value">{df_filtered['Ma_KH'].nunique()}</div><div class="kpi-sub" style="color:#94a3b8;">Khách hàng</div></div>""", unsafe_allow_html=True)
    c4.markdown(f"""<div class="kpi-card"><div class="kpi-title">Danh Mục SP Active</div><div class="kpi-value">{df_filtered['Ten_SP'].nunique()}</div><div class="kpi-sub" style="color:#f59e0b;">SKU</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 5. TÁI THIẾT KẾ CÁC BIỂU ĐỒ CHUẨN UI/UX
    # ---------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 1. Ma Trận BCG Tối Ưu (Rõ Chữ)",
        "🗺️ 2. Biểu Đồ Cây Thi Thị Trường (Thay Heatmap)",
        "📈 3. Xu Hướng Top Sản Phẩm (Gọn Gàng)",
        "🏆 4. Top Nhà Phân Phối Tương Thích"
    ])

    # ---------------------------------------------------------
    # TAB 1: BCG SCATTER (FIX LỖI ĐÈ CHỮ)
    # ---------------------------------------------------------
    with tab1:
        st.markdown("##### 🎯 Ma Trận Ưu Tiên Tăng Trưởng (BCG Product Matrix)")
        st.caption("💡 *Đã lược bỏ nhãn chữ chồng chéo. Rê chuột vào từng điểm để xem chi tiết tên Sản phẩm & Tỉnh.*")

        bcg_df = df_filtered.groupby(['Dia_Ban_Tieu_Thu', 'Ten_SP']).agg(
            Revenue=('Doanh_Thu', 'sum'),
            Volume=('San_Luong', 'sum')
        ).reset_index()

        if not bcg_df.empty:
            avg_rev = bcg_df['Revenue'].mean()
            avg_vol = bcg_df['Volume'].mean()

            def classify(row):
                if row['Revenue'] >= avg_rev and row['Volume'] >= avg_vol: return '🌟 Ngôi Sao (Đẩy mạnh)'
                elif row['Revenue'] >= avg_rev: return '🐄 Bò Sữa (Tối ưu lợi nhuận)'
                elif row['Volume'] >= avg_vol: return '❓ Dấu Hỏi (Thử nghiệm tăng giá)'
                else: return '⚠️ Yếu Kém (Tái cấu trúc)'

            bcg_df['Phan_Loai'] = bcg_df.apply(classify, axis=1)

            # Scatter Plot KHÔNG HIỆN TEXT TRỰC TIẾP ĐỂ TRÁNH ĐÈ
            fig_bcg = px.scatter(
                bcg_df, x='Volume', y='Revenue', color='Phan_Loai',
                hover_name='Ten_SP', hover_data={'Dia_Ban_Tieu_Thu': True, 'Revenue': ':,', 'Volume': ':,'},
                color_discrete_map={
                    '🌟 Ngôi Sao (Đẩy mạnh)': '#38bdf8',
                    '🐄 Bò Sữa (Tối ưu lợi nhuận)': '#34d399',
                    '❓ Dấu Hỏi (Thử nghiệm tăng giá)': '#fbbf24',
                    '⚠️ Yếu Kém (Tái cấu trúc)': '#f87171'
                }
            )
            fig_bcg.add_hline(y=avg_rev, line_dash="dash", line_color="#64748b", annotation_text="TB Doanh Thu")
            fig_bcg.add_vline(x=avg_vol, line_dash="dash", line_color="#64748b", annotation_text="TB Sản Lượng")
            fig_bcg.update_traces(marker=dict(size=14, opacity=0.85, line=dict(width=1, color='#ffffff')))
            fig_bcg.update_layout(**DARK_LAYOUT, height=450, legend_title_text="Phân Loại Chiến Lược")
            st.plotly_chart(fig_bcg, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 2: TREEMAP (THAY THẾ HEATMAP BỊ LÍU CHỮ)
    # ---------------------------------------------------------
    with tab2:
        st.markdown("##### 🗺️ Biểu Đồ Cây Phân Cấp Thi Thị Trường (Cực Kỳ Dễ Đọc)")
        st.caption("💡 *Thay thế cho Heatmap cũ. Kích thước ô thể hiện Doanh thu/Sản lượng, phân cấp rõ ràng từng Tỉnh ➔ Sản phẩm.*")

        tree_df = df_filtered.groupby(['Dia_Ban_Tieu_Thu', 'Ten_SP'])[unit_choice].sum().reset_index()
        tree_df = tree_df[tree_df[unit_choice] > 0]

        if not tree_df.empty:
            fig_tree = px.treemap(
                tree_df,
                path=['Dia_Ban_Tieu_Thu', 'Ten_SP'],
                values=unit_choice,
                color=unit_choice,
                color_continuous_scale='Blues'
            )
            fig_tree.update_traces(textinfo="label+value+percent parent")
            fig_tree.update_layout(**DARK_LAYOUT, height=500)
            st.plotly_chart(fig_tree, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 3: LINE CHART TOP 5 (FIX LỖI SPAGHETTI)
    # ---------------------------------------------------------
    with tab3:
        st.markdown("##### 📈 Biến Động Chu Kỳ - Top 5 Sản Phẩm Chủ Lực")
        st.caption("💡 *Tự động lọc Top 5 Sản phẩm đóng góp lớn nhất để tránh chồng chéo đường biểu đồ.*")

        top5_skus = df_filtered.groupby('Ten_SP')[unit_choice].sum().nlargest(5).index.tolist()
        
        # Cho phép người dùng tùy chọn thêm nếu muốn
        selected_display_skus = st.multiselect("Tùy chọn dòng sản phẩm muốn xem:", options=df_filtered['Ten_SP'].unique(), default=top5_skus)

        trend_df = df_filtered[df_filtered['Ten_SP'].isin(selected_display_skus)].groupby(['Thang', 'Ten_SP'])[unit_choice].sum().reset_index()

        if not trend_df.empty:
            fig_line = px.line(
                trend_df, x='Thang', y=unit_choice, color='Ten_SP', markers=True,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
            fig_line.update_layout(**DARK_LAYOUT, height=420, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_line, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 4: TOP NPP (RÕ RÀNG, NỔI BẬT NỀN ĐÊN)
    # ---------------------------------------------------------
    with tab4:
        st.markdown("##### 🏆 Top 15 Nhà Phân Phối Đóng Góp Lớn Nhất")
        
        npp_df = df_filtered.groupby('Thuyet_Minh_NPP')[unit_choice].sum().reset_index()
        npp_df = npp_df.sort_values(by=unit_choice, ascending=True).tail(15)

        # Cắt ngắn tên hiển thị nếu quá dài
        npp_df['Short_Name'] = npp_df['Thuyet_Minh_NPP'].apply(lambda x: x[:35] + '...' if len(x) > 35 else x)

        if not npp_df.empty:
            fig_npp = px.bar(
                npp_df, x=unit_choice, y='Short_Name', orientation='h',
                text_auto='.2s' if unit_choice == 'Doanh_Thu' else ',.0f',
                hover_name='Thuyet_Minh_NPP'
            )
            fig_npp.update_traces(marker_color='#38bdf8', textposition='outside')
            fig_npp.update_layout(**DARK_LAYOUT, height=450, yaxis_title="")
            st.plotly_chart(fig_npp, use_container_width=True)

else:
    st.info("👋 Vui lòng tải lên file **Master Danh Mục** và **Dữ liệu Sản Lượng** ở thanh bên trái để khởi tạo Báo Cáo.")
