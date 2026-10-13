import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# =========================================================
# KONFIGURASI
# =========================================================
st.set_page_config(
    page_title="Dashboard Analisis Siswa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 750;
        margin-bottom: 0.15rem;
    }
    .subtitle {
        color: #64748b;
        margin-bottom: 1.2rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 14px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).parent / "latihan1.csv"

# =========================================================
# FUNGSI DATA
# =========================================================
@st.cache_data
def read_csv_file(file_path):
    return pd.read_csv(file_path)

def clean_numeric(series):
    return pd.to_numeric(series, errors="coerce")

def metric_mean(dataframe, column):
    if column not in dataframe.columns:
        return None
    values = clean_numeric(dataframe[column]).dropna()
    return float(values.mean()) if not values.empty else None

def percent(condition):
    condition = condition.dropna()
    return float(condition.mean() * 100) if not condition.empty else None

def show_metric(label, value, suffix=""):
    if value is None or pd.isna(value):
        st.metric(label, "Tidak tersedia")
    else:
        st.metric(label, f"{value:,.2f}{suffix}")

# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="main-title">📊 Dashboard Analisis Data Siswa</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Analisis nilai ujian, kehadiran, kebiasaan belajar, '
    'tidur, penggunaan layar, dan kepuasan siswa.</div>',
    unsafe_allow_html=True
)

# =========================================================
# MEMUAT DATA
# =========================================================
if DATA_FILE.exists():
    try:
        df = read_csv_file(str(DATA_FILE))
    except Exception as error:
        st.error(f"File CSV gagal dibaca: {error}")
        st.stop()
else:
    st.warning(f"File data tidak ditemukan: {DATA_FILE}")
    uploaded = st.file_uploader("Unggah file latihan1.csv", type=["csv"])
    if uploaded is None:
        st.info(
            "Simpan file latihan1.csv di folder yang sama dengan app.py, "
            "atau unggah file CSV menggunakan tombol di atas."
        )
        st.stop()
    try:
        df = pd.read_csv(uploaded)
    except Exception as error:
        st.error(f"File CSV gagal dibaca: {error}")
        st.stop()

if df.empty:
    st.error("File CSV tidak memiliki baris data.")
    st.stop()

# Sidebar
st.sidebar.title("⚙️ Pengaturan Dashboard")
st.sidebar.write(f"**Jumlah baris:** {len(df):,}")
st.sidebar.write(f"**Jumlah kolom:** {len(df.columns):,}")

search_text = st.sidebar.text_input("Cari data (opsional)", "")
if search_text.strip():
    mask = df.astype(str).apply(
        lambda column: column.str.contains(search_text, case=False, na=False)
    ).any(axis=1)
    view_df = df.loc[mask]
else:
    view_df = df.copy()

numeric = df.select_dtypes(include=np.number).drop(
    columns=["Student_ID"], errors="ignore"
)

# =========================================================
# RINGKASAN
# =========================================================
st.header("Ringkasan Dataset")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Jumlah Siswa / Baris", f"{len(df):,}")
m2.metric("Jumlah Variabel", f"{len(df.columns):,}")
m3.metric("Variabel Numerik", f"{len(numeric.columns):,}")
m4.metric("Sel Kosong", f"{int(df.isna().sum().sum()):,}")

with st.expander("Lihat informasi kolom"):
    info_df = pd.DataFrame({
        "Nama Kolom": df.columns,
        "Tipe Data": [str(dtype) for dtype in df.dtypes],
        "Data Terisi": [int(df[col].notna().sum()) for col in df.columns],
        "Data Kosong": [int(df[col].isna().sum()) for col in df.columns],
        "Nilai Unik": [int(df[col].nunique(dropna=True)) for col in df.columns],
    })
    st.dataframe(info_df, hide_index=True, use_container_width=True)

st.divider()

# =========================================================
# INDIKATOR UTAMA
# =========================================================
st.header("Indikator Utama")
indicator_specs = [
    ("Exam_Score", "Rata-rata Nilai Ujian"),
    ("Attendance", "Rata-rata Kehadiran"),
    ("Study_Hours", "Rata-rata Jam Belajar"),
    ("Screen_Hours", "Rata-rata Jam Layar"),
    ("Sleep_Hours", "Rata-rata Jam Tidur"),
    ("Satisfaction", "Rata-rata Kepuasan"),
]
available_indicators = [
    (col, label) for col, label in indicator_specs if col in df.columns
]

if available_indicators:
    for start in range(0, len(available_indicators), 3):
        cols = st.columns(3)
        for cell, (column, label) in zip(
            cols, available_indicators[start:start + 3]
        ):
            with cell:
                show_metric(label, metric_mean(df, column))
else:
    st.info(
        "Kolom indikator standar tidak ditemukan. Periksa nama kolom CSV "
        "pada bagian Pratinjau Data."
    )

# =========================================================
# STATISTIK DESKRIPTIF
# =========================================================
st.header("Statistik Deskriptif")
if not numeric.empty:
    stats = numeric.agg(["count", "mean", "median", "std", "min", "max"]).T
    stats.columns = [
        "Jumlah Data", "Rata-rata", "Median",
        "Standar Deviasi", "Minimum", "Maksimum"
    ]
    st.dataframe(stats.round(3), use_container_width=True)
    st.download_button(
        "📥 Unduh Statistik Deskriptif",
        data=stats.round(3).to_csv().encode("utf-8"),
        file_name="statistik_deskriptif.csv",
        mime="text/csv",
    )
else:
    st.info("Tidak ada kolom numerik untuk dihitung statistiknya.")

# =========================================================
# DISTRIBUSI GENDER
# =========================================================
st.header("Distribusi Gender")
if "Gender" in df.columns:
    gender_counts = df["Gender"].fillna("Tidak diketahui").value_counts()
    left, right = st.columns([1, 2])
    with left:
        st.dataframe(
            gender_counts.rename_axis("Gender").reset_index(name="Jumlah"),
            hide_index=True,
            use_container_width=True,
        )
    with right:
        st.bar_chart(gender_counts)
else:
    st.info("Kolom Gender tidak ditemukan di dataset.")

# =========================================================
# DISTRIBUSI NILAI UJIAN
# =========================================================
st.header("Distribusi Nilai Ujian")
if "Exam_Score" in df.columns:
    scores = clean_numeric(df["Exam_Score"]).dropna()
    if not scores.empty:
        bins = [0, 50, 60, 70, 80, 90, 101]
        labels = ["<50", "50–59", "60–69", "70–79", "80–89", "90–100"]
        in_range = scores[(scores >= 0) & (scores <= 100)]
        score_dist = pd.cut(
            in_range, bins=bins, labels=labels, right=False
        ).value_counts().reindex(labels, fill_value=0)
        st.bar_chart(score_dist)
        c1, c2, c3 = st.columns(3)
        c1.metric("Nilai Tertinggi", f"{scores.max():.2f}")
        c2.metric("Nilai Terendah", f"{scores.min():.2f}")
        c3.metric("Nilai ≥ 80", f"{(scores >= 80).mean() * 100:.1f}%")
        if len(in_range) != len(scores):
            st.caption("Sebagian nilai berada di luar rentang 0–100 dan tidak masuk grafik distribusi.")
    else:
        st.info("Kolom Exam_Score tidak memiliki nilai numerik yang valid.")
else:
    st.info("Kolom Exam_Score tidak ditemukan.")

# =========================================================
# KORELASI
# =========================================================
st.header("Korelasi Antarvariabel")
if len(numeric.columns) >= 2:
    corr = numeric.corr().round(3)
    st.dataframe(corr, use_container_width=True)

    selected_corr = st.selectbox(
        "Pilih variabel untuk melihat korelasinya",
        options=list(corr.columns),
    )
    related = corr[selected_corr].drop(labels=[selected_corr]).dropna()
    if not related.empty:
        related = related.sort_values(ascending=False)
        st.subheader(f"Korelasi dengan {selected_corr}")
        st.bar_chart(related)
    st.caption(
        "Korelasi berkisar dari -1 hingga +1. Korelasi menunjukkan hubungan "
        "statistik dan tidak dengan sendirinya membuktikan sebab-akibat."
    )
else:
    st.info("Diperlukan minimal dua kolom numerik untuk menghitung korelasi.")

# =========================================================
# INDIKATOR KEPUTUSAN
# =========================================================
st.header("Indikator Keputusan")
decision_specs = [
    ("Exam_Score", "Nilai ujian ≥ 80", lambda values: values >= 80),
    ("Exam_Score", "Nilai ujian < 60", lambda values: values < 60),
    ("Attendance", "Kehadiran ≥ 85", lambda values: values >= 85),
    ("Attendance", "Kehadiran < 75", lambda values: values < 75),
]
decision_rows = []
for column, label, condition in decision_specs:
    if column in df.columns:
        values = clean_numeric(df[column]).dropna()
        if not values.empty:
            selected = condition(values)
            decision_rows.append({
                "Indikator": label,
                "Jumlah Siswa": int(selected.sum()),
                "Persentase": f"{selected.mean() * 100:.1f}%",
            })

if decision_rows:
    st.dataframe(
        pd.DataFrame(decision_rows),
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("Indikator keputusan membutuhkan kolom Exam_Score dan/atau Attendance.")

# =========================================================
# GRAFIK VARIABEL NUMERIK PILIHAN
# =========================================================
st.header("Eksplorasi Variabel")
if len(numeric.columns) > 0:
    selected_columns = st.multiselect(
        "Pilih variabel numerik untuk dibandingkan",
        options=list(numeric.columns),
        default=list(numeric.columns[:min(3, len(numeric.columns))]),
    )
    if selected_columns:
        st.line_chart(numeric[selected_columns])
    else:
        st.info("Pilih setidaknya satu variabel untuk menampilkan grafik.")
else:
    st.info("Tidak ada variabel numerik untuk dibuat grafik.")

# =========================================================
# PRATINJAU DAN FILTER DATA
# =========================================================
st.header("Pratinjau Data Siswa")
st.caption(f"Menampilkan {len(view_df):,} baris yang cocok dengan pencarian.")
st.dataframe(view_df.head(8), hide_index=True, use_container_width=True)

with st.expander("Lihat seluruh data yang cocok"):
    st.dataframe(view_df, hide_index=True, use_container_width=True)

st.download_button(
    label="📥 Unduh Data CSV",
    data=view_df.to_csv(index=False).encode("utf-8"),
    file_name="data_siswa.csv",
    mime="text/csv",
)

st.caption("Dashboard Analisis Data Siswa • Dibuat dengan Streamlit")
