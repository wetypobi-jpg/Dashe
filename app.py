import streamlit as st
from supabase import create_client

# ==========================================
# 1. 初始化連線與基本設定
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def init_connection():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

st.set_page_config(
    page_title="吾映良品柒 - 社區管理系統", page_icon="🏢", layout="wide"
)

# 初始化登入狀態
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False

# ==========================================
# 2. 未登入狀態：顯示登入與更改密碼畫面
# ==========================================
if not st.session_state.logged_in:
  st.title("🏢 吾映良品柒 - 社區管理系統")
  st.write("歡迎來到吾映良品柒社區專屬管理平台，請輸入您的戶號與密碼登入。")
  st.markdown("---")

  col_left, col_right = st.columns([1, 1], gap="large")

  with col_left:
    st.subheader("💡 系統功能簡介")
    st.markdown("""
        * **現任與歷屆委員**：快速查詢主委、監委、財委名單。
        * **管理費繳交紀錄**：各戶歷年管理費繳費狀態總覽。
        * **供應商名冊**：社區常用修繕廠商電話與評價備註。
        
        *各戶預設登入密碼與相關資訊已於 LINE 群組公佈。*
        """)

  with col_right:
    st.subheader("🔐 住戶 / 管理員登入")
    with st.form("login_form"):
      login_unit = st.text_input("請輸入戶號 (例如: 608 或 608-23)")
      login_pass = st.text_input("請輸入密碼", type="password")
      community_pin = st.text_input(
          "社區驗證碼 (PIN)", type="password", placeholder="請輸入本社區代碼"
      )
      submit_btn = st.form_submit_button("登入系統")

      if submit_btn:
        clean_unit = login_unit.strip()
        if community_pin != "608":
          st.error("❌ 社區驗證碼錯誤！")
        else:
          response = supabase.table("units").select("*").execute()
          matched_user = None
          if response.data:
            for u in response.data:
              if str(u.get("unit_code")).strip() == clean_unit:
                matched_user = u
                break

          if matched_user and str(matched_user.get("password")).strip() == str(
              login_pass
          ).strip():
            st.session_state.logged_in = True
            st.session_state.user_code = clean_unit
            st.session_state.is_admin = bool(matched_user.get("is_admin"))
            st.success("登入成功！載入中...")
            st.rerun()
          else:
            st.error("❌ 戶號或密碼錯誤，請重新輸入！")

    with st.expander("🔑 首次登入或忘記密碼？點此更改密碼"):
      with st.form("login_change_pass_form"):
        target_u = st.text_input("請輸入您的戶號", key="l_unit")
        old_p = st.text_input("原密碼", type="password", key="l_old")
        new_p = st.text_input("設定新密碼", type="password", key="l_new")
        submit_l_change = st.form_submit_button("確認更新密碼")

        if submit_l_change:
          c_u = target_u.strip()
          res = supabase.table("units").select("*").execute()
          found = None
          if res.data:
            for x in res.data:
              if str(x.get("unit_code")).strip() == c_u:
                found = x
                break
          if found and str(found.get("password")).strip() == old_p.strip():
            supabase.table("units").update({"password": new_p.strip()}).eq(
                "unit_code", c_u
            ).execute()
            st.success("🎉 密碼修改成功！請使用新密碼登入。")
          else:
            st.error("❌ 戶號或原密碼錯誤！")

  st.stop()  # 未登入時停止執行後續程式碼

# ==========================================
# 3. 已登入狀態：側邊欄導覽選單與各頁面實作
# ==========================================
st.sidebar.title("🏢 吾映良品柒")
st.sidebar.success(
    f"目前登入：{st.session_state.user_code}"
    f" {'(管理員)' if st.session_state.is_admin else ''}"
)
st.sidebar.markdown("---")

st.sidebar.write("📌 **功能導覽列**")
menu = st.sidebar.radio(
    "選擇功能",
    [
        "🏠 首頁",
        "👥 現任委員",
        "📜 歷屆委員名單",
        "💰 管理費繳交紀錄",
        "🛠️ 供應商名冊",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 登出系統", use_container_width=True):
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False
  st.rerun()

# ------------------------------------------
# 頁面：首頁
# ------------------------------------------
if menu == "🏠 首頁":
  st.title("🏢 吾映良品柒社區管理系統")
  st.success(f"目前登入戶號：{st.session_state.user_code}")
  st.write("歡迎使用社區專屬管理系統！")
  st.info("👈 請從左側選單切換您要查看的功能分頁。")

# ------------------------------------------
# 頁面：現任委員
# ------------------------------------------
elif menu == "👥 現任委員":
  st.title("🏢 吾映良品柒社區 - 現任委員名單 (2024-2026)")
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
  else:
    st.warning("目前資料庫中尚未設定現任委員。")

# ------------------------------------------
# 頁面：歷屆委員名單
# ------------------------------------------
elif menu == "📜 歷屆委員名單":
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

# ------------------------------------------
# 頁面：管理費繳交紀錄
# ------------------------------------------
elif menu == "💰 管理費繳交紀錄":
  st.title("💰 吾映良品柒社區 - 管理費繳交紀錄")

  all_fees_raw = supabase.table("fee_records").select("*").execute().data

  if all_fees_raw:
    available_years = sorted(list(set([str(f["year"]) for f in all_fees_raw])))
    selected_year = st.selectbox("選擇查詢年度", available_years)
  else:
    selected_year = "115"

  st.markdown(f"### 📅 {selected_year} 年度繳交狀態")

  if st.session_state.is_admin:
    st.success(
        f"👑 您目前是以【管理員 ({st.session_state.user_code})】身份登入，可檢視與維護全社區總表。"
    )

    year_fees = [
        f for f in all_fees_raw if str(f.get("year")) == str(selected_year)
    ]
    if year_fees:
      st.dataframe(year_fees, use_container_width=True)
    else:
      st.info(f"目前 {selected_year} 年度尚無繳交紀錄資料。")

    with st.expander(
        f"➕ 新增或更新 {selected_year} 年度某戶繳費狀態 (管理員專用)"
    ):
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
        input_year = st.text_input("輸入年度 (例如: 115)", value=selected_year)
        pay_status = st.selectbox("繳費狀態", ["已繳1000元", "未繳"])
        signer = st.text_input(
            "簽收人 (例如: 608-23)", value=st.session_state.user_code
        )
        notes = st.text_input("備註")
        submit_fee = st.form_submit_button("儲存繳費紀錄")

        if submit_fee:
          existing = (
              supabase.table("fee_records")
              .select("id")
              .eq("unit_code", target_unit)
              .eq("year", input_year.strip())
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
                "year": input_year.strip(),
                "status": pay_status,
                "amount": 1000,
                "notes": f"簽收人: {signer} | 備註: {notes}",
            }).execute()
          st.success(f"已成功更新 {target_unit} 的 {input_year} 年度繳費紀錄！")
          st.rerun()
  else:
    st.info(
        f"🏠 您目前是以【住戶】身份登入 (戶號: {st.session_state.user_code})，僅顯示您"
        f"個人的 {selected_year} 年繳費紀錄。"
    )
    my_fees = [
        f
        for f in all_fees_raw
        if str(f.get("unit_code")) == str(st.session_state.user_code)
        and str(f.get("year")) == str(selected_year)
    ]
    if my_fees:
      st.table(my_fees)
    else:
      st.info(f"查無您的 {selected_year} 年度繳費紀錄，或管理員尚未登錄。")

# ------------------------------------------
# 頁面：供應商名冊
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
