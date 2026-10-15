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

# 注入 CSS 讓表格與區塊置中顯示，並增加外觀質感
st.markdown("""
    <style>
    /* 將表格容器置中 */
    .centered-table {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    /* 調整表格標題與文字居中對齊感 */
    h3, h1 {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📜歷屆委員服務統計與名單")
st.write(
    "在這裡您可以查詢各戶歷年來擔任委員的**總服務次數與職稱統計**，以及詳細的歷史任期紀錄。"
)
st.markdown("---")

all_committees = supabase.table("committees").select("*").execute().data

if all_committees:
  # 1. 計算統計次數
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

  # 確保 主任委員、財務委員、監察委員 欄位都存在
  for r in ["主任委員", "財務委員", "監察委員"]:
    if r not in pivot_table.columns:
      pivot_table[r] = 0

  # 計算總服務次數
  pivot_table["總服務次數"] = (
      pivot_table["主任委員"]
      + pivot_table["財務委員"]
      + pivot_table["監察委員"]
  )


  # 定義自訂排序函式：將戶號如 "608-23" 拆解為 (608, 23) 以進行正確的數字遞增排序
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


  # 套用自訂排序到 DataFrame 中
  pivot_table["sort_key"] = pivot_table["unit_code"].apply(sort_unit_key)
  pivot_table = pivot_table.sort_values(by="sort_key").drop(
      columns=["sort_key"]
  )
  pivot_table = pivot_table.reset_index(drop=True)

  # 重新排序與命名欄位
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
  
  # 使用欄位排版讓表格居中顯示（左右留白，中間放表格）
  col_l, col_m, col_r = st.columns([0.5, 9, 0.5])
  with col_m:
      st.dataframe(pivot_table, use_container_width=True)

  st.markdown("---")

  # 2. 歷屆詳細清單 (使用 expander，預設關閉 expanded=False)
  with st.expander("🔍 點擊展開：查看歷屆詳細任期與名單清單", expanded=False):
    table_data = []
    for c in all_committees:
      table_data.append({
          "任期/年份": c["year"],
          "職稱": c["role"],
          "戶號": c["unit_code"],
          "備註": "現任委員" if c.get("is_current") else "歷史紀錄",
      })
    st.dataframe(table_data, use_container_width=True)
else:
  st.info("目前尚無委員資料。")
