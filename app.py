import streamlit as st
import pandas as pd
import re
import unicodedata
import io

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Hệ thống Báo cáo & Phân tích Doanh số",
    page_icon="📊",
    layout="wide"
)

def remove_accents(input_str):
    """Loại bỏ dấu tiếng Việt và ký tự đặc biệt để so sánh tên cột linh hoạt"""
    if pd.isna(input_str) or input_str is None:
        return ""
    s = str(input_str).strip()
    nfkd_form = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

def read_excel_smart(file_bytes):
    """
    Đọc file Excel thông minh: Tự động duyệt các dòng đầu để tìm dòng tiêu đề thực sự,
    tránh lỗi Unnamed do ô trống hoặc tiêu đề báo cáo ở dòng 1.
    """
    df_raw = pd.read_excel(io.BytesIO(file_bytes), header=None)
    
    header_idx = None
    # Quét 20 dòng đầu tiên để tìm dòng chứa tiêu đề
    for i in range(min(20, len(df_raw))):
        row_str = " ".join([remove_accents(x) for x in df_raw.iloc[i].values if pd.notna(x)])
        if any(k in row_str for k in ['ma kh', 'makh', 'ma npp', 'stt', 'ten npp', 'ten kh']):
            header_idx = i
            break
            
    if header_idx is not None:
        headers = [str(x).strip() if pd.notna(x) else f"Unnamed: {idx}" for idx, x in enumerate(df_raw.iloc[header_idx].values)]
        df = df_raw.iloc[header_idx + 1:].copy()
        df.columns = headers
    else:
        df = df_raw.copy()
        df.columns = [str(c).strip() for c in df.columns]
        
    return df

# ---------------------------------------------------------
# 2. XỬ LÝ DỮ LIỆU & THAM CHIẾU THEO MÃ_KH
# ---------------------------------------------------------
@st.cache_data
def process_excel_files(file_npp_bytes, files_sales_tuples):
    try:
        # --- A. Đọc và chuẩn hóa File Danh mục NPP (Master Data) ---
        df_npp = read_excel_smart(file_npp_bytes)
        
        # Nhận diện cột trong File Danh mục
        c_npp_code = next((c for c in df_npp.columns if any(k in remove_accents(c) for k in ['ma kh', 'makh', 'ma npp', 'ma khach hang'])), None)
        c_npp_name = next((c for c in df_npp.columns if any(k in remove_accents(c) for k in ['ten npp', 'ten nha phan phoi', 'ten khach hang', 'ten kh'])), None)
        c_region = next((c for c in df_npp.columns if any(k in remove_accents(c) for k in ['dia ban', 'tinh', 'khu vuc', 'vung'])), None)
        
        if not c_npp_code:
            return None, f"⚠️ Không tìm thấy cột 'Mã KH' trong File Danh mục NPP. Các cột phát hiện được: {list(df_npp.columns)}"
            
        # Tạo bảng Master gọn nhẹ
        cols_to_keep = [c_npp_code]
        if c_npp_name: cols_to_keep.append(c_npp_name)
        if c_region: cols_to_keep.append(c_region)
        
        df_npp_clean = df_npp[cols_to_keep].copy()
        
        # Đổi tên cột chuẩn
        rename_master = {c_npp_code: 'Ma_KH'}
        if c_npp_name: rename_master[c_npp_name] = 'Ten_NPP_Master'
        if c_region: rename_master[c_region] = 'Dia_Ban'
        df_npp_clean = df_npp_clean.rename(columns=rename_master)
        
        # Làm sạch Mã KH trong Master
        df_npp_clean['Ma_KH'] = df_npp_clean['Ma_KH'].astype(str).str.strip()
        df_npp_clean = df_npp_clean.dropna(subset=['Ma_KH'])
        df_npp_clean = df_npp_clean[df_npp_clean['Ma_KH'] != 'nan']
        df_npp_clean = df_npp_clean.drop_duplicates(subset=['Ma_KH'])

        if 'Ten_NPP_Master' not in df_npp_clean.columns:
            df_npp_clean['Ten_NPP_Master'] = df_npp_clean['Ma_KH']
        if 'Dia_Ban' not in df_npp_clean.columns:
            df_npp_clean['Dia_Ban'] = 'Chưa phân vùng'

        # --- B. Đọc các File Sản lượng Tháng & Lấy Mã_KH ---
        parsed_sales_list = []
        
        for fname, fbytes in files_sales_tuples:
            df_temp = read_excel_smart(fbytes)
            
            c_code = next((c for c in df_temp.columns if any(k in remove_accents(c) for k in ['ma kh', 'makh', 'ma npp', 'ma khach hang'])), None)
            c_name = next((c for c in df_temp.columns if any(k in remove_accents(c) for k in ['ten npp', 'ten nha phan phoi', 'ten kh'])), None)
            c_sp = next((c for c in df_temp.columns if any(k in remove_accents(c) for k in ['san pham', 'ten sp', 'mat hang'])), None)
            c_sl = next((c for c in df_temp.columns if any(k in remove_accents(c) for k in ['so luong', 'san luong', 'sl'])), None)
            c_dt = next((c for c in df_temp.columns if any(k in remove_accents(c) for k in ['doanh thu', 'thanh tien', 'giao dich'])), None)
            
            if not c_sp:
                continue # Bỏ qua nếu không có cột sản phẩm
                
            # Điền bù dữ liệu Mã KH nếu bị empty do merge cell dọc
            if c_code: df_temp[c_code] = df_temp[c_code].ffill()
            if c_name: df_temp[c_name] = df_temp[c_name].ffill()
            
            # Đổi tên cột
            rename_dict = {c_sp: 'Ten_SP'}
            if c_code: rename_dict[c_code] = 'Ma_KH'
            if c_name: rename_dict[c_name] = 'Ten_NPP_File'
            if c_sl: rename_dict[c_sl] = 'San_Luong'
            if c_dt: rename_dict[c_dt] = 'Doanh_Thu'
            
            df_temp = df_temp.rename(columns=rename_dict)
            
            if 'Ma_KH' not in df_temp.columns: df_temp['Ma_KH'] = 'UNKNOWN'
            if 'Ten_NPP_File' not in df_temp.columns: df_temp['Ten_NPP_File'] = df_temp['Ma_KH']
            if 'San_Luong' not in df_temp.columns: df_temp['San_Luong'] = 0
            if 'Doanh_Thu' not in df_temp.columns: df_temp['Doanh_Thu'] = 0
            
            # Làm sạch dữ liệu số
            df_temp['San_Luong'] = pd.to_numeric(df_temp['San_Luong'], errors='coerce').fillna(0)
            df_temp['Doanh_Thu'] = pd.to_numeric(df_temp['Doanh_Thu'], errors='coerce').fillna(0)
            df_temp['Ma_KH'] = df_temp['Ma_KH'].astype(str).str.strip()
            
            # Lấy thông tin tháng từ tên file (Ví dụ: San luong T6 2026.xlsx -> Tháng 06)
            month_match = re.search(r'T(\d{1,2})', fname, re.IGNORECASE)
            if month_match:
                df_temp['Thang'] = f"Tháng {int(month_match.group(1)):02d}"
            else:
                df_temp['Thang'] = fname
                
            parsed_sales_list.append(df_temp[['Ma_KH', 'Ten_NPP_File', 'Ten_SP', 'San_Luong', 'Doanh_Thu', 'Thang']])
            
        if not parsed_sales_list:
            return None, "⚠️ Không thể đọc được dữ liệu sản lượng từ các file sản lượng đã chọn."
            
        df_all_sales = pd.concat(parsed_sales_list, ignore_index=True)
        
        # --- C. VLOOKUP / THAM CHIẾU TỪ DANH MỤC THÔNG QUA MÃ_KH ---
        df_master = pd.merge(
            df_all_sales, 
            df_npp_clean[['Ma_KH', 'Ten_NPP_Master', 'Dia_Ban']], 
            on='Ma_KH', 
            how='left'
        )
        
        # Ưu tiên lấy Tên NPP từ Danh mục chuẩn, nếu không có trong danh mục mới lấy tên ở file tháng
        df_master['Ten_NPP'] = df_master['Ten_NPP_Master'].fillna(df_master['Ten_NPP_File'])
        df_master['Dia_Ban'] = df_master['Dia_Ban'].fillna('Chưa phân vùng')
        
        # Thuyết minh NPP chuẩn dạng: [MÃ KH] - Tên NPP
        df_master['Thuyet_Minh_NPP'] = "[" + df_master['Ma_KH'] + "] - " + df_master['Ten_NPP'].astype(str)
        
        return df_master, None

    except Exception as e:
        return None, f"⚠️ Đã xảy ra lỗi khi xử lý tập tin: {str(e)}"

# ---------------------------------------------------------
# 3. GIAO DIỆN HỆ THỐNG
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
            with st.spinner("⏳ Đang phân tích tiêu đề và kết nối dữ liệu theo Mã_KH..."):
                npp_bytes = file_npp.read()
                sales_tuples = tuple((f.name, f.read()) for f in files_sales)
                
                df_res, err = process_excel_files(npp_bytes, sales_tuples)
                
                if err:
                    st.error(err)
                else:
                    st.session_state["df_master"] = df_res
                    st.success(f"✅ Kết nối dữ liệu theo Mã_KH thành công! Tổng cộng {len(df_res):,} dòng dữ liệu.")

    if "df_master" in st.session_state:
        st.markdown("---")
        st.subheader("🔍 Kết quả xem trước dữ liệu (Preview)")
        st.dataframe(st.session_state["df_master"].head(50), use_container_width=True)

with tab2:
    if "df_master" not in st.session_state:
        st.info("👋 Vui lòng nạp dữ liệu ở Tab **TẢI LÊN & ĐỐI SOÁT DỮ LIỆU** trước.")
    else:
        df = st.session_state["df_master"]
        
        # Bộ lọc tương tác
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_thang = st.multiselect("Lọc theo Tháng:", options=sorted(df['Thang'].unique()), default=sorted(df['Thang'].unique()))
        with col_f2:
            selected_diaban = st.multiselect("Lọc theo Địa bàn:", options=sorted(df['Dia_Ban'].unique()), default=sorted(df['Dia_Ban'].unique()))
            
        df_filtered = df[(df['Thang'].isin(selected_thang)) & (df['Dia_Ban'].isin(selected_diaban))]
        
        # Chỉ số Tổng quan
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng Sản Lượng", f"{df_filtered['San_Luong'].sum():,.0f}")
        m2.metric("Tổng Doanh Thu", f"{df_filtered['Doanh_Thu'].sum():,.0f} VNĐ")
        m3.metric("Số Nhà Phân Phối", f"{df_filtered['Ma_KH'].nunique():,}")
        m4.metric("Số Mặt Hàng", f"{df_filtered['Ten_SP'].nunique():,}")
        
        st.markdown("---")
        st.subheader("📋 Bảng tổng hợp theo Nhà Phân Phối & Sản Phẩm")
        
        pivot_df = df_filtered.pivot_table(
            index=['Dia_Ban', 'Thuyet_Minh_NPP', 'Ten_SP'],
            columns='Thang',
            values='San_Luong',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        st.dataframe(pivot_df, use_container_width=True)
