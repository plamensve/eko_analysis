import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# -------------------------
# STYLE (BLUE KPI)
# -------------------------
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #0f172a;
    border: 1px solid #1e3a8a;
    padding: 15px;
    border-radius: 10px;
}
div[data-testid="metric-container"] label {
    color: #60a5fa;
}
div[data-testid="metric-container"] div {
    color: #3b82f6;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# LOAD DATA
# -------------------------
df = pd.read_excel("combined.xlsx")

# -------------------------
# CLEAN
# -------------------------
df.columns = df.columns.str.strip()
df["Дата"] = pd.to_datetime(df["Дата"])
df["Име на артикул"] = df["Име на артикул"].str.strip().str.upper()

# -------------------------
# SAFE COLUMN MAPPING
# -------------------------
def get_col(possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() == col.lower():
                return col
    return None

gta_sum_col = get_col(["Сума по GTA цена"])
eko_sum_col = get_col(["Сума по Еко цена", "Сума по ЕКО цена"])
gta_price_col = get_col(["GTA цена"])
eko_price_col = get_col(["Еко цена", "ЕКО цена"])

df.rename(columns={
    gta_sum_col: "gta_sum",
    eko_sum_col: "eko_sum",
    gta_price_col: "gta_price",
    eko_price_col: "eko_price"
}, inplace=True)

# -------------------------
# PRODUCTS
# -------------------------
valid_products = [
    "DIESEL EKONOMY",
    "95 EKONOMY UNLEADED",
    "DIESEL DOUBLE FILTERED",
    "EKO RACING 100"
]

df = df[df["Име на артикул"].isin(valid_products)]

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.header("Filters")

company = st.sidebar.selectbox("Company", df["company"].unique())

products = st.sidebar.multiselect(
    "Products",
    valid_products,
    default=valid_products
)

start_date = st.sidebar.date_input("Start date", df["Дата"].min())
end_date = st.sidebar.date_input("End date", df["Дата"].max())

# -------------------------
# FILTER
# -------------------------
filtered = df[
    (df["company"] == company) &
    (df["Име на артикул"].isin(products)) &
    (df["Дата"] >= pd.to_datetime(start_date)) &
    (df["Дата"] <= pd.to_datetime(end_date))
]

# -------------------------
# HEADER
# -------------------------
st.title(f"{company}")

# -------------------------
# KPI
# -------------------------
total_liters = filtered["Литри"].sum()
gta_total = filtered["gta_sum"].sum()
eko_total = filtered["eko_sum"].sum()
difference = gta_total - eko_total

avg_gta_price = filtered["gta_price"].mean()
avg_eko_price = filtered["eko_price"].mean()

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("Total Liters", round(float(total_liters), 3))
k2.metric("Avg GTA Price", round(avg_gta_price, 3))
k3.metric("Avg EKO Price", round(avg_eko_price, 3))
k4.metric("Total GTA (€)", round(gta_total, 2))
k5.metric("Total EKO (€)", round(eko_total, 2))
k6.metric("Difference (€)", round(difference, 2), delta=round(difference, 2))

# -------------------------
# PLOT FUNCTION (FIXED)
# -------------------------
def plot_chart(data, title):
    if data.empty:
        st.warning(f"No data for {title}")
        return

    grouped = data.groupby("Дата")["Литри"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(14, 8))  # по-голяма диаграма

    # фон
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    # основна линия
    ax.plot(
        grouped["Дата"],
        grouped["Литри"],
        linewidth=3,
        marker="o",
        markersize=6,
        color="#3b82f6",
        label="Daily"
    )

    # fill
    ax.fill_between(
        grouped["Дата"],
        grouped["Литри"],
        alpha=0.15,
        color="#3b82f6"
    )

    # average линия
    ax.axhline(
        grouped["Литри"].mean(),
        color="#ef4444",
        linestyle="--",
        linewidth=1.5,
        label="Average"
    )

    # grid
    ax.grid(True, linestyle="--", alpha=0.2)

    # по-добро управление на датите
    step = max(1, len(grouped) // 10)

    ax.set_xticks(grouped["Дата"][::step])
    ax.set_xticklabels(
        grouped["Дата"][::step].dt.strftime("%d %b"),  # по-четимо (01 Mar)
        rotation=90,
        ha="center",
        color="white"
    )

    # стил
    ax.set_title(title, color="white", fontsize=16, pad=15)
    ax.set_ylabel("Liters", color="white")

    ax.tick_params(axis='y', colors='white')

    # махаме рамки
    for spine in ax.spines.values():
        spine.set_visible(False)

    # легенда
    legend = ax.legend(facecolor="#1e293b", edgecolor="none")
    for text in legend.get_texts():
        text.set_color("white")

    plt.tight_layout()
    st.pyplot(fig)

# -------------------------
# GRID
# -------------------------
c1, c2 = st.columns(2)

with c1:
    plot_chart(
        filtered[filtered["Име на артикул"] == "DIESEL EKONOMY"],
        "DIESEL EKONOMY"
    )

    plot_chart(
        filtered[filtered["Име на артикул"] == "DIESEL DOUBLE FILTERED"],
        "DIESEL DOUBLE FILTERED"
    )

with c2:
    plot_chart(
        filtered[filtered["Име на артикул"] == "95 EKONOMY UNLEADED"],
        "95 EKONOMY UNLEADED"
    )

    plot_chart(
        filtered[filtered["Име на артикул"] == "EKO RACING 100"],
        "EKO RACING 100"
    )

# -------------------------
# TABLE
# -------------------------
st.subheader("Transactions")

st.dataframe(
    filtered.sort_values("Дата", ascending=False),
    use_container_width=True
)