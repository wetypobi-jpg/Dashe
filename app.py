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
# 2. 頁面標題與工作欄設定
# ==========================================
st.set_page_config(page_title="608社區管理系統", page_icon="🏢", layout="wide")

st.sidebar.title("🏢 608社區管理系統")

# Session State 初始化登入狀態
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False

# ==========================================
# 3. 登入與修改密碼區塊 (Sidebar)
# ==========================================
if not st.session_state.logged_in:
  st.sidebar.subheader("🔐 住戶/管理員登入")
  login_unit = st.sidebar.text_input("請輸入戶號 (例如: 608-1)")
  login_pass = st.sidebar.text_input("請輸入密碼", type="password")

  if st.sidebar.button("登入"):
    # 查詢資料庫驗證密碼
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
      st.sidebar.success(f"歡迎 {login_unit} 登入！")
      st.rerun()
    else:
      st.sidebar.error("戶號或密碼錯誤！")

  st.stop()  # 未登入前停止執行後續網頁
else:
  st.sidebar.success(
      f"目前登入：{st.session_state.user_code}"
      f" {'(管理員)' if st.session_state.is_admin else ''}"
  )

  # 短期開放：修改密碼功能
  with st.sidebar.expander("🔑 變更個人密碼"):
    old_pass = st.text_input("原密碼", type="password", key="old_pass")
    new_pass = st.text_input("新密碼", type="password", key="new_pass")
    if st.button("確認修改密碼"):
      # 驗證原密碼
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

  # 側邊欄導覽選單
  st.sidebar.markdown("---")
  menu = st.sidebar.radio(
      "功能選單",
      ["🏠 首頁 (現任委員)", "📜 歷屆委員名單", "💰 管理費繳交紀錄", "🛠️ 供應商名冊"],
  )

# ==========================================
# 4. 各頁面內容實作
# ==========================================

# ------------------------------------------
# 頁面一：首頁 (現任委員)
# ------------------------------------------
if menu == "🏠 首頁 (現任委員)":
  st.title("🏢 608社區管委會 - 現任委員名單")
  st.write("歡迎使用 608 社區管理系統！以下為本屆現任委員資訊：")

  # 從資料庫抓取現任委員 (is_current = True)
  current_committee = (
      supabase.table("committees")
      .select("*")
      .eq("is_current", True)
      .execute()
      .data
  )

  if current_committee:
    # 呈現三巨頭或現任委員卡片
    col1, col2, col3 = st.columns(3)

    # 簡單過濾主委、財委、監委
    roles_display = {"主任委員": col1, "財務委員": col2, "監察委員": col3}

    for item in current_committee:
      role = item.get("role")
      name = item.get("name")
      unit = item.get("unit_code")
      term = item.get("term")

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
    # 讓使用者依「屆數」或「年份」篩選
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
    # 類別篩選
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
        st.write(f"**聯絡人**：{v.get('contact_person', '未填寫')}社")
        st.markdown(
            f"📞 **電話**：[{v['phone']}](tel:{v['phone']})"
        )  # 支援手機直接點擊撥號
        st.write(f"**最近服務年份**：{v.get('last_service_year', '無')}")
        st.write(f"**評價與備註**：{v.get('notes', '無')}")
  else:
    st.info("目前尚無供應商資料。")
