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

st.title("🛠️ 維修與供應商名冊")
st.write("平時找不到師傅？常用維修廠商與電話總整理：")

vendors = supabase.table("vendors").select("*").execute().data

if vendors:
  categories = list(set([v["category"] for v in vendors]))
  selected_cat = st.selectbox("依服務類別篩選", ["全部顯示"] + categories)

  if selected_cat != "全部顯示":
    display_vendors = [v for v in vendors if v["category"] == selected_cat]
  else:
    display_vendors = vendors

  for v in display_vendors:
    with st.expander(f"🏢 {v['vendor_name']} （類別：{v['category']}）"):
      st.write(f"**聯絡人**：{v.get('contact_person', '未填寫')}")
      st.markdown(f"📞 **電話**：[{v['phone']}](tel:{v['phone']})")
      st.write(f"**最近服務年份**：{v.get('last_service_year', '無')}")
      st.write(f"**評價與備註**：{v.get('notes', '無')}")
else:
  st.info("目前尚無供應商資料。")
