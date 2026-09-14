import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import unicodedata

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="KHATOCO - Hệ Thống Báo Cáo Thương Mại", page_icon="📊", layout="wide")

# CSS Tối ưu không gian hiển thị & Card Styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #F1F5F9;
    }
    .stApp {
        background-color: #0F172A;
    }
    
    /* Thu gọn padding mặc định của Streamlit */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Header Chuyên Nghiệp */
    .dashboard-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 12px 24px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .header-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #38BDF8;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .header-subtitle {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 2px;
    }
    
    /* KPI Card Thiết kế mới */
    .kpi-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-left: 4px solid #38BDF8;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }
    .kpi-title {
        font-size: 0.72rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 4px 0 2px 0;
    }
    .kpi-sub {
        font-size: 0.72rem;
        color: #38BDF8;
    }
    
    /* Container Khối Biểu Đồ */
    .chart-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
    }
    
    /* Đề xuất Giải pháp Box */
    .solution-card {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-left: 4px solid #EF4444;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    
    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1E293B;
        padding: 4px 8px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 6px;
        color: #94A3B8;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ DỮ LIỆU & RÀ SOÁT ---
def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    s1 = unicodedata.normalize('NFKD', input_str).encode('ASCII', 'ignore').decode('utf-8')
    return s1.lower().strip()

def read_excel_smart(file_obj):
    df_raw = pd.read_excel(file_obj)
    header_idx = None
    for i in range(min(15, len(df_raw))):
        row_str = " ".join(df_raw.iloc[i].dropna().astype(str).tolist()).lower()
        row_str_norm = remove_accents(row_str)
        if 'ma kh' in row_str_norm or 'stt' in row_str_norm:
            header_idx = i
            break
            
    file_obj.seek(0)
    if header_idx is not None:
        df = pd.read_excel(file_obj, skiprows=header_idx + 1)
    else:
        df = pd.read_excel(file_obj)
    
    df.columns = [str(c).strip() for c in df.columns]
    return df

def find_column(df, keywords):
    for col in df.columns:
        col_norm = remove_accents(str(col))
        for kw in keywords:
            if kw in col_norm: return col
    return None

if 'df_master' not in st.session_state: st.session_state['df_master'] = pd.DataFrame()

# --- 3. HEADER CHÍNH ---
st.markdown("""
<div class="dashboard-header">
    <div>
        <h1 class="header-title">BÁO CÁO GIÁM SÁT KINH DOANH KHATOCO</h1>
        <div class="header-subtitle">Hệ thống Phân tích Chuyên sâu & Kiểm soát Tiêu thụ v6.0</div>
    </div>
    <span style="background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid #059669; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">● TRỰC TUYẾN</span>
</div>
""", unsafe_allow_html=True)

tab_dashboard, tab_upload = st.tabs(["📊 BẢNG ĐIỀU KHIỂN & PHÂN TÍCH CHUYÊN SÂU", "⚙️ TẢI LÊN & RÀ SOÁT DỮ LIỆU"])

# ==========================================
# TAB 2: TẢI LÊN & RÀ SOÁT DỮ LIỆU
# ==========================================
with tab_upload:
    st.markdown("<h4 style='color:#38BDF8; margin-bottom: 12px;'>📥 KHO DỮ LIỆU ĐẦU VÀO</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='border: 2px dashed #38BDF8; padding: 15px; border-radius: 10px; background: #1E293B;'><b>📂 1. DANH MỤC NPP & ĐỊA BÀN</b></div>", unsafe_allow_html=True)
        file_npp = st.file_uploader("Upload File Danh mục (Danh muc NPP...xlsx)", type=['xlsx'], key="npp")
        
    with col2:
        st.markdown("<div style='border: 2px dashed #38BDF8; padding: 15px; border-radius: 10px; background: #1E293B;'><b>📂 2. SẢN LƯỢNG & DOANH THU THÁNG</b></div>", unsafe_allow_html=True)
        files_sales = st.file_uploader("Upload các File Sản lượng (T6, T7, T8...)", type=['xlsx'], accept_multiple_files=True, key="sales")
        
    if st.button("🚀 THỰC HIỆN KẾT NỐI MÃ_KH & RÀ SOÁT DỮ LIỆU", use_container_width=True, type="primary"):
        if not file_npp or not files_sales:
            st.error("⚠️ **CẢNH BÁO:** Vui lòng tải lên đầy đủ cả File Danh mục NPP và ít nhất 1 File Sản lượng!")
        else:
            errors = []
            with st.spinner("🔍 Hệ thống đang kiểm tra và đối soát Mã_KH..."):
                try:
                    df_npp = read_excel_smart(file_npp)
                    c_npp_code = find_column(df_npp, ['ma kh', 'makh', 'ma khach hang'])
                    c_npp_name = find_column(df_npp, ['ten nha phan phoi', 'ten npp', 'khach hang'])
                    c_region = find_column(df_npp, ['dia ban', 'tinh', 'khu vuc'])
                    
                    if not c_npp_code: errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Thiếu cột **'Mã KH'**.")
                    if not c_npp_name: errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Thiếu cột **'Tên nhà phân phối / đại lý'**.")
                    if not c_region: errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Thiếu cột **'Địa bàn tiêu thụ'**.")
                except Exception as e:
                    errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Lỗi đọc file ({e}).")

                parsed_sales_list = []
                for f in files_sales:
                    try:
                        df_temp = read_excel_smart(f)
                        c_code = find_column(df_temp, ['ma kh', 'makh', 'ma khach hang'])
                        c_name = find_column(df_temp, ['ten nha phan phoi', 'ten npp', 'khach hang'])
                        c_sp = find_column(df_temp, ['san pham', 'ten sp', 'hang hoa'])
                        c_sl = find_column(df_temp, ['so luong', 'san luong', 'slg'])
                        c_dt = find_column(df_temp, ['doanh thu', 'thanh tien'])
                        
                        missing = []
                        if not c_code and not c_name: missing.append("Mã KH hoặc Tên NPP")
                        if not c_sp: missing.append("Sản phẩm")
                        if not c_sl: missing.append("Số lượng / Sản lượng")
                        
                        if missing:
                            errors.append(f"❌ **File Sản lượng (`{f.name}`):** Thiếu các cột: **{', '.join(missing)}**.")
                        else:
                            if c_code: df_temp[c_code] = df_temp[c_code].ffill()
                            if c_name: df_temp[c_name] = df_temp[c_name].ffill()
                            
                            df_temp = df_temp.dropna(subset=[c_sp])
                            df_temp = df_temp.rename(columns={
                                c_code: 'Ma_KH', c_name: 'Ten_NPP', c_sp: 'Ten_SP', 
                                c_sl: 'San_Luong', c_dt: 'Doanh_Thu' if c_dt else 'Doanh_Thu'
                            })
                            if 'Doanh_Thu' not in df_temp.columns or not c_dt:
                                df_temp['Doanh_Thu'] = 0
                                
                            month_match = re.search(r'T(\d{1,2})', f.name, re.IGNORECASE)
                            df_temp['Thang'] = f"Tháng {int(month_match.group(1)):02d}" if month_match else f.name
                            parsed_sales_list.append(df_temp)
                    except Exception as e:
                        errors.append(f"❌ **File Sản lượng (`{f.name}`):** Lỗi dữ liệu ({e}).")

            if errors:
                st.error("🚨 **PHÁT HIỆN LỖI DỮ LIỆU ĐẦU VÀO!** Vui lòng kiểm tra lại theo thông báo bên dưới:")
                for err in errors: st.markdown(err)
            else:
                df_npp_clean = df_npp[[c_npp_code, c_npp_name, c_region]].copy()
                df_npp_clean.columns = ['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']
                df_npp_clean['Ma_KH'] = df_npp_clean['Ma_KH'].astype(str).str.strip()
                
                df_all_sales = pd.concat(parsed_sales_list, ignore_index=True)
                df_all_sales['Ma_KH'] = df_all_sales['Ma_KH'].astype(str).str.strip()
                
                df_master = pd.merge(df_all_sales, df_npp_clean[['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']], on='Ma_KH', how='left')
                df_master['Ten_NPP'] = df_master['Ten_NPP_Master'].fillna(df_master['Ten_NPP'])
                df_master['Dia_Ban'] = df_master['Dia_Ban'].fillna('Chưa phân vùng')
                df_master['Thuyet_Minh_NPP'] = "[" + df_master['Ma_KH'] + "] - " + df_master['Ten_NPP'].astype(str)
                
                st.session_state['df_master'] = df_master
                st.success("🎉 **KẾT NỐI MÃ_KH HOÀN HẢO!** Dữ liệu đã được liên kết chuẩn hóa 100%. Vui lòng bấm sang Tab Bảng Điều Khiển.")

# ==========================================
# TAB 1: BẢNG ĐIỀU KHIỂN & PHÂN TÍCH CHUYÊN SÂU
# ==========================================
with tab_dashboard:
    df = st.session_state['df_master']
    
    if df.empty:
        st.info("💡 **HƯỚNG DẪN:** Vui lòng chuyển sang Tab **[⚙️ TẢI LÊN & RÀ SOÁT DỮ LIỆU]** để tải file Excel báo cáo lên hệ thống.")
    else:
        # --- BỘ LỌC TỐI ƯU KHÔNG GIAN ---
        st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#38BDF8; margin-bottom:6px;'>🔍 BỘ LỌC ĐA CHIỀU (THAM CHIẾU MÃ_KH)</div>", unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)
        with f1: sel_thang = st.multiselect("Kỳ Báo Cáo", sorted(df['Thang'].dropna().unique()), placeholder="Tất cả các tháng")
        with f2: sel_db = st.multiselect("Địa Bàn", sorted(df['Dia_Ban'].dropna().unique()), placeholder="Tất cả địa bàn")
        with f3: sel_sp = st.multiselect("Sản Phẩm", sorted(df['Ten_SP'].dropna().unique()), placeholder="Tất cả sản phẩm")
        with f4: sel_npp = st.multiselect("Nhà Phân Phối (Mã KH)", sorted(df['Thuyet_Minh_NPP'].dropna().unique()), placeholder="Tất cả NPP")
        
        df_filtered = df.copy()
        if sel_thang: df_filtered = df_filtered[df_filtered['Thang'].isin(sel_thang)]
        if sel_db: df_filtered = df_filtered[df_filtered['Dia_Ban'].isin(sel_db)]
        if sel_sp: df_filtered = df_filtered[df_filtered['Ten_SP'].isin(sel_sp)]
        if sel_npp: df_filtered = df_filtered[df_filtered['Thuyet_Minh_NPP'].isin(sel_npp)]
        
        # --- CÁC CHỈ SỐ KPI CHÍNH ---
        k1, k2, k3, k4 = st.columns(4)
        
        tong_dt = df_filtered['Doanh_Thu'].sum()
        tong_sl = df_filtered['San_Luong'].sum()
        so_npp = df_filtered['Ma_KH'].nunique()
        so_db = df_filtered['Dia_Ban'].nunique()
        
        with k1:
            st.markdown(f'''
            <div class="kpi-card" style="border-left-color: #38BDF8;">
                <div class="kpi-title">TỔNG DOANH THU</div>
                <div class="kpi-value">{tong_dt:,.0f} <span style="font-size:0.8rem; font-weight:normal;">đ</span></div>
                <div class="kpi-sub">Theo bộ lọc hiện tại</div>
            </div>
            ''', unsafe_allow_html=True)
        with k2:
            st.markdown(f'''
            <div class="kpi-card" style="border-left-color: #34D399;">
                <div class="kpi-title">TỔNG SẢN LƯỢNG</div>
                <div class="kpi-value">{tong_sl:,.0f} <span style="font-size:0.8rem; font-weight:normal;">bao</span></div>
                <div class="kpi-sub">Sản lượng tiêu thụ thực tế</div>
            </div>
            ''', unsafe_allow_html=True)
        with k3:
            st.markdown(f'''
            <div class="kpi-card" style="border-left-color: #818CF8;">
                <div class="kpi-title">NPP / MÃ KH PHÁT SINH</div>
                <div class="kpi-value">{so_npp} <span style="font-size:0.8rem; font-weight:normal;">Mã KH</span></div>
                <div class="kpi-sub">Đã đối soát danh mục</div>
            </div>
            ''', unsafe_allow_html=True)
        with k4:
            st.markdown(f'''
            <div class="kpi-card" style="border-left-color: #FBBF24;">
                <div class="kpi-title">ĐỘ PHỦ THỊ TRƯỜNG</div>
                <div class="kpi-value">{so_db} <span style="font-size:0.8rem; font-weight:normal;">Tỉnh/Thành</span></div>
                <div class="kpi-sub">Địa bàn phát sinh doanh số</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        # --- SUB-TABS PHÂN TÍCH & CẢNH BÁO ---
        sub_t1, sub_t2, sub_t3, sub_t4, sub_t5 = st.tabs([
            "🚨 CẢNH BÁO BIẾN ĐỘNG MOM", 
            "🧩 MA TRẬN SẢN PHẨM × ĐỊA BÀN", 
            "🛍️ CƠ CẤU SẢN PHẨM THEO MÃ_KH", 
            "🌍 CƠ CẤU THỊ TRƯỜNG & PARETO", 
            "📋 BẢNG THAM CHIẾU MÃ_KH CHI TIẾT"
        ])
        
        # -------------------------------------------------------------
        # SUB-TAB 1: CẢNH BÁO BIẾN ĐỘNG MOM & GIẢI PHÁP
        # -------------------------------------------------------------
        with sub_t1:
            c_select1, c_select2 = st.columns(2)
            all_months = sorted(df['Thang'].dropna().unique().tolist())
            with c_select1: curr_m = st.selectbox("Kỳ Báo Cáo (Tháng Hiện Tại):", all_months, index=len(all_months)-1 if len(all_months)>0 else 0)
            with c_select2: comp_m = st.selectbox("Kỳ Đối Soát (Tháng Liền Trước):", all_months, index=max(0, len(all_months)-2) if len(all_months)>0 else 0)
            
            if curr_m != comp_m:
                df_curr = df_filtered[df_filtered['Thang'] == curr_m].groupby(['Ma_KH', 'Thuyet_Minh_NPP']).agg({'San_Luong': 'sum', 'Doanh_Thu': 'sum'}).reset_index()
                df_comp = df_filtered[df_filtered['Thang'] == comp_m].groupby(['Ma_KH', 'Thuyet_Minh_NPP']).agg({'San_Luong': 'sum', 'Doanh_Thu': 'sum'}).reset_index()
                
                merged = pd.merge(df_curr, df_comp, on=['Ma_KH', 'Thuyet_Minh_NPP'], how='outer', suffixes=('_KyBaoCao', '_KySoSanh')).fillna(0)
                merged['ChenhLech_SL'] = merged['San_Luong_KyBaoCao'] - merged['San_Luong_KySoSanh']
                merged['Tyle_MoM_SL(%)'] = (merged['ChenhLech_SL'] / merged['San_Luong_KySoSanh'].replace(0, 1) * 100).round(1)
                
                def get_alert_status(pct):
                    if pct <= -15: return "🔴 Báo động đỏ (Giảm >15%)"
                    elif -15 < pct <= -5: return "🟡 Cảnh báo giảm"
                    elif pct >= 15: return "🟢 Tăng trưởng tốt"
                    return "⚪ Đi ngang"
                
                merged['Trang_Thai'] = merged['Tyle_MoM_SL(%)'].apply(get_alert_status)
                
                col_chart, col_solutions = st.columns([1.1, 0.9])
                
                with col_chart:
                    st.markdown("##### 📊 Top Nhà Phân Phối Biến Động Sản Lượng Mạnh Nhất")
                    top_changes = pd.concat([
                        merged.sort_values(by='ChenhLech_SL', ascending=True).head(5),
                        merged.sort_values(by='ChenhLech_SL', ascending=False).head(5)
                    ]).drop_duplicates()
                    
                    fig_mom = px.bar(
                        top_changes, x='ChenhLech_SL', y='Thuyet_Minh_NPP', orientation='h',
                        color='Tyle_MoM_SL(%)',
                        color_continuous_scale=['#EF4444', '#FBBF24', '#10B981'],
                        text_auto=',.0f', title=""
                    )
                    fig_mom.update_layout(
                        height=350, margin=dict(l=10, r=20, t=10, b=20),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                        xaxis=dict(title="Sản lượng tăng/giảm (bao)", showgrid=True, gridcolor='#334155'),
                        yaxis=dict(title="", showgrid=False), coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_mom, use_container_width=True)
                    
                with col_solutions:
                    st.markdown("##### 💡 Đề Xuất Giải Pháp Bán Hàng Trọng Tâm")
                    bad_npps = merged[merged['Tyle_MoM_SL(%)'] <= -15].sort_values(by='ChenhLech_SL', ascending=True)
                    
                    if not bad_npps.empty:
                        st.write(f"Phát hiện **{len(bad_npps)} NPP** sụt giảm sản lượng trên **15%**:")
                        for _, row in bad_npps.head(3).iterrows():
                            st.markdown(f"""
                            <div class="solution-card">
                                <b style="color:#F8FAFC;">{row['Thuyet_Minh_NPP']}</b><br>
                                <span style="color:#F87171;">📉 Giảm: {abs(row['ChenhLech_SL']):,.0f} bao ({row['Tyle_MoM_SL(%)']}%)</span><br>
                                <span style="font-size:0.78rem; color:#94A3B8;">
                                <b>Hành động:</b> Giám sát bán hàng (SS) kiểm tra tồn kho điểm bán và chương trình khuyến mãi cạnh tranh.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("🟢 Tất cả các Nhà phân phối đều giữ đà tăng trưởng ổn định!")

                st.markdown("##### 📋 Bảng Chi Tiết Biến Động Giữa 2 Kỳ")
                st.dataframe(
                    merged[['Ma_KH', 'Thuyet_Minh_NPP', 'San_Luong_KySoSanh', 'San_Luong_KyBaoCao', 'ChenhLech_SL', 'Tyle_MoM_SL(%)', 'Trang_Thai']]
                    .sort_values(by='ChenhLech_SL', ascending=True),
                    use_container_width=True, height=200
                )
            else:
                st.info("Vui lòng chọn 2 tháng khác nhau để đối soát.")

        # -------------------------------------------------------------
        # SUB-TAB 2: MA TRẬN SẢN PHẨM × ĐỊA BÀN (HEATMAP)
        # -------------------------------------------------------------
        with sub_t2:
            st.markdown("##### 🧩 Bản Đồ Nhiệt: Phân Bổ Sản Lượng Sản Phẩm Theo Địa Bàn Tiêu Thụ")
            
            metric_choice = st.radio("Chọn chỉ số hiển thị ma trận:", ["Sản Lượng (bao)", "Doanh Thu (đồng)"], horizontal=True)
            col_target = 'San_Luong' if metric_choice == "Sản Lượng (bao)" else 'Doanh_Thu'
            
            pivot_geo = df_filtered.pivot_table(index='Ten_SP', columns='Dia_Ban', values=col_target, aggfunc='sum', fill_value=0)
            
            if not pivot_geo.empty:
                fig_heat = px.imshow(
                    pivot_geo,
                    labels=dict(x="Địa Bàn Tiêu Thụ", y="Dòng Sản Phẩm", color=metric_choice),
                    color_continuous_scale="Cividis",
                    text_auto=',.0f',
                    title=""
                )
                fig_heat.update_layout(
                    height=380, margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                    xaxis=dict(title="", showgrid=False),
                    yaxis=dict(title="", showgrid=False)
                )
                st.plotly_chart(fig_heat, use_container_width=True)
                
                st.markdown("💡 **Gợi ý phân tích:** Các ô có **màu tối hoặc giá trị 0** thể hiện dải sản phẩm chưa phủ được vào địa bàn đó. Giám sát bán hàng cần tập trung mở rộng kênh phân phối.")
            else:
                st.warning("Không có dữ liệu phù hợp với bộ lọc.")

        # -------------------------------------------------------------
        # SUB-TAB 3: CƠ CẤU SẢN PHẨM THEO MÃ_KH (NPP)
        # -------------------------------------------------------------
        with sub_t3:
            st.markdown("##### 🛍️ Phân Tích Cơ Cấu Dòng Sản Phẩm Tiêu Thụ Theo Từng Mã_KH / NPP")
            
            # Cột chồng Stacked Bar Chart
            fig_stack = px.bar(
                df_filtered, x="San_Luong", y="Thuyet_Minh_NPP", color="Ten_SP",
                orientation="h",
                title="",
                color_discrete_sequence=px.colors.qualitative.Bold,
                text_auto=',.0f'
            )
            fig_stack.update_layout(
                height=380, margin=dict(l=10, r=20, t=10, b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                xaxis=dict(title="Tổng Sản Lượng (bao)", showgrid=True, gridcolor='#334155'),
                yaxis=dict(title="", showgrid=False, autorange="reversed"),
                barmode='stack',
                legend=dict(title="Sản Phẩm", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_stack, use_container_width=True)
            
            # Bảng chi tiết Pivot theo Mã_KH x sản phẩm
            st.markdown("##### 📋 Bảng Báo Cáo Chi Tiết Sản Lượng Sản Phẩm (bao) Theo Mã_KH")
            pivot_npp_prod = df_filtered.pivot_table(index=['Ma_KH', 'Ten_NPP', 'Dia_Ban'], columns='Ten_SP', values='San_Luong', aggfunc='sum', fill_value=0).reset_index()
            st.dataframe(pivot_npp_prod, use_container_width=True, height=220)

        # -------------------------------------------------------------
        # SUB-TAB 4: CƠ CẤU THỊ TRƯỜNG & PARETO (ABC ANALYSIS)
        # -------------------------------------------------------------
        with sub_t4:
            c_reg1, c_reg2 = st.columns([1, 1])
            
            region_df = df_filtered.groupby('Dia_Ban').agg({'San_Luong':'sum', 'Doanh_Thu':'sum'}).reset_index().sort_values(by='San_Luong', ascending=False)
            
            with c_reg1:
                fig_donut = px.pie(
                    region_df, names='Dia_Ban', values='San_Luong', hole=0.5,
                    title="<b>TỶ TRỌNG SẢN LƯỢNG THEO TỈNH / THÀNH</b>",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                fig_donut.update_layout(
                    height=340, margin=dict(l=20, r=20, t=35, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                    showlegend=False
                )
                st.plotly_chart(fig_donut, use_container_width=True)
                
            with c_reg2:
                # Phân tích Pareto ABC Sản Phẩm
                prod_abc = df_filtered.groupby('Ten_SP').agg({'Doanh_Thu': 'sum', 'San_Luong': 'sum'}).reset_index()
                prod_abc = prod_abc.sort_values(by='Doanh_Thu', ascending=False)
                tot_rev = prod_abc['Doanh_Thu'].sum()
                
                if tot_rev > 0:
                    prod_abc['Cum_DT'] = prod_abc['Doanh_Thu'].cumsum()
                    prod_abc['Cum_Pct'] = (prod_abc['Cum_DT'] / tot_rev) * 100
                    
                    def classify_abc(pct):
                        if pct <= 80: return 'Hạng A (Chủ lực - 80% DT)'
                        elif pct <= 95: return 'Hạng B (Phát triển - 15% DT)'
                        else: return 'Hạng C (Tiềm năng/Mới - 5% DT)'
                        
                    prod_abc['Phan_Hang_Pareto'] = prod_abc['Cum_Pct'].apply(classify_abc)
                    prod_abc['Don_Gia_Binh_Quan'] = (prod_abc['Doanh_Thu'] / prod_abc['San_Luong'].replace(0, 1)).round(0)
                    
                    st.markdown("##### 🏆 Phân Hạng Pareto ABC Dòng Sản Phẩm")
                    st.dataframe(
                        prod_abc[['Ten_SP', 'San_Luong', 'Doanh_Thu', 'Don_Gia_Binh_Quan', 'Phan_Hang_Pareto']].rename(columns={
                            'Ten_SP': 'Sản Phẩm', 'San_Luong': 'Sản Lượng (bao)', 
                            'Doanh_Thu': 'Doanh Thu (đ)', 'Don_Gia_Binh_Quan': 'Đơn Giá TB (đ)',
                            'Phan_Hang_Pareto': 'Phân Hạng ABC'
                        }),
                        use_container_width=True, height=280
                    )

        # -------------------------------------------------------------
        # SUB-TAB 5: BẢNG THAM CHIẾU CHI TIẾT
        # -------------------------------------------------------------
        with sub_t5:
            st.markdown("##### 📋 Dữ Liệu Tham Chiếu Chi Tiết Mã_KH")
            st.dataframe(
                df_filtered[['Thang', 'Ma_KH', 'Ten_NPP', 'Dia_Ban', 'Ten_SP', 'San_Luong', 'Doanh_Thu']], 
                use_container_width=True, height=360
            )
