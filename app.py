import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# -------------------------
# STYLE
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

/* SELECTBOX + DATE POINTER */
div[data-baseweb="select"],
div[data-baseweb="select"] *,
input[type="date"] {
    cursor: pointer !important;
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
df["Литри"] = pd.to_numeric(df["Литри"], errors="coerce")

# -------------------------
# SAFE COLUMN MAPPING
# -------------------------
def get_col(possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() == col.lower():
                return col
    return None

df.rename(columns={
    get_col(["Сума по GTA цена"]): "gta_sum",
    get_col(["Сума по Еко цена", "Сума по ЕКО цена"]): "eko_sum",
    get_col(["GTA цена"]): "gta_price",
    get_col(["Еко цена", "ЕКО цена"]): "eko_price"
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
# EMPLOYEE MAP
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

df["Номер на карта"] = df["Номер на карта"].astype(str).str.strip().str.replace(".0", "", regex=False)
df["employee"] = df["Номер на карта"].map(card_map).fillna("UNKNOWN")

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.header("Filters")

start_date = st.sidebar.date_input("Start date", df["Дата"].min())
end_date = st.sidebar.date_input("End date", df["Дата"].max())

# -------------------------
# DESCRIPTION (NEW)
# -------------------------
st.sidebar.markdown("""
---

### ℹ️ Как работи дашбордът

Този дашборд анализира потреблението на гориво на база транзакции.

**Глобално:**
- Филтърът за дата влияе на всички табове
- Данните се агрегират по дни и продукти

---

### 📊 Company Overview
- Анализ по избрана фирма
- KPI: Total, Average, Peak
- Дневни трендове по продукти

---

### ⛽ Product Comparison
- Сравнение между различни продукти и фирми
- Филтриране чрез чекбокси

---

### 👤 Employee Analysis
- Анализ по служители
- Филтриране на конкретни хора
""")

# -------------------------
# GLOBAL FILTER
# -------------------------
filtered_global = df[
    (df["Дата"] >= pd.to_datetime(start_date)) &
    (df["Дата"] <= pd.to_datetime(end_date))
]

st.title("Анализ на потреблението - бензиностанции ЕКО")

tab1, tab2, tab3 = st.tabs([
    "Company Overview",
    "Product Comparison",
    "Employee Analysis"
])

# =========================
# TAB 1
# =========================
with tab1:

    company = st.selectbox("Company", filtered_global["company"].unique())

    if "tab1_init" not in st.session_state:
        for p in valid_products:
            st.session_state[f"tab1_{p}"] = True
        st.session_state.tab1_init = True

    col1, col2 = st.columns(2)

    if col1.button("Select All"):
        for p in valid_products:
            st.session_state[f"tab1_{p}"] = True

    if col2.button("Clear All"):
        for p in valid_products:
            st.session_state[f"tab1_{p}"] = False

    cols = st.columns(len(valid_products))
    selected_products = []

    for i, p in enumerate(valid_products):
        if cols[i].checkbox(p, key=f"tab1_{p}"):
            selected_products.append(p)

    filtered = filtered_global[
        (filtered_global["company"] == company) &
        (filtered_global["Име на артикул"].isin(selected_products))
    ]

    if filtered.empty:
        st.warning("No data")
    else:

        cols = st.columns(2)

        for i, product in enumerate(valid_products):

            product_df = filtered[filtered["Име на артикул"] == product]

            if product_df.empty:
                continue

            trend = (
                product_df.groupby("Дата")["Литри"]
                .sum()
                .reset_index()
                .sort_values("Дата")
            )

            total = trend["Литри"].sum()
            avg = trend["Литри"].mean()
            peak_row = trend.loc[trend["Литри"].idxmax()]

            col = cols[i % 2]

            with col:
                st.markdown(f"### {product}")

                k1, k2, k3 = st.columns(3)
                k1.metric("Total", round(total, 1))
                k2.metric("Avg", round(avg, 1))
                k3.metric("Peak",
                          peak_row["Дата"].strftime("%d %b"),
                          f"{round(peak_row['Литри'], 1)} L")

                fig, ax = plt.subplots(figsize=(8, 4.5))

                fig.patch.set_facecolor("#0f172a")
                ax.set_facecolor("#0f172a")

                ax.plot(trend["Дата"], trend["Литри"],
                        marker="o", linewidth=2, color="#3b82f6")

                ax.axhline(avg, linestyle="--", linewidth=2, color="#ef4444")

                ax.fill_between(trend["Дата"], trend["Литри"], alpha=0.15)

                ax.set_title("Daily Consumption", color="white")
                ax.tick_params(axis='x', rotation=90, colors="white")
                ax.tick_params(axis='y', colors="white")

                ax.grid(True, linestyle="--", alpha=0.2)

                for spine in ax.spines.values():
                    spine.set_visible(False)

                plt.tight_layout()
                st.pyplot(fig)

        st.subheader("Transactions")
        st.dataframe(filtered.sort_values("Дата", ascending=False), use_container_width=True)

# =========================
# TAB 2
# =========================
with tab2:

    if "prod_initialized" not in st.session_state:
        for p in valid_products:
            st.session_state[f"prod_{p}"] = True
        st.session_state.prod_initialized = True

    col1, col2 = st.columns(2)

    if col1.button("Select All Products"):
        for p in valid_products:
            st.session_state[f"prod_{p}"] = True

    if col2.button("Clear All Products"):
        for p in valid_products:
            st.session_state[f"prod_{p}"] = False

    cols = st.columns(len(valid_products))
    selected_products = []

    for i, p in enumerate(valid_products):
        if cols[i].checkbox(p, key=f"prod_{p}"):
            selected_products.append(p)

    product_stats = filtered_global[
        filtered_global["Име на артикул"].isin(selected_products)
    ]

    if not product_stats.empty:

        st.markdown("### Consumption by Company")

        agg = (
            product_stats
            .groupby("company")["Литри"]
            .sum()
            .sort_values(ascending=False)
        )

        fig, ax = plt.subplots(figsize=(15, 12))

        fig.patch.set_facecolor("#0f172a")
        ax.set_facecolor("#0f172a")

        bars = ax.barh(
            agg.index,
            agg.values
        )

        ax.invert_yaxis()

        # текст върху баровете
        for i, v in enumerate(agg.values):
            ax.text(
                v,
                i,
                f" {round(v, 1)}",
                va="center",
                color="white"
            )

        ax.set_title("Total Consumption by Company", color="white")

        ax.tick_params(axis='x', colors="white")
        ax.tick_params(axis='y', colors="white")

        ax.grid(axis="x", linestyle="--", alpha=0.2)

        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.tight_layout()

        st.pyplot(fig)

    st.dataframe(product_stats)

# =========================
# TAB 3
# =========================
with tab3:

    employee_df = filtered_global[
        filtered_global["company"] == "ДЖИ ТИ ЕЙ ПЕТРОЛИУМ"
    ]

    employees_list = sorted(employee_df["employee"].unique())

    if "emp_initialized" not in st.session_state:
        for e in employees_list:
            st.session_state[f"emp_{e}"] = True
        st.session_state.emp_initialized = True

    col1, col2 = st.columns(2)

    if col1.button("Select All Employees"):
        for e in employees_list:
            st.session_state[f"emp_{e}"] = True

    if col2.button("Clear All Employees"):
        for e in employees_list:
            st.session_state[f"emp_{e}"] = False

    cols = st.columns(4)
    selected = []

    for i, emp in enumerate(employees_list):
        if cols[i % 4].checkbox(emp, key=f"emp_{emp}"):
            selected.append(emp)

    employee_df = employee_df[employee_df["employee"].isin(selected)]

    if not employee_df.empty:

        st.markdown("### Employee KPI")

        # -------------------------
        # AGG
        # -------------------------
        agg = (
            employee_df
            .groupby("employee")["Литри"]
            .sum()
            .sort_values(ascending=False)
        )

        total = agg.sum()
        avg = agg.mean()
        top_employee = agg.idxmax()
        top_value = agg.max()

        # =========================
        # TOP KPI CARDS
        # =========================
        c1, c2, c3 = st.columns(3)

        c1.markdown(f"""
        <div style="
            background: linear-gradient(135deg,#0f172a,#1e293b);
            padding:20px;
            border-radius:12px;
            border:1px solid #1e3a8a;">
            <div style="color:#60a5fa;font-size:13px;">TOTAL CONSUMPTION</div>
            <div style="color:white;font-size:26px;font-weight:700;">
                {round(total,1)} L
            </div>
        </div>
        """, unsafe_allow_html=True)

        c2.markdown(f"""
        <div style="
            background: linear-gradient(135deg,#0f172a,#1e293b);
            padding:20px;
            border-radius:12px;
            border:1px solid #1e3a8a;">
            <div style="color:#60a5fa;font-size:13px;">AVERAGE / EMPLOYEE</div>
            <div style="color:white;font-size:26px;font-weight:700;">
                {round(avg,1)} L
            </div>
        </div>
        """, unsafe_allow_html=True)

        c3.markdown(f"""
        <div style="
            background: linear-gradient(135deg,#0f172a,#1e293b);
            padding:20px;
            border-radius:12px;
            border:1px solid #1e3a8a;">
            <div style="color:#60a5fa;font-size:13px;">TOP EMPLOYEE</div>
            <div style="color:white;font-size:18px;font-weight:700;">
                {top_employee}
            </div>
            <div style="color:#3b82f6;font-size:16px;">
                {round(top_value,1)} L
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # BREAKDOWN GRID
        # =========================
        st.markdown("### Employee Breakdown")

        cols = st.columns(4)

        for i, (emp, val) in enumerate(agg.items()):
            col = cols[i % 4]

            # highlight top 3
            if i < 3:
                border = "#3b82f6"
                bg = "linear-gradient(135deg,#1e293b,#020617)"
            else:
                border = "#1e3a8a"
                bg = "#0f172a"

            col.markdown(f"""
            <div style="
                background:{bg};
                padding:15px;
                border-radius:10px;
                border:1px solid {border};
                margin-bottom:15px;">
                <div style="color:white;font-size:14px;">
                    {emp}
                </div>
                <div style="
                    color:#3b82f6;
                    font-size:20px;
                    font-weight:700;">
                    {round(val,1)} L
                </div>
            </div>
            """, unsafe_allow_html=True)

    # -------------------------
    # TABLE
    # -------------------------
    st.dataframe(employee_df)