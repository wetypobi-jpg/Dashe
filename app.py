import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def init_connection():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

st.set_page_config(
    page_title="吾映良品柒 - 社區管理系統", page_icon="🏢", layout="wide"
)

# 初始化登入狀態 (包含 is_admin 與 role，已移除 is_treasurer)
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False
  st.session_state.role = None

# ==========================================
# 未登入狀態：顯示登入與更改密碼畫面
# ==========================================
if not st.session_state.logged_in:
  st.title("🏢 吾映良品柒 - 社區管理系統")
  st.write("歡迎來到吾映良品柒社區專屬管理平台，請輸入您的戶號與密碼登入。")
  st.markdown("---")

  col_left, col_right = st.columns([1, 1], gap="large")

  with col_left:
    st.subheader("💡 系統功能簡介")
    st.markdown("""
        * **委員與歷屆名單**：本屆現任委員與各戶歷年服務次數統計。
        * **管理費繳交紀錄**：各戶歷年管理費繳費狀態與金額明細。
        * **供應商名冊**：社區常用修繕廠商電話與聯繫資料。
        
        *各戶預設登入密碼與相關資訊已於 LINE 群組公佈，請登入後修改密碼。*  
        *系統使用問題請洽608-23號。*
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
            # 完整回傳資料庫中的 role 資訊 (例如 '主委', '財委', '監委' 或 None)
            st.session_state.role = matched_user.get("role")
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

  st.stop()

# ==========================================
# 已登入狀態：側邊欄與首頁歡迎區塊
# ==========================================
st.sidebar.title("🏢 吾映良品柒")

role_badge = ""
if st.session_state.is_admin:
  role_badge = "(管理員)"
elif st.session_state.get("role"):
  role_badge = f"({st.session_state.role})"
else:
  role_badge = "(住戶)"

st.sidebar.success(f"目前登入：{st.session_state.user_code} {role_badge}")
st.sidebar.markdown("---")

if st.sidebar.button("🚪 登出系統", use_container_width=True):
  st.session_state.logged_in = False
  st.session_state.user_code = ""
  st.session_state.is_admin = False
  st.session_state.role = None
  st.rerun()

st.title("🏢 吾映良品柒社區管理系統")
st.success(f"目前登入戶號：{st.session_state.user_code}")
st.write("歡迎使用社區專屬管理系統！")
st.info(
    "👈 請從左側選單切換您要查看的功能（委員與歷屆名單、管理費繳交紀錄、供應商名冊）。"
)
