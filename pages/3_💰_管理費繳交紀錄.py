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
  selected_year = "2026"

st.markdown(f"### 📅 {selected_year} 年度繳交狀態")

# ==========================================
# 權限判定與動態抓取當年度財委 (格式：戶號(任期-職稱))
# ==========================================
current_year_str = str(datetime.now().year)
units_data = supabase.table("units").select("*").execute().data
committees_data = supabase.table("committees").select("*").execute().data

is_current_treasurer = False
default_treasurer_signer = st.session_state.user_code  # 預設備援

current_user_unit = None
if units_data:
  for u in units_data:
    if str(u.get("unit_code")) == str(st.session_state.user_code):
      current_user_unit = u
      break

if committees_data:
  for c in committees_data:
    year_str = str(c.get("year", ""))
    if current_year_str in year_str and c.get("role") == "財務委員":
      t_unit = c.get("unit_code", "")
      default_treasurer_signer = f"{t_unit}({year_str}-財委)"
      break

if current_user_unit and current_user_unit.get("role") == "財委":
  is_current_treasurer = True

has_management_rights = (
    (current_user_unit and current_user_unit.get("is_admin"))
    or (current_user_unit and current_user_unit.get("role") == "財委")
    or is_current_treasurer
)


# 輔助函式：將原始資料轉為乾淨、中文表頭且無 ID 的 DataFrame
def format_fee_dataframe(fees_list):
  if not fees_list:
    return pd.DataFrame()
  df = pd.DataFrame(fees_list)

  if "id" in df.columns:
    df = df.drop(columns=["id"])

  rename_map = {
      "unit_code": "戶號",
      "year": "年度",
      "status": "繳費狀態",
      "amount": "付款金額 (元)",
      "payment_method": "付款方式",
      "payment_date": "付款日期",
      "notes": "備註 / 簽收人",
  }
  df = df.rename(columns=rename_map)

  preferred_order = [
      "戶號",
      "年度",
      "繳費狀態",
      "付款金額 (元)",
      "付款方式",
      "付款日期",
      "備註 / 簽收人",
  ]
  existing_cols = [c for c in preferred_order if c in df.columns]
  other_cols = [c for c in df.columns if c not in preferred_order]
  df = df[existing_cols + other_cols]

  return df


if has_management_rights:
  role_title = (
      "管理員"
      if (current_user_unit and current_user_unit.get("is_admin"))
      else "財務委員"
  )
  st.success(
      f"👑 您目前是以【{role_title} ({st.session_state.user_code})】身份登入，可檢視與維護全社區總表。"
  )

  year_fees = [
      f for f in all_fees_raw if str(f.get("year")) == str(selected_year)
  ]
  if year_fees:
    df_display = format_fee_dataframe(year_fees)
    st.dataframe(df_display, use_container_width=True)
  else:
    st.info(f"目前 {selected_year} 年度尚無繳交紀錄資料。")

  with st.expander("➕ 新增或更新 住戶繳費狀態 (管理/財委專用)"):
    edit_options = ["➕ 新增一筆紀錄"]
    fee_map = {}
    for f in year_fees:
      label = f"戶號 {f['unit_code']} （狀態：{f['status']} | 金額：{f['amount']}）"
      edit_options.append(label)
      fee_map[label] = f

    selected_action = st.selectbox(
        "選擇操作模式（如需修改請直接點選該戶紀錄，或選擇新增）", edit_options
    )

    default_unit = "608"
    default_status = "未繳"
    default_amount = 1000
    default_method = "現金"
    default_date = date.today()
    default_notes = ""
    target_record_id = None

    if selected_action != "➕ 新增一筆紀錄":
      target_record = fee_map[selected_action]
      default_unit = target_record.get("unit_code", "608")
      default_status = target_record.get("status", "未繳")
      try:
        default_amount = int(target_record.get("amount", 1000))
      except:
        default_amount = 1000
      default_method = target_record.get("payment_method", "現金")
      d_str = target_record.get("payment_date")
      if d_str:
        try:
          default_date = datetime.strptime(str(d_str), "%Y-%m-%d").date()
        except:
          default_date = date.today()
      default_notes = target_record.get("notes", "")
      target_record_id = target_record.get("id")

    with st.form("update_fee_form"):
      all_units_list = [
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
      ]
      unit_index = (
          all_units_list.index(default_unit)
          if default_unit in all_units_list
          else 0
      )
      target_unit = st.selectbox(
          "選擇戶號", all_units_list, index=unit_index
      )

      input_year = st.text_input("輸入年度 (例如: 2026)", value=selected_year)

      status_options = ["已繳", "未繳"]
      status_index = (
          status_options.index(default_status)
          if default_status in status_options
          else 0
      )
      pay_status = st.selectbox(
          "繳費狀態", status_options, index=status_index
      )

      col_f1, col_f2, col_f3 = st.columns(3)
      with col_f1:
        # 修正數值型態一致性（皆為 int）
        pay_amount = st.number_input(
            "付款金額 (元)", value=int(default_amount), step=100
        )
      with col_f2:
        method_options = ["現金", "轉帳", "Line Pay", "其他"]
        method_index = (
            method_options.index(default_method)
            if default_method in method_options
            else 0
        )
        pay_method = st.selectbox(
            "付款方式", method_options, index=method_index
        )
      with col_f3:
        pay_date = st.date_input("付款日期", value=default_date)

      signer = st.text_input("簽收人", value=default_treasurer_signer)
      notes = st.text_input("備註", value=default_notes)
      submit_fee = st.form_submit_button("儲存繳費紀錄")

      if submit_fee:
        payload = {
            "unit_code": target_unit,
            "year": input_year.strip(),
            "status": pay_status,
            "amount": pay_amount,
            "payment_method": pay_method,
            "payment_date": str(pay_date),
            "notes": f"簽收人: {signer} | 備註: {notes}",
        }

        if target_record_id:
          supabase.table("fee_records").update(payload).eq(
              "id", target_record_id
          ).execute()
        else:
          existing = (
              supabase.table("fee_records")
              .select("id")
              .eq("unit_code", target_unit)
              .eq("year", input_year.strip())
              .execute()
              .data
          )
          if existing:
            supabase.table("fee_records").update(payload).eq(
                "id", existing[0]["id"]
            ).execute()
          else:
            supabase.table("fee_records").insert(payload).execute()

        st.success(f"已成功儲存 {target_unit} 的 {input_year} 年度繳費紀錄！")
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
    df_my = format_fee_dataframe(my_fees)
    st.dataframe(df_my, use_container_width=True)
  else:
    st.info(f"查無您的 {selected_year} 年度繳費紀錄，或管理員尚未登錄。")
