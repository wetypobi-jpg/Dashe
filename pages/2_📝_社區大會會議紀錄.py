from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 權限與登入檢查
if (
    "logged_in" not in st.session_state
    or not st.session_state.logged_in
    or not st.session_state.user_code
):
    st.warning("⚠️ 請先至首頁登入系統！")
    st.stop()

st.title("📝 吾映良品柒社區 - 社區大會會議紀錄")
st.markdown("在這裡您可以查看歷次社區大會的詳細會議紀錄與決議事項。")
st.markdown("---")

# 取得當前使用者身分與權限
units_data = supabase.table("units").select("*").execute().data
current_user_unit = None
if units_data:
    for u in units_data:
        if str(u.get("unit_code")) == str(st.session_state.user_code):
            current_user_unit = u
            break

is_admin = current_user_unit and current_user_unit.get("is_admin")

# 讀取會議紀錄資料
minutes_raw = (
    supabase.table("meeting_minutes")
    .select("*")
    .order("meeting_date", desc=True)
    .execute()
    .data
)

if is_admin:
    st.success(
        f"👑 您目前是以【管理員 ({st.session_state.user_code})】身分登入，可進行會議紀錄的新增與維護。"
    )

    with st.expander("➕ 新增或發布新的社區大會會議紀錄 (管理員專用)"):
        with st.form("add_meeting_form"):
            new_title = st.text_input(
                "會議標題", placeholder="例如：2026年度第一次區分所有權人會議"
            )
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                new_date = st.date_input("會議日期", value=date.today())
            with col_m2:
                new_attendees = st.number_input(
                    "出席戶數/人數", min_value=0, value=15, step=1
                )

            new_content = st.text_area(
                "會議紀錄內容 (支援 Markdown 語法)",
                height=250,
                placeholder="請輸入討論事項、決議結果及交辦事項...",
            )

            submit_minute = st.form_submit_button("發布會議紀錄")

            if submit_minute:
                if not new_title.strip() or not new_content.strip():
                    st.error("❌ 會議標題與內容不得為空！")
                else:
                    payload = {
                        "meeting_date": str(new_date),
                        "title": new_title.strip(),
                        "content": new_content.strip(),
                        "attendees_count": int(new_attendees),
                        "creator_unit": st.session_state.user_code,
                    }
                    supabase.table("meeting_minutes").insert(payload).execute()
                    st.success("🎉 會議紀錄已成功發布！")
                    st.rerun()

st.markdown("### 📚 歷次會議紀錄列表")

if minutes_raw:
    # 建立年份篩選
    years_list = sorted(
        list(
            set(
                [
                    str(m["meeting_date"][:4])
                    for m in minutes_raw
                    if "meeting_date" in m
                ]
            )
        ),
        reverse=True,
    )
    selected_year = st.selectbox("📅 選擇查看年度", ["全部顯示"] + years_list)

    filtered_minutes = minutes_raw
    if selected_year != "全部顯示":
        filtered_minutes = [
            m
            for m in minutes_raw
            if str(m["meeting_date"]).startswith(selected_year)
        ]

    for m in filtered_minutes:
        m_id = m.get("id")
        m_title = m.get("title")
        m_date = m.get("meeting_date")
        m_attendees = m.get("attendees_count", 0)
        m_creator = m.get("creator_unit", "")
        m_content = m.get("content", "")

        with st.container():
            st.markdown(f"#### 📌 {m_date}｜{m_title}")
            st.caption(
                f"👥 出席戶數：{m_attendees} 戶 ｜ ✍️ 記錄人：{m_creator}"
            )

            # 顯示本文內容
            st.markdown(m_content)

            # 若為管理員，提供刪除或修改的按鈕選項
            if is_admin:
                if st.button(
                    f"🗑️ 刪除此筆紀錄 ({m_title})", key=f"del_min_{m_id}"
                ):
                    supabase.table("meeting_minutes").delete().eq(
                        "id", m_id
                    ).execute()
                    st.warning(f"已刪除會議紀錄：{m_title}")
                    st.rerun()

            st.markdown("---")
else:
    st.info("目前尚無任何社區大會會議紀錄。")
