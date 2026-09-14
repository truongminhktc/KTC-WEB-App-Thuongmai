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
</style>
"""
st.markdown(CUSTOM_DARK_CSS, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ & RÀ SOÁT DỮ LIỆU THÔNG MINH ---
def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    s1 = unicodedata.normalize('NFKD', input_str).encode('ASCII', 'ignore').decode('utf-8')
    return s1.lower().strip()

def read_excel_smart(file_obj):
    """ Tự động tìm dòng tiêu đề (header) thực sự của file Excel KHATOCO """
    df_raw = pd.read_excel(file_obj)
    header_idx = None
    
    # Quét 15 dòng đầu tiên để tìm dòng chứa tiêu đề bảng
    for i in range(min(15, len(df_raw))):
        row_str = " ".join(df_raw.iloc[i].dropna().astype(str).tolist()).lower()
        row_str_norm = remove_accents(row_str)
        if any(kw in row_str_norm for kw in ['ma kh', 'ten nha phan phoi', 'npp', 'san pham', 'dia ban']):
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
    """ Tìm tên cột dựa trên danh sách từ khóa """
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
        <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">App: KTC-WEB-App-Thuongmai | Hệ thống phân tích & Kiểm soát Tự Động v3.1</div>
    </div>
    <span style="background: #064E3B; color: #6EE7B7; border: 1px solid #065F46; padding: 4px 12px; border-radius: 12px;">TRỰC TUYẾN</span>
</div>
""", unsafe_allow_html=True)

tab_dashboard, tab_upload = st.tabs(["📊 BẢNG ĐIỀU KHIỂN & PHÂN TÍCH", "⚙️ TẢI LÊN DỮ LIỆU (KÉO THẢ)"])

# ==========================================
# TAB 2: KHU VỰC CẬP NHẬT & RÀ SOÁT DỮ LIỆU
# ==========================================
with tab_upload:
    st.markdown("### 📥 KHO DỮ LIỆU ĐẦU VÀO")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='upload-box'><h4>📂 1. DANH MỤC NPP & ĐỊA BÀN</h4></div>", unsafe_allow_html=True)
        file_npp = st.file_uploader("Tải 1 file Danh mục (Danh muc NPP...xlsx)", type=['xlsx'], key="npp")
        
    with col2:
        st.markdown("<div class='upload-box'><h4>📂 2. SẢN LƯỢNG TIÊU THỤ</h4></div>", unsafe_allow_html=True)
        files_sales = st.file_uploader("Tải các file Sản lượng (T6, T7, T8...)", type=['xlsx'], accept_multiple_files=True, key="sales")
        
    if st.button("🚀 THỰC HIỆN XỬ LÝ & RÀ SOÁT DỮ LIỆU", use_container_width=True, type="primary"):
        if not file_npp or not files_sales:
            st.error("⚠️ **CẢNH BÁO:** Vui lòng tải lên đầy đủ cả 2 mục: File Danh mục NPP và ít nhất 1 File Sản lượng!")
        else:
            errors = []
            
            with st.spinner("🔍 Hệ thống đang kiểm tra tính hợp lệ của cấu trúc file..."):
                # --- A. RÀ SOÁT FILE DANH MỤC NPP ---
                try:
                    df_npp = read_excel_smart(file_npp)
                    c_npp_name = find_column(df_npp, ['ten nha phan phoi', 'ten npp', 'khach hang'])
                    c_region = find_column(df_npp, ['dia ban', 'tinh', 'khu vuc'])
                    
                    if not c_npp_name:
                        errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Không tìm thấy cột **'Tên nhà phân phối'**. (Cột hiện có: `{list(df_npp.columns)}`)")
                    if not c_region:
                        errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** Không tìm thấy cột **'Địa bàn tiêu thụ'**. (Cột hiện có: `{list(df_npp.columns)}`)")
                except Exception as e:
                    errors.append(f"❌ **File Danh mục (`{file_npp.name}`):** File bị lỗi định dạng hoặc hỏng ({e}).")

                # --- B. RÀ SOÁT CÁC FILE SẢN LƯỢNG ---
                parsed_sales_list = []
                for f in files_sales:
                    try:
                        df_temp = read_excel_smart(f)
                        c_npp = find_column(df_temp, ['ten nha phan phoi', 'ten npp', 'khach hang'])
                        c_sp = find_column(df_temp, ['san pham', 'ten sp', 'hang hoa'])
                        c_sl = find_column(df_temp, ['so luong', 'san luong', 'slg'])
                        c_dt = find_column(df_temp, ['doanh thu', 'thanh tien'])
                        
                        missing_cols = []
                        if not c_npp: missing_cols.append("Tên nhà phân phối")
                        if not c_sp: missing_cols.append("Sản phẩm")
                        if not c_sl: missing_cols.append("Số lượng / Sản lượng")
                        
                        if missing_cols:
                            errors.append(f"❌ **File Sản lượng (`{f.name}`):** Thiếu các cột quan trọng: **{', '.join(missing_cols)}**. (Các cột đọc được: `{list(df_temp.columns)}`)")
                        else:
                            # Chuẩn hóa cột
                            df_temp = df_temp.rename(columns={c_npp: 'Ten_NPP', c_sp: 'Ten_SP', c_sl: 'San_Luong'})
                            if c_dt: df_temp = df_temp.rename(columns={c_dt: 'Doanh_Thu'})
                            else: df_temp['Doanh_Thu'] = 0
                            
                            # Xóa các dòng tổng cộng hoặc tiêu đề nhóm
                            df_temp = df_temp.dropna(subset=['Ten_SP'])
                            df_temp['Ten_NPP'] = df_temp['Ten_NPP'].ffill()
                            
                            month_match = re.search(r'T(\d{1,2})', f.name, re.IGNORECASE)
                            df_temp['Thang'] = f"Tháng {int(month_match.group(1)):02d}" if month_match else f.name
                            parsed_sales_list.append(df_temp)
                    except Exception as e:
                        errors.append(f"❌ **File Sản lượng (`{f.name}`):** Không thể đọc dữ liệu ({e}).")

            # --- C. HIỂN THỊ CẢNH BÁO HƯỚNG DẪN HOẶC HOÀN TẤT ---
            if errors:
                st.error("🚨 **PHÁT HIỆN LỖI DỮ LIỆU ĐẦU VÀO!** Vui lòng kiểm tra và sửa lại theo hướng dẫn dưới đây:")
                for err in errors:
                    st.markdown(err)
                st.info("""
                🛠️ **HƯỚNG DẪN KHẮC PHỤC TRONG 30 GIÂY:**
                1. Mở file Excel bị báo lỗi ở trên.
                2. Kiểm tra dòng chứa tiêu đề (STT, Mã KH, Tên nhà phân phối, Sản phẩm, Số lượng, Doanh thu...).
                3. Đảm bảo các từ khóa quan trọng không bị viết tắt quá lạ hoặc để ô trống.
                4. Lưu lại file và tiến hành kéo thả lại vào ứng dụng.
                """)
            else:
                # Xử lý gộp dữ liệu Master
                df_npp_clean = df_npp[[c_npp_name, c_region]].rename(columns={c_npp_name: 'Ten_NPP', c_region: 'Dia_Ban'})
                df_npp_clean['Ten_NPP_Key'] = df_npp_clean['Ten_NPP'].astype(str).apply(remove_accents)
                
                df_all_sales = pd.concat(parsed_sales_list, ignore_index=True)
                df_all_sales['Ten_NPP_Key'] = df_all_sales['Ten_NPP'].astype(str).apply(remove_accents)
                
                df_master = pd.merge(df_all_sales, df_npp_clean[['Ten_NPP_Key', 'Dia_Ban']], on='Ten_NPP_Key', how='left')
                df_master['Dia_Ban'] = df_master['Dia_Ban'].fillna('Chưa phân vùng')
                
                st.session_state['df_master'] = df_master
                st.success("🎉 **XỬ LÝ THÀNH CÔNG!** Dữ liệu đã hợp lệ 100%. Vui lòng bấm sang Tab **[📊 BẢNG ĐIỀU KHIỂN & PHÂN TÍCH]** để xem báo cáo.")

# ==========================================
# TAB 1: BẢNG ĐIỀU KHIỂN & PHÂN TÍCH QUẢN TRỊ
# ==========================================
with tab_dashboard:
    df = st.session_state['df_master']
    
    if df.empty:
        st.warning("⚠️ **CHƯA CÓ DỮ LIỆU:** Vui lòng chuyển sang Tab **[⚙️ TẢI LÊN DỮ LIỆU]** để tải các file Excel báo cáo lên.")
    else:
        # --- BỘ LỌC ĐỘNG ---
        st.markdown("### 🔍 BỘ LỌC DỮ LIỆU")
        f1, f2, f3, f4 = st.columns(4)
        with f1: sel_thang = st.multiselect("Tháng", sorted(df['Thang'].dropna().unique()))
        with f2: sel_db = st.multiselect("Địa Bàn", sorted(df['Dia_Ban'].dropna().unique()))
        with f3: sel_sp = st.multiselect("Sản Phẩm", sorted(df['Ten_SP'].dropna().unique()))
        with f4: sel_npp = st.multiselect("Nhà Phân Phối", sorted(df['Ten_NPP'].dropna().unique()))
        
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
        
        with k1: st.markdown(f'<div class="dark-card"><div class="dark-card-title">TỔNG DOANH THU (ĐỒNG)</div><div class="dark-card-value">{tong_dt:,.0f}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="dark-card"><div class="dark-card-title">TỔNG SẢN LƯỢNG (BAO)</div><div class="dark-card-value">{tong_sl:,.0f}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="dark-card"><div class="dark-card-title">NPP PHÁT SINH GIAO DỊCH</div><div class="dark-card-value">{so_npp}</div></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="dark-card"><div class="dark-card-title">ĐỘ PHỦ THỊ TRƯỜNG</div><div class="dark-card-value">{so_db} <span style="font-size:14px; font-weight:normal;">Tỉnh/Thành</span></div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 3 SUB-TABS PHÂN TÍCH QUẢN TRỊ ---
        sub_t1, sub_t2, sub_t3 = st.tabs(["🚨 CẢNH BÁO BIẾN ĐỘNG MoM", "📊 PHÂN TÍCH XU HƯỚNG & CƠ CẤU", "📋 BẢNG DỮ LIỆU CHI TIẾT"])
        
        with sub_t1:
            st.markdown("#### Đánh giá Tăng/Giảm Sản lượng giữa 2 kỳ")
            c1, c2 = st.columns(2)
            all_months = sorted(df['Thang'].dropna().unique().tolist())
            with c1: curr_m = st.selectbox("Chọn Kỳ báo cáo (Tháng gần nhất):", all_months, index=len(all_months)-1 if len(all_months)>0 else 0)
            with c2: comp_m = st.selectbox("Chọn Kỳ đối soát (Tháng liền trước):", all_months, index=max(0, len(all_months)-2) if len(all_months)>0 else 0)
            
            if curr_m != comp_m:
                df_curr = df_filtered[df_filtered['Thang'] == curr_m].groupby('Ten_NPP').agg({'San_Luong': 'sum', 'Doanh_Thu': 'sum'}).reset_index()
                df_comp = df_filtered[df_filtered['Thang'] == comp_m].groupby('Ten_NPP').agg({'San_Luong': 'sum', 'Doanh_Thu': 'sum'}).reset_index()
                
                merged = pd.merge(df_curr, df_comp, on='Ten_NPP', how='outer', suffixes=('_KyBaoCao', '_KySoSanh')).fillna(0)
                merged['ChenhLech_SL'] = merged['San_Luong_KyBaoCao'] - merged['San_Luong_KySoSanh']
                merged['Tyle_MoM(%)'] = (merged['ChenhLech_SL'] / merged['San_Luong_KySoSanh'].replace(0, 1) * 100).round(2)
                
                def get_alert(pct):
                    if pct <= -15: return "🔴 Báo động đỏ (Giảm mạnh)"
                    elif -15 < pct <= -5: return "🟡 Cảnh báo (Giảm)"
                    elif pct >= 15: return "🟢 Tăng trưởng tốt"
                    return "⚪ Đi ngang"
                
                merged['Trang_Thai'] = merged['Tyle_MoM(%)'].apply(get_alert)
                st.dataframe(merged.sort_values(by='ChenhLech_SL', ascending=True), use_container_width=True)
            else:
                st.info("Vui lòng chọn 2 kỳ khác nhau để hệ thống tính toán chênh lệch.")

        with sub_t2:
            r1, r2 = st.columns(2)
            with r1:
                st.markdown("**1. Xu Hướng Sản Lượng Qua Các Tháng**")
                trend_df = df_filtered.groupby('Thang').agg({'San_Luong':'sum'}).reset_index()
                fig1 = px.line(trend_df, x='Thang', y='San_Luong', markers=True, title="Biểu Đồ Biến Động Sản Lượng")
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
                st.plotly_chart(fig1, use_container_width=True)
                
            with r2:
                st.markdown("**2. Cơ Cấu Tiêu Thụ Theo Địa Bàn**")
                pie_df = df_filtered.groupby('Dia_Ban').agg({'San_Luong':'sum'}).reset_index()
                fig2 = px.pie(pie_df, names='Dia_Ban', values='San_Luong', hole=0.4, title="Tỷ Trọng Sản Lượng Theo Tỉnh/Thành")
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
                st.plotly_chart(fig2, use_container_width=True)
                
            st.markdown("**3. Phân Tích Chuyên Sâu Theo Mặt Hàng Sản Phẩm**")
            prod_df = df_filtered.groupby('Ten_SP').agg({'San_Luong':'sum', 'Doanh_Thu':'sum'}).reset_index().sort_values(by='San_Luong', ascending=False)
            fig3 = px.bar(prod_df, x='Ten_SP', y='San_Luong', color='Doanh_Thu', title="Sản Lượng & Doanh Thu Chi Tiết Theo Sản Phẩm")
            fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
            st.plotly_chart(fig3, use_container_width=True)

        with sub_t3:
            st.markdown("#### Bảng Dữ Liệu Chi Tiết")
            st.dataframe(df_filtered[['Thang', 'Dia_Ban', 'Ten_NPP', 'Ten_SP', 'San_Luong', 'Doanh_Thu']], use_container_width=True)
