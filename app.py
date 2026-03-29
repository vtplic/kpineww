import streamlit as st
import pandas as pd

st.set_page_config(page_title="KPI Dashboard", layout="wide")

st.markdown("<h1 style='text-align: center;'>📊 KPI Dashboard</h1>", unsafe_allow_html=True)

# ===== INIT KPI =====
default_kpi = {
    "phat": 96.74,
    "phat_dg": 92.99,
    "phat_l1": 98.00,
    "thu": 98.09,
    "thu_l1": 96.00
}

if "kpi" not in st.session_state:
    st.session_state.kpi = default_kpi.copy()

# ===== KPI INPUT =====
st.markdown("### 🎯 Ngưỡng KPI")
cols = st.columns(5)

kpi_phat = cols[0].number_input("Phát thành công (%)", 0.0, 100.0, st.session_state.kpi["phat"])
kpi_phat_dg = cols[1].number_input("Phát TC đúng giờ (%)", 0.0, 100.0, st.session_state.kpi["phat_dg"])
kpi_phat_l1 = cols[2].number_input("Phát đúng giờ L1 (%)", 0.0, 100.0, st.session_state.kpi["phat_l1"])
kpi_thu = cols[3].number_input("Thu TC đúng giờ (%)", 0.0, 100.0, st.session_state.kpi["thu"])
kpi_thu_l1 = cols[4].number_input("Thu đúng giờ L1 (%)", 0.0, 100.0, st.session_state.kpi["thu_l1"])

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

if files_phat and files_thu:

    df = load_phat(files_phat).merge(load_thu(files_thu), on="Tên Tuyến", how="left")

    for col in df.columns:
        if col != "Tên Tuyến":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # filter
    routes = df["Tên Tuyến"].dropna().unique().tolist()
    selected_routes = st.multiselect("📍 Chọn tuyến hiển thị", routes, default=routes)
    if selected_routes:
        df = df[df["Tên Tuyến"].isin(selected_routes)]

    # score
    def score(row):
        s = 0
        k = st.session_state.kpi
        if row["Phát thành công"] >= k["phat"]: s+=1
        if row["Phát TC đúng giờ"] >= k["phat_dg"]: s+=1
        if row["Phát đúng giờ lần 1"] >= k["phat_l1"]: s+=1
        if row["Thu TC đúng giờ"] >= k["thu"]: s+=1
        if row["Thu đúng giờ lần 1"] >= k["thu_l1"]: s+=1
        return f"{s}/5 tiêu chí"

    df["Đạt KPI"] = df.apply(score, axis=1)

    # format
    df_display = df.copy()
    for col in df.columns:
        if col not in ["Tên Tuyến","Đạt KPI"]:
            df_display[col] = df_display[col].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

    k = st.session_state.kpi

    df_display = df_display.rename(columns={
        "Phát thành công": f"Phát thành công (≥ {k['phat']}%)",
        "Phát TC đúng giờ": f"Phát TC đúng giờ (≥ {k['phat_dg']}%)",
        "Phát đúng giờ lần 1": f"Phát đúng giờ L1 (≥ {k['phat_l1']}%)",
        "Thu TC đúng giờ": f"Thu TC đúng giờ (≥ {k['thu']}%)",
        "Thu đúng giờ lần 1": f"Thu đúng giờ L1 (≥ {k['thu_l1']}%)"
    })

    # ===== STYLE HTML =====
    def color(val, threshold):
        try:
            v = float(str(val).replace("%",""))
            return "#c6efce" if v >= threshold else "#ffc7ce"
        except:
            return ""

    html = "<table style='width:100%; border-collapse:collapse; font-size:16px; font-weight:900;'>"

    # header
    html += "<tr>"
    for col in df_display.columns:
        html += f"<th style='background:#d9e1f2; padding:6px; text-align:center;'>{col}</th>"
    html += "</tr>"

    # rows
    for _, row in df_display.iterrows():
        html += "<tr>"
        for col in df_display.columns:
            val = row[col]
            style = "padding:4px; text-align:center;"

            if "Phát thành công" in col:
                style += f"background:{color(val, k['phat'])};"
            elif "Phát TC đúng giờ" in col:
                style += f"background:{color(val, k['phat_dg'])};"
            elif "Phát đúng giờ L1" in col:
                style += f"background:{color(val, k['phat_l1'])};"
            elif "Thu TC đúng giờ" in col:
                style += f"background:{color(val, k['thu'])};"
            elif "Thu đúng giờ L1" in col:
                style += f"background:{color(val, k['thu_l1'])};"

            html += f"<td style='{style}'>{val}</td>"
        html += "</tr>"

    html += "</table>"

    st.markdown("## 📊 Kết quả")
    st.markdown(html, unsafe_allow_html=True)

else:
    st.warning("⚠️ Upload đủ 2 file để xem kết quả")
