import streamlit as st
import pandas as pd
import re
import unicodedata
import io

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG & CÁC HÀM BỔ TRỢ
# ---------------------------------------------------------
st.set_page_config(
    page_title="Hệ thống Báo cáo & Phân tích Doanh số",
    page_icon="📊",
    layout="wide"
)

def remove_accents(input_str):
    """Loại bỏ dấu tiếng Việt để so sánh tên cột linh hoạt hơn"""
    if not isinstance(input_str, str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

# ---------------------------------------------------------
# 2. HÀM XỬ LÝ DỮ LIỆU CÓ CACHE THÔNG MINH
# ---------------------------------------------------------
@st.cache_data
def process_excel_files(file_npp_bytes, files_sales_tuples):
    """
    Nhận dữ liệu thô dạng bytes để phục vụ streamlit caching,
    dùng io.BytesIO() để pandas đọc dữ liệu Excel an toàn.
    """
    try:
        # --- A. Đọc File Danh mục NPP ---
        df_npp_raw = pd.read_excel(io.BytesIO(file_npp_bytes))
        
        # Tìm hàng tiêu đề chứa 'mã kh' hoặc 'stt'
        header_idx = None
        for i in range(min(15, len(df_npp_raw))):
            row_str = " ".join(df_npp_raw.iloc[i].dropna().astype(str).tolist())
            if 'ma kh' in remove_accents(row_str) or 'stt' in remove_accents(row_str):
                header_idx = i
                break
                
        if header_idx is not None and header_idx > 0:
            df_npp = pd.read_excel(io.BytesIO(file_npp_bytes), header=header_idx)
        else:
            df_npp = df_npp_raw

        df_npp.columns = [str(c).strip() for c in df_npp.columns]
        
        c_npp_code = next((c for c in df_npp.columns if 'ma kh' in remove_accents(c)), None)
        c_npp_name = next((c for c in df_npp.columns if 'ten nha phan phoi' in remove_accents(c) or 'ten npp' in remove_accents(c)), None)
        c_region = next((c for c in df_npp.columns if 'dia ban' in remove_accents(c) or 'tinh' in remove_accents(c)), None)
        
        if not c_npp_code or not c_npp_name or not c_region:
            return None, f"⚠️ File Danh mục NPP thiếu các cột cần thiết (Mã KH, Tên NPP, Địa bàn/Tỉnh). Các cột tìm thấy: {list(df_npp.columns)}"
            
        df_npp_clean = df_npp[[c_npp_code, c_npp_name, c_region]].copy()
        df_npp_clean.columns = ['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']
        df_npp_clean['Ma_KH'] = df_npp_clean['Ma_KH'].astype(str).str.strip()
        df_npp_clean = df_npp_clean.drop_duplicates(subset=['Ma_KH'])
        
        # --- B. Đọc các File Sản lượng Tháng ---
        parsed_sales_list = []
        
        for fname, fbytes in files_sales_tuples:
            df_temp_raw = pd.read_excel(io.BytesIO(fbytes))
            
            h_idx = None
            for i in range(min(15, len(df_temp_raw))):
                row_str = " ".join(df_temp_raw.iloc[i].dropna().astype(str).tolist())
                if 'ma kh' in remove_accents(row_str) or 'stt' in remove_accents(row_str):
                    h_idx = i
                    break
            
            if h_idx is not None and h_idx > 0:
                df_temp = pd.read_excel(io.BytesIO(fbytes), header=h_idx)
            else:
                df_temp = df_temp_raw
                
            df_temp.columns = [str(c).strip() for c in df_temp.columns]
            
            c_code = next((c for c in df_temp.columns if 'ma kh' in remove_accents(c)), None)
            c_name = next((c for c in df_temp.columns if 'ten npp' in remove_accents(c) or 'ten nha phan phoi' in remove_accents(c)), None)
            c_sp = next((c for c in df_temp.columns if 'san pham' in remove_accents(c) or 'ten sp' in remove_accents(c)), None)
            c_sl = next((c for c in df_temp.columns if 'so luong' in remove_accents(c) or 'san luong' in remove_accents(c)), None)
            c_dt = next((c for c in df_temp.columns if 'doanh thu' in remove_accents(c) or 'thanh tien' in remove_accents(c)), None)
            
            if not c_sp:
                continue
                
            # Điền bù dữ liệu Mã KH & Tên NPP bị rỗng do merge cell
            if c_code: df_temp[c_code] = df_temp[c_code].ffill()
            if c_name: df_temp[c_name] = df_temp[c_name].ffill()
            
            # Lọc bỏ dòng trống Sản phẩm
            df_temp = df_temp.dropna(subset=[c_sp]).copy()
            
            # Chuẩn hóa tên cột
            rename_dict = {c_sp: 'Ten_SP'}
            if c_code: rename_dict[c_code] = 'Ma_KH'
            if c_name: rename_dict[c_name] = 'Ten_NPP'
            if c_sl: rename_dict[c_sl] = 'San_Luong'
            if c_dt: rename_dict[c_dt] = 'Doanh_Thu'
            
            df_temp = df_temp.rename(columns=rename_dict)
            
            if 'Ma_KH' not in df_temp.columns: df_temp['Ma_KH'] = 'UNKNOWN'
            if 'Ten_NPP' not in df_temp.columns: df_temp['Ten_NPP'] = 'Chưa xác định'
            if 'San_Luong' not in df_temp.columns: df_temp['San_Luong'] = 0
            if 'Doanh_Thu' not in df_temp.columns: df_temp['Doanh_Thu'] = 0
            
            # Ép kiểu dữ liệu số
            df_temp['San_Luong'] = pd.to_numeric(df_temp['San_Luong'], errors='coerce').fillna(0)
            df_temp['Doanh_Thu'] = pd.to_numeric(df_temp['Doanh_Thu'], errors='coerce').fillna(0)
            
            # Nhận diện tháng từ tên file (Ví dụ: San luong T6 2026.xlsx -> Tháng 06)
            month_match = re.search(r'T(\d{1,2})', fname, re.IGNORECASE)
            if month_match:
                m_num = int(month_match.group(1))
                df_temp['Thang'] = f"Tháng {m_num:02d}"
            else:
                df_temp['Thang'] = fname
                
            parsed_sales_list.append(df_temp[['Ma_KH', 'Ten_NPP', 'Ten_SP', 'San_Luong', 'Doanh_Thu', 'Thang']])
            
        if not parsed_sales_list:
            return None, "⚠️ Không thể đọc được dữ liệu sản lượng từ các file đã tải lên."
            
        df_all_sales = pd.concat(parsed_sales_list, ignore_index=True)
        df_all_sales['Ma_KH'] = df_all_sales['Ma_KH'].astype(str).str.strip()
        
        # --- C. Kết nối Mã KH từ Master với Dữ liệu Sản lượng ---
        df_master = pd.merge(df_all_sales, df_npp_clean[['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']], on='Ma_KH', how='left')
        
        # Ưu tiên lấy tên chuẩn Master, nếu không có lấy tên gốc trong file tháng
        df_master['Ten_NPP'] = df_master['Ten_NPP_Master'].fillna(df_master['Ten_NPP'])
        df_master['Dia_Ban'] = df_master['Dia_Ban'].fillna('Chưa phân vùng')
        
        # Thuyết minh NPP dạng: [MÃ KH] - Tên NPP
        df_master['Thuyet_Minh_NPP'] = "[" + df_master['Ma_KH'] + "] - " + df_master['Ten_NPP'].astype(str)
        
        return df_master, None

    except Exception as e:
        return None, f"⚠️ Đã xảy ra lỗi khi xử lý tập tin: {str(e)}"

# ---------------------------------------------------------
# 3. GIAO DIỆN CHÍNH (UI)
# ---------------------------------------------------------
st.title("📊 TẢI LÊN DỮ LIỆU BÁO CÁO")

tab1, tab2 = st.tabs(["🚀 TẢI LÊN & ĐỐI SOÁT DỮ LIỆU", "📈 BẢNG ĐIỀU KHIỂN & PHÂN TÍCH CHI TIẾT"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        file_npp = st.file_uploader(
            "📁 Upload File Danh mục (Danh muc NPP...xlsx)",
            type=["xlsx", "xls"],
            key="uploader_npp"
        )
    with col2:
        files_sales = st.file_uploader(
            "📁 Upload các File Sản lượng Tháng (T6, T7, T8...)",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key="uploader_sales"
        )
        
    btn_process = st.button("📌 NẠP DỮ LIỆU & KẾT NỐI MÃ_KH", type="primary", use_container_width=True)

    if btn_process:
        if not file_npp:
            st.warning("⚠️ Vui lòng tải lên file Danh mục NPP.")
        elif not files_sales:
            st.warning("⚠️ Vui lòng tải lên ít nhất một file Sản lượng tháng.")
        else:
            with st.spinner("⏳ Đang đọc và kết nối dữ liệu từ các tập tin..."):
                # Chuẩn bị bytes để truyền vào hàm cached
                npp_bytes = file_npp.read()
                sales_tuples = tuple((f.name, f.read()) for f in files_sales)
                
                df_res, err = process_excel_files(npp_bytes, sales_tuples)
                
                if err:
                    st.error(err)
                else:
                    st.session_state["df_master"] = df_res
                    st.success(f"✅ Đã nạp thành công {len(df_res):,} dòng dữ liệu!")

    # Hiển thị dữ liệu xem trước nếu đã xử lý xong
    if "df_master" in st.session_state:
        st.markdown("---")
        st.subheader("🔍 Dữ liệu sau khi kết nối (Preview)")
        st.dataframe(st.session_state["df_master"].head(50), use_container_width=True)

with tab2:
    if "df_master" not in st.session_state:
        st.info("👋 Vui lòng nạp dữ liệu ở Tab **TẢI LÊN & ĐỐI SOÁT DỮ LIỆU** trước.")
    else:
        df = st.session_state["df_master"]
        st.subheader("📊 Tổng quan dữ liệu")
        
        # Bộ lọc
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_thang = st.multiselect("Lọc theo Tháng:", options=sorted(df['Thang'].unique()), default=sorted(df['Thang'].unique()))
        with col_f2:
            selected_diaban = st.multiselect("Lọc theo Địa bàn:", options=sorted(df['Dia_Ban'].unique()), default=sorted(df['Dia_Ban'].unique()))
            
        df_filtered = df[(df['Thang'].isin(selected_thang)) & (df['Dia_Ban'].isin(selected_diaban))]
        
        # Các chỉ số Metric
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng Sản Lượng", f"{df_filtered['San_Luong'].sum():,.0f}")
        m2.metric("Tổng Doanh Thu", f"{df_filtered['Doanh_Thu'].sum():,.0f} VNĐ")
        m3.metric("Số Nhà Phân Phối", f"{df_filtered['Ma_KH'].nunique():,}")
        m4.metric("Số Mặt Hàng", f"{df_filtered['Ten_SP'].nunique():,}")
        
        st.markdown("---")
        st.subheader("📋 Bảng chi tiết sản lượng theo Nhà Phân Phối")
        
        pivot_df = df_filtered.pivot_table(
            index=['Dia_Ban', 'Thuyet_Minh_NPP', 'Ten_SP'],
            columns='Thang',
            values='San_Luong',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        st.dataframe(pivot_df, use_container_width=True)
