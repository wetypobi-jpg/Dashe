from datetime import date, datetime, time
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

st.title("📝 吾映良品柒社區 - 議事與活動紀錄")
st.markdown("在這裡您可以查閱社區大會會議紀錄，以及歷年來社區所做的大小重要記事與活動歷程。")
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

if is_admin:
    st.success(
        f"👑 您目前是以【管理員 ({st.session_state.user_code})】身分登入，可進行資料的新增與維護。"
    )

# 建立頁籤切換
tab_minutes, tab_events = st.tabs(["📋 社區大會會議紀錄", "📅 社區重要記事與活動歷程"])

# ==========================================
# 頁籤一：社區大會會議紀錄
# ==========================================
with tab_minutes:
    st.subheader("📋 歷次社區大會會議紀錄與決議")

    if is_admin:
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
                    height=200,
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

    # 讀取會議紀錄資料
    minutes_raw = (
        supabase.table("meeting_minutes")
        .select("*")
        .order("meeting_date", desc=True)
        .execute()
        .data
    )

    if minutes_raw:
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
        selected_year_m = st.selectbox("📅 選擇查看年度 (會議紀錄)", ["全部顯示"] + years_list, key="sel_year_m")

        filtered_minutes = minutes_raw
        if selected_year_m != "全部顯示":
            filtered_minutes = [
                m
                for m in minutes_raw
                if str(m["meeting_date"]).startswith(selected_year_m)
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
                    f"👥 出席戶數：{m_attendees} 戶 ｜ ✍️ 記錄人（戶號）：{m_creator}"
                )
                st.markdown(m_content)

                if is_admin:
                    if st.button(
                        f"🗑️ 刪除此筆會議紀錄 ({m_title})", key=f"del_min_{m_id}"
                    ):
                        supabase.table("meeting_minutes").delete().eq(
                            "id", m_id
                        ).execute()
                        st.warning(f"已刪除會議紀錄：{m_title}")
                        st.rerun()
                st.markdown("---")
    else:
        st.info("目前尚無任何社區大會會議紀錄。")

# ==========================================
# 頁籤二：社區重要記事與活動歷程
# ==========================================
with tab_events:
    st.subheader("📅 社區大小事與重要活動歷程紀錄")
    st.markdown("供住戶與管理團隊查閱各期間所執行的重大事項（含精確起訖時間）。")

    if is_admin:
        with st.expander("➕ 新增社區重要記事/活動 (管理員專用)"):
            with st.form("add_event_form"):
                event_title = st.text_input(
                    "記事/活動標題", placeholder="例如：收取2026年度公共費用"
                )
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    st.markdown("**開始時間**")
                    start_d = st.date_input("開始日期", value=date.today(), key="start_d")
                    start_t = st.time_input("開始時間", value=time(9, 0), key="start_t")
                with col_e2:
                    st.markdown("**結束時間 (選填區間)**")
                    has_end = st.checkbox("啟用結束時間區間", value=False)
                    end_d = st.date_input("結束日期", value=date.today(), key="end_d") if has_end else None
                    end_t = st.time_input("結束時間", value=time(18, 0), key="end_t") if has_end else None

                event_category = st.selectbox(
                    "類別", ["一般記事", "財務收費", "委員決議", "修繕維護", "交接事項"]
                )

                event_desc = st.text_area(
                    "記事詳細說明",
                    height=150,
                    placeholder="請輸入該事件的詳細執行內容或結果...",
                )

                submit_event = st.form_submit_button("儲存社區記事")

                if submit_event:
                    if not event_title.strip() or not event_desc.strip():
                        st.error("❌ 記事標題與說明不得為空！")
                    else:
                        start_datetime = datetime.combine(start_d, start_t)
                        end_datetime = datetime.combine(end_d, end_t) if has_end and end_d and end_t else None

                        payload_e = {
                            "start_time": str(start_datetime),
                            "end_time": str(end_datetime) if end_datetime else None,
                            "title": event_title.strip(),
                            "category": event_category,
                            "description": event_desc.strip(),
                            "creator_unit": st.session_state.user_code,
                        }
                        supabase.table("community_events").insert(payload_e).execute()
                        st.success("🎉 社區記事已成功新增！")
                        st.rerun()

    # 讀取社區記事資料
    events_raw = (
        supabase.table("community_events")
        .select("*")
        .order("start_time", desc=True)
        .execute()
        .data
    )

    if events_raw:
        years_list_e = sorted(
            list(
                set(
                    [
                        str(e["start_time"][:4])
                        for e in events_raw
                        if "start_time" in e
                    ]
                )
            ),
            reverse=True,
        )
        selected_year_e = st.selectbox("📅 選擇查看年度 (社區記事)", ["全部顯示"] + years_list_e, key="sel_year_e")

        filtered_events = events_raw
        if selected_year_e != "全部顯示":
            filtered_events = [
                e
                for e in events_raw
                if str(e["start_time"]).startswith(selected_year_e)
            ]

        for e in filtered_events:
            e_id = e.get("id")
            e_title = e.get("title")
            e_start = e.get("start_time")
            e_end = e.get("end_time")
            e_cat = e.get("category", "一般記事")
            e_desc = e.get("description", "")
            e_creator = e.get("creator_unit", "")

            # 組合日期時間顯示格式
            time_display = e_start
            if e_end:
                time_display = f"{e_start} ～ {e_end}"

            with st.container():
                st.markdown(f"#### 🔹 【{e_cat}】{time_display}｜{e_title}")
                st.caption(f"✍️ 紀錄人（戶號）：{e_creator}")
                st.write(e_desc)

                if is_admin:
                    if st.button(
                        f"🗑️ 刪除此筆記事 ({e_title})", key=f"del_ev_{e_id}"
                    ):
                        supabase.table("community_events").delete().eq(
                            "id", e_id
                        ).execute()
                        st.warning(f"已刪除記事：{e_title}")
                        st.rerun()
                st.markdown("---")
    else:
        st.info("目前尚無任何社區重要記事記錄。")
