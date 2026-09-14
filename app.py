import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="KHATOCO - Executive Command Center", page_icon="🛡️", layout="wide")

# --- CSS STYLING ---
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

# --- KHỞI TẠO BỘ NHỚ DỮ LIỆU ---
if 'master_data' not in st.session_state:
    st.session_state['master_data'] = pd.DataFrame()

# --- HEADER ---
st.markdown(f"""
<div class="fpt-header">
    <div>
        <h1 class="fpt-title">BÁO CÁO GIÁM SÁT KINH DOANH KHATOCO</h1>
        <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">App: KTC-WEB-App-Thuongmai | Version 2.0 (Auto-Upload)</div>
    </div>
    <span style="background: #064E3B; color: #6EE7B7; border: 1px solid #065F46; padding: 4px 12px; border-radius: 12px;">TRỰC TUYẾN</span>
</div>
""", unsafe_allow_html=True)

# --- CHIA 2 TABS CHÍNH ---
tab_dashboard, tab_upload = st.tabs(["📊 BẢNG ĐIỀU KHIỂN BÁO CÁO", "⚙️ QUẢN LÝ & CẬP NHẬT DỮ LIỆU (KÉO THẢ)"])

# ==========================================
# TAB 2: KHU VỰC CẬP NHẬT DỮ LIỆU KÉO THẢ
# ==========================================
with tab_upload:
    st.markdown("### 📥 KHO DỮ LIỆU ĐẦU VÀO")
    st.markdown("<p style='color:#94A3B8;'>Hãy kéo thả các file Excel từ máy tính của bạn vào đúng 2 phân khu dưới đây. Hệ thống sẽ tự động đọc, gộp dữ liệu và phân tích.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='upload-box'><h4>📂 1. DANH MỤC NPP & ĐỊA BÀN</h4><p style='font-size:12px; color:gray;'>Thả 1 file Excel danh mục vào đây</p></div>", unsafe_allow_html=True)
        file_npp = st.file_uploader("", type=['xlsx'], key="npp")
        
    with col2:
        st.markdown("<div class='upload-box'><h4>📂 2. SẢN LƯỢNG TIÊU THỤ CÁC THÁNG</h4><p style='font-size:12px; color:gray;'>Bôi đen và thả tất cả các file T6, T7, T8... vào đây cùng lúc</p></div>", unsafe_allow_html=True)
        files_sales = st.file_uploader("", type=['xlsx'], accept_multiple_files=True, key="sales")
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 THỰC HIỆN XỬ LÝ & TỔNG HỢP DỮ LIỆU", use_container_width=True, type="primary"):
        if not file_npp:
            st.error("⚠️ Bạn chưa tải lên file Danh mục NPP!")
        elif not files_sales:
            st.error("⚠️ Bạn chưa tải lên bất kỳ file Sản lượng nào!")
        else:
            with st.spinner("Đang xử lý và hợp nhất dữ liệu..."):
                try:
                    # Đọc các file sản lượng và tự nhận diện tháng từ tên file
                    list_df = []
                    for f in files_sales:
                        df_temp = pd.read_excel(f)
                        
                        # Thuật toán tự tìm chữ T6, T7, T8 trong tên file
                        month_match = re.search(r'T(\d{1,2})', f.name, re.IGNORECASE)
                        if month_match:
                            df_temp['Kỳ Báo Cáo'] = f"Tháng {int(month_match.group(1)):02d}"
                        else:
                            df_temp['Kỳ Báo Cáo'] = f.name # Nếu không có chữ T, lấy luôn tên file
                            
                        list_df.append(df_temp)
                        
                    df_all_sales = pd.concat(list_df, ignore_index=True)
                    
                    # Lưu vào bộ nhớ tạm của hệ thống
                    st.session_state['master_data'] = df_all_sales
                    st.success(f"✅ Đã xử lý thành công {len(files_sales)} file sản lượng. Vui lòng chuyển sang tab 📊 BẢNG ĐIỀU KHIỂN để xem!")
                except Exception as e:
                    st.error(f"❌ Có lỗi xảy ra trong quá trình đọc file: {e}")

# ==========================================
# TAB 1: BẢNG ĐIỀU KHIỂN
# ==========================================
with tab_dashboard:
    df_final = st.session_state['master_data']
    
    if df_final.empty:
        st.warning("⚠️ Dữ liệu đang trống. Vui lòng sang Tab '⚙️ QUẢN LÝ & CẬP NHẬT DỮ LIỆU' để tải file Excel lên.")
    else:
        st.markdown("### 📈 TỔNG QUAN THỊ TRƯỜNG")
        
        # Cố gắng tìm các cột số để tính tổng (Đề phòng tên cột trong file Excel thật khác nhau)
        num_cols = df_final.select_dtypes(include=['number']).columns.tolist()
        
        # Render KPIs
        if len(num_cols) >= 2:
            k1, k2, k3, k4 = st.columns(4)
            val1 = df_final[num_cols[0]].sum()
            val2 = df_final[num_cols[1]].sum()
            with k1: st.markdown(f'<div class="dark-card"><div class="dark-card-title">Tổng {num_cols[0]}</div><div class="dark-card-value">{val1:,.0f}</div></div>', unsafe_allow_html=True)
            with k2: st.markdown(f'<div class="dark-card"><div class="dark-card-title">Tổng {num_cols[1]}</div><div class="dark-card-value">{val2:,.0f}</div></div>', unsafe_allow_html=True)
            with k3: st.markdown(f'<div class="dark-card"><div class="dark-card-title">Kỳ Báo Cáo</div><div class="dark-card-value">{df_final["Kỳ Báo Cáo"].nunique()}</div></div>', unsafe_allow_html=True)
            with k4: st.markdown(f'<div class="dark-card"><div class="dark-card-title">Tổng số dòng DL</div><div class="dark-card-value">{len(df_final):,.0f}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Biểu đồ và Bảng số liệu
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### Bảng Dữ Liệu Chi Tiết")
            st.dataframe(df_final, use_container_width=True, height=400)
            
        with c2:
            st.markdown("#### Biểu đồ phân bổ")
            if 'Kỳ Báo Cáo' in df_final.columns and len(num_cols) > 0:
                # Group by tháng
                df_group = df_final.groupby('Kỳ Báo Cáo')[num_cols[0]].sum().reset_index()
                fig = px.bar(df_group, x='Kỳ Báo Cáo', y=num_cols[0], title=f"Biểu đồ {num_cols[0]} qua các tháng")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chưa đủ dữ liệu để vẽ biểu đồ.")
