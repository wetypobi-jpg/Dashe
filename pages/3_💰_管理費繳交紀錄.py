from datetime import date, datetime
import pandas as pd
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

st.title("💰 吾映良品柒社區 - 管理費繳交紀錄")

all_fees_raw = supabase.table("fee_records").select("*").execute().data

if all_fees_raw:
  available_years = sorted(list(set([str(f["year"]) for f in all_fees_raw])))
  selected_year = st.selectbox("選擇查詢年度", available_years)
else:
  selected_year = "115"

st.markdown(f"### 📅 {selected_year} 年度繳交狀態")

# ==========================================
# 權限判定與動態抓取當年度財委 (格式：戶號(任期-職稱))
# ==========================================
current_year_str = str(datetime.now().year)
units_data = supabase.table("units").select("*").execute().data
committees_data = supabase.table("committees").select("*").execute().data

is_current_treasurer = False
default_treasurer_signer = st.session_state.user_code  # 預設備援

# 1. 先從 units 檢查該使用者是否具備管理員或財委身分
current_user_unit = None
if units_data:
  for u in units_data:
    if str(u.get("unit_code")) == str(st.session_state.user_code):
      current_user_unit = u
      break

# 2. 自動尋找當年度的財委並組合格式 "戶號(任期-職稱)"
if committees_data:
  for c in committees_data:
    year_str = str(c.get("year", ""))
    if current_year_str in year_str and c.get("role") == "財務委員":
      t_unit = c.get("unit_code", "")
      t_name = c.get("name", "")
      # 組合格式：戶號(任期-財委) 或 戶號(姓名-財委)
      default_treasurer_signer = f"{t_unit}({year_str}-財委)"
      break

# 如果 units 裡面直接記錄了 role == '財委' 也可以做雙重對照
if current_user_unit and current_user_unit.get("role") == "財委":
  is_current_treasurer = True

has_management_rights = (
    (current_user_unit and current_user_unit.get("is_admin"))
    or (current_user_unit and current_user_unit.get("role") in ["主委", "財委"])
    or is_current_treasurer
)

if has_management_rights:
  user_role_label = (
      "管理員"
      if (current_user_unit and current_user_unit.get("is_admin"))
      else (
          current_user_unit.get("role")
          if (current_user_unit and current_user_unit.get("role"))
          else "財務委員"
      )
  )
  st.success(
      f"👑 您目前是以【{user_role_label} ({st.session_state.user_code})】身份登入，可檢視與維護全社區總表。"
  )

  year_fees = [
      f for f in all_fees_raw if str(f.get("year")) == str(selected_year)
  ]
  if year_fees:
    st.dataframe(year_fees, use_container_width=True)
  else:
    st.info(f"目前 {selected_year} 年度尚無繳交紀錄資料。")

  with st.expander("➕ 新增或更新 住戶繳費狀態 (管理/財委專用)"):
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
      pay_status = st.selectbox("繳費狀態", ["已繳", "未繳"])

      col_f1, col_f2, col_f3 = st.columns(3)
      with col_f1:
        pay_amount = st.number_input("付款金額 (元)", value=1000, step=100)
      with col_f2:
        pay_method = st.selectbox(
            "付款方式", ["現金", "轉帳", "Line Pay", "其他"]
        )
      with col_f3:
        pay_date = st.date_input("付款日期", value=date.today())

      # 簽收人預設自動帶入：戶號(任期-財委)
      signer = st.text_input("簽收人", value=default_treasurer_signer)
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

        payload = {
            "unit_code": target_unit,
            "year": input_year.strip(),
            "status": pay_status,
            "amount": pay_amount,
            "payment_method": pay_method,
            "payment_date": str(pay_date),
            "notes": f"簽收人: {signer} | 備註: {notes}",
        }

        if existing:
          supabase.table("fee_records").update(payload).eq(
              "id", existing[0]["id"]
          ).execute()
        else:
          supabase.table("fee_records").insert(payload).execute()

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
    st.dataframe(my_fees, use_container_width=True)
  else:
    st.info(f"查無您的 {selected_year} 年度繳費紀錄，或管理員尚未登錄。")
