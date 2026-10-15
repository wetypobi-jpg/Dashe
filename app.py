import streamlit as st
from supabase import create_client

# ==========================================
# 1. 從 Streamlit 內建安全環境讀取 Supabase 設定
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def init_connection():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

# ==========================================
# 2. 頁面基本設定
# ==========================================
st.set_page_config(page_title="608社區管理系統", page_icon="🏢", layout="wide")

# Session State 初始化登入狀態
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False

# ==========================================
# 3. 未登入狀態：將登入畫面移至主畫面（左右分栏，右側登入）
# ==========================================
if not st.session_state.logged_in:
  st.title("🏢 608社區管理系統")
  st.write("歡迎來到 608 社區專屬管理平台，請先登入以繼續操作。")
  st.markdown("---")

  # 建立左右兩欄（左側說明，右側放登入表單）
  col_left, col_right = st.columns([1, 1], gap="large")

  with col_left:
    st.subheader("💡 系統功能簡介")
    st.markdown("""
        * **現任與歷屆委員**：快速查詢主委、監委、財委名單與歷史交接紀錄。
        * **管理費繳交紀錄**：各戶專屬繳費查詢與管理員總表。
        * **供應商名冊**：社區常用修繕廠商電話與評價備註，隨時找得到人！
        
        *如有帳號或密碼相關問題，請聯絡社區管委會管理員。*
        """)

  with col_right:
    st.subheader("🔐 住戶 / 管理員登入")
    with st.form("login_form"):
      login_unit = st.text_input("請輸入戶號 (例如: 608 或 608-1)")
      login_pass = st.text_input("請輸入密碼", type="password")
      submit_btn = st.form_submit_button("登入系統")

      if submit_btn:
        response = (
            supabase.table("units")
            .select("*")
            .eq("unit_code", login_unit)
            .execute()
        )
        user_data = response.data

        if user_data and user_data[0]["password"] == login_pass:
          st.session_state.logged_in = True
          st.session_state.user_code = login_unit
          st.session_state.is_admin = user_data[0]["is_admin"]
          st.success("登入成功！載入中...")
          st.rerun()
        else:
          st.error("戶號或密碼錯誤，請重新輸入！")

  st.stop()  # 未登入前停止執行後續頁面

# ==========================================
# 4. 已登入狀態：側邊欄顯示導覽與個人設定
# ==========================================
st.sidebar.title("🏢 608社區管理系統")
st.sidebar.success(
    f"目前登入：{st.session_state.user_code}"
    f" {'(管理員)' if st.session_state.is_admin else ''}"
)

# 修改密碼功能
with st.sidebar.expander("🔑 變更個人密碼"):
  old_pass = st.text_input("原密碼", type="password", key="old_pass")
  new_pass = st.text_input("新密碼", type="password", key="new_pass")
  if st.button("確認修改密碼"):
    check = (
        supabase.table("units")
        .select("password")
        .eq("unit_code", st.session_state.user_code)
        .execute()
    )
    if check.data and check.data[0]["password"] == old_pass:
      supabase.table("units").update({"password": new_pass}).eq(
          "unit_code", st.session_state.user_code
      ).execute()
      st.success("密碼修改成功！")
    else:
      st.error("原密碼錯誤！")

if st.sidebar.button("登出系統"):
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False
  st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "功能選單",
    ["🏠 首頁 (現任委員)", "📜 歷屆委員名單", "💰 管理費繳交紀錄", "🛠️ 供應商名冊"],
)

# ==========================================
# 5. 各頁面內容實作
# ==========================================

# ------------------------------------------
# 頁面一：首頁 (現任委員)
# ------------------------------------------
if menu == "🏠 首頁 (現任委員)":
  st.title("🏢 608社區管委會 - 現任委員名單")
  st.write("以下為本屆現任委員資訊：")

  current_committee = (
      supabase.table("committees")
      .select("*")
      .eq("is_current", True)
      .execute()
      .data
  )

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

    st.markdown("---")
    st.subheader("📋 其他本屆委員與幹部")
    other_members = [
        c
        for c in current_committee
        if c.get("role") not in roles_display.keys()
    ]
    if other_members:
      for om in other_members:
        st.write(
            f"- **{om.get('role')}**：{om.get('name')} (戶號: {om.get('unit_code')})"
        )
    else:
      st.write("目前無其他額外委員登錄。")
  else:
    st.warning(
        "目前資料庫中尚未設定現任委員（請至 Supabase 將 is_current 設為"
        " True）。"
    )

# ------------------------------------------
# 頁面二：歷屆委員名單
# ------------------------------------------
elif menu == "📜 歷屆委員名單":
  st.title("📜 歷屆委員會任期紀錄")
  st.write("查詢過往各屆的委員名單與任期交接紀錄：")

  all_committees = supabase.table("committees").select("*").execute().data

  if all_committees:
    terms = sorted(list(set([c["term"] for c in all_committees])))
    selected_term = st.selectbox("選擇查詢屆數", terms)

    filtered_data = [c for c in all_committees if c["term"] == selected_term]

    st.table([
        {
            "屆數": c["term"],
            "年度": c["year"],
            "職稱": c["role"],
            "戶號": c["unit_code"],
            "姓名": c["name"],
        }
        for c in filtered_data
    ])
  else:
    st.info("目前尚無歷屆委員資料。")

# ------------------------------------------
# 頁面三：管理費繳交紀錄
# ------------------------------------------
elif menu == "💰 管理費繳交紀錄":
  st.title("💰 年度管理費繳交紀錄")

  if st.session_state.is_admin:
    st.success("👑 您目前是以【管理員】身份登入，可檢視全社區繳交總表。")
    all_fees = supabase.table("fee_records").select("*").execute().data
    if all_fees:
      st.dataframe(all_fees, use_container_width=True)
    else:
      st.info("目前尚無管理費紀錄。")
  else:
    st.info(
        f"🏠 您目前是以【住戶】身份登入 (戶號: {st.session_state.user_code})，僅顯示您"
        "個人的繳交紀錄。"
    )
    my_fees = (
        supabase.table("fee_records")
        .select("*")
        .eq("unit_code", st.session_state.user_code)
        .execute()
        .data
    )
    if my_fees:
      st.table(my_fees)
    else:
      st.info("查無您的繳費紀錄，或本年度尚未建立資料。")

# ------------------------------------------
# 頁面四：供應商名冊
# ------------------------------------------
elif menu == "🛠️ 供應商名冊":
  st.title("🛠️ 社區維修與供應商名冊")
  st.write("平時找不到師傅？常用維修廠商與電話總整理：")

  vendors = supabase.table("vendors").select("*").execute().data

  if vendors:
    categories = list(set([v["category"] for v in vendors]))
    selected_cat = st.selectbox(
        "依服務類別篩選", ["全部顯示"] + categories
    )

    if selected_cat != "全部顯示":
      display_vendors = [v for v in vendors if v["category"] == selected_cat]
    else:
      display_vendors = vendors

    for v in display_vendors:
      with st.expander(
          f"🏢 {v['vendor_name']} （類別：{v['category']}）"
      ):
        st.write(f"**聯絡人**：{v.get('contact_person', '未填寫')}")
        st.markdown(f"📞 **電話**：[{v['phone']}](tel:{v['phone']})")
        st.write(f"**最近服務年份**：{v.get('last_service_year', '無')}")
        st.write(f"**評價與備註**：{v.get('notes', '無')}")
  else:
    st.info("目前尚無供應商資料。")
