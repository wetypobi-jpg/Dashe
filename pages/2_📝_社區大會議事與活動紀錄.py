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
user_role = current_user_unit.get("role") if current_user_unit else None

# 權限判斷：管理員可全權操作；主委、財委、監委可新增與更新
can_manage = is_admin or user_role in ["主委", "財委", "監委"]

if can_manage:
    role_title = "管理員" if is_admin else f"{user_role}"
    st.success(
        f"👑 您目前是以【{role_title} ({st.session_state.user_code})】身分登入，可進行內容的新增與維護。"
    )

# 建立頁籤切換
tab_minutes, tab_events = st.tabs(["📋 社區大會會議紀錄", "📅 社區重要記事與活動歷程"])

# ==========================================
# 頁籤一：社區大會會議紀錄
# ==========================================
with tab_minutes:
    st.subheader("📋 歷次社區大會會議紀錄與決議")

    # 新增會議紀錄表單
    if can_manage:
        with st.expander("➕ 【點此展開】新增或發布新的社區大會會議紀錄"):
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

                submit_minute = st.form_submit_button("📢 確認並發布會議紀錄")

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

        st.markdown("---")
        
        if "edit_meeting_id" not in st.session_state:
            st.session_state.edit_meeting_id = None

        for m in filtered_minutes:
            m_id = m.get("id")
            m_title = m.get("title")
            m_date = m.get("meeting_date")
            m_attendees = m.get("attendees_count", 0)
            m_creator = m.get("creator_unit", "")
            m_content = m.get("content", "")

            # 整張卡片改用 expander 包覆收合
            with st.expander(f"📌 [{m_date}] {m_title} (出席: {m_attendees}戶)"):
                st.caption(f"👥 出席戶數：**{m_attendees} 戶** ｜ ✍️ 紀錄人：`{m_creator}`")

                if can_manage:
                    col_b1, col_b2 = st.columns([1, 1])
                    with col_b1:
                        if st.session_state.edit_meeting_id == m_id:
                            if st.button("❌ 取消編輯", key=f"cancel_m_{m_id}"):
                                st.session_state.edit_meeting_id = None
                                st.rerun()
                        else:
                            if st.button("✏️ 編輯更新", key=f"edit_btn_m_{m_id}"):
                                st.session_state.edit_meeting_id = m_id
                                st.rerun()
                    with col_b2:
                        if is_admin:
                            if st.button("🗑️ 刪除此筆紀錄", key=f"del_min_{m_id}"):
                                supabase.table("meeting_minutes").delete().eq("id", m_id).execute()
                                st.warning(f"已刪除會議紀錄：{m_title}")
                                st.rerun()

                if st.session_state.edit_meeting_id == m_id:
                    st.markdown("---")
                    st.info(f"✏️ 正在修改會議紀錄：**{m_title}**")
                    with st.form(f"update_meeting_form_{m_id}"):
                        up_title = st.text_input("會議標題", value=m_title)
                        col_u1, col_u2 = st.columns(2)
                        with col_u1:
                            try:
                                default_d = datetime.strptime(str(m_date), "%Y-%m-%d").date()
                            except:
                                default_d = date.today()
                            up_date = st.date_input("會議日期", value=default_d)
                        with col_u2:
                            up_attendees = st.number_input("出席戶數/人數", min_value=0, value=int(m_attendees), step=1)

                        up_content = st.text_area("會議紀錄內容 (支援 Markdown)", value=m_content, height=200)

                        submit_update_m = st.form_submit_button("💾 儲存修改")
                        if submit_update_m:
                            payload_up = {
                                "meeting_date": str(up_date),
                                "title": up_title.strip(),
                                "content": up_content.strip(),
                                "attendees_count": int(up_attendees),
                            }
                            supabase.table("meeting_minutes").update(payload_up).eq("id", m_id).execute()
                            st.session_state.edit_meeting_id = None
                            st.success("✅ 會議紀錄更新成功！")
                            st.rerun()
                else:
                    st.markdown("---")
                    st.markdown(m_content)
    else:
        st.info("目前尚無任何社區大會會議紀錄。")

# ==========================================
# 頁籤二：社區重要記事與活動歷程
# ==========================================
with tab_events:
    st.subheader("📅 社區大小事與重要活動歷程紀錄")

    # 新增記事表單
    if can_manage:
        with st.expander("➕ 【點此展開】新增社區重要記事/活動"):
            with st.form("add_event_form"):
                event_title = st.text_input(
                    "記事/活動標題", placeholder="例如：收取2026年度公共費用"
                )
                
                st.markdown("---")
                st.markdown("⏱️ **起訖時間設定**")
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.markdown("**開始時間**")
                    start_d = st.date_input("開始日期", value=date.today(), key="start_d")
                    start_t = st.time_input("開始時間", value=time(9, 0), key="start_t")
                with col_s2:
                    st.markdown("**結束時間**")
                    end_d = st.date_input("結束日期", value=date.today(), key="end_d")
                    end_t = st.time_input("結束時間", value=time(18, 0), key="end_t")

                st.markdown("---")
                event_category = st.selectbox(
                    "類別", ["一般記事", "財務收費", "委員決議", "修繕維護", "交接事項"]
                )

                event_desc = st.text_area(
                    "記事詳細說明",
                    height=150,
                    placeholder="請輸入該事件的詳細執行內容或結果...",
                )

                submit_event = st.form_submit_button("💾 確認並儲存社區記事")

                if submit_event:
                    if not event_title.strip() or not event_desc.strip():
                        st.error("❌ 記事標題與說明不得為空！")
                    else:
                        start_datetime = datetime.combine(start_d, start_t)
                        end_datetime = datetime.combine(end_d, end_t)

                        payload_e = {
                            "start_time": str(start_datetime),
                            "end_time": str(end_datetime),
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

        st.markdown("---")

        if "edit_event_id" not in st.session_state:
            st.session_state.edit_event_id = None

        for e in filtered_events:
            e_id = e.get("id")
            e_title = e.get("title")
            e_start = str(e.get("start_time", "")).replace("T", " ")
            e_end = str(e.get("end_time", "")).replace("T", " ") if e.get("end_time") else ""
            e_cat = e.get("category", "一般記事")
            e_desc = e.get("description", "")
            e_creator = e.get("creator_unit", "")

            # 組合日期時間顯示格式（無 T 字樣）
            time_display = e_start
            if e_end:
                time_display = f"{e_start} ～ {e_end}"

            # 整張卡片採用 st.expander 收合，並將期間字體放大且同行顯示
            with st.expander(f"🔹 【{e_cat}】 {e_title}"):
                st.markdown(
                    f"<p style='font-size: 16px; font-weight: bold; margin-bottom: 5px;'>⏱️ 期間：{time_display}</p>"
                    f"<p style='font-size: 14px; color: gray;'>✍️ 紀錄人（戶號）：<b>{e_creator}</b></p>",
                    unsafe_allow_html=True
                )
                st.markdown("---")

                if can_manage:
                    col_eb1, col_eb2 = st.columns([1, 1])
                    with col_eb1:
                        if st.session_state.edit_event_id == e_id:
                            if st.button("❌ 取消編輯", key=f"cancel_e_{e_id}"):
                                st.session_state.edit_event_id = None
                                st.rerun()
                        else:
                            if st.button("✏️ 編輯更新", key=f"edit_btn_e_{e_id}"):
                                st.session_state.edit_event_id = e_id
                                st.rerun()
                    with col_eb2:
                        if is_admin:
                            if st.button("🗑️ 刪除此筆記事", key=f"del_ev_{e_id}"):
                                supabase.table("community_events").delete().eq("id", e_id).execute()
                                st.warning(f"已刪除記事：{e_title}")
                                st.rerun()

                if st.session_state.edit_event_id == e_id:
                    st.markdown("---")
                    st.info(f"✏️ 正在修改記事：**{e_title}**")
                    with st.form(f"update_event_form_{e_id}"):
                        up_e_title = st.text_input("記事/活動標題", value=e_title)
                        
                        try:
                            dt_start = datetime.strptime(str(e_start), "%Y-%m-%d %H:%M:%S")
                        except:
                            dt_start = datetime.now()

                        dt_end = None
                        if e_end:
                            try:
                                dt_end = datetime.strptime(str(e_end), "%Y-%m-%d %H:%M:%S")
                            except:
                                pass

                        col_us1, col_us2 = st.columns(2)
                        with col_us1:
                            up_start_d = st.date_input("開始日期", value=dt_start.date(), key=f"up_sd_{e_id}")
                            up_start_t = st.time_input("開始時間", value=dt_start.time(), key=f"up_st_{e_id}")
                        with col_us2:
                            up_end_d = st.date_input("結束日期", value=dt_end.date() if dt_end else date.today(), key=f"up_ed_{e_id}")
                            up_end_t = st.time_input("結束時間", value=dt_end.time() if dt_end else time(18, 0), key=f"up_et_{e_id}")

                        up_category = st.selectbox(
                            "類別", ["一般記事", "財務收費", "委員決議", "修繕維護", "交接事項"],
                            index=["一般記事", "財務收費", "委員決議", "修繕維護", "交接事項"].index(e_cat) if e_cat in ["一般記事", "財務收費", "委員決議", "修繕維護", "交接事項"] else 0
                        )

                        up_desc = st.text_area("記事詳細說明", value=e_desc, height=150)

                        submit_update_e = st.form_submit_button("💾 儲存修改")
                        if submit_update_e:
                            up_start_dt = datetime.combine(up_start_d, up_start_t)
                            up_end_dt = datetime.combine(up_end_d, up_end_t)

                            payload_up_e = {
                                "start_time": str(up_start_dt),
                                "end_time": str(up_end_dt),
                                "title": up_e_title.strip(),
                                "category": up_category,
                                "description": up_desc.strip(),
                            }
                            supabase.table("community_events").update(payload_up_e).eq("id", e_id).execute()
                            st.session_state.edit_event_id = None
                            st.success("✅ 社區記事更新成功！")
                            st.rerun()
                else:
                    st.markdown("---")
                    st.write(e_desc)
    else:
        st.info("目前尚無任何社區重要記事記錄。")
