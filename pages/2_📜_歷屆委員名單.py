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

st.title("📜 吾映良品柒 - 歷屆委員服務統計與名單")
st.write(
    "在這裡您可以透過分頁查詢各戶的**服務次數統計總表**，或是依特定戶號快速過濾檢視**詳細的歷史任期紀錄**。"
)
st.markdown("---")

all_committees = supabase.table("committees").select("*").execute().data

if all_committees:
  # 建立 Tab 分頁介面
  tab1, tab2 = st.tabs(["📊 各戶服務次數統計總表", "📋 歷屆詳細任期清單"])

  # ------------------------------------------
  # 頁籤一：統計總表
  # ------------------------------------------
  with tab1:
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

    st.subheader("📊 各戶委員服務次數統計總表")
    st.write("查詢各戶歷年來為社區服務的總次數與各職稱分布（依戶號遞增排序）：")

    col_l, col_m, col_r = st.columns([0.5, 9, 0.5])
    with col_m:
      st.dataframe(pivot_table, use_container_width=True)

  # ------------------------------------------
  # 頁籤二：詳細任期清單 + 戶號篩選選單 (已移除備註欄位)
  # ------------------------------------------
  with tab2:
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
