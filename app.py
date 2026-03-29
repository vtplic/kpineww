import streamlit as st
import pandas as pd

st.set_page_config(page_title="KPI Dashboard", layout="wide")

st.markdown("<h1 style='text-align: center;'>📊 KPI Dashboard</h1>", unsafe_allow_html=True)

# ===== INIT KPI =====
default_kpi = {
    "phat": 96.74,
    "phat_dg": 92.99,
    "phat_l1": 98.0,
    "thu": 98.09,
    "thu_l1": 96.0
}

if "kpi" not in st.session_state:
    st.session_state.kpi = default_kpi.copy()

# ===== KPI INPUT =====
st.markdown("### 🎯 Ngưỡng KPI")

colk1, colk2, colk3, colk4, colk5 = st.columns(5)

kpi_phat = colk1.number_input("Phát thành công (%)", 0.0, 100.0, st.session_state.kpi["phat"])
kpi_phat_dg = colk2.number_input("Phát TC đúng giờ (%)", 0.0, 100.0, st.session_state.kpi["phat_dg"])
kpi_phat_l1 = colk3.number_input("Phát đúng giờ L1 (%)", 0.0, 100.0, st.session_state.kpi["phat_l1"])
kpi_thu = colk4.number_input("Thu TC đúng giờ (%)", 0.0, 100.0, st.session_state.kpi["thu"])
kpi_thu_l1 = colk5.number_input("Thu đúng giờ L1 (%)", 0.0, 100.0, st.session_state.kpi["thu_l1"])

if st.button("💾 Lưu KPI"):
    st.session_state.kpi = {
        "phat": kpi_phat,
        "phat_dg": kpi_phat_dg,
        "phat_l1": kpi_phat_l1,
        "thu": kpi_thu,
        "thu_l1": kpi_thu_l1
    }
    st.success("Đã lưu KPI!")

# ===== UPLOAD =====
col1, col2 = st.columns(2)

with col1:
    files_phat = st.file_uploader("📦 Khâu phát", type=["xlsx"], accept_multiple_files=True)

with col2:
    files_thu = st.file_uploader("💰 Khâu thu", type=["xlsx"], accept_multiple_files=True)

# ===== LOAD =====
def load_phat(files):
    dfs = []
    for f in files:
        df = pd.read_excel(f, usecols="D,F,I,J", skiprows=1)
        df.columns = ["Tên Tuyến","Phát thành công","Phát TC đúng giờ","Phát đúng giờ lần 1"]
        df = df[df["Tên Tuyến"].notna()]
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def load_thu(files):
    dfs = []
    for f in files:
        df = pd.read_excel(f, usecols="D,I,J", skiprows=2)
        df.columns = ["Tên Tuyến","Thu TC đúng giờ","Thu đúng giờ lần 1"]
        df = df[df["Tên Tuyến"].notna()]
        df = df[df["Tên Tuyến"] != "TỔNG"]
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# ===== PROCESS =====
if files_phat and files_thu:

    df_phat = load_phat(files_phat)
    df_thu = load_thu(files_thu)

    df = df_phat.merge(df_thu, on="Tên Tuyến", how="left")

    for col in df.columns:
        if col != "Tên Tuyến":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ===== KPI SCORE =====
    def calc_score(row):
        score = 0
        if pd.notna(row["Phát thành công"]) and row["Phát thành công"] >= st.session_state.kpi["phat"]:
            score += 1
        if pd.notna(row["Phát TC đúng giờ"]) and row["Phát TC đúng giờ"] >= st.session_state.kpi["phat_dg"]:
            score += 1
        if pd.notna(row["Phát đúng giờ lần 1"]) and row["Phát đúng giờ lần 1"] >= st.session_state.kpi["phat_l1"]:
            score += 1
        if pd.notna(row["Thu TC đúng giờ"]) and row["Thu TC đúng giờ"] >= st.session_state.kpi["thu"]:
            score += 1
        if pd.notna(row["Thu đúng giờ lần 1"]) and row["Thu đúng giờ lần 1"] >= st.session_state.kpi["thu_l1"]:
            score += 1
        return f"{score}/5 tiêu chí"

    df["Đạt KPI"] = df.apply(calc_score, axis=1)

    # ===== FORMAT % =====
    df_display = df.copy()
    for col in df.columns:
        if col not in ["Tên Tuyến", "Đạt KPI"]:
            df_display[col] = df_display[col].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

    # ===== FILTER =====
    routes = df["Tên Tuyến"].dropna().unique().tolist()
    if routes:
        selected_routes = st.multiselect("Chọn tuyến hiển thị", routes, default=routes)
        if selected_routes:
            df = df[df["Tên Tuyến"].isin(selected_routes)]
            df_display = df_display[df_display["Tên Tuyến"].isin(selected_routes)]

    # ===== HIGHLIGHT CELL =====
    def highlight_cell(val, threshold):
        try:
            val = float(str(val).replace("%", ""))
            return "background-color: #ffcccc" if val < threshold else ""
        except:
            return ""

    styled = df_display.style

    styled = styled.applymap(lambda v: highlight_cell(v, st.session_state.kpi["phat"]), subset=["Phát thành công"])
    styled = styled.applymap(lambda v: highlight_cell(v, st.session_state.kpi["phat_dg"]), subset=["Phát TC đúng giờ"])
    styled = styled.applymap(lambda v: highlight_cell(v, st.session_state.kpi["phat_l1"]), subset=["Phát đúng giờ lần 1"])
    styled = styled.applymap(lambda v: highlight_cell(v, st.session_state.kpi["thu"]), subset=["Thu TC đúng giờ"])
    styled = styled.applymap(lambda v: highlight_cell(v, st.session_state.kpi["thu_l1"]), subset=["Thu đúng giờ lần 1"])

    st.markdown("## 📊 Kết quả")
    st.dataframe(styled)

else:
    st.warning("⚠️ Upload đủ 2 file để xem kết quả")
