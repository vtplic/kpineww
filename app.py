import html

import pandas as pd
import streamlit as st

st.set_page_config(page_title="KPI Dashboard", layout="wide")

st.markdown(
    "<h1 style='text-align: center;'>📊 KPI Dashboard Bưu cục Liên Chiểu</h1>",
    unsafe_allow_html=True,
)

# ===== INIT KPI =====
default_kpi = {
    "phat": 96.82,
    "phat_dg": 98.3,
    "thu": 99,
}

if "kpi" not in st.session_state:
    st.session_state.kpi = default_kpi.copy()
else:
    # Giữ tương thích nếu session cũ vẫn còn key KPI L1.
    st.session_state.kpi = {
        key: st.session_state.kpi.get(key, value)
        for key, value in default_kpi.items()
    }

# ===== KPI INPUT =====
st.markdown("### 🎯 Ngưỡng KPI")
cols = st.columns(3)

kpi_phat = cols[0].number_input(
    "Phát thành công (%)",
    min_value=0.0,
    max_value=100.0,
    value=float(st.session_state.kpi["phat"]),
    step=0.01,
)
kpi_phat_dg = cols[1].number_input(
    "Phát TC đúng giờ (%)",
    min_value=0.0,
    max_value=100.0,
    value=float(st.session_state.kpi["phat_dg"]),
    step=0.01,
)
kpi_thu = cols[2].number_input(
    "Thu TC đúng giờ (%)",
    min_value=0.0,
    max_value=100.0,
    value=float(st.session_state.kpi["thu"]),
    step=0.01,
)

if st.button("💾 Lưu KPI"):
    st.session_state.kpi = {
        "phat": kpi_phat,
        "phat_dg": kpi_phat_dg,
        "thu": kpi_thu,
    }
    st.success("Đã lưu KPI!")

# ===== UPLOAD =====
col1, col2 = st.columns(2)
with col1:
    files_phat = st.file_uploader(
        "📦 Khâu phát (Baocaotonghopkhauphat)",
        type=["xlsx"],
        accept_multiple_files=True,
    )
with col2:
    files_thu = st.file_uploader(
        "💰 Khâu thu (Baocaotonghopkhauthu)",
        type=["xlsx"],
        accept_multiple_files=True,
    )


def clean_route(value):
    """Chuẩn hóa tên tuyến/nhân viên để ghép file phát/thu ổn định hơn."""
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def load_excel_files(files, *, usecols, skiprows, columns, source_label):
    dfs = []
    errors = []

    for f in files:
        try:
            df = pd.read_excel(f, usecols=usecols, skiprows=skiprows)
            df.columns = columns
            df["Tên Tuyến"] = df["Tên Tuyến"].map(clean_route)
            df = df[df["Tên Tuyến"] != ""]
            df = df[df["Tên Tuyến"].str.upper() != "TỔNG"]
            dfs.append(df)
        except Exception as exc:
            errors.append(f"{source_label} - {getattr(f, 'name', 'file')}: {exc}")

    if errors:
        st.error("Không đọc được một số file:\n" + "\n".join(f"- {err}" for err in errors))

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame(columns=columns)


def load_phat(files):
    return load_excel_files(
        files,
        usecols="D,F,I",
        skiprows=1,
        columns=["Tên Tuyến", "Phát thành công", "Phát TC đúng giờ"],
        source_label="Khâu phát",
    )


def load_thu(files):
    return load_excel_files(
        files,
        usecols="D,I",
        skiprows=2,
        columns=["Tên Tuyến", "Thu TC đúng giờ"],
        source_label="Khâu thu",
    )


def normalize_metrics(df):
    for col in df.columns:
        if col != "Tên Tuyến":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def group_by_route(df):
    """Gom các dòng trùng tuyến/nhân viên khi upload nhiều file.

    Nếu trùng, lấy trung bình các chỉ số để tránh nhân đôi dòng.
    """
    if df.empty:
        return df
    return df.groupby("Tên Tuyến", as_index=False).mean(numeric_only=True)


def add_score_columns(df):
    """Thêm số tiêu chí đạt và nhãn điểm KPI."""
    k = st.session_state.kpi
    result = df.copy()
    result["Số tiêu chí đạt"] = 0
    result["Số tiêu chí đạt"] += (result["Phát thành công"].notna() & (result["Phát thành công"] >= k["phat"])).astype(int)
    result["Số tiêu chí đạt"] += (result["Phát TC đúng giờ"].notna() & (result["Phát TC đúng giờ"] >= k["phat_dg"])).astype(int)
    result["Số tiêu chí đạt"] += (result["Thu TC đúng giờ"].notna() & (result["Thu TC đúng giờ"] >= k["thu"])).astype(int)
    result["Đạt KPI"] = result["Số tiêu chí đạt"].map(lambda x: f"{x}/3 tiêu chí")
    return result


def sort_by_score(df):
    """Xếp hạng từ cao đến thấp theo số tiêu chí đạt, rồi theo tên."""
    return df.sort_values(
        by=["Số tiêu chí đạt", "Tên Tuyến"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)


def make_display_df(df):
    k = st.session_state.kpi
    display = df.drop(columns=["Số tiêu chí đạt"], errors="ignore").copy()

    for col in display.columns:
        if col not in ["Tên Tuyến", "Đạt KPI"]:
            display[col] = display[col].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

    return display.rename(
        columns={
            "Phát thành công": f"Phát thành công (≥ {k['phat']:.2f}%)",
            "Phát TC đúng giờ": f"Phát TC đúng giờ (≥ {k['phat_dg']:.2f}%)",
            "Thu TC đúng giờ": f"Thu TC đúng giờ (≥ {k['thu']:.2f}%)",
        }
    )


def color(val, threshold):
    try:
        v = float(str(val).replace("%", ""))
        return "#c6efce" if v >= threshold else "#ffc7ce"
    except Exception:
        return ""


def render_kpi_table(df, *, title):
    """Render bảng KPI có tô màu đạt/chưa đạt."""
    k = st.session_state.kpi
    df_display = make_display_df(df)

    html_table = "<table style='width:100%; border-collapse:collapse; font-size:16px; font-weight:900;'>"

    # header
    html_table += "<tr>"
    for col in df_display.columns:
        html_table += (
            "<th style='background:#d9e1f2; padding:6px; text-align:center; "
            "border:1px solid #999;'>"
            f"{html.escape(str(col))}</th>"
        )
    html_table += "</tr>"

    # rows
    for _, row in df_display.iterrows():
        html_table += "<tr>"
        for col in df_display.columns:
            val = row[col]
            style = "padding:4px; text-align:center; border:1px solid #999;"

            if "Phát thành công" in col:
                style += f"background:{color(val, k['phat'])};"
            elif "Phát TC đúng giờ" in col:
                style += f"background:{color(val, k['phat_dg'])};"
            elif "Thu TC đúng giờ" in col:
                style += f"background:{color(val, k['thu'])};"

            html_table += f"<td style='{style}'>{html.escape(str(val))}</td>"
        html_table += "</tr>"

    html_table += "</table>"

    st.markdown(title)
    st.markdown(html_table, unsafe_allow_html=True)


if files_phat and files_thu:
    df_phat = group_by_route(normalize_metrics(load_phat(files_phat)))
    df_thu = group_by_route(normalize_metrics(load_thu(files_thu)))

    if df_phat.empty or df_thu.empty:
        st.warning("⚠️ Chưa có dữ liệu hợp lệ trong file đã upload.")
        st.stop()

    df = df_phat.merge(df_thu, on="Tên Tuyến", how="left")

    missing_thu = df["Thu TC đúng giờ"].isna().sum()
    if missing_thu:
        st.warning(f"⚠️ Có {missing_thu} tuyến bên file phát chưa khớp dữ liệu khâu thu.")

    # Tính điểm trên danh sách gốc trước, để bảng riêng không bị mất lựa chọn
    # khi anh bỏ/xóa nhân viên khỏi bảng chung.
    df_all = sort_by_score(add_score_columns(df))
    routes = df_all["Tên Tuyến"].tolist()

    # ===== FILTER =====
    selected_routes = st.multiselect(
        "📍 Chọn tuyến/nhân viên hiển thị ở bảng chung",
        routes,
        default=routes,
        help="Bỏ chọn ở đây chỉ ẩn khỏi bảng chung, không làm mất người đã chọn trong bảng riêng.",
    )

    # ===== CUSTOM TABLE =====
    st.markdown("### 🧲 Tạo bảng kết quả riêng")
    custom_routes = st.multiselect(
        "Kéo/chọn tuyến hoặc nhân viên muốn đưa vào bảng riêng",
        options=routes,
        default=[],
        key="custom_routes",
        help="Bấm vào ô rồi chọn tên trong danh sách. Bảng riêng độc lập với bộ lọc bảng chung.",
    )

    if custom_routes:
        df_custom = df_all[df_all["Tên Tuyến"].isin(custom_routes)]
        render_kpi_table(df_custom, title="## ⭐ Bảng kết quả riêng")

    # Bảng chung: theo bộ lọc bảng chung, đồng thời tự loại người đã đưa vào bảng riêng.
    df_main = df_all[df_all["Tên Tuyến"].isin(selected_routes)]
    if custom_routes:
        df_main = df_main[~df_main["Tên Tuyến"].isin(custom_routes)]

    # ===== MAIN TABLE =====
    render_kpi_table(df_main, title="## 📊 Kết quả tổng — xếp hạng từ cao đến thấp")

else:
    st.warning("⚠️ Upload đủ 2 nhóm file để xem kết quả")
