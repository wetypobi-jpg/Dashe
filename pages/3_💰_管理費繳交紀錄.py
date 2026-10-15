from datetime import date
import pandas as pd
import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 權限檢查：未登入者禁止進入
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
# 判斷是否具備管理權限 (管理員 或 財委)
# ==========================================
has_management_rights = st.session_state.get(
    "is_admin", False
) or st.session_state.get("is_treasurer", False)

if has_management_rights:
  role_title = (
      "管理員" if st.session_state.get("is_admin") else "財務委員"
  )
  st.success(
      f"👑 您目前是以【{role_title} ({st.session_state.user_code})】身份登入，可檢視與維護全社區總表。"
  )

  year_fees = [
      f for f in all_fees_raw if str(f.get("year")) == str(selected_year)
  ]
  if year_fees:
    st.dataframe(year_fees, use_container_width=True)
  else:
    st.info(f"目前 {selected_year} 年度尚無繳交紀錄資料。")

  # 管理權限專用：新增與更新表單 (包含金額、付款方式、付款日期)
  with st.expander(
      f"➕ 新增或更新 {selected_year} 年度某戶繳費狀態 (管理員/財委專用)"
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

# ==========================================
# 一般住戶身分：僅能查詢自己的個人繳交紀錄
# ==========================================
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
