import streamlit as st
import pandas as pd
import re
import unicodedata
import io

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Hệ Thống Phân Tích Sản Lượng KTC",
    page_icon="📊",
    layout="wide"
)

def normalize_text(text):
    """Chuẩn hóa chuỗi để tìm kiếm cột linh hoạt"""
    if not isinstance(text, str):
        return ""
    text = text.replace('_', ' ')
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    return text.lower().strip()

def process_data(file_dm, files_san_luong):
    # ---------------------------------------------------------
    # 1. ĐỌC VÀ CHUẨN HÓA FILE DANH MỤC MASTER
    # ---------------------------------------------------------
    df_dm_raw = pd.read_excel(file_dm, header=None)
    
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
    
    # ---------------------------------------------------------
    # 2. ĐỌC VÀ TỔNG HỢP CÁC FILE SẢN LƯỢNG
    # ---------------------------------------------------------
    sales_frames = []
    for f in files_san_luong:
        df_raw = pd.read_excel(f, header=None)
        
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
        
        # Forward Fill Mã_KH và Tên_NPP xuống các dòng sản phẩm
        if c_code: df[c_code] = df[c_code].ffill()
        if c_name: df[c_name] = df[c_name].ffill()
        
        # Lọc dòng sản phẩm hợp lệ
        df_prod = df[df[c_sp].notna()].copy()
        df_prod[c_sp] = df_prod[c_sp].astype(str).str.strip()
        df_prod = df_prod[~df_prod[c_sp].str.lower().str.contains('sản phẩm|tổng cộng|cộng')]
        
        # Nhận diện tên Tháng từ tên file
        file_name = getattr(f, 'name', str(f))
        m_match = re.search(r'T(\d{1,2})', file_name, re.IGNORECASE)
        thang_label = f"Tháng {int(m_match.group(1)):02d}" if m_match else file_name
        
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
    
    # ---------------------------------------------------------
    # 3. LIÊN KẾT BẰNG MÃ_KH VÀ TẠO THUYẾT MINH
    # ---------------------------------------------------------
    df_merged = pd.merge(df_all_sales, df_dm_clean, on='Ma_KH', how='left')
    
    # Lấy Tên NPP từ Master, fallback về tên trong file sản lượng
    df_merged['Ten_NPP_Khai_Bao'] = df_merged['Ten_NPP_Master'].fillna(df_merged['Ten_NPP_File'])
    df_merged['Thuyet_Minh_NPP'] = "[" + df_merged['Ma_KH'] + "] - " + df_merged['Ten_NPP_Khai_Bao']
    df_merged['Dia_Ban_Tieu_Thu'] = df_merged['Dia_Ban_Master'].fillna('Chưa phân vùng')
    
    return df_merged

# ---------------------------------------------------------
# 4. GIAO DIỆN STREAMLIT
# ---------------------------------------------------------
st.title("📊 Báo Cáo Sản Lượng & Thuyết Minh Nhà Phân Phối")
st.markdown("---")

# Sidebar Upload File
st.sidebar.header("📁 Tải Dữ Liệu Đầu Vào")
file_dm = st.sidebar.file_uploader("1. File Danh mục NPP Master (.xlsx)", type=["xlsx"])
files_sl = st.sidebar.file_uploader("2. Các file Sản lượng tháng (.xlsx)", type=["xlsx"], accept_multiple_files=True)

if file_dm and files_sl:
    try:
        with st.spinner("Đang tổng hợp và đối soát dữ liệu..."):
            df = process_data(file_dm, files_sl)
        
        st.success("Tải và tổng hợp dữ liệu thành công!")
        
        # Thống kê nhanh (KPIs)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng Sản Lượng", f"{df['San_Luong'].sum():,.0f}")
        col2.metric("Tổng Doanh Thu (VNĐ)", f"{df['Doanh_Thu'].sum():,.0f}")
        col3.metric("Số Nhà Phân Phối", f"{df['Ma_KH'].nunique()}")
        col4.metric("Số Mặt Hàng", f"{df['Ten_SP'].nunique()}")
        
        st.markdown("---")
        
        # Bộ lọc tương tác
        st.subheader("🔍 Bộ Lọc Tìm Kiếm")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        selected_months = f_col1.multiselect("Lọc theo Tháng", options=sorted(df['Thang'].unique()), default=sorted(df['Thang'].unique()))
        selected_regions = f_col2.multiselect("Lọc theo Địa bàn", options=sorted(df['Dia_Ban_Tieu_Thu'].unique()), default=sorted(df['Dia_Ban_Tieu_Thu'].unique()))
        selected_npps = f_col3.multiselect("Lọc theo Thuyết minh NPP", options=sorted(df['Thuyet_Minh_NPP'].unique()), default=sorted(df['Thuyet_Minh_NPP'].unique()))
        
        # Áp dụng bộ lọc
        df_filtered = df[
            (df['Thang'].isin(selected_months)) &
            (df['Dia_Ban_Tieu_Thu'].isin(selected_regions)) &
            (df['Thuyet_Minh_NPP'].isin(selected_npps))
        ]
        
        # Tab hiển thị Chi tiết & Tổng hợp
        tab1, tab2 = st.tabs(["📋 Dữ Liệu Chi Tiết", "📈 Báo Cáo Tổng Hợp"])
        
        with tab1:
            st.dataframe(
                df_filtered[['Thang', 'Ma_KH', 'Thuyet_Minh_NPP', 'Dia_Ban_Tieu_Thu', 'Ten_SP', 'San_Luong', 'Doanh_Thu']],
                use_container_width=True
            )
            
            # Xuất file Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Data_Tong_Hop')
            
            st.download_button(
                label="📥 Tải Báo Cáo Excel",
                data=output.getvalue(),
                file_name="Bao_Cao_San_Luong_Tong_Hop.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        with tab2:
            st.subheader("Sản Lượng & Doanh Thu Theo Nhà Phân Phối")
            summary_npp = df_filtered.groupby(['Thuyet_Minh_NPP', 'Dia_Ban_Tieu_Thu'], as_index=False)[['San_Luong', 'Doanh_Thu']].sum()
            st.dataframe(summary_npp.sort_values(by='San_Luong', ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Xảy ra lỗi trong quá trình xử lý: {e}")
else:
    st.info("👋 Vui lòng tải lên file **Danh mục Master** và ít nhất **1 file Sản lượng** ở thanh bên trái để bắt đầu.")
