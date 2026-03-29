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
df = pd.read_csv("combined.csv", dtype={"Номер на карта": str})

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

products = []

st.sidebar.markdown("### Products")

for p in valid_products:
    if st.sidebar.checkbox(p, value=True):
        products.append(p)

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

# -------------------------
# PRODUCT COMPARISON
# -------------------------
st.subheader("Product Consumption by Company")

st.markdown("### Select product")

# init
if "selected_product" not in st.session_state:
    st.session_state.selected_product = valid_products[0]


# callback
def select_product(p):
    st.session_state.selected_product = p


# layout
cols = st.columns(len(valid_products))

for i, p in enumerate(valid_products):
    is_active = st.session_state.selected_product == p

    cols[i].button(
        p,
        key=f"btn_{p}",
        on_click=select_product,
        args=(p,),
        type="primary" if is_active else "secondary"
    )

selected_product = st.session_state.selected_product

# филтър + агрегация
product_stats = df[
    (df["Име на артикул"] == selected_product) &
    (df["Дата"] >= pd.to_datetime(start_date)) &
    (df["Дата"] <= pd.to_datetime(end_date))
    ].groupby("company")["Литри"].sum().reset_index()

# сортиране
product_stats = product_stats.sort_values(
    "Литри",
    ascending=False
)

# KPI лидер
if not product_stats.empty:
    top = product_stats.iloc[0]

    st.metric(
        f"Top consumer - {selected_product}",
        top["company"],
        f"{round(top['Литри'], 2)} L"
    )

# таблица
st.dataframe(product_stats, use_container_width=True)

# -------------------------
# BAR CHART (visual comparison)
# -------------------------
if not product_stats.empty:

    fig, ax = plt.subplots(figsize=(15, 10))

    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    product_stats = product_stats.sort_values(
        "Литри",
        ascending=False
    )

    bars = ax.barh(
        product_stats["company"],
        product_stats["Литри"],
        color="#3b82f6",
    )

    ax.invert_yaxis()

    # -------------------------
    # VALUE LABELS
    # -------------------------
    max_val = product_stats["Литри"].max()

    for i, v in enumerate(product_stats["Литри"]):
        ax.text(
            v + max_val * 0.01,
            i,
            f"{v:.2f}",
            va='center',
            ha='left',
            color='white',
            fontsize=10
        )

    # -------------------------
    # STYLE
    # -------------------------
    ax.set_title(
        selected_product,
        color="white",
        fontsize=16,
        y=1.05  # изнася заглавието нагоре
    )

    ax.set_xlabel("Liters", color="white")
    ax.set_ylabel("Company", color="white")

    ax.tick_params(axis='x', colors="white")
    ax.tick_params(axis='y', colors="white")

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(True, linestyle="--", alpha=0.2)

    st.pyplot(fig)


# -------------------------
# CARD MAP
# -------------------------
card_map = {
    "78970110027720035": "ДИМИТЪР НЕСТОРОВ",
    "78970110027720043": "ПЛАМЕН ДОБРЕВ",
    "78970110027720076": "СИМЕОН ХАДЖИЕВ",
    "78970110027720084": "ВЕСЕЛА НИКОЛОВА",
    "78970110027720092": "СТЕФАН ШИШКОВ",
    "78970110027720118": "ТЕОДОРА ПОПОВА",
    "78970110027720126": "ЕВТИМОВ",
    "78970110027720142": "ГЕОРГИ КАЛЧЕВ",
    "78970110027720159": "ГЕОРГИ КАЛЧЕВ - ПЛЕВЕН",
    "78970110027720217": "ЕНЕРДЖИ ПЛЮС",
    "78970110027720233": "БОЯН А. ПОПОВА",
    "78970110027720068": "А. ПОПОВА",
    "78970110027720027": "Б. ИВАНЧЕВ",
    "78970110027720241": "ИВАЙЛО ТОТЕВ",
    "78970110027720100": "ГЕОРГИ КАЛЧЕВ"
}

# -------------------------
# CREATE EMPLOYEE COLUMN (ВАЖНО)
# -------------------------
df["Номер на карта"] = (
    df["Номер на карта"]
    .astype(str)
    .str.strip()
    .str.replace(".0", "", regex=False)
)

employees = []

for card in df["Номер на карта"]:
    name = "UNKNOWN"
    for key in card_map:
        if card == key:
            name = card_map[key]
            break
    employees.append(name)

df["employee"] = employees

# -------------------------
# SECTION
# -------------------------
st.subheader("Employee Transactions")

# независим dataset (само GTA)
employee_df = df[
    (df["company"] == "ДЖИ ТИ ЕЙ ПЕТРОЛИУМ") &
    (df["Дата"] >= pd.to_datetime(start_date)) &
    (df["Дата"] <= pd.to_datetime(end_date))
]

# -------------------------
# FILTER ПО СЛУЖИТЕЛ (100% WORKING)
# -------------------------
st.markdown("### Select Employees")

employees_list = sorted(employee_df["employee"].unique())

# init
if "selected_employees" not in st.session_state:
    st.session_state.selected_employees = employees_list.copy()

# -------------------------
# BUTTONS (FIX)
# -------------------------
col1, col2 = st.columns(2)

if col1.button("Select All"):
    st.session_state.selected_employees = employees_list.copy()
    for emp in employees_list:
        st.session_state[f"emp_{emp}"] = True

if col2.button("Clear All"):
    st.session_state.selected_employees = []
    for emp in employees_list:
        st.session_state[f"emp_{emp}"] = False

# -------------------------
# CHECKBOX GRID
# -------------------------
num_cols = 4
cols = st.columns(num_cols)

new_selected = []

for i, emp in enumerate(employees_list):
    col = cols[i % num_cols]

    key = f"emp_{emp}"

    # важно – sync със state
    if key not in st.session_state:
        st.session_state[key] = emp in st.session_state.selected_employees

    val = col.checkbox(emp, key=key)

    if val:
        new_selected.append(emp)

# update
st.session_state.selected_employees = new_selected

# -------------------------
# APPLY FILTER
# -------------------------
if st.session_state.selected_employees:
    employee_df = employee_df[
        employee_df["employee"].isin(st.session_state.selected_employees)
    ]
else:
    employee_df = employee_df.iloc[0:0]

# -------------------------
# KPI
# -------------------------
total_liters = employee_df["Литри"].sum()
total_transactions = len(employee_df)

avg_price = employee_df["gta_price"].mean() if "gta_price" in employee_df else 0

k1, k2, k3 = st.columns(3)

k1.metric("Total Liters", round(total_liters, 2))
k2.metric("Transactions", total_transactions)
k3.metric("Avg Price", round(avg_price, 3))

# -------------------------
# TABLE
# -------------------------
st.dataframe(
    employee_df.sort_values("Дата", ascending=False),
    use_container_width=True
)
























