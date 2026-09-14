import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="KHATOCO - Executive Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FPT ENTERPRISE DARK STYLING ---
CUSTOM_DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #F3F4F6;
    }
    .stApp { background-color: #0B0F17; }
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937;
    }
    .fpt-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        color: #FFFFFF;
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .fpt-title { font-size: 1.5rem; font-weight: 700; margin: 0; color: #38BDF8; }
    .fpt-subtitle { font-size: 0.85rem; color: #94A3B8; margin-top: 4px; }
    
    .dark-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
    }
    .dark-card-title { font-size: 0.75rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; }
    .dark-card-value { font-size: 1.7rem; font-weight: 700; color: #F8FAFC; margin: 4px 0; }
    .dark-card-sub { font-size: 0.8rem; font-weight: 500; }
    .text-green { color: #34D399; }
    .text-red { color: #F87171; }
    
    div[data-baseweb="select"] > div { background-color: #1E293B !important; color: #F8FAFC !important; border-color: #475569 !important; }
    div[role="listbox"] { background-color: #1E293B !important; color: #F8FAFC !important; }
    .stMultiSelect label, .stSelectbox label, .stTextInput label, .stDateInput label { color: #CBD5E1 !important; font-weight: 600 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 16px; border-bottom: 1px solid #334155; }
    .stTabs [data-baseweb="tab"] { color: #94A3B8; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #38BDF8 !important; border-bottom: 2px solid #38BDF8 !important; }
</style>
"""
st.markdown(CUSTOM_DARK_CSS, unsafe_allow_html=True)

# --- QUẢN LÝ TÀI KHOẢN ---
DEFAULT_USERS = {'truongminh@khatoco.vn': '123456', 'ceo@khatoco.vn': '123456'}
if 'users' not in st.session_state: st.session_state['users'] = DEFAULT_USERS.copy()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: st.session_state['current_user'] = None
if 'extra_data' not in st.session_state: st.session_state['extra_data'] = pd.DataFrame()

PLOTLY_DARK_LAYOUT = dict(
    font=dict(family='Inter, sans-serif', color='#94A3B8'),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(showgrid=False, zeroline=False, color='#64748B'),
    yaxis=dict(showgrid=True, gridcolor='#334155', zeroline=False, color='#64748B')
)

# --- DỮ LIỆU MẪU MẶC ĐỊNH SẴN SÀNG ---
def generate_sample_data():
    return pd.DataFrame([
        {"Ma_KH": "NPP01", "Ten_NPP": "NPP Khánh Hòa", "Dia_Ban": "Khánh Hòa", "Ten_SP": "Khatoco Gold", "San_Luong": 15000, "Don_Gia": 12000, "Doanh_Thu": 180000000, "Thang": "Tháng 06"},
        {"Ma_KH": "NPP01", "Ten_NPP": "NPP Khánh Hòa", "Dia_Ban": "Khánh Hòa", "Ten_SP": "Khatoco Gold", "San_Luong": 14000, "Don_Gia": 12000, "Doanh_Thu": 168000000, "Thang": "Tháng 07"},
        {"Ma_KH": "NPP01", "Ten_NPP": "NPP Khánh Hòa", "Dia_Ban": "Khánh Hòa", "Ten_SP": "Khatoco Gold", "San_Luong": 11000, "Don_Gia": 12000, "Doanh_Thu": 132000000, "Thang": "Tháng 08"},
        {"Ma_KH": "NPP02", "Ten_NPP": "NPP TP.HCM", "Dia_Ban": "TP. Hồ Chí Minh", "Ten_SP": "Khatoco Silver", "San_Luong": 32000, "Don_Gia": 10000, "Doanh_Thu": 320000000, "Thang": "Tháng 06"},
        {"Ma_KH": "NPP02", "Ten_NPP": "NPP TP.HCM", "Dia_Ban": "TP. Hồ Chí Minh", "Ten_SP": "Khatoco Silver", "San_Luong": 35000, "Don_Gia": 10000, "Doanh_Thu": 350000000, "Thang": "Tháng 07"},
        {"Ma_KH": "NPP02", "Ten_NPP": "NPP TP.HCM", "Dia_Ban": "TP. Hồ Chí Minh", "Ten_SP": "Khatoco Silver", "San_Luong": 38000, "Don_Gia": 10000, "Doanh_Thu": 380000000, "Thang": "Tháng 08"},
        {"Ma_KH": "NPP03", "Ten_NPP": "NPP Đà Nẵng", "Dia_Ban": "Đà Nẵng", "Ten_SP": "Khatoco Premium", "San_Luong": 20000, "Don_Gia": 15000, "Doanh_Thu": 300000000, "Thang": "Tháng 06"},
        {"Ma_KH": "NPP03", "Ten_NPP": "NPP Đà Nẵng", "Dia_Ban": "Đà Nẵng", "Ten_SP": "Khatoco Premium", "San_Luong": 18000, "Don_Gia": 15000, "Doanh_Thu": 270000000, "Thang": "Tháng 07"},
        {"Ma_KH": "NPP03", "Ten_NPP": "NPP Đà Nẵng", "Dia_Ban": "Đà Nẵng", "Ten_SP": "Khatoco Premium", "San_Luong": 12000, "Don_Gia": 15000, "Doanh_Thu": 180000000, "Thang": "Tháng 08"},
    ])

def calculate_mom_alerts(df, group_col, current_month, compare_month):
    df_curr = df[df['Thang'] == current_month].groupby(group_col).agg(Doanh_Thu_Curr=('Doanh_Thu', 'sum')).reset_index()
    df_comp = df[df['Thang'] == compare_month].groupby(group_col).agg(Doanh_Thu_Comp=('Doanh_Thu', 'sum')).reset_index()
    merged = pd.merge(df_curr, df_comp, on=group_col, how='outer').fillna(0)
    merged['Chenh_Lech_VNĐ'] = merged['Doanh_Thu_Curr'] - merged['Doanh_Thu_Comp']
    merged['Phan_Tram_MoM'] = merged.apply(
        lambda r: ((r['Doanh_Thu_Curr'] - r['Doanh_Thu_Comp']) / r['Doanh_Thu_Comp'] * 100) 
        if r['Doanh_Thu_Comp'] > 0 else (100.0 if r['Doanh_Thu_Curr'] > 0 else 0.0), axis=1
    )
    def get_status(row):
        pct = row['Phan_Tram_MoM']
        if pct <= -15: return "🔴 CẢNH BÁO ĐỎ"
        elif -15 < pct <= -5: return "🟡 CẢNH BÁO VÀNG"
        elif pct >= 15: return "🟢 TĂNG TRƯỜNG"
        return "⚪ BÌNH THƯỜNG"
    merged['Trang_Thai'] = merged.apply(get_status, axis=1)
    return merged.sort_values(by='Chenh_Lech_VNĐ', ascending=True)

# --- TRANG ĐĂNG NHẬP ---
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        st.markdown("<h2 style='color: #38BDF8; text-align: center;'>KHATOCO ERP SYSTEM</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; text-align: center;'>Tên ứng dụng: KTC-WEB-App-Thuongmai</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("Tài khoản", value="ceo@khatoco.vn").strip().lower()
            password = st.text_input("Mật khẩu", value="123456", type="password")
            if st.form_submit_button("ĐĂNG NHẬP", use_container_width=True):
                if email in st.session_state['users'] and st.session_state['users'][email] == password:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = email
                    st.rerun()
                else:
                    st.error("Sai tài khoản/mật khẩu")

# --- DASHBOARD CHÍNH ---
def main_dashboard():
    st.markdown(f"""
    <div class="fpt-header">
        <div>
            <h1 class="fpt-title">BÁO CÁO GIÁM SÁT KINH DOANH KHATOCO</h1>
            <div class="fpt-subtitle">App: KTC-WEB-App-Thuongmai | CEO: {st.session_state['current_user']}</div>
        </div>
        <span style="background: #064E3B; color: #6EE7B7; border: 1px solid #065F46; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem;">ONLINE</span>
    </div>
    """, unsafe_allow_html=True)

    df_final = generate_sample_data()
    if not st.session_state['extra_data'].empty:
        df_final = pd.concat([df_final, st.session_state['extra_data']], ignore_index=True)

    with st.sidebar:
        st.markdown("<h3 style='color: #F8FAFC;'>📥 NHẬP DỮ LIỆU</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Tải file Excel", type=['xlsx', 'csv'])
        month_input = st.text_input("Tên kỳ (VD: Tháng 09)")
        if st.button("Hợp Nhất", use_container_width=True):
            if uploaded_file and month_input:
                new_df = pd.read_excel(uploaded_file)
                new_df['Thang'] = month_input
                st.session_state['extra_data'] = pd.concat([st.session_state['extra_data'], new_df], ignore_index=True)
                st.success("Cập nhật thành công!")
            else: st.warning("Cần điền tên kỳ báo cáo!")
        st.markdown("---")
        if st.button("🚪 Đăng xuất"): st.session_state['logged_in'] = False; st.rerun()

    # Bộ lọc
    f1, f2, f3 = st.columns(3)
    with f1: sel_db = st.multiselect("Địa bàn", df_final['Dia_Ban'].unique())
    with f2: sel_sp = st.multiselect("Sản phẩm", df_final['Ten_SP'].unique())
    with f3: sel_npp = st.multiselect("Nhà phân phối", df_final['Ten_NPP'].unique())

    df_filtered = df_final.copy()
    if sel_db: df_filtered = df_filtered[df_filtered['Dia_Ban'].isin(sel_db)]
    if sel_sp: df_filtered = df_filtered[df_filtered['Ten_SP'].isin(sel_sp)]
    if sel_npp: df_filtered = df_filtered[df_filtered['Ten_NPP'].isin(sel_npp)]

    # Dynamic KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="dark-card"><div class="dark-card-title">Doanh Thu</div><div class="dark-card-value">{df_filtered["Doanh_Thu"].sum()/1e6:,.0f} Tr</div><div class="dark-card-sub text-green">▲ 8.4%</div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="dark-card"><div class="dark-card-title">Sản Lượng</div><div class="dark-card-value">{df_filtered["San_Luong"].sum():,.0f} Bao</div><div class="dark-card-sub text-green">▲ 5.1%</div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="dark-card"><div class="dark-card-title">NPP Active</div><div class="dark-card-value">{df_filtered["Ten_NPP"].nunique()}</div><div class="dark-card-sub text-green">100%</div></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="dark-card"><div class="dark-card-title">Thị Trường</div><div class="dark-card-value">{df_filtered["Dia_Ban"].nunique()} Tỉnh</div><div class="dark-card-sub text-green">Bao phủ</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🚨 CẢNH BÁO BIẾN ĐỘNG", "📈 XU HƯỚNG", "📊 BẢNG DỮ LIỆU CHI TIẾT"])
    
    with tab1:
        c1, c2 = st.columns(2)
        all_months = df_filtered['Thang'].unique().tolist()
        with c1: curr_m = st.selectbox("Kỳ báo cáo:", all_months, index=len(all_months)-1)
        with c2: comp_m = st.selectbox("Kỳ đối soát:", all_months, index=max(0, len(all_months)-2))
        if curr_m != comp_m:
            res = calculate_mom_alerts(df_filtered, 'Ten_NPP', curr_m, comp_m)
            st.dataframe(res, use_container_width=True, hide_index=True)

    with tab2:
        t_df = df_filtered.groupby('Thang').agg({'Doanh_Thu': 'sum', 'San_Luong': 'sum'}).reset_index()
        fig = px.line(t_df, x='Thang', y='Doanh_Thu', title="Biểu Đồ Doanh Thu MoM", markers=True)
        fig.update_traces(line_color='#38BDF8', line_width=3)
        fig.update_layout(PLOTLY_DARK_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with tab3: st.dataframe(df_filtered, use_container_width=True)

if not st.session_state['logged_in']: login_page()
else: main_dashboard()