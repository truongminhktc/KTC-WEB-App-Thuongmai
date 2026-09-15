import streamlit as st
import pandas as pd
import re
import unicodedata

def normalize_text(text):
    """Chuẩn hóa chuỗi để tìm kiếm cột chính xác"""
    if not isinstance(text, str):
        return ""
    text = text.replace('_', ' ')
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    return text.lower().strip()

def load_and_process_data(file_dm, files_san_luong):
    # ----------------------------------------------------
    # 1. ĐỌC VÀ CHUẨN HÓA FILE DANH MỤC MASTER
    # ----------------------------------------------------
    df_dm_raw = pd.read_excel(file_dm, header=None)
    
    # Tìm dòng chứa Header
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
    
    # ----------------------------------------------------
    # 2. ĐỌC VÀ XỬ LÝ CÁC FILE SẢN LƯỢNG
    # ----------------------------------------------------
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
        
        # Forward fill để gán Mã_KH và Tên_NPP xuống các dòng sản phẩm con
        if c_code: df[c_code] = df[c_code].ffill()
        if c_name: df[c_name] = df[c_name].ffill()
        
        # Lọc lấy các dòng sản phẩm hợp lệ
        df_prod = df[df[c_sp].notna()].copy()
        df_prod[c_sp] = df_prod[c_sp].astype(str).str.strip()
        df_prod = df_prod[~df_prod[c_sp].str.lower().str.contains('sản phẩm|tổng cộng|cộng')]
        
        # Xử lý tên Tháng
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
    
    # ----------------------------------------------------
    # 3. LINK DỮ LIỆU DỰA TRÊN CỘT Mã_KH & TẠO CỘT THUYẾT MINH
    # ----------------------------------------------------
    df_merged = pd.merge(df_all_sales, df_dm_clean, on='Ma_KH', how='left')
    
    # Ưu tiên lấy tên từ Danh mục, nếu không có thì lấy tên trong File sản lượng
    df_merged['Ten_NPP_Hien_Thi'] = df_merged['Ten_NPP_Master'].fillna(df_merged['Ten_NPP_File'])
    
    # Tạo cột Thuyết minh chính: [Mã_KH] - Tên NPP
    df_merged['Thuyet_Minh_NPP'] = "[" + df_merged['Ma_KH'] + "] - " + df_merged['Ten_NPP_Hien_Thi']
    
    # Gán địa bàn tiêu thụ
    df_merged['Dia_Ban'] = df_merged['Dia_Ban_Master'].fillna('Chưa phân vùng')
    
    return df_merged
