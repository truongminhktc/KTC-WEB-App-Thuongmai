import streamlit as st
import pandas as pd
import plotly.express as px
import re
import unicodedata

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN ---
st.set_page_config(page_title="KHATOCO - Báo Cáo Thương Mại", page_icon="🛡️", layout="wide")

CUSTOM_DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #F3F4F6; }
    .stApp { background-color: #0B0F17; }
    .fpt-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155; color: #FFFFFF; padding: 20px 28px; 
        border-radius: 12px; margin-bottom: 20px; display: flex; 
        justify-content: space-between; align-items: center;
    }
    .fpt-title { font-size: 1.5rem; font-weight: 700; margin: 0; color: #38BDF8; }
    .dark-card { background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 18px; }
    .dark-card-title { font-size: 0.75rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; }
    .dark-card-value { font-size: 1.7rem; font-weight: 700; color: #F8FAFC; margin: 4px 0; }
    .upload-box { border: 2px dashed #38BDF8; padding: 20px; border-radius: 10px; text-align: center; background-color: #111827; }
    .text-green { color: #34D399; }
    .text-red { color: #F87171; }
</style>
"""
st.markdown(CUSTOM_DARK_CSS, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ DỮ LIỆU THÔNG MINH ---
def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    s1 = unicodedata.normalize('NFKD', input_str).encode('ASCII', 'ignore').decode('utf-8')
    return s1.lower().strip()

def find_column(df, keywords):
    """Tự động tìm tên cột trong Excel dựa trên từ khóa"""
    for col in df.columns:
        col_norm = remove_accents(str(col))
        for kw in keywords:
            if kw in col_norm: return col
    return None

if 'df_master' not in st.session_state: st.session_state['df_master'] = pd.DataFrame()

# --- 3. GIAO DIỆN CHÍNH ---
st.markdown(f"""
<div class="fpt-header">
    <div>
        <h1 class="fpt-title">BÁO CÁO GIÁM SÁT KINH DOANH KHATOCO</h1>
        <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">App: KTC-WEB-App-Thuongmai | Hệ thống phân tích Tự Động (Auto-BI)</div>
    </div>
    <span style="background: #064E3B; color: #6EE7B7; border: 1px solid #065F46; padding: 4px 12px; border-radius: 12px;">TRỰC TUYẾN</span>
</div>
""", unsafe_allow_html=True)

tab_dashboard, tab_upload = st.tabs(["📊 BẢNG ĐIỀU KHIỂN & PHÂN TÍCH", "⚙️ TẢI LÊN DỮ LIỆU (KÉO THẢ)"])

# ==========================================
# TAB 2: KHU VỰC CẬP NHẬT DỮ LIỆU KÉO THẢ
# ==========================================
with tab_upload:
    st.markdown("### 📥 KHO DỮ LIỆU ĐẦU VÀO")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='upload-box'><h4>📂 1. DANH MỤC NPP & ĐỊA BÀN</h4></div>", unsafe_allow_html=True)
        file_npp = st.file_uploader("Tải 1 file Danh mục", type=['xlsx'], key="npp")
        
    with col2:
        st.markdown("<div class='upload-box'><h4>📂 2. SẢN LƯỢNG TIÊU THỤ</h4></div>", unsafe_allow_html=True)
        files_sales = st.file_uploader("Tải các file T6, T7, T8...", type=['xlsx'], accept_multiple_files=True, key="sales")
        
    if st.button("🚀 THỰC HIỆN XỬ LÝ & TỔNG HỢP DỮ LIỆU", use_container_width=True, type="primary"):
        if not file_npp or not files_sales:
            st.error("⚠️ Vui lòng tải đủ cả file Danh mục và các file Sản lượng!")
        else:
            with st.spinner("Hệ thống đang AI hóa và khớp nối dữ liệu..."):
                try:
                    # 1. Đọc và chuẩn hóa Danh mục NPP
                    df_npp = pd.read_excel(file_npp)
                    col_npp_name = find_column(df_npp, ['ten npp', 'khach hang', 'npp']) or df_npp.columns[0]
                    col_region = find_column(df_npp, ['dia ban', 'tinh', 'khu vuc']) or df_npp.columns[1]
                    
                    df_npp = df_npp[[col_npp_name, col_region]].rename(columns={col_npp_name: 'Ten_NPP', col_region: 'Dia_Ban'})
                    df_npp['Ten_NPP_Key'] = df_npp['Ten_NPP'].astype(str).apply(remove_accents)
                    
                    # 2. Đọc và gộp các file Sản lượng
                    list_df = []
                    for f in files_sales:
                        df_temp = pd.read_excel(f)
                        # Tìm tháng từ tên file
                        month_match = re.search(r'T(\d{1,2})', f.name, re.IGNORECASE)
                        df_temp['Thang'] = f"Tháng {int(month_match.group(1)):02d}" if month_match else f.name
                        
                        # Tự động tìm các cột quan trọng trong file Sản lượng
                        c_npp = find_column(df_temp, ['ten npp', 'khach hang', 'npp'])
                        c_sp = find_column(df_temp, ['san pham', 'ten sp', 'hang hoa'])
                        c_sl = find_column(df_temp, ['san luong', 'so luong', 'slg'])
                        c_dt = find_column(df_temp, ['doanh thu', 'thanh tien', 'gia tri'])
                        
                        # Đổi tên cột chuẩn hóa
                        rename_dict = {}
                        if c_npp: rename_dict[c_npp] = 'Ten_NPP'
                        if c_sp: rename_dict[c_sp] = 'Ten_SP'
                        if c_sl: rename_dict[c_sl] = 'San_Luong'
                        if c_dt: rename_dict[c_dt] = 'Doanh_Thu'
                        
                        df_temp = df_temp.rename(columns=rename_dict)
                        list_df.append(df_temp)
                        
                    df_all_sales = pd.concat(list_df, ignore_index=True)
                    df_all_sales['Ten_NPP_Key'] = df_all_sales.get('Ten_NPP', pd.Series(dtype=str)).astype(str).apply(remove_accents)
                    
                    # 3. Hợp nhất (Merge) file Sản lượng và file Danh mục NPP để lấy Địa Bàn
                    df_master = pd.merge(df_all_sales, df_npp[['Ten_NPP_Key', 'Dia_Ban']], on='Ten_NPP_Key', how='left')
                    
                    # Điền giá trị mặc định nếu thiếu cột
                    if 'Ten_SP' not in df_master.columns: df_master['Ten_SP'] = "Không xác định"
                    if 'San_Luong' not in df_master.columns: df_master['San_Luong'] = 0
                    if 'Doanh_Thu' not in df_master.columns: df_master['Doanh_Thu'] = 0
                    if 'Dia_Ban' not in df_master.columns: df_master['Dia_Ban'] = "Khác"
                    
                    st.session_state['df_master'] = df_master
                    st.success("✅ Đã xử lý xong! Vui lòng chuyển sang tab BẢNG ĐIỀU KHIỂN & PHÂN TÍCH.")
                except Exception as e:
                    st.error(f"❌ Lỗi xử lý file: {e}")

# ==========================================
# TAB 1: BẢNG ĐIỀU KHIỂN & PHÂN TÍCH QUẢN TRỊ
# ==========================================
with tab_dashboard:
    df = st.session_state['df_master']
    
    if df.empty:
        st.info("⚠️ Vui lòng tải dữ liệu ở Tab [⚙️ TẢI LÊN DỮ LIỆU] trước để hiển thị báo cáo.")
    else:
        # --- BỘ LỌC ĐỘNG ---
        st.markdown("### 🔍 BỘ LỌC DỮ LIỆU")
        f1, f2, f3, f4 = st.columns(4)
        with f1: sel_thang = st.multiselect("Tháng", sorted(df['Thang'].unique()))
        with f2: sel_db = st.multiselect("Địa Bàn", df['Dia_Ban'].dropna().unique())
        with f3: sel_sp = st.multiselect("Sản Phẩm", df['Ten_SP'].dropna().unique())
        with f4: sel_npp = st.multiselect("Nhà Phân Phối", df['Ten_NPP'].dropna().unique())
        
        df_filtered = df.copy()
        if sel_thang: df_filtered = df_filtered[df_filtered['Thang'].isin(sel_thang)]
        if sel_db: df_filtered = df_filtered[df_filtered['Dia_Ban'].isin(sel_db)]
        if sel_sp: df_filtered = df_filtered[df_filtered['Ten_SP'].isin(sel_sp)]
        if sel_npp: df_filtered = df_filtered[df_filtered['Ten_NPP'].isin(sel_npp)]
        
        # --- CHỈ SỐ KPI QUẢN TRỊ ---
        st.markdown("### 📈 TỔNG QUAN HIỆU QUẢ KINH DOANH")
        k1, k2, k3, k4 = st.columns(4)
        
        tong_dt = df_filtered['Doanh_Thu'].sum()
        tong_sl = df_filtered['San_Luong'].sum()
        so_npp = df_filtered['Ten_NPP'].nunique()
        so_db = df_filtered['Dia_Ban'].nunique()
        
        with k1: st.markdown(f'<div class="dark-card"><div class="dark-card-title">TỔNG DOANH THU</div><div class="dark-card-value">{tong_dt:,.0f}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="dark-card"><div class="dark-card-title">TỔNG SẢN LƯỢNG</div><div class="dark-card-value">{tong_sl:,.0f}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="dark-card"><div class="dark-card-title">NPP PHÁT SINH GD</div><div class="dark-card-value">{so_npp}</div></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="dark-card"><div class="dark-card-title">ĐỘ PHỦ THỊ TRƯỜNG</div><div class="dark-card-value">{so_db} <span style="font-size:14px; font-weight:normal;">Khu vực</span></div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 3 SUB-TABS PHÂN TÍCH ---
        sub_t1, sub_t2, sub_t3 = st.tabs(["🚨 CẢNH BÁO BIẾN ĐỘNG MoM", "📊 PHÂN TÍCH XU HƯỚNG & CƠ CẤU", "📋 BẢNG DỮ LIỆU CHI TIẾT"])
        
        with sub_t1:
            st.markdown("#### Đánh giá Tăng/Giảm giữa 2 kỳ")
            c1, c2 = st.columns(2)
            all_months = sorted(df['Thang'].dropna().unique().tolist())
            with c1: curr_m = st.selectbox("Chọn Kỳ báo cáo:", all_months, index=len(all_months)-1 if len(all_months)>0 else 0)
            with c2: comp_m = st.selectbox("Chọn Kỳ đối soát:", all_months, index=max(0, len(all_months)-2) if len(all_months)>0 else 0)
            
            if curr_m != comp_m:
                df_curr = df_filtered[df_filtered['Thang'] == curr_m].groupby('Ten_NPP').agg({'Doanh_Thu': 'sum', 'San_Luong': 'sum'}).reset_index()
                df_comp = df_filtered[df_filtered['Thang'] == comp_m].groupby('Ten_NPP').agg({'Doanh_Thu': 'sum', 'San_Luong': 'sum'}).reset_index()
                
                merged = pd.merge(df_curr, df_comp, on='Ten_NPP', how='outer', suffixes=('_HienTai', '_Truoc')).fillna(0)
                merged['ChenhLech_SanLuong'] = merged['San_Luong_HienTai'] - merged['San_Luong_Truoc']
                merged['TyLe_MoM(%)'] = (merged['ChenhLech_SanLuong'] / merged['San_Luong_Truoc'].replace(0, 1) * 100).round(2)
                
                def get_alert(pct):
                    if pct <= -15: return "🔴 Báo động đỏ"
                    elif -15 < pct <= -5: return "🟡 Cảnh báo giảm"
                    elif pct >= 15: return "🟢 Tăng trưởng tốt"
                    return "⚪ Đi ngang"
                
                merged['Trang_Thai'] = merged['TyLe_MoM(%)'].apply(get_alert)
                st.dataframe(merged.sort_values(by='ChenhLech_SanLuong', ascending=True), use_container_width=True)
            else:
                st.info("Vui lòng chọn 2 kỳ khác nhau để so sánh.")

        with sub_t2:
            r1, r2 = st.columns(2)
            with r1:
                st.markdown("**1. Xu Hướng Sản Lượng & Doanh Thu Qua Các Tháng**")
                trend_df = df_filtered.groupby('Thang').agg({'Doanh_Thu':'sum', 'San_Luong':'sum'}).reset_index()
                fig1 = px.line(trend_df, x='Thang', y='San_Luong', markers=True, title="Biểu Đồ Sản Lượng")
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
                st.plotly_chart(fig1, use_container_width=True)
                
            with r2:
                st.markdown("**2. Cơ Cấu Tiêu Thụ Theo Địa Bàn**")
                pie_df = df_filtered.groupby('Dia_Ban').agg({'San_Luong':'sum'}).reset_index()
                fig2 = px.pie(pie_df, names='Dia_Ban', values='San_Luong', hole=0.4, title="Tỷ trọng Địa Bàn")
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
                st.plotly_chart(fig2, use_container_width=True)
                
            st.markdown("**3. Phân Tích Chuyên Sâu Theo Sản Phẩm**")
            prod_df = df_filtered.groupby('Ten_SP').agg({'San_Luong':'sum', 'Doanh_Thu':'sum'}).reset_index().sort_values(by='San_Luong', ascending=False)
            fig3 = px.bar(prod_df, x='Ten_SP', y='San_Luong', color='Doanh_Thu', title="Sản Lượng & Doanh Thu Theo Sản Phẩm")
            fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
            st.plotly_chart(fig3, use_container_width=True)

        with sub_t3:
            st.markdown("#### Bảng Dữ Liệu Gốc Đã Qua Xử Lý")
            st.dataframe(df_filtered, use_container_width=True)
