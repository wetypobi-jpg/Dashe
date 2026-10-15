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

st.title("👥 現任委員名單")
st.write("以下為本屆現任委員資訊：")

current_committee = (
    supabase.table("committees")
    .select("*")
    .eq("is_current", True)
    .execute()
    .data
)

if not current_committee:
  current_committee = [
      {"role": "主任委員", "name": "住戶 608-22", "unit_code": "608-22"},
      {"role": "監察委員", "name": "住戶 608-18", "unit_code": "608-18"},
      {"role": "財務委員", "name": "住戶 608-5", "unit_code": "608-5"},
  ]

if current_committee:
  col1, col2, col3 = st.columns(3)
  roles_display = {"主任委員": col1, "財務委員": col2, "監察委員": col3}

  for item in current_committee:
    role = item.get("role")
    name = item.get("name")
    unit = item.get("unit_code")

    target_col = roles_display.get(role, col1)
    with target_col:
      st.info(f"**{role}**\n\n👤 **{name}**\n\n🏠 戶號：`{unit}`")
else:
  st.warning("目前資料庫中尚未設定現任委員。")
