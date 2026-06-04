import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse
from datetime import datetime
import json
import gspread

# --- STYLING & COMPACTING CONFIGURATION ---
st.set_page_config(page_title="Readings Register", layout="wide")

# Injecting comprehensive CSS styling targeting user inputs and layout headers
st.markdown("""
    <style>
        /* Remove Top White Header Bar & Decoration lines */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
            height: 0px !important;
        }
        .stApp [data-testid="stDecoration"] {
            display: none !important;
        }
        
        /* Base Background Theme Adjustments */
        .stApp {
            background-color: #1e120b;
            color: #ffffff;
        }
        
        /* Sidebar layout styling */
        [data-testid="stSidebar"] {
            background-color: #2c1d16;
            border-right: 1px solid #422d22;
        }
        
        /* Darker, High-Contrast Data Entry Inputs */
        div[data-baseweb="select"] > div, 
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        input, textarea {
            background-color: #120a06 !important;
            color: #ffffff !important;
            border: 1px solid #6b4c3a !important;
        }
        
        /* High contrast for label headers sitting over inputs */
        label, p, span, .stWidgetLabel {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Dark Theme Style for Submit Entry Button */
        button[kind="primaryFormSubmit"], .stFormSubmitButton > button {
            background-color: #120a06 !important;
            color: #ffffff !important;
            border: 1px solid #8c644d !important;
            font-weight: bold !important;
            transition: all 0.2s ease;
        }
        button[kind="primaryFormSubmit"]:hover, .stFormSubmitButton > button:hover {
            background-color: #2c1d16 !important;
            border-color: #ffffff !important;
        }
        
        /* Compact typography layout controls */
        h1, h2, h3, h4 {
            margin-top: 2px !important;
            margin-bottom: 4px !important;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            color: #ffffff !important;
            font-weight: bold !important;
        }
        div.block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# BILINGUAL TRANSLATION MATRIX (Stacked English & Vietnamese Labels)
# =====================================================================
T_TITLE = "📚 Readings Register \n\n *Nhật Ký Đọc Kinh Thánh*"
T_FORM_HDR = "### 📝 Entry Form \n\n *Đơn Nhập Liệu*"
T_USER_SEL = "User (Người đọc):"
T_CUST_NAME = "Name (Họ và Tên):"
T_CUST_PHONE = "WhatsApp (with +) (Số điện thoại):"
T_DATETIME = "Date & Time (Ngày & Giờ):"
T_BIBLEREF = "Bible Reference (Sách & Chương đã đọc):"
T_CHAPTERS = "Chapters (Số chương):"
T_GODSPOKE = "God's Message (Suy ngẫm / Ghi chú):"
T_GODOBEY = "Obedience Step (Lời hứa / Vâng phục):"
T_SUBMIT = "Submit Entry / Gửi Nhật Ký"
T_MISSING = "Missing fields! / Vui lòng điền đầy đủ các thông tin!"
T_SAVED = "Saved! / Đã lưu thành công!"

T_PERIOD_MODE = "Period Mode (Chọn mốc thời gian):"
T_CURR_MONTH  = "Current Month / Tháng này"
T_CUST_RANGE  = "Custom Range / Tùy chọn"
T_START       = "Start (Từ ngày):"
T_END         = "End (Đến ngày):"

T_LEADERBOARD = "### 📊 Progress Leaderboard \n\n *Bảng Tiến Độ Đọc Kinh Thánh*"
T_SENDER_ID   = "Sender Identity (Tên người gửi):"
T_WA_SHARE    = "### 📲 WhatsApp Direct Share \n\n *Chia Sẻ Trực Tiếp Qua WhatsApp*"
T_WA_LAUNCH   = "💬 Launch WhatsApp & Pre-fill Template Text / Mở WhatsApp & Gửi Tin Nhắn"
T_JOURNAL     = "### 📋 Shared Reflection Journal \n\n *Nhật Ký Suy Ngẫm Chung*"

# Chart Multi-Language Legend Mappings
MAP_METRIC = {
    "Chapters": "Chapters / Số Chương",
    "Sessions": "Sessions / Số Lần Đọc",
    "Days Read": "Days Read / Số Ngày Đọc",
    "Missed Days": "Missed Days / Số Ngày Chưa Đọc"
}

# --- GLOBAL DICTIONARY DATA ---
USER_DIRECTORY = {
    "Katelyn": "+60193763635",
    "Thoa": "+601155080892",
    "Ruth": "+60183668919",
    "Sarah": "+60168412926",
    "Tham": "+60169159217",
    "Tina": "+601121103011",
    "Hannah": "+60182499896",
    "hs": "+60122193637"
}

st.title(T_TITLE)

# =====================================================================
# DATA STORAGE LAYER: SERVICE ACCOUNT JSON CONNECTION MANAGER
# =====================================================================
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1iPxF9ftWROX-_BbBBGKC3rkgRn5QcCIrvcbB3jVoH1g/edit?usp=sharing"
CREDENTIALS_FILE = "sheets-ai-automation-3a77cb6b83b6.json"

@st.cache_data(ttl=0)
def fetch_sheet_records():
    try:
        # If running on Streamlit Cloud, use the Secrets text box
        if "creds" in st.secrets:
            creds = json.loads(st.secrets["creds"])
        # If running locally on your computer, use your local JSON file
        else:
            with open(CREDENTIALS_FILE, "r") as f:
                creds = json.load(f)
        
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open_by_url(GOOGLE_SHEET_URL)
        worksheet = sh.get_worksheet(0)
        records = worksheet.get_all_records()
        return pd.DataFrame(records), worksheet
    except Exception as e:
        st.error(f"Google Cloud connection failed: {e}")
        return pd.DataFrame(), None

raw_df, target_worksheet = fetch_sheet_records()

# Check structure fallback maps if sheet is empty
if raw_df is None or len(raw_df) == 0:
    raw_df = pd.DataFrame(columns=["Timestamp", "Name", "BibleReference", "ChaptersRead", "GodSpoke", "GodObey", "Phone"])

# --- SIDEBAR COMPACT ENTRY ---
st.sidebar.markdown(T_FORM_HDR)
user_options = list(USER_DIRECTORY.keys()) + ["Others"]
selected_name = st.sidebar.selectbox(T_USER_SEL, options=user_options)

custom_name = ""
custom_phone = ""
if selected_name == "Others":
    custom_name = st.sidebar.text_input(T_CUST_NAME).strip()
    custom_phone = st.sidebar.text_input(T_CUST_PHONE).strip()

with st.sidebar.form(key="reading_form", clear_on_submit=True):
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    input_timestamp = st.sidebar.text_input(T_DATETIME, value=current_time_str)
    
    reading_ref = st.sidebar.text_input(T_BIBLEREF)
    chapters = st.sidebar.number_input(T_CHAPTERS, min_value=0, step=1, value=0)
    god_spoke = st.sidebar.text_area(T_GODSPOKE, height=65)
    god_obey = st.sidebar.text_area(T_GODOBEY, height=65)
    submit_button = st.form_submit_button(label=T_SUBMIT)

if "last_active_user" not in st.session_state:
    st.session_state["last_active_user"] = list(USER_DIRECTORY.keys())[0]

if submit_button:
    final_name = custom_name if selected_name == "Others" else selected_name
    final_phone = custom_phone if selected_name == "Others" else USER_DIRECTORY.get(selected_name, "")
    
    if selected_name == "Others" and (not custom_name or not custom_phone):
        st.sidebar.error(T_MISSING)
    else:
        if target_worksheet is not None:
            try:
                # Build the appended row matched exactly to the sheet structure
                row_to_append = [
                    input_timestamp,
                    final_name,
                    reading_ref,
                    int(chapters),
                    god_spoke,
                    god_obey,
                    final_phone
                ]
                target_worksheet.append_row(row_to_append)
                
                st.session_state["last_active_user"] = final_name
                st.sidebar.success(T_SAVED)
                st.cache_data.clear()
                st.rerun()
            except Exception as write_err:
                st.sidebar.error(f"Write error: {write_err}")
        else:
            st.sidebar.error("Database connection was unavailable.")

# --- MAIN CONTROLS & GRAPH ---
has_data = len(raw_df) > 0

if has_data:
    time_col = "Timestamp" if "Timestamp" in raw_df.columns else "Date"
    ref_col = "BibleReference" if "BibleReference" in raw_df.columns else "ReadingReference"
    
    raw_df["ParsedDate"] = pd.to_datetime(raw_df[time_col], format='mixed', errors='coerce').dt.date
    raw_df = raw_df.dropna(subset=["ParsedDate"])
    
    filter_mode = st.radio(T_PERIOD_MODE, options=[T_CURR_MONTH, T_CUST_RANGE], horizontal=True)
    today = datetime.now().date()
    if filter_mode == T_CURR_MONTH:
        start_filter = today.replace(day=1)
        end_filter = today
    else:
        col1, col2 = st.columns(2)
        with col1: start_filter = st.date_input(T_START, today.replace(day=1))
        with col2: end_filter = st.date_input(T_END, today)
            
    filtered_df = raw_df[(raw_df["ParsedDate"] >= start_filter) & (raw_df["ParsedDate"] <= end_filter)]
    
    if len(filtered_df) > 0:
        total_days_in_period = (end_filter - start_filter).days + 1
        all_users = filtered_df["Name"].dropna().unique()
        calculated_records = []
        
        for user in all_users:
            user_df = filtered_df[filtered_df["Name"] == user]
            calculated_records.append({
                "Name": user,
                "Chapters": pd.to_numeric(user_df["ChaptersRead"], errors='coerce').sum(),
                "Sessions": len(user_df),
                "Days Read": user_df["ParsedDate"].nunique(),
                "Missed Days": max(0, total_days_in_period - user_df["ParsedDate"].nunique())
            })
            
        calc_df = pd.DataFrame(calculated_records)
        
        # --- HORIZONTAL GRAPH WITH INTENSIFIED LABELS ---
        st.markdown(T_LEADERBOARD)
        melted_df = calc_df.melt(id_vars=["Name"], value_vars=["Chapters", "Sessions", "Days Read", "Missed Days"], var_name="Metric", value_name="Count")
        melted_df["Metric Display"] = melted_df["Metric"].map(MAP_METRIC)
        
        fig = px.bar(
            melted_df, y="Name", x="Count", color="Metric Display", orientation='h', barmode="stack", text="Count",
            color_discrete_map={
                MAP_METRIC["Chapters"]: "#A0C4FF",     
                MAP_METRIC["Sessions"]: "#B9FBC0",     
                MAP_METRIC["Days Read"]: "#FDE2E4",    
                MAP_METRIC["Missed Days"]: "#FFD6A5"   
            }
        )
        
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff", size=13), 
            xaxis=dict(
                title=dict(text="Count / Số Lượng", font=dict(color="#ffffff", size=14)),
                tickfont=dict(color="#ffffff", size=12),
                gridcolor="#422d22"
            ),
            yaxis=dict(
                title=dict(text="Users / Người Đọc", font=dict(color="#ffffff", size=14)),
                tickfont=dict(color="#ffffff", size=13)
            ),
            legend=dict(
                orientation="h", y=-0.25, x=0.5, xanchor="center",
                title=dict(text="Metrics / Tiêu Chí:", font=dict(color="#ffffff", size=12)),
                font=dict(color="#ffffff", size=12) 
            )
        )
        
        fig.update_traces(
            textposition="inside", 
            insidetextanchor="middle",
            textfont=dict(color="#120a06", size=12, weight="bold")
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        
        # --- WHATSAPP UTILITY EXPORT SUITE ---
        st.markdown(T_WA_SHARE)
        
        if st.session_state["last_active_user"] in all_users:
            default_index = list(all_users).index(st.session_state["last_active_user"])
        else:
            default_index = 0
            
        share_user = st.selectbox(T_SENDER_ID, options=all_users, index=default_index)
        
        user_stats = calc_df[calc_df["Name"] == share_user]
        if not user_stats.empty:
            row = user_stats.iloc[0]
            summary_text = (
                f"📖 *Bible Reading Update ({start_filter} to {end_filter})*\n"
                f"👤 Member: {share_user}\n"
                f"📊 Chapters: {row['Chapters']} | Sessions: {row['Sessions']}\n"
                f"✨ Days Read: {row['Days Read']} | Missed: {row['Missed Days']}"
            )
            
            user_log_match = raw_df[raw_df["Name"] == share_user].dropna(subset=["Phone"])
            phone_num = str(user_log_match.iloc[-1]["Phone"]).strip() if not user_log_match.empty and str(user_log_match.iloc[-1]["Phone"]).strip() != "" else USER_DIRECTORY.get(share_user, "")
            phone_num = phone_num.replace(" ", "").replace("-", "")
            whatsapp_url = f"https://wa.me/{phone_num}?text={urllib.parse.quote(summary_text)}"
            
            st.markdown(f"""
            <table style="width:100%; border-collapse: collapse; background-color: #2c1d16; border: 1px solid #422d22; font-size:13px; margin-bottom:10px;">
                <tr style="background-color: #422d22; color: #ffffff; font-weight: bold;">
                    <th style="padding: 6px; border: 1px solid #422d22; width: 45%;">Step 1: Save Layout Chart (Bước 1: Lưu Biểu Đồ)</th>
                    <th style="padding: 6px; border: 1px solid #422d22; width: 55%;">Step 2: Upload to WhatsApp (Bước 2: Gửi Qua WhatsApp)</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #422d22; color: #f5f0eb; vertical-align: top;">
                        Hover over graph menu bar. Click the 📷 <b>Camera Icon</b> to instantly download chart image file inside your system <b>Downloads</b> folder.
                        <br><br><i>Rê chuột qua góc phải biểu đồ. Nhấp vào biểu tượng hình 📷 <b>Máy Ảnh</b> để tải ảnh tiến độ về thư mục <b>Downloads</b>.</i>
                    </td>
                    <td style="padding: 8px; border: 1px solid #422d22; color: #f5f0eb; vertical-align: top;">
                        Press green link block below. In your active WhatsApp dialogue popup, click the <b>Paperclip (+) attachment icon</b>, choose saved chart file, then hit Send.
                        <br><br><i>Nhấp vào nút liên kết màu nâu phía dưới. Trong giao diện chat WhatsApp, nhấn biểu tượng <b>Ghim Đính Kèm (+)</b>, chọn ảnh biểu đồ vừa tải về rồi gửi đi.</i>
                    </td>
                </tr>
            </table>
            """, unsafe_allow_html=True)
            
            if phone_num:
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="padding:10px; background-color:#7c5c43; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold; font-size:14px; width:100%;">{T_WA_LAUNCH}</button></a>', unsafe_allow_html=True)
        
        # --- REFLECTION JOURNALS ---
        st.markdown(T_JOURNAL)
        
        display_df = filtered_df.copy()[[time_col, "Name", ref_col, "ChaptersRead", "GodSpoke", "GodObey"]]
        display_df.columns = ["Timestamp", "Name", "Bible Reference", "Chapters", "God's Message", "Obedience Step"]
        st.dataframe(display_df.sort_values(by="Timestamp", ascending=False), use_container_width=True, hide_index=True)
