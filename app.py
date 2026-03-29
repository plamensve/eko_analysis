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
# VALID PRODUCTS (FIXED)
# -------------------------
valid_products = [
    "DIESEL EKONOMY",
    "95 EKONOMY UNLEADED",
    "DIESEL DOUBLE FILTERED",
    "EKO RACING 100"
]

df = df[df["Име на артикул"].isin(valid_products)]

# -------------------------
# SIDEBAR FILTERS
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
# FILTER DATA
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
st.title("Fuel Analytics Dashboard")

# -------------------------
# KPI SECTION (FINAL)
# -------------------------
total_liters = filtered["Литри"].sum()

gta_total = filtered["gta_sum"].sum()
eko_total = filtered["eko_sum"].sum()

difference = gta_total - eko_total

avg_gta_price = filtered["gta_price"].mean()
avg_eko_price = filtered["eko_price"].mean()

# layout
k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("Total Liters", int(total_liters))
k2.metric("Avg GTA Price", round(avg_gta_price, 3))
k3.metric("Avg EKO Price", round(avg_eko_price, 3))

k4.metric("Total GTA (€)", round(gta_total, 2))
k5.metric("Total EKO (€)", round(eko_total, 2))

# цветна логика за разлика
k6.metric(
    "Difference (€)",
    round(difference, 2),
    delta=round(difference, 2)
)

# -------------------------
# SECOND ROW KPIs
# -------------------------
k6, k7 = st.columns(2)

k6.metric("Avg GTA Price", round(avg_gta_price, 3))
k7.metric("Avg EKO Price", round(avg_eko_price, 3))

# -------------------------
# PLOT FUNCTION
# -------------------------
def plot_chart(data, title):
    if data.empty:
        st.warning(f"No data for {title}")
        return

    fig, ax = plt.subplots(figsize=(6, 3))

    mean_value = data["Литри"].mean()

    ax.bar(data["Дата"], data["Литри"])
    ax.axhline(mean_value, color="red", linestyle="--")

    ax.set_title(title)
    ax.set_ylabel("Liters")
    ax.tick_params(axis='x', rotation=90)

    st.pyplot(fig)

# -------------------------
# GRID LAYOUT (2x2)
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