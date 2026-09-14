import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import unicodedata

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN CUỘN TRANG TỰ NHIÊN ---
st.set_page_config(page_title="KHATOCO - Executive Commercial Dashboard", page_icon="📊", layout="wide")

# CSS Tối ưu giao diện Dark Slate, Cuộn trang mượt mà
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
    
    /* Layout cuộn trang tự nhiên */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 95% !important;
    }
    
    /* Header Cao cấp */
    .dashboard-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .header-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #38BDF8;
        margin: 0;
    }
    .header-subtitle {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-top: 4px;
    }
    
    /* Executive Summary Box cho CEO */
    .exec-summary-box {
        background: linear-gradient(135deg, #1E293B 0%, #111827 100%);
        border: 1px solid #38BDF8;
        border-left: 6px solid #38BDF8;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
    
    /* KPI Cards */
    .kpi-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 6px 0 4px 0;
    }
    .kpi-sub {
        font-size: 0.78rem;
    }
    
    /* Card Container cho Biểu đồ */
    .chart-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Style Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #1E293B;
        padding: 6px 10px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #94A3B8;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ & ĐỐI SOÁT DỮ LIỆU ---
def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    s1 = unicodedata.normalize('NFKD', input_str).encode('ASCII', 'ignore').decode('utf-8')
    return s1.lower().strip()

@st.cache_data
def process_excel_files(file_npp_bytes, files_sales_tuples):
    df_npp_raw = pd.read_excel(file_npp_bytes)
    header_idx = None
    for i in range(min(15, len(df_npp_raw))):
        row_str = " ".join(df_npp_raw.iloc[i].dropna().astype(str).tolist()).lower()
        if 'ma kh' in remove_accents(row_str) or 'stt' in remove_accents(row_str):
            header_idx = i
            break
            
    if header_idx is not None:
        df_npp = pd.read_excel(file_npp_bytes, skiprows=header_idx + 1)
    else:
        df_npp = df_npp_raw

    df_npp.columns = [str(c).strip() for c in df_npp.columns]
    
    c_npp_code = next((c for c in df_npp.columns if 'ma kh' in remove_accents(c)), None)
    c_npp_name = next((c for c in df_npp.columns if 'ten nha phan phoi' in remove_accents(c) or 'ten npp' in remove_accents(c)), None)
    c_region = next((c for c in df_npp.columns if 'dia ban' in remove_accents(c) or 'tinh' in remove_accents(c)), None)
    
    if not c_npp_code or not c_npp_name or not c_region:
        return None, "Lỗi định dạng cột trong File Danh mục NPP."
        
    df_npp_clean = df_npp[[c_npp_code, c_npp_name, c_region]].copy()
    df_npp_clean.columns = ['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']
    df_npp_clean['Ma_KH'] = df_npp_clean['Ma_KH'].astype(str).str.strip()
    
    parsed_sales_list = []
    for fname, fbytes in files_sales_tuples:
        df_temp_raw = pd.read_excel(fbytes)
        h_idx = None
        for i in range(min(15, len(df_temp_raw))):
            row_str = " ".join(df_temp_raw.iloc[i].dropna().astype(str).tolist()).lower()
            if 'ma kh' in remove_accents(row_str) or 'stt' in remove_accents(row_str):
                h_idx = i
                break
        
        df_temp = pd.read_excel(fbytes, skiprows=h_idx + 1) if h_idx is not None else df_temp_raw
        df_temp.columns = [str(c).strip() for c in df_temp.columns]
        
        c_code = next((c for c in df_temp.columns if 'ma kh' in remove_accents(c)), None)
        c_name = next((c for c in df_temp.columns if 'ten npp' in remove_accents(c) or 'ten nha phan phoi' in remove_accents(c)), None)
        c_sp = next((c for c in df_temp.columns if 'san pham' in remove_accents(c) or 'ten sp' in remove_accents(c)), None)
        c_sl = next((c for c in df_temp.columns if 'so luong' in remove_accents(c) or 'san luong' in remove_accents(c)), None)
        c_dt = next((c for c in df_temp.columns if 'doanh thu' in remove_accents(c) or 'thanh tien' in remove_accents(c)), None)
        
        if c_code: df_temp[c_code] = df_temp[c_code].ffill()
        if c_name: df_temp[c_name] = df_temp[c_name].ffill()
        
        df_temp = df_temp.dropna(subset=[c_sp])
        df_temp = df_temp.rename(columns={
            c_code: 'Ma_KH', c_name: 'Ten_NPP', c_sp: 'Ten_SP', 
            c_sl: 'San_Luong', c_dt: 'Doanh_Thu' if c_dt else 'Doanh_Thu'
        })
        if 'Doanh_Thu' not in df_temp.columns or not c_dt: df_temp['Doanh_Thu'] = 0
        
        month_match = re.search(r'T(\d{1,2})', fname, re.IGNORECASE)
        df_temp['Thang'] = f"Tháng {int(month_match.group(1)):02d}" if month_match else fname
        parsed_sales_list.append(df_temp)
        
    df_all_sales = pd.concat(parsed_sales_list, ignore_index=True)
    df_all_sales['Ma_KH'] = df_all_sales['Ma_KH'].astype(str).str.strip()
    
    df_master = pd.merge(df_all_sales, df_npp_clean[['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']], on='Ma_KH', how='left')
    df_master['Ten_NPP'] = df_master['Ten_NPP_Master'].fillna(df_master['Ten_NPP'])
    df_master['Dia_Ban'] = df_master['Dia_Ban'].fillna('Chưa phân vùng')
    df_master['Thuyet_Minh_NPP'] = "[" + df_master['Ma_KH'] + "] - " + df_master['Ten_NPP'].astype(str)
    
    return df_master, None

if 'df_master' not in st.session_state: st.session_state['df_master'] = pd.DataFrame()

# --- 3. HEADER CHÍNH ---
st.markdown("""
<div class="dashboard-header">
    <div>
        <h1 class="header-title">HỆ THỐNG GIÁM SÁT THƯƠNG MẠI & PHÂN TÍCH TIÊU THỤ KHATOCO</h1>
        <div class="header-subtitle">Phiên bản Báo cáo Điều hành Chuyên sâu (Executive Dashboard v7.0)</div>
    </div>
    <span style="background: rgba(14, 165, 233, 0.15); color: #38BDF8; border: 1px solid #0284C7; padding: 6px 16px; border-radius: 20px; font-size: 0.82rem; font-weight: 600;">● CHẾ ĐỘ ĐIỀU HÀNH</span>
</div>
""", unsafe_allow_html=True)

tab_dashboard, tab_upload = st.tabs(["📊 BẢNG ĐIỀU KHIỂN & PHÂN TÍCH CHI TIẾT", "⚙️ TẢI LÊN & ĐỐI SOÁT DỮ LIỆU"])

# ==========================================
# TAB 2: TẢI LÊN DỮ LIỆU
# ==========================================
with tab_upload:
    st.markdown("<h4 style='color:#38BDF8; margin-bottom: 12px;'>📥 TẢI LÊN DỮ LIỆU BÁO CÁO</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        file_npp = st.file_uploader("📂 Upload File Danh mục (Danh muc NPP...xlsx)", type=['xlsx'], key="npp")
    with col2:
        files_sales = st.file_uploader("📂 Upload các File Sản lượng Tháng (T6, T7, T8...)", type=['xlsx'], accept_multiple_files=True, key="sales")
        
    if st.button("🚀 NẠP DỮ LIỆU & KẾT NỐI MÃ_KH", use_container_width=True, type="primary"):
        if not file_npp or not files_sales:
            st.error("⚠️ Vui lòng tải lên đầy đủ File Danh mục NPP và File Sản lượng.")
        else:
            with st.spinner("⏳ Hệ thống đang đối soát dữ liệu..."):
                sales_tuples = [(f.name, f.read()) for f in files_sales]
                df_res, err = process_excel_files(file_npp.read(), sales_tuples)
                if err:
                    st.error(f"❌ Lỗi: {err}")
                else:
                    st.session_state['df_master'] = df_res
                    st.success("🎉 Nạp dữ liệu thành công! Hãy chuyển sang Tab [📊 BẢNG ĐIỀU KHIỂN].")

# ==========================================
# TAB 1: BẢNG ĐIỀU KHIỂN PHÂN TÍCH CHUYÊN SÂU
# ==========================================
with tab_dashboard:
    df = st.session_state['df_master']
    
    if df.empty:
        st.info("💡 **HƯỚNG DẪN:** Vui lòng chuyển sang Tab **[⚙️ TẢI LÊN & ĐỐI SOÁT DỮ LIỆU]** để tải file Excel báo cáo lên hệ thống.")
    else:
        # --- BỘ LỌC TOÀN CỤC ---
        st.markdown("<div style='font-size:0.9rem; font-weight:700; color:#38BDF8; margin-bottom:8px;'>🔍 BỘ LỌC DỮ LIỆU TOÀN CỤC</div>", unsafe_allow_html=True)
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
            st.markdown(f'''<div class="kpi-card" style="border-left: 4px solid #38BDF8;">
                <div class="kpi-title">TỔNG DOANH THU</div>
                <div class="kpi-value">{tong_dt:,.0f} <span style="font-size:0.8rem;">đ</span></div>
                <div class="kpi-sub" style="color:#38BDF8;">Doanh số thực ghi nhận</div>
            </div>''', unsafe_allow_html=True)
        with k2:
            st.markdown(f'''<div class="kpi-card" style="border-left: 4px solid #34D399;">
                <div class="kpi-title">TỔNG SẢN LƯỢNG</div>
                <div class="kpi-value">{tong_sl:,.0f} <span style="font-size:0.8rem;">bao</span></div>
                <div class="kpi-sub" style="color:#34D399;">Khối lượng tiêu thụ</div>
            </div>''', unsafe_allow_html=True)
        with k3:
            st.markdown(f'''<div class="kpi-card" style="border-left: 4px solid #818CF8;">
                <div class="kpi-title">NPP / MÃ_KH HOẠT ĐỘNG</div>
                <div class="kpi-value">{so_npp} <span style="font-size:0.8rem;">Mã KH</span></div>
                <div class="kpi-sub" style="color:#818CF8;">Số NPP phát sinh đơn</div>
            </div>''', unsafe_allow_html=True)
        with k4:
            st.markdown(f'''<div class="kpi-card" style="border-left: 4px solid #FBBF24;">
                <div class="kpi-title">ĐỘ PHỦ THỊ TRƯỜNG</div>
                <div class="kpi-value">{so_db} <span style="font-size:0.8rem;">Khu vực</span></div>
                <div class="kpi-sub" style="color:#FBBF24;">Tỉnh/Thành phát sinh hàng</div>
            </div>''', unsafe_allow_html=True)

        # --- TÓM TẮT ĐIỀU HÀNH DÀNH CHO CEO ---
        # Tính toán nhanh dữ liệu cho CEO Summary
        top_sp_name = df_filtered.groupby('Ten_SP')['San_Luong'].sum().idxmax() if not df_filtered.empty else "N/A"
        top_npp_name = df_filtered.groupby('Thuyet_Minh_NPP')['San_Luong'].sum().idxmax() if not df_filtered.empty else "N/A"
        
        # Risk Check: Concentration Top 3 NPP
        npp_share = df_filtered.groupby('Thuyet_Minh_NPP')['San_Luong'].sum().sort_values(ascending=False)
        top3_pct = (npp_share.head(3).sum() / tong_sl * 100) if tong_sl > 0 else 0
        
        st.markdown(f"""
        <div class="exec-summary-box">
            <h5 style="color:#38BDF8; margin-top:0; margin-bottom:8px;">👔 EXECUTIVE SUMMARY (BÁO CÁO TÓM TẮT CHO CEO)</h5>
            <div style="font-size:0.88rem; color:#E2E8F0; line-height:1.6;">
                • <b>Sản phẩm chủ lực:</b> Dòng sản phẩm <b>{top_sp_name}</b> dẫn đầu tiêu thụ với tỷ trọng đóng góp lớn nhất.<br>
                • <b>Nhà phân phối lớn nhất:</b> <b>{top_npp_name}</b> đạt sản lượng cao nhất toàn hệ thống.<br>
                • <b>Cảnh báo Rủi ro Tập trung Doanh số:</b> Top 3 NPP chiếm <b>{top3_pct:.1f}%</b> tổng sản lượng. 
                {"<span style='color:#F87171;'>(⚠️ Mức độ phụ thuộc cao, cần mở rộng độ phủ NPP nhỏ)</span>" if top3_pct > 50 else "<span style='color:#34D399;'>(🟢 Tỷ lệ phân bổ an toàn)</span>"}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- SUB-TABS PHÂN TÍCH CHUYÊN SÂU ---
        sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs([
            "📦 PHÂN TÍCH SẢN PHẨM CHUYÊN SÂU", 
            "🏪 PHÂN TÍCH NHÀ PHÂN PHỐI (MÃ_KH)", 
            "🌍 PHÂN TÍCH THỊ TRƯỜNG & KHU VỰC",
            "🔍 TÙY BIẾN CHI TIẾT & TRUY VẤN (DRILL-DOWN)"
        ])
        
        # =============================================================
        # SUB-TAB 1: PHÂN TÍCH SẢN PHẨM CHUYÊN SÂU
        # =============================================================
        with sub_t1:
            st.markdown("### 📦 1. TỶ LỆ TIÊU THỤ & BIẾN ĐỘNG MOM SẢN PHẨM")
            
            c_p1, c_p2 = st.columns([1, 1])
            
            with c_p1:
                st.markdown("##### 📊 Tỷ Lệ Đóng Góp Sản Lượng Theo Sản Phẩm (%)")
                prod_sl = df_filtered.groupby('Ten_SP').agg({'San_Luong': 'sum', 'Doanh_Thu': 'sum'}).reset_index()
                prod_sl['TyLe(%)'] = (prod_sl['San_Luong'] / tong_sl * 100).round(1) if tong_sl > 0 else 0
                prod_sl = prod_sl.sort_values(by='San_Luong', ascending=False)
                
                fig_prod_pie = px.pie(
                    prod_sl, names='Ten_SP', values='San_Luong',
                    color_discrete_sequence=px.colors.qualitative.Dark24,
                    hole=0.45
                )
                fig_prod_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_prod_pie.update_layout(
                    height=380, margin=dict(l=10, r=10, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94A3B8', family='Plus Jakarta Sans'), showlegend=False
                )
                st.plotly_chart(fig_prod_pie, use_container_width=True)
                
            with c_p2:
                st.markdown("##### 📈 Biến Động Sản Lượng Sản Phẩm So Với Tháng Trước (MoM)")
                all_m = sorted(df['Thang'].dropna().unique().tolist())
                if len(all_m) >= 2:
                    curr_m = all_m[-1]
                    prev_m = all_m[-2]
                    
                    p_curr = df_filtered[df_filtered['Thang']==curr_m].groupby('Ten_SP')['San_Luong'].sum()
                    p_prev = df_filtered[df_filtered['Thang']==prev_m].groupby('Ten_SP')['San_Luong'].sum()
                    
                    df_p_mom = pd.DataFrame({'Thang_HienTai': p_curr, 'Thang_Truoc': p_prev}).fillna(0).reset_index()
                    df_p_mom['Biên_Động'] = df_p_mom['Thang_HienTai'] - df_p_mom['Thang_Truoc']
                    df_p_mom['Phan_Tram(%)'] = (df_p_mom['Biên_Động'] / df_p_mom['Thang_Truoc'].replace(0, 1) * 100).round(1)
                    
                    fig_p_mom = px.bar(
                        df_p_mom, x='Biên_Động', y='Ten_SP', orientation='h',
                        color='Phan_Tram(%)',
                        color_continuous_scale=['#EF4444', '#FBBF24', '#10B981'],
                        text_auto=',.0f'
                    )
                    fig_p_mom.update_layout(
                        height=380, margin=dict(l=10, r=20, t=20, b=20),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                        xaxis=dict(title=f"Tăng/Giảm sản lượng ({curr_m} vs {prev_m})", showgrid=True, gridcolor='#334155'),
                        yaxis=dict(title="", showgrid=False), coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_p_mom, use_container_width=True)
                else:
                    st.info("Cần ít nhất 2 tháng dữ liệu để so sánh MoM.")

            st.markdown("##### 🗺️ Phân Bổ Tiêu Thụ Sản Phẩm Theo Thị Trường Khu Vực (Địa Bàn)")
            pivot_prod_geo = df_filtered.pivot_table(index='Ten_SP', columns='Dia_Ban', values='San_Luong', aggfunc='sum', fill_value=0)
            
            fig_prod_geo = px.imshow(
                pivot_prod_geo,
                labels=dict(x="Địa Bàn Tiêu Thụ", y="Sản Phẩm", color="Sản Lượng (bao)"),
                color_continuous_scale="Viridis", text_auto=',.0f'
            )
            fig_prod_geo.update_layout(
                height=400, margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94A3B8', family='Plus Jakarta Sans')
            )
            st.plotly_chart(fig_prod_geo, use_container_width=True)

        # =============================================================
        # SUB-TAB 2: PHÂN TÍCH NHÀ PHÂN PHỐI (MÃ_KH)
        # =============================================================
        with sub_t2:
            st.markdown("### 🏪 2. PHÂN TÍCH TOÀN DIỆN NHÀ PHÂN PHỐI (MÃ_KH)")
            
            c_n1, c_n2 = st.columns([1.1, 0.9])
            
            with c_n1:
                st.markdown("##### 🏆 Tỷ Lệ Tiêu Thụ Của NPP So Với Toàn Công Ty (%)")
                npp_tot = df_filtered.groupby('Thuyet_Minh_NPP').agg({'San_Luong':'sum', 'Doanh_Thu':'sum'}).reset_index()
                npp_tot['TyLe_Tong(%)'] = (npp_tot['San_Luong'] / tong_sl * 100).round(2) if tong_sl > 0 else 0
                npp_tot = npp_tot.sort_values(by='San_Luong', ascending=False)
                
                fig_npp_share = px.bar(
                    npp_tot.head(10), x='TyLe_Tong(%)', y='Thuyet_Minh_NPP', orientation='h',
                    color='San_Luong', color_continuous_scale='Blues',
                    text_auto='.2f', title="Top 10 NPP Đóng Góp Sản Lượng Nhiều Nhất (%)"
                )
                fig_npp_share.update_layout(
                    height=420, margin=dict(l=10, r=20, t=35, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                    xaxis=dict(title="% Đóng góp vào tổng sản lượng", showgrid=True, gridcolor='#334155'),
                    yaxis=dict(title="", showgrid=False, autorange="reversed"), coloraxis_showscale=False
                )
                st.plotly_chart(fig_npp_share, use_container_width=True)
                
            with c_n2:
                st.markdown("##### 📊 Cơ Cấu Sản Phẩm Tiêu Thụ Trong Từng NPP (%)")
                fig_npp_mix = px.bar(
                    df_filtered, x="San_Luong", y="Thuyet_Minh_NPP", color="Ten_SP",
                    orientation="h", barmode="stack",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_npp_mix.update_layout(
                    height=420, margin=dict(l=10, r=10, t=10, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                    xaxis=dict(title="Sản lượng tiêu thụ (bao)", showgrid=True, gridcolor='#334155'),
                    yaxis=dict(title="", showgrid=False, autorange="reversed"),
                    legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_npp_mix, use_container_width=True)

            st.markdown("##### 📈 So Sánh Biến Động Tăng/Giảm Sản Lượng NPP So Với Tháng Trước")
            if len(all_m) >= 2:
                curr_m = all_m[-1]
                prev_m = all_m[-2]
                
                n_curr = df_filtered[df_filtered['Thang']==curr_m].groupby(['Ma_KH', 'Thuyet_Minh_NPP'])['San_Luong'].sum()
                n_prev = df_filtered[df_filtered['Thang']==prev_m].groupby(['Ma_KH', 'Thuyet_Minh_NPP'])['San_Luong'].sum()
                
                df_n_mom = pd.DataFrame({'Thang_HienTai': n_curr, 'Thang_Truoc': n_prev}).fillna(0).reset_index()
                df_n_mom['Chenh_Lech'] = df_n_mom['Thang_HienTai'] - df_n_mom['Thang_Truoc']
                df_n_mom['Phan_Tram_MoM(%)'] = (df_n_mom['Chenh_Lech'] / df_n_mom['Thang_Truoc'].replace(0, 1) * 100).round(1)
                
                st.dataframe(
                    df_n_mom.sort_values(by='Chenh_Lech', ascending=True).rename(columns={
                        'Ma_KH': 'Mã KH', 'Thuyet_Minh_NPP': 'Nhà Phân Phối',
                        'Thang_Truoc': f'Sản Lượng {prev_m}', 'Thang_HienTai': f'Sản Lượng {curr_m}',
                        'Chenh_Lech': 'Chênh Lệch (bao)', 'Phan_Tram_MoM(%)': 'Tăng/Giảm (%)'
                    }),
                    use_container_width=True, height=280
                )

        # =============================================================
        # SUB-TAB 3: PHÂN TÍCH THỊ TRƯỜNG & KHU VỰC
        # =============================================================
        with sub_t3:
            st.markdown("### 🌍 3. PHÂN TÍCH TIÊU THỤ THEO THỊ TRƯỜNG KHU VỰC")
            
            reg_agg = df_filtered.groupby('Dia_Ban').agg({'San_Luong':'sum', 'Doanh_Thu':'sum', 'Ma_KH':'nunique'}).reset_index()
            reg_agg['TyLe_SL(%)'] = (reg_agg['San_Luong'] / tong_sl * 100).round(1) if tong_sl > 0 else 0
            reg_agg = reg_agg.sort_values(by='San_Luong', ascending=False)
            
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                fig_reg_bar = px.bar(
                    reg_agg, x='Dia_Ban', y='San_Luong', text_auto=',.0f',
                    color='San_Luong', color_continuous_scale='Tealgrn',
                    title="Sản Lượng Tiêu Thụ Theo Tỉnh / Thành"
                )
                fig_reg_bar.update_layout(
                    height=380, margin=dict(l=10, r=10, t=35, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                    xaxis=dict(title="", showgrid=False), coloraxis_showscale=False
                )
                st.plotly_chart(fig_reg_bar, use_container_width=True)
                
            with c_r2:
                fig_reg_npp = px.bar(
                    reg_agg, x='Dia_Ban', y='Ma_KH', text_auto=True,
                    color='Ma_KH', color_continuous_scale='Purples',
                    title="Số Lượng NPP Phát Sinh Đơn Theo Tỉnh / Thành"
                )
                fig_reg_npp.update_layout(
                    height=380, margin=dict(l=10, r=10, t=35, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94A3B8', family='Plus Jakarta Sans'),
                    xaxis=dict(title="", showgrid=False), coloraxis_showscale=False
                )
                st.plotly_chart(fig_reg_npp, use_container_width=True)

        # =============================================================
        # SUB-TAB 4: TÙY BIẾN CHI TIẾT & TRUY VẤN (DRILL-DOWN)
        # =============================================================
        with sub_t4:
            st.markdown("### 🔍 4. SOI SÂU CHI TIẾT THEO NHU CẦU TÙY BIẾN")
            
            st.markdown("##### 🎯 Chọn Đích Danh 1 Nhà Phân Phối Để Phân Tích 360 Độ")
            all_npp_list = sorted(df['Thuyet_Minh_NPP'].dropna().unique().tolist())
            selected_single_npp = st.selectbox("Chọn Mã_KH / NPP cần soi sâu:", all_npp_list)
            
            if selected_single_npp:
                df_npp_single = df[df['Thuyet_Minh_NPP'] == selected_single_npp]
                
                single_sl = df_npp_single['San_Luong'].sum()
                single_dt = df_npp_single['Doanh_Thu'].sum()
                single_db = df_npp_single['Dia_Ban'].iloc[0] if not df_npp_single.empty else "N/A"
                
                st.info(f"📍 **Nhà Phân Phối:** {selected_single_npp} | **Địa Bàn:** {single_db} | **Tổng Sản Lượng:** {single_sl:,.0f} bao | **Tổng Doanh Thu:** {single_dt:,.0f} đ")
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    fig_single_sp = px.pie(
                        df_npp_single.groupby('Ten_SP')['San_Luong'].sum().reset_index(),
                        names='Ten_SP', values='San_Luong', title=f"Cơ Cấu Sản Phẩm Tiêu Thụ Của NPP",
                        hole=0.4
                    )
                    fig_single_sp.update_layout(height=320, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#94A3B8'))
                    st.plotly_chart(fig_single_sp, use_container_width=True)
                    
                with col_d2:
                    fig_single_trend = px.line(
                        df_npp_single.groupby('Thang')['San_Luong'].sum().reset_index(),
                        x='Thang', y='San_Luong', markers=True, title=f"Xu Hướng Sản Lượng Qua Các Tháng"
                    )
                    fig_single_trend.update_layout(height=320, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#94A3B8'))
                    st.plotly_chart(fig_single_trend, use_container_width=True)

            st.markdown("---")
            st.markdown("##### 📋 Bảng Chi Tiết Toàn Bộ Dữ Liệu & Nút Xuất File Excel")
            st.dataframe(df_filtered[['Thang', 'Ma_KH', 'Ten_NPP', 'Dia_Ban', 'Ten_SP', 'San_Luong', 'Doanh_Thu']], use_container_width=True, height=350)
            
            # Export CSV Button
            csv_data = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 TẢI DỮ LIỆU ĐÃ LỌC VỀ EXCEL (CSV)",
                data=csv_data,
                file_name="Bao_Cao_Khatoco_Filtered.csv",
                mime="text/csv",
                type="primary"
            )
