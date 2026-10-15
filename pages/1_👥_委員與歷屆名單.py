from datetime import datetime
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

st.markdown("""
    <style>
    .centered-table {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👥 委員名單與歷屆紀錄")
st.write("在這裡您可以查看本屆現任委員，或是切換至分頁查詢歷屆服務次數與詳細任期紀錄。")
st.markdown("---")

all_committees = supabase.table("committees").select("*").execute().data

if all_committees:
  tab1, tab2, tab3 = st.tabs([
      "👥 本屆現任委員",
      "📊 各戶服務次數統計總表",
      "📋 歷屆詳細任期清單",
  ])

  # ==========================================
  # 頁籤一：本屆現任委員 (透過當前年份 2026 自動比對)
  # ==========================================
  with tab1:
    st.subheader("🏢 吾映良品柒社區 - 現任委員名單 (2024-2026)")
    st.write("以下為本屆現任委員資訊：")

    current_year_str = str(datetime.now().year)  # 取得 2026

    # 篩選出任期年份包含當前年份的紀錄
    current_committee = []
    for c in all_committees:
      year_range = str(c.get("year", ""))
      if current_year_str in year_range:
        current_committee.append(c)

    # 自動備援防護名單
    if not current_committee:
      current_committee = [
          {"role": "主任委員", "name": "住戶 608-22", "unit_code": "608-22"},
          {"role": "監察委員", "name": "住戶 608-18", "unit_code": "608-18"},
          {"role": "財務委員", "name": "住戶 608-5", "unit_code": "608-5"},
      ]

    if current_committee:
      col1, col2, col3 = st.columns(3)
      roles_display = {"主任委員": col1, "財務委員": col2, "監察委員": col3}

      for item in current_committee:
        role = item.get("role")
        name = item.get("name", "住戶")
        unit = item.get("unit_code")

        target_col = roles_display.get(role, col1)
        with target_col:
          st.info(f"**{role}**\n\n👤 **{name}**\n\n🏠 戶號：`{unit}`")
    else:
      st.warning("目前資料庫中尚未設定現任委員。")

  # ==========================================
  # 頁籤二：各戶服務次數統計總表
  # ==========================================
  with tab2:
    st.subheader("📊 各戶委員服務次數統計總表")
    st.write("查詢各戶歷年來為社區服務的總次數與各職稱分布（依戶號遞增排序）：")

    df = pd.DataFrame(all_committees)

    pivot_table = (
        df.pivot_table(
            index="unit_code",
            columns="role",
            values="id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )

    for r in ["主任委員", "財務委員", "監察委員"]:
      if r not in pivot_table.columns:
        pivot_table[r] = 0

    pivot_table["總服務次數"] = (
        pivot_table["主任委員"]
        + pivot_table["財務委員"]
        + pivot_table["監察委員"]
    )


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


    pivot_table["sort_key"] = pivot_table["unit_code"].apply(sort_unit_key)
    pivot_table = pivot_table.sort_values(by="sort_key").drop(
        columns=["sort_key"]
    )
    pivot_table = pivot_table.reset_index(drop=True)

    cols_order = [
        "unit_code",
        "總服務次數",
        "主任委員",
        "財務委員",
        "監察委員",
    ]
    pivot_table = pivot_table[[c for c in cols_order if c in pivot_table.columns]]
    pivot_table.columns = [
        "戶號",
        "總服務次數",
        "擔任主委次數",
        "擔任財委次數",
        "擔任監委次數",
    ]

    col_l, col_m, col_r = st.columns([0.5, 9, 0.5])
    with col_m:
      st.dataframe(pivot_table, use_container_width=True)

  # ==========================================
  # 頁籤三：歷屆詳細任期清單
  # ==========================================
  with tab3:
    st.subheader("📋 歷屆詳細任期與名單查詢")

    all_units = sorted(
        list(set([str(c["unit_code"]) for c in all_committees])),
        key=sort_unit_key,
    )
    unit_options = ["全部顯示"] + all_units

    selected_unit_filter = st.selectbox("🔍 選擇或過濾特定戶號", unit_options)

    table_data = []
    for c in all_committees:
      unit_c = str(c["unit_code"])
      if selected_unit_filter != "全部顯示" and unit_c != selected_unit_filter:
        continue
      table_data.append({
          "任期/年份": c["year"],
          "職稱": c["role"],
          "戶號": unit_c,
      })

    if table_data:
      st.dataframe(table_data, use_container_width=True)
    else:
      st.info(f"查無符合戶號「{selected_unit_filter}」的歷史紀錄。")
else:
  st.info("目前尚無委員資料。")
