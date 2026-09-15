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
    page_title="KTC C-Suite Strategic Executive Analytics",
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
    
    /* Executive Insight Box */
    .ceo-box {
        background: #131c31;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 25px;
    }
    .ceo-title { color: #38bdf8; font-weight: 700; font-size: 1rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
    .ceo-content { color: #cbd5e1; font-size: 0.9rem; line-height: 1.6; }

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

    /* Quadrant Card Custom */
    .quad-card {
        background: #1e293b;
        border-radius: 8px;
        padding: 14px;
        border-top: 3px solid #64748b;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Layout Plotly dùng chung cho Dark Mode
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
# 2. XỬ LÝ DỮ LIỆU chuẩn hóa
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
    
    with st.spinner("⚡ Đang kết nối dữ liệu chiến lược C-Suite..."):
        df = process_data(dm_bytes, sl_tuples)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Bộ Lọc Tầm Nhìn Quản Trị")
    
    selected_months = st.sidebar.multiselect("Chu kỳ Tháng", options=sorted(df['Thang'].unique()), default=sorted(df['Thang'].unique()))
    selected_regions = st.sidebar.multiselect("Địa Bàn / Tỉnh", options=sorted(df['Dia_Ban_Tieu_Thu'].unique()), default=sorted(df['Dia_Ban_Tieu_Thu'].unique()))

    df_filtered = df[(df['Thang'].isin(selected_months)) & (df['Dia_Ban_Tieu_Thu'].isin(selected_regions))]

    unit_choice = st.sidebar.radio("Đơn vị đo lường:", ["Doanh_Thu", "San_Luong"], format_func=lambda x: "Doanh Thu (VNĐ)" if x == "Doanh_Thu" else "Sản Lượng (Bao)")
    unit_label = "VNĐ" if unit_choice == "Doanh_Thu" else "Bao"

    # ---------------------------------------------------------
    # 4. DASHBOARD HEADER & KPI CARDS
    # ---------------------------------------------------------
    st.markdown("""
    <div class="csuite-header">
        <h2>🏛️ BÁO CÁO QUẢN TRỊ CHIẾN LƯỢC C-SUITE (BASELINE MASTER)</h2>
        <p>Hệ thống hỗ trợ ra quyết định: Thị trường x Sản phẩm x Năng lực Nhà Phân Phối</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    total_rev = df_filtered['Doanh_Thu'].sum()
    total_vol = df_filtered['San_Luong'].sum()
    active_npp = df_filtered['Ma_KH'].nunique()
    active_sku = df_filtered['Ten_SP'].nunique()

    c1.markdown(f"""<div class="kpi-card"><div class="kpi-title">Tổng Doanh Thu</div><div class="kpi-value">{total_rev/1e9:,.2f} Tỷ</div><div class="kpi-sub" style="color:#10b981;">VNĐ</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="kpi-card"><div class="kpi-title">Tổng Sản Lượng</div><div class="kpi-value">{total_vol:,.0f}</div><div class="kpi-sub" style="color:#38bdf8;">Bao</div></div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="kpi-card"><div class="kpi-title">Số Lượng NPP Active</div><div class="kpi-value">{active_npp}</div><div class="kpi-sub" style="color:#94a3b8;">Khách hàng</div></div>""", unsafe_allow_html=True)
    c4.markdown(f"""<div class="kpi-card"><div class="kpi-title">Danh Mục SP Active</div><div class="kpi-value">{active_sku}</div><div class="kpi-sub" style="color:#f59e0b;">SKU</div></div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 5. KHỐI NHẬN ĐỊNH ĐIỀU HÀNH CẤP CAO (CEO EXECUTIVE INSIGHTS)
    # ---------------------------------------------------------
    # Tính toán chỉ số quản trị động
    top_region = df_filtered.groupby('Dia_Ban_Tieu_Thu')['Doanh_Thu'].sum().idxmax() if not df_filtered.empty else "N/A"
    top_region_rev = df_filtered.groupby('Dia_Ban_Tieu_Thu')['Doanh_Thu'].sum().max() if not df_filtered.empty else 0
    top_region_pct = (top_region_rev / total_rev * 100) if total_rev > 0 else 0

    top3_npp_rev = df_filtered.groupby('Thuyet_Minh_NPP')['Doanh_Thu'].sum().nlargest(3).sum() if not df_filtered.empty else 0
    top3_npp_pct = (top3_npp_rev / total_rev * 100) if total_rev > 0 else 0

    st.markdown(f"""
    <div class="ceo-box">
        <div class="ceo-title">💡 NHẬN ĐỊNH ĐIỀU HÀNH CẤP CAO (EXECUTIVE SUMMARY & CEO DIRECTIVES)</div>
        <div class="ceo-content">
            • <b>Tập trung thị trường:</b> Địa bàn <b>{top_region}</b> đang đóng góp lớn nhất với <b>{top_region_rev/1e9:,.2f} tỷ VNĐ</b> (chiếm <b>{top_region_pct:.1f}%</b> tổng doanh số toàn hệ thống).<br>
            • <b>Rủi ro kênh phân phối:</b> Top 3 Nhà Phân Phối lớn nhất đang nắm giữ <b>{top3_npp_pct:.1f}%</b> tổng doanh thu. Cần có chính sách quản trị công nợ và chống đứt gãy kênh linh hoạt.<br>
            • <b>Định hướng danh mục:</b> Tập trung nguồn lực Marketing/Khuyến mãi vào nhóm <b>Ngôi Sao</b> và kiểm soát dòng tiền ở nhóm <b>Bò Sữa</b>. Rà soát kiên quyết khai tử các SKU nhóm <b>Yếu Kém</b> liên tục 3 tháng không tăng trưởng.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 6. HỆ THỐNG TAB CHIẾN LƯỢC TOÀN DIỆN
    # ---------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 1. Ma Trận BCG & Chỉ Đạo Sản Phẩm",
        "🗺️ 2. Phân Bổ Thị Trường & Địa Bàn",
        "📈 3. Xu Hướng Tăng Trưởng SKU",
        "🏆 4. Năng Lực & Rủi Ro Kênh NPP",
        "📋 5. Lộ Trình CEO & Dữ Liệu Chi Tiết"
    ])

    # ---------------------------------------------------------
    # TAB 1: MA TRẬN BCG & CHỈ ĐẠO CHIẾN LƯỢC SẢN PHẨM
    # ---------------------------------------------------------
    with tab1:
        st.markdown("##### 🎯 Ma Trận Tăng Trưởng BCG (Tối Ưu Hiển Thị Rõ Chữ)")
        st.caption("💡 *Đã lược bỏ các nhãn chữ đè nhau. Rê chuột vào điểm bất kỳ để xem chính xác Tên sản phẩm & Thị trường.*")

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
            fig_bcg.update_traces(marker=dict(size=14, opacity=0.85, line=dict(width=1, color='#ffffff')))
            fig_bcg.update_layout(**DARK_LAYOUT, height=430, legend_title_text="Phân Loại Sản Phẩm")
            st.plotly_chart(fig_bcg, use_container_width=True)

            st.markdown("---")
            st.markdown("##### 📌 Bảng Báo Cáo Phân Lớp & Chỉ Đạo Cụ Thể Từ CEO")
            
            col_s, col_m, col_q, col_d = st.columns(4)
            with col_s:
                st.markdown("<div class='quad-card' style='border-color:#38bdf8;'><b>🌟 NGUỒN LỰC TĂNG TRƯỞNG (NGÔI SAO)</b><br><small>Doanh thu Cao | Sản lượng Cao</small></div>", unsafe_allow_html=True)
                st.dataframe(bcg_df[bcg_df['Phan_Loai'] == '🌟 Ngôi Sao'][['Ten_SP', 'Revenue']], hide_index=True, use_container_width=True)
                st.caption("👉 **Chỉ đạo:** Dồn 60% ngân sách MKT, duy trì tồn kho ưu tiên.")

            with col_m:
                st.markdown("<div class='quad-card' style='border-color:#34d399;'><b>🐄 DÒNG TIỀN CHỦ LỰC (BÒ SỮA)</b><br><small>Doanh thu Cao | Sản lượng Thấp</small></div>", unsafe_allow_html=True)
                st.dataframe(bcg_df[bcg_df['Phan_Loai'] == '🐄 Bò Sữa'][['Ten_SP', 'Revenue']], hide_index=True, use_container_width=True)
                st.caption("👉 **Chỉ đạo:** Giảm chi phí bán hàng, tối ưu lợi nhuận thuần.")

            with col_q:
                st.markdown("<div class='quad-card' style='border-color:#fbbf24;'><b>❓ CƠ HỘI ĐỘT PHÁ (DẤU HỎI)</b><br><small>Doanh thu Thấp | Sản lượng Cao</small></div>", unsafe_allow_html=True)
                st.dataframe(bcg_df[bcg_df['Phan_Loai'] == '❓ Dấu Hỏi'][['Ten_SP', 'Revenue']], hide_index=True, use_container_width=True)
                st.caption("👉 **Chỉ đạo:** Điều chỉnh chính sách giá/chiết khấu để tăng biên lợi nhuận.")

            with col_d:
                st.markdown("<div class='quad-card' style='border-color:#f87171;'><b>⚠️ NGUY CƠ LẠNG PHÍ (YẾU KÉM)</b><br><small>Doanh thu Thấp | Sản lượng Thấp</small></div>", unsafe_allow_html=True)
                st.dataframe(bcg_df[bcg_df['Phan_Loai'] == '⚠️ Yếu Kém'][['Ten_SP', 'Revenue']], hide_index=True, use_container_width=True)
                st.caption("👉 **Chỉ đạo:** Lên kế hoạch loại bỏ (Phase-out) trong 60 ngày.")

    # ---------------------------------------------------------
    # TAB 2: PHÂN BỔ THỊ TRƯỜNG & ĐỊA BÀN
    # ---------------------------------------------------------
    with tab2:
        st.markdown("##### 🗺️ Biểu Đồ Cây Phân Cấp Thi Thị Trường (Treemap Phân Cấp)")
        st.caption("💡 *Thay thế Heatmap cũ để tránh bị chèn ép chữ. Tỉnh chiếm diện tích càng lớn thể hiện tỷ trọng đóng góp càng cao.*")

        tree_df = df_filtered.groupby(['Dia_Ban_Tieu_Thu', 'Ten_SP'])[unit_choice].sum().reset_index()
        tree_df = tree_df[tree_df[unit_choice] > 0]

        if not tree_df.empty:
            fig_tree = px.treemap(
                tree_df, path=['Dia_Ban_Tieu_Thu', 'Ten_SP'], values=unit_choice,
                color=unit_choice, color_continuous_scale='Blues'
            )
            fig_tree.update_traces(textinfo="label+value+percent parent")
            fig_tree.update_layout(**DARK_LAYOUT, height=480)
            st.plotly_chart(fig_tree, use_container_width=True)

            st.markdown("##### 🔍 Đánh Giá Độ Phủ Thị Trường:")
            reg_summary = df_filtered.groupby('Dia_Ban_Tieu_Thu').agg(
                Doanh_Thu=('Doanh_Thu', 'sum'),
                So_NPP=('Ma_KH', 'nunique'),
                So_SKU=('Ten_SP', 'nunique')
            ).reset_index().sort_values(by='Doanh_Thu', ascending=False)
            
            st.dataframe(reg_summary, hide_index=True, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 3: XU HƯỚNG TĂNG TRƯỜNG SKU
    # ---------------------------------------------------------
    with tab3:
        st.markdown("##### 📈 Biến Động Chu Kỳ Tăng Trưởng - Top Sản Phẩm Chủ Lực")
        st.caption("💡 *Tự động chọn Top 5 SKU đóng góp chính để tránh đường vẽ chèn ép rối mắt.*")

        top5_skus = df_filtered.groupby('Ten_SP')[unit_choice].sum().nlargest(5).index.tolist()
        selected_display_skus = st.multiselect("Tùy chọn danh mục sản phẩm theo dõi:", options=df_filtered['Ten_SP'].unique(), default=top5_skus)

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
    # TAB 4: NĂNG LỰC & RỦI RO KÊNH NPP
    # ---------------------------------------------------------
    with tab4:
        st.markdown("##### 🏆 Top 15 Nhà Phân Phối Đóng Góp Lớn Nhất")
        
        npp_df = df_filtered.groupby('Thuyet_Minh_NPP')[unit_choice].sum().reset_index()
        npp_df = npp_df.sort_values(by=unit_choice, ascending=True).tail(15)
        npp_df['Short_Name'] = npp_df['Thuyet_Minh_NPP'].apply(lambda x: x[:38] + '...' if len(x) > 38 else x)

        if not npp_df.empty:
            fig_npp = px.bar(
                npp_df, x=unit_choice, y='Short_Name', orientation='h',
                text_auto='.2s' if unit_choice == 'Doanh_Thu' else ',.0f',
                hover_name='Thuyet_Minh_NPP'
            )
            fig_npp.update_traces(marker_color='#38bdf8', textposition='outside')
            fig_npp.update_layout(**DARK_LAYOUT, height=450, yaxis_title="")
            st.plotly_chart(fig_npp, use_container_width=True)

            st.markdown("##### ⚠️ Phân Tích Mức Độ Tập Trung & Rủi Ro Phụ Thuộc (Pareto NPP):")
            st.info(f"Top 3 NPP đóng góp {top3_npp_pct:.1f}% tổng doanh số. Cần đảm bảo hạn mức tín dụng công nợ nằm trong tầm kiểm soát an toàn.")

    # ---------------------------------------------------------
    # TAB 5: LỘ TRÌNH CEO & DỮ LIỆU CHI TIẾT
    # ---------------------------------------------------------
    with tab5:
        st.markdown("##### 🚀 Lộ Trình Hành Động Chiến Lược CEO (Executive Roadmap)")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.markdown("""
            **GIAI ĐOẠN 1: TỐI ƯU HÓA (1 - 3 Thắng)**
            * Cut-off toàn bộ SKU nhóm Yếu Kém không tạo ra biên lợi nhuận.
            * Áp dụng chính sách kiểm soát hạn mức công nợ với Top 3 NPP lớn nhất.
            * Tối ưu tồn kho tại các thị trường trọng điểm.
            """, unsafe_allow_style=True)
            
        with col_r2:
            st.markdown("""
            **GIAI ĐOẠN 2: BỨC PHÁ (3 - 6 Tháng)**
            * Đẩy mạnh ngân sách Marketing cho nhóm Sản phẩm Ngôi Sao.
            * Mở rộng thêm 15-20% số lượng NPP tại các Tỉnh tiềm năng.
            * Thử nghiệm điều chính giá bán với nhóm Dấu Hỏi.
            """, unsafe_allow_style=True)

        with col_r3:
            st.markdown("""
            **GIAI ĐOẠN 3: BỀN VỮNG (6 - 12 Tháng)**
            * Số hóa 100% quản trị chuỗi cung ứng và Sell-out từ NPP.
            * Xây dựng chương trình đối tác chiến lược cho Top 20% NPP xuất sắc.
            * Định hình lại toàn bộ danh mục SKU thế hệ mới.
            """, unsafe_allow_style=True)

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
    st.info("👋 Vui lòng tải lên **Master Danh Mục** và **Dữ liệu Sản Lượng** ở thanh bên trái để khởi tạo Báo Cáo Chuẩn Cơ Sở.")
