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

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False

# ==========================================
# 2. 使用 st.navigation 自訂左側選單名稱
# ==========================================
# 這裡可以把原本叫 app.py 的首頁自訂標題改為 "首頁" 或 "住戶登入"
pg = st.navigation({

        st.Page("app.py", title="🏠首頁", default=True),
        st.Page("pages/1_👥_現任委員.py", title="現任委員"),
        st.Page("pages/2_📜_歷屆委員名單.py", title="歷屆委員名單"),
        st.Page("pages/3_💰_管理費繳交紀錄.py", title="管理費繳交紀錄"),
        st.Page("pages/4_🛠️_供應商名冊.py", title="供應商名冊"),
    
})

# ==========================================
# 3. 首頁 / 登入頁面實際內容
# ==========================================
if st.session_state.logged_in:
  st.title("🏢 吾映良品柒社區管理系統")
  st.success(
      f"目前登入戶號：{st.session_state.user_code}"
      f" {'(管理員)' if st.session_state.is_admin else ''}"
  )
  st.write("您已經成功登入系統！")
  st.info(
      "👈 請從左側選單切換您要查看的功能（現任委員、歷屆委員、管理費繳交紀錄、供應商名冊）。"
  )

  st.markdown("---")
  if st.button("🚪 登出系統", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_code = ""
    st.session_state.is_admin = False
    st.rerun()
else:
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

# 最後透過 pg.run() 渲染整體的導覽與頁面
pg.run()
