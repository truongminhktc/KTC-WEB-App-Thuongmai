import streamlit as st
import pandas as pd
import plotly.express as px
import re
import unicodedata

# --- 1. CẤU HÌNH TRANG & GIAO DIỆN ---
st.set_page_config(page_title="KHATOCO - Hệ Thống Quản Trị Bán Hàng", page_icon="🛡️", layout="wide")

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
    .dark-card-value { font-size: 1.6rem; font-weight: 700; color: #F8FAFC; margin: 4px 0; }
    .upload-box { border: 2px dashed #38BDF8; padding: 20px; border-radius: 10px; text-align: center; background-color: #111827; }
    .solution-box { background-color: #111827; border-left: 4px solid #38BDF8; padding: 15px; border-radius: 6px; margin-top: 10px; }
</style>
"""
st.markdown(CUSTOM_DARK_CSS, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ & TỰ ĐỘNG CHUẨN HÓA MÃ_KH ---
def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    s1 = unicodedata.normalize('NFKD', input_str).encode('ASCII', 'ignore').decode('utf-8')
    return s1.lower().strip()

def read_excel_smart(file_obj):
    """ Tự động tìm dòng tiêu đề thực sự chứa Mã KH, Tên NPP... """
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

# --- 3. GIAO DIỆN CHÍNH ---
st.markdown("""
<div class="fpt-header">
    <div>
        <h1 class="fpt-title">BÁO CÁO GIÁM SÁT KINH DOANH KHATOCO</h1>
        <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">App: KTC-WEB-App-Thuongmai | Hệ thống phân tích Tham chiếu Mã_KH & Quản trị v4.0</div>
    </div>
    <span style="background: #064E3B; color: #6EE7B7; border: 1px solid #065F46; padding: 4px 12px; border-radius: 12px;">TRỰC TUYẾN</span>
</div>
""", unsafe_allow_html=True)

tab_dashboard, tab_upload = st.tabs(["📊 BẢNG ĐIỀU KHIỂN & PHÂN TÍCH CHUYÊN SÂU", "⚙️ TẢI LÊN DỮ LIỆU & RÀ SOÁT"])

# ==========================================
# TAB 2: TẢI LÊN & RÀ SOÁT DỮ LIỆU
# ==========================================
with tab_upload:
    st.markdown("### 📥 KHO DỮ LIỆU ĐẦU VÀO")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='upload-box'><h4>📂 1. DANH MỤC NPP & ĐỊA BÀN</h4></div>", unsafe_allow_html=True)
        file_npp = st.file_uploader("Tải file Danh mục (Chứa Mã KH, Tên NPP, Địa bàn...)", type=['xlsx'], key="npp")
        
    with col2:
        st.markdown("<div class='upload-box'><h4>📂 2. SẢN LƯỢNG & DOANH THU THÁNG</h4></div>", unsafe_allow_html=True)
        files_sales = st.file_uploader("Tải các file Sản lượng (T6, T7, T8...)", type=['xlsx'], accept_multiple_files=True, key="sales")
        
    if st.button("🚀 THỰC HIỆN KẾT NỐI MÃ_KH & XỬ LÝ DỮ LIỆU", use_container_width=True, type="primary"):
        if not file_npp or not files_sales:
            st.error("⚠️ **CẢNH BÁO:** Vui lòng tải lên đủ cả File Danh mục NPP và ít nhất 1 File Sản lượng!")
        else:
            errors = []
            with st.spinner("🔍 Hệ thống đang kiểm tra và liên kết Mã_KH..."):
                # --- A. ĐỌC VÀ LẤY MÃ KH FILE DANH MỤC ---
                try:
                    df_npp = read_excel_smart(file_npp)
                    c_npp_code = find_column(df_npp, ['ma kh', 'makh', 'ma khach hang'])
                    c_npp_name = find_column(df_npp, ['ten nha phan phoi', 'ten npp', 'khach hang'])
                    c_region = find_column(df_npp, ['dia ban', 'tinh', 'khu vuc'])
                    
                    if not c_npp_code:
                        errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Thiếu cột **'Mã KH'**.")
                    if not c_npp_name:
                        errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Thiếu cột **'Tên nhà phân phối / đại lý'**.")
                    if not c_region:
                        errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Thiếu cột **'Địa bàn tiêu thụ'**.")
                except Exception as e:
                    errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Lỗi đọc file ({e}).")

                # --- B. ĐỌC CÁC FILE SẢN LƯỢNG ---
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
                            errors.append(f"❌ **File Sản lượng (`{f.name}`):** Thiếu thông tin: **{', '.join(missing)}**.")
                        else:
                            # Forward fill Mã KH và Tên NPP
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
                        errors.append(f"❌ **File Sản lượng (`{f.name}`):** Lỗi đọc dữ liệu ({e}).")

            if errors:
                st.error("🚨 **PHÁT HIỆN LỖI CẤU TRÚC DỮ LIỆU!** Vui lòng điều chỉnh file theo phản hồi:")
                for err in errors: st.markdown(err)
            else:
                # Gộp dữ liệu theo Mã_KH
                df_npp_clean = df_npp[[c_npp_code, c_npp_name, c_region]].copy()
                df_npp_clean.columns = ['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']
                df_npp_clean['Ma_KH'] = df_npp_clean['Ma_KH'].astype(str).str.strip()
                
                df_all_sales = pd.concat(parsed_sales_list, ignore_index=True)
                df_all_sales['Ma_KH'] = df_all_sales['Ma_KH'].astype(str).str.strip()
                
                # Merge dữ liệu theo Mã_KH
                df_master = pd.merge(df_all_sales, df_npp_clean[['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']], on='Ma_KH', how='left')
                
                # Ưu tiên lấy Tên NPP chuẩn từ Danh mục, nếu không có lấy từ file sản lượng
                df_master['Ten_NPP'] = df_master['Ten_NPP_Master'].fillna(df_master['Ten_NPP'])
                df_master['Dia_Ban'] = df_master['Dia_Ban'].fillna('Chưa phân vùng')
                
                # Tạo cột thuyết minh đầy đủ: [Mã KH] - Tên NPP
                df_master['Thuyet_Minh_NPP'] = "[" + df_master['Ma_KH'] + "] - " + df_master['Ten_NPP'].astype(str)
                
                st.session_state['df_master'] = df_master
                st.success("🎉 **KẾT NỐI MÃ_KH THÀNH CÔNG!** Toàn bộ dữ liệu đã được đối soát chính xác theo Mã KH.")

# ==========================================
# TAB 1: BẢNG ĐIỀU KHIỂN & PHÂN TÍCH QUẢN TRỊ
# ==========================================
with tab_dashboard:
    df = st.session_state['df_master']
    
    if df.empty:
        st.warning("⚠️ **CHƯA CÓ DỮ LIỆU:** Vui lòng chuyển sang Tab **[⚙️ TẢI LÊN DỮ LIỆU & RÀ SOÁT]** để tải dữ liệu lên.")
    else:
        # --- BỘ LỌC ĐỘNG THAM CHIẾU MÃ KH ---
        st.markdown("### 🔍 BỘ LỌC CHUYÊN SÂU QUẢN TRỊ")
        f1, f2, f3, f4 = st.columns(4)
        with f1: sel_thang = st.multiselect("Kỳ Báo Cáo (Tháng)", sorted(df['Thang'].dropna().unique()))
        with f2: sel_db = st.multiselect("Địa Bàn (Thị Trường)", sorted(df['Dia_Ban'].dropna().unique()))
        with f3: sel_sp = st.multiselect("Dòng Sản Phẩm", sorted(df['Ten_SP'].dropna().unique()))
        with f4: sel_npp = st.multiselect("Nhà Phân Phối (Theo Mã_KH)", sorted(df['Thuyet_Minh_NPP'].dropna().unique()))
        
        df_filtered = df.copy()
        if sel_thang: df_filtered = df_filtered[df_filtered['Thang'].isin(sel_thang)]
        if sel_db: df_filtered = df_filtered[df_filtered['Dia_Ban'].isin(sel_db)]
        if sel_sp: df_filtered = df_filtered[df_filtered['Ten_SP'].isin(sel_sp)]
        if sel_npp: df_filtered = df_filtered[df_filtered['Thuyet_Minh_NPP'].isin(sel_npp)]
        
        # --- CÁC CHỈ SỐ KPI CHÍNH ---
        st.markdown("### 📈 CHỈ SỐ QUẢN TRỊ TỔNG QUAN")
        k1, k2, k3, k4 = st.columns(4)
        
        tong_dt = df_filtered['Doanh_Thu'].sum()
        tong_sl = df_filtered['San_Luong'].sum()
        so_npp = df_filtered['Ma_KH'].nunique()
        so_db = df_filtered['Dia_Ban'].nunique()
        
        with k1: st.markdown(f'<div class="dark-card"><div class="dark-card-title">TỔNG DOANH THU (ĐỒNG)</div><div class="dark-card-value">{tong_dt:,.0f}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="dark-card"><div class="dark-card-title">TỔNG SẢN LƯỢNG (BAO)</div><div class="dark-card-value">{tong_sl:,.0f}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="dark-card"><div class="dark-card-title">SỐ MÃ KH/NPP GIAO DỊCH</div><div class="dark-card-value">{so_npp}</div></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="dark-card"><div class="dark-card-title">ĐỘ PHỦ THỊ TRƯỜNG (TỈNH)</div><div class="dark-card-value">{so_db}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 4 SUB-TABS PHÂN TÍCH & GIẢI PHÁP BÁN HÀNG ---
        sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs([
            "🚨 CẢNH BÁO BIẾN ĐỘNG & ĐỀ XUẤT GIẢI PHÁP", 
            "🛍️ PHÂN TÍCH SẢN PHẨM & CƠ CẤU", 
            "🌍 PHÂN TÍCH THỊ TRƯỜNG & ĐỊA BÀN", 
            "📋 BẢNG THAM CHIẾU MÃ_KH CHI TIẾT"
        ])
        
        # TAB 1: CẢNH BÁO & GIẢI PHÁP
        with sub_t1:
            st.markdown("#### 🚨 Đánh giá Biến động Doanh thu & Sản lượng MoM theo Mã_KH")
            c1, c2 = st.columns(2)
            all_months = sorted(df['Thang'].dropna().unique().tolist())
            with c1: curr_m = st.selectbox("Chọn Kỳ Báo Cáo:", all_months, index=len(all_months)-1 if len(all_months)>0 else 0)
            with c2: comp_m = st.selectbox("Chọn Kỳ Đối Soát:", all_months, index=max(0, len(all_months)-2) if len(all_months)>0 else 0)
            
            if curr_m != comp_m:
                df_curr = df_filtered[df_filtered['Thang'] == curr_m].groupby(['Ma_KH', 'Thuyet_Minh_NPP']).agg({'San_Luong': 'sum', 'Doanh_Thu': 'sum'}).reset_index()
                df_comp = df_filtered[df_filtered['Thang'] == comp_m].groupby(['Ma_KH', 'Thuyet_Minh_NPP']).agg({'San_Luong': 'sum', 'Doanh_Thu': 'sum'}).reset_index()
                
                merged = pd.merge(df_curr, df_comp, on=['Ma_KH', 'Thuyet_Minh_NPP'], how='outer', suffixes=('_KyBaoCao', '_KySoSanh')).fillna(0)
                merged['ChenhLech_SL'] = merged['San_Luong_KyBaoCao'] - merged['San_Luong_KySoSanh']
                merged['ChenhLech_DT'] = merged['Doanh_Thu_KyBaoCao'] - merged['Doanh_Thu_KySoSanh']
                merged['Tyle_MoM_SL(%)'] = (merged['ChenhLech_SL'] / merged['San_Luong_KySoSanh'].replace(0, 1) * 100).round(2)
                
                def get_alert(pct):
                    if pct <= -15: return "🔴 Báo động đỏ (Giảm >15%)"
                    elif -15 < pct <= -5: return "🟡 Cảnh báo giảm"
                    elif pct >= 15: return "🟢 Tăng trưởng tốt"
                    return "⚪ Đi ngang"
                
                merged['Trang_Thai'] = merged['Tyle_MoM_SL(%)'].apply(get_alert)
                
                st.dataframe(
                    merged[['Ma_KH', 'Thuyet_Minh_NPP', 'San_Luong_KySoSanh', 'San_Luong_KyBaoCao', 'ChenhLech_SL', 'Tyle_MoM_SL(%)', 'Doanh_Thu_KyBaoCao', 'Trang_Thai']]
                    .sort_values(by='ChenhLech_SL', ascending=True), 
                    use_container_width=True
                )
                
                # GIẢI PHÁP CHO BỘ PHẬN BÁN HÀNG
                st.markdown("### 💡 ĐỀ XUẤT GIẢI PHÁP CHO BỘ PHẬN BÁN HÀNG")
                bad_npps = merged[merged['Tyle_MoM_SL(%)'] <= -15]
                
                if not bad_npps.empty:
                    st.markdown(f"Có **{len(bad_npps)} Nhà phân phối** rơi vào ngưỡng **🔴 Báo động đỏ (Giảm trên 15%)**.")
                    for _, row in bad_npps.iterrows():
                        st.markdown(f"""
                        <div class="solution-box">
                            <b>Mã KH: {row['Ma_KH']} - {row['Thuyet_Minh_NPP']}</b><br>
                            - 📉 <i>Sản lượng giảm:</i> <b>{row['ChenhLech_SL']:,.0f} bao</b> ({row['Tyle_MoM_SL(%)']}%)<br>
                            - 🎯 <b>Giải pháp bán hàng đề xuất:</b><br>
                              1. Giám sát bán hàng (SS) làm việc trực tiếp để kiểm tra tồn kho tại kho Đại lý.<br>
                              2. Rà soát chính sách chiết khấu, chương trình khuyến mãi đối thủ cạnh tranh trên địa bàn.<br>
                              3. Đẩy mạnh các dòng sản phẩm chủ lực để bù đắp sản lượng hụt.
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("🎉 Tất cả các Nhà phân phối đều duy trì đà tăng trưởng tốt, không có mã khách hàng nào rơi vào diện báo động đỏ!")

            else:
                st.info("Vui lòng chọn 2 kỳ báo cáo khác nhau để đối soát.")

        # TAB 2: PHÂN TÍCH SẢN PHẨM
        with sub_t2:
            st.markdown("#### 🛍️ Phân Tích Hiệu Quả Kinh Doanh Theo Sản Phẩm")
            prod_summary = df_filtered.groupby('Ten_SP').agg({'San_Luong': 'sum', 'Doanh_Thu': 'sum'}).reset_index()
            prod_summary['Don_Gia_TB'] = (prod_summary['Doanh_Thu'] / prod_summary['San_Luong'].replace(0, 1)).round(0)
            prod_summary = prod_summary.sort_values(by='San_Luong', ascending=False)
            
            r1, r2 = st.columns(2)
            with r1:
                fig_prod = px.bar(prod_summary, x='San_Luong', y='Ten_SP', orientation='h', color='Doanh_Thu', title="Top Sản Phẩm Theo Sản Lượng (Bao)")
                fig_prod.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
                st.plotly_chart(fig_prod, use_container_width=True)
            with r2:
                st.markdown("**Bảng Tổng Hợp Sản Phẩm & Đơn Giá TB**")
                st.dataframe(prod_summary, use_container_width=True)

        # TAB 3: PHÂN TÍCH THỊ TRƯỜNG & ĐỊA BÀN
        with sub_t3:
            st.markdown("#### 🌍 Phân Tích Cơ Cấu Tiêu Thụ Theo Địa Bàn / Tỉnh Thành")
            r1, r2 = st.columns(2)
            with r1:
                region_df = df_filtered.groupby('Dia_Ban').agg({'San_Luong':'sum', 'Doanh_Thu':'sum'}).reset_index()
                fig_region = px.pie(region_df, names='Dia_Ban', values='San_Luong', hole=0.4, title="Cơ Cấu Tỷ Trọng Sản Lượng Theo Địa Bàn")
                fig_region.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
                st.plotly_chart(fig_region, use_container_width=True)
            with r2:
                fig_region_dt = px.bar(region_df, x='Dia_Ban', y='Doanh_Thu', title="Doanh Thu Tiêu Thụ Theo Địa Bàn (Đồng)")
                fig_region_dt.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
                st.plotly_chart(fig_region_dt, use_container_width=True)

        # TAB 4: BẢNG DỮ LIỆU THAM CHIẾU
        with sub_t4:
            st.markdown("#### 📋 Dữ Liệu Tham Chiếu Gốc Chuẩn Hóa Mã_KH")
            st.dataframe(
                df_filtered[['Thang', 'Ma_KH', 'Ten_NPP', 'Dia_Ban', 'Ten_SP', 'San_Luong', 'Doanh_Thu']], 
                use_container_width=True
            )
