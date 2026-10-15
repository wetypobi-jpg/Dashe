import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if (
    "logged_in" not in st.session_state
    or not st.session_state.logged_in
    or not st.session_state.user_code
):
  st.warning("⚠️ 請先至首頁登入系統！")
  st.stop()

st.title("📜 吾映良品柒 - 歷屆委員名單總覽")
st.write("依據社區歷史紀錄整理之歷屆委員與任期對照表：")

all_committees = supabase.table("committees").select("*").execute().data

if all_committees:
  table_data = []
  for c in all_committees:
    table_data.append({
        "任期/年份": c["year"],
        "職稱": c["role"],
        "戶號": c["unit_code"],
        "備註": "現任委員" if c["is_current"] else "歷史紀錄",
    })
  st.dataframe(table_data, use_container_width=True)
else:
  st.info("目前尚無委員資料。")
