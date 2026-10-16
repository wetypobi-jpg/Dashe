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

st.title("💰 管理費繳交紀錄")
st.markdown("---")

all_fees_raw = supabase.table("fee_records").select("*").execute().data

current_year_str = str(datetime.now().year)  # 取得今年 (2026)

if all_fees_raw:
    available_years = sorted(list(set([str(f["year"]) for f in all_fees_raw])))
    if current_year_str not in available_years:
        available_years.insert(0, current_year_str)
    selected_year = st.selectbox("選擇查詢年度", available_years)
else:
    selected_year = current_year_str

st.markdown(f"### 📅 {selected_year} 年度繳交狀態")

# ==========================================
# 權限判定與動態抓取當年度財委
# ==========================================
units_data = supabase.table("units").select("*").execute().data
committees_data = supabase.table("committees").select("*").execute().data

is_current_treasurer = False
default_treasurer_signer = st.session_state.user_code

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


# 輔助函式：將原始資料轉為中文表頭且無 ID 的 DataFrame（簽收人與備註分開）
def format_fee_dataframe(fees_list):
    if not fees_list:
        return pd.DataFrame()
    df = pd.DataFrame(fees_list)

    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # 排序輔助函數：依 608、608-1、608-2... 遞增排序
    def sort_unit_key(unit_str):
        if unit_str == "608":
            return (608, 0)
        parts = str(unit_str).split("-")
        try:
            base = int(parts[0])
            sub = int(parts[1]) if len(parts) > 1 else 0
            return (base, sub)
        except ValueError:
            return (999, 999)

    if "unit_code" in df.columns:
        df["sort_key"] = df["unit_code"].apply(sort_unit_key)
        df = df.sort_values(by="sort_key").drop(columns=["sort_key"])
        df = df.reset_index(drop=True)

    # 如果舊資料是用 notes 欄位，相容對應到新的簽收人/備註
    rename_map = {
        "unit_code": "戶號",
        "year": "年度",
        "status": "繳費狀態",
        "amount": "付款金額 (元)",
        "payment_method": "付款方式",
        "payment_date": "付款日期",
        "notes": "簽收人",
        "remarks": "備註",
    }
    df = df.rename(columns=rename_map)

    preferred_order = [
        "戶號",
        "年度",
        "繳費狀態",
        "付款金額 (元)",
        "付款方式",
        "付款日期",
        "簽收人",
        "備註",
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
        f"👑 您目前是以【{role_title} ({st.session_state.user_code})】身份登入, 可檢視與維護全社區總表。"
    )

    year_fees = [
        f for f in all_fees_raw if str(f.get("year")) == str(selected_year)
    ]
    if year_fees:
        df_display = format_fee_dataframe(year_fees)
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info(f"目前 {selected_year} 年度尚無繳交紀錄資料。")

    if str(selected_year) != current_year_str:
        st.warning(
            f"⚠️ 依規定，管理與維護功能僅開放限今年度（{current_year_str}年）的資料。"
        )
    else:
        with st.expander(
            f"➕ 新增或更新 {current_year_str} 年度住戶繳費狀態 (管理/財委專用)"
        ):
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

            col_u1, col_u2 = st.columns([2, 3])
            with col_u1:
                selected_target_unit = st.selectbox(
                    "請選擇要新增或修改的住戶戶號", all_units_list
                )

            existing_record = None
            for f in year_fees:
                if str(f.get("unit_code")) == str(selected_target_unit):
                    existing_record = f
                    break

            default_status = (
                existing_record.get("status", "未繳")
                if existing_record
                else "未繳"
            )
            default_amount = (
                int(existing_record.get("amount", 1000))
                if existing_record
                else 1000
            )
            default_method = (
                existing_record.get("payment_method", "現金")
                if existing_record
                else "現金"
            )
            default_date = date.today()
            if existing_record and existing_record.get("payment_date"):
                try:
                    default_date = datetime.strptime(
                        str(existing_record.get("payment_date")), "%Y-%m-%d"
                    ).date()
                except:
                    pass

            # 簽收人與備註獨立抓取
            default_signer = (
                existing_record.get("notes", default_treasurer_signer)
                if existing_record
                else default_treasurer_signer
            )
            default_remarks = (
                existing_record.get("remarks", "") if existing_record else ""
            )
            record_id = existing_record.get("id") if existing_record else None

            with col_u2:
                if existing_record:
                    st.info(
                        f"ℹ️ 該住戶有資料，以下是自動帶入之內容，修改後送出即為更新。"
                    )
                else:
                    st.info(
                        f"ℹ️ 無資料，注意現為新增功能，送出後將新增紀錄。"
                    )

            with st.form("update_fee_form"):
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

                # 獨立的簽收人與備註輸入框
                signer = st.text_input("簽收人", value=default_signer)
                remarks = st.text_input("備註", value=default_remarks)

                submit_fee = st.form_submit_button("儲存繳費紀錄")

                if submit_fee:
                    # 防呆檢查：若記錄不存在，且資料庫中已存在該年度該戶號的資料，則阻止新增避免重複
                    if not record_id:
                        latest_check = (
                            supabase.table("fee_records")
                            .select("id")
                            .eq("unit_code", selected_target_unit)
                            .eq("year", current_year_str)
                            .execute()
                        )
                        if latest_check.data and len(latest_check.data) > 0:
                            st.error(
                                f"❌ 錯誤：戶號 `{selected_target_unit}` 在 {current_year_str} 年度已有繳費紀錄，每戶每年僅能有一筆資料，請直接修改現有資料！"
                            )
                            st.stop()

                    payload = {
                        "unit_code": selected_target_unit,
                        "year": current_year_str,
                        "status": pay_status,
                        "amount": pay_amount,
                        "payment_method": pay_method,
                        "payment_date": str(pay_date),
                        "notes": signer,  # 獨立儲存至 notes (簽收人)
                        "remarks": remarks,  # 獨立儲存至 remarks (備註)
                    }

                    if record_id:
                        supabase.table("fee_records").update(payload).eq(
                            "id", record_id
                        ).execute()
                    else:
                        supabase.table("fee_records").insert(payload).execute()

                    st.success(
                        f"已成功儲存戶號 `{selected_target_unit}` 的"
                        f" {current_year_str} 年度繳費紀錄！"
                    )
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
