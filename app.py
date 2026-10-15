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
st.set_page_config(
    page_title="吾映良品柒 - 社區管理系統", page_icon="🏢", layout="wide"
)

# Session State 初始化登入狀態
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False

# ==========================================
# 3. 未登入狀態：登入畫面 (右側)
# ==========================================
if not st.session_state.logged_in:
  st.title("🏢 吾映良品柒 - 社區管理系統")
  st.write(
      "歡迎來到吾映良品柒社區專屬管理平台，請輸入戶號、預設密碼 (8888)"
      " 與社區驗證碼登入。"
  )
  st.markdown("---")

  col_left, col_right = st.columns([1, 1], gap="large")

  with col_left:
    st.subheader("💡 系統功能簡介")
    st.markdown("""
        * **社區名稱**：吾映良品柒
        * **初次登入說明**：所有戶號預設密碼皆為 **`8888`**。
        * **管理員專區**：戶號 **`608-23`** 為本社區管理員帳號。
        * **現任與歷屆委員**：快速查詢主委、監委、財委名單。
        * **管理費與供應商**：各戶 115 年繳費紀錄與常用修繕電話。
        """)

  with col_right:
    st.subheader("🔐 住戶 / 管理員登入")
    with st.form("login_form"):
      login_unit = st.text_input("請輸入戶號 (例如: 608 或 608-23)")
      login_pass = st.text_input("請輸入密碼 (預設 8888)", type="password")
      community_pin = st.text_input(
          "社區驗證碼 (PIN)",
          type="password",
          placeholder="請輸入本社區代碼",
      )
      submit_btn = st.form_submit_button("登入系統")

      if submit_btn:
        # 驗證社區 PIN 碼是否為 "608"
        if community_pin != "608":
          st.error("❌ 社區驗證碼錯誤！請輸入正確的社區代碼 (608)。")
        else:
          # 查詢資料庫驗證戶號與密碼
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
            st.error("❌ 戶號或密碼錯誤，請重新輸入！")

  st.stop()  # 未登入前停止執行後續頁面

# ==========================================
# 4. 已登入狀態：側邊欄導覽選單
# ==========================================
st.sidebar.title("🏢 吾映良品柒")
st.sidebar.success(
    f"目前登入：{st.session_state.user_code}"
    f" {'(管理員)' if st.session_state.is_admin else ''}"
)

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "功能選單",
    [
        "🏠 首頁 (現任委員)",
        "📜 歷屆委員名單",
        "💰 115年管理費紀錄",
        "🛠️ 供應商名冊",
        "🔑 變更個人密碼",
    ],
)

if st.sidebar.button("登出系統"):
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False
  st.rerun()

# ==========================================
# 5. 各頁面內容實作
# ==========================================

# ------------------------------------------
# 頁面一：首頁 (現任委員)
# ------------------------------------------
if menu == "🏠 首頁 (現任委員)":
  st.title("🏢 吾映良品柒社區 - 現任委員名單")
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
    st.warning("目前資料庫中尚未設定現任委員。")

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
# 頁面三：115年管理費繳交紀錄
# ------------------------------------------
elif menu == "💰 115年管理費繳交紀錄":
  st.title("💰 吾映良品柒社區管理費 115 年繳交紀錄")

  if st.session_state.is_admin:
    st.success("👑 您目前是以【管理員 (608-23)】身份登入，可檢視與維護全社區總表。")

    # 管理員可以直接檢視或新增/更新紀錄
    all_fees = (
        supabase.table("fee_records")
        .select("*")
        .eq("year", "115")
        .execute()
        .data
    )

    if all_fees:
      st.dataframe(all_fees, use_container_width=True)
    else:
      st.info("目前 115 年度尚無繳交紀錄資料。")

    with st.expander("➕ 新增或更新某戶繳費狀態"):
      with st.form("update_fee_form"):
        target_unit = st.selectbox(
            "選擇戶號",
            [
                "608",
                "608-1",
                "608-2",
                "608-3",
                "608-5",
                "608-6",
                "608-7",
                "608-8",
                "608-9",
                "608-10",
                "608-11",
                "608-12",
                "608-13",
                "608-15",
                "608-16",
                "608-17",
                "608-18",
                "608-19",
                "608-20",
                "608-21",
                "608-22",
                "608-23",
                "608-25",
                "608-26",
                "608-27",
            ],
        )
        pay_status = st.selectbox("繳費狀態", ["已繳1000元", "未繳"])
        signer = st.text_input("簽收人 (例如: 608-23)")
        notes = st.text_input("備註")
        submit_fee = st.form_submit_button("儲存繳費紀錄")

        if submit_fee:
          # 檢查是否已有該戶 115 年紀錄
          existing = (
              supabase.table("fee_records")
              .select("id")
              .eq("unit_code", target_unit)
              .eq("year", "115")
              .execute()
              .data
          )
          if existing:
            supabase.table("fee_records").update({
                "status": pay_status,
                "notes": f"簽收人: {signer} | 備註: {notes}",
                "amount": 1000,
            }).eq("id", existing[0]["id"]).execute()
          else:
            supabase.table("fee_records").insert({
                "unit_code": target_unit,
                "year": "115",
                "status": pay_status,
                "amount": 1000,
                "notes": f"簽收人: {signer} | 備註: {notes}",
            }).execute()
          st.success(f"已成功更新 {target_unit} 的繳費紀錄！")
          st.rerun()
  else:
    st.info(
        f"🏠 您目前是以【住戶】身份登入 (戶號: {st.session_state.user_code})，僅顯示您"
        "個人的 115 年繳費紀錄。"
    )
    my_fees = (
        supabase.table("fee_records")
        .select("*")
        .eq("unit_code", st.session_state.user_code)
        .eq("year", "115")
        .execute()
        .data
    )
    if my_fees:
      st.table(my_fees)
    else:
      st.info("查無您的 115 年度繳費紀錄，或管理員尚未登錄。")

# ------------------------------------------
# 頁面四：供應商名冊
# ------------------------------------------
elif menu == "🛠️ 供應商名冊":
  st.title("🛠️ 吾映良品柒社區 - 維修與供應商名冊")
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

# ------------------------------------------
# 頁面五：變更個人密碼
# ------------------------------------------
elif menu == "🔑 變更個人密碼":
  st.title("🔑 變更個人登入密碼")
  st.write(
      f"目前登入戶號：**{st.session_state.user_code}**。請輸入原密碼與新密碼進行修改。"
  )
  st.markdown("---")

  with st.form("change_pass_form"):
    old_pass = st.text_input("請輸入原密碼 (初次為 8888)", type="password")
    new_pass = st.text_input("請輸入新密碼", type="password")
    confirm_pass = st.text_input("再次確認新密碼", type="password")
    submit_change = st.form_submit_button("確認更改密碼")

    if submit_change:
      if not old_pass or not new_pass or not confirm_pass:
        st.warning("請填寫所有欄位！")
      elif new_pass != confirm_pass:
        st.error("❌ 兩次輸入的新密碼不一致，請重新檢查！")
      else:
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
          st.success("🎉 密碼修改成功！下次登入請使用新密碼。")
        else:
          st.error("❌ 原密碼錯誤，驗證失敗！")
