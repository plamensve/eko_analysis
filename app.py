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
df = pd.read_csv("combined_data/combined.csv", dtype={"Номер на карта": str})

# -------------------------
# LOAD TRANSPORT DATA
# -------------------------
transport_df = pd.read_csv("transport/transport_data.csv")

transport_df.columns = transport_df.columns.str.strip()

transport_df["КУРС_ДАТА"] = pd.to_datetime(transport_df["КУРС_ДАТА"])

transport_df["КМ"] = pd.to_numeric(transport_df["КМ"], errors="coerce")
transport_df["Л"] = pd.to_numeric(transport_df["Л"], errors="coerce")
transport_df["€_ЦЕНА_ОБЩО"] = pd.to_numeric(transport_df["€_ЦЕНА_ОБЩО"], errors="coerce")

# KPI
transport_df["€/км"] = transport_df["€_ЦЕНА_ОБЩО"] / transport_df["КМ"]
transport_df["л/км"] = transport_df["Л"] / transport_df["КМ"]
transport_df["€/л"] = transport_df["€_ЦЕНА_ОБЩО"] / transport_df["Л"]

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

---

### 🚛 Transport Analysis
- Показва ефективността на транспортите (км, литри, разходи)
- Данните се филтрират последователно (cascading filters)
""")

# -------------------------
# GLOBAL FILTER
# -------------------------
filtered_global = df[
    (df["Дата"] >= pd.to_datetime(start_date)) &
    (df["Дата"] <= pd.to_datetime(end_date))
]

st.title("GTA Petroleum Ltd. – Operational Analytics Dashboard")

tab1, tab2, tab3, tab4 = st.tabs([
    "Company Overview",
    "Product Comparison",
    "Employee Analysis",
    "Transport Analysis"
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
            <div style="color:white;font-size:26px;font-weight:700;">
                {top_employee}
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

st.markdown("""
<style>
.filter-card {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #1e3a8a;
    margin-bottom: 10px;
}
.filter-title {
    color: #60a5fa;
    font-size: 16px;
    font-weight: 600;
}

/* =========================
   METRIC CARDS (ADD THIS)
========================= */
.metric-card {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    border: 1px solid #1e3a8a;
    padding: 16px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 5px;
}

.metric-title {
    color: #60a5fa;
    font-size: 18px;
}

.metric-value {
    color: white;
    font-size: 24px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)


# =========================
# TAB 4 - TRANSPORT
# =========================
with tab4:

    st.subheader("Transport Efficiency Dashboard")

    # -------------------------
    # BASE FILTER (GLOBAL DATE)
    # -------------------------
    tdf = transport_df[
        (transport_df["КУРС_ДАТА"] >= pd.to_datetime(start_date)) &
        (transport_df["КУРС_ДАТА"] <= pd.to_datetime(end_date))
    ].copy()

    # -------------------------
    # TRADER GROUP
    # -------------------------
    tdf["group"] = tdf["ТЪРГОВЕЦ"].apply(
        lambda x: x if x in ["Vesela Nikolova", "Simeon Hadzhiev"] else "Other"
    )

    groups = sorted(tdf["group"].dropna().unique())

    # RESET
    if "tr_keys" not in st.session_state or st.session_state.tr_keys != groups:
        for k in list(st.session_state.keys()):
            if k.startswith("tr_"):
                del st.session_state[k]
        for g in groups:
            st.session_state[f"tr_{g}"] = True
        st.session_state.tr_keys = groups

    # -------------------------
    # TRADERS
    # -------------------------
    st.markdown("""
    <div class="filter-card">
        <div class="filter-title">ТЪРГОВЕЦ</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    if col1.button("Select All Traders"):
        for g in groups:
            st.session_state[f"tr_{g}"] = True

    if col2.button("Clear All Traders"):
        for g in groups:
            st.session_state[f"tr_{g}"] = False

    cols = st.columns(3)
    selected_groups = []

    for i, g in enumerate(groups):
        if cols[i % 3].checkbox(g, key=f"tr_{g}"):
            selected_groups.append(g)

    st.markdown("</div>", unsafe_allow_html=True)

    if selected_groups:
        tdf = tdf[tdf["group"].isin(selected_groups)]
    else:
        tdf = tdf.iloc[0:0]

    # =========================
    # CARRIERS
    # =========================
    all_carriers = sorted(tdf["ПРЕВОЗВАЧ"].dropna().unique())

    if "car_keys" not in st.session_state or st.session_state.car_keys != all_carriers:
        for k in list(st.session_state.keys()):
            if k.startswith("car_"):
                del st.session_state[k]
        for c in all_carriers:
            st.session_state[f"car_{c}"] = True
        st.session_state.car_keys = all_carriers

    st.markdown("""
    <div class="filter-card">
        <div class="filter-title">ПРЕВОЗВАЧ</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    if col1.button("Select All Carriers"):
        for c in all_carriers:
            st.session_state[f"car_{c}"] = True

    if col2.button("Clear All Carriers"):
        for c in all_carriers:
            st.session_state[f"car_{c}"] = False

    cols = st.columns(4)
    selected_carriers = []

    for i, c in enumerate(all_carriers):
        if cols[i % 4].checkbox(c, key=f"car_{c}"):
            selected_carriers.append(c)

    st.markdown("</div>", unsafe_allow_html=True)

    if selected_carriers:
        tdf = tdf[tdf["ПРЕВОЗВАЧ"].isin(selected_carriers)]
    else:
        tdf = tdf.iloc[0:0]

    # =========================
    # DRIVERS (NEW)
    # =========================
    all_drivers = sorted(tdf["ШОФЬОР"].dropna().unique())

    if "drv_keys" not in st.session_state or st.session_state.drv_keys != all_drivers:
        for k in list(st.session_state.keys()):
            if k.startswith("drv_"):
                del st.session_state[k]
        for d in all_drivers:
            st.session_state[f"drv_{d}"] = True
        st.session_state.drv_keys = all_drivers

    st.markdown("""
    <div class="filter-card">
        <div class="filter-title">ШОФЬОР</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    if col1.button("Select All Drivers"):
        for d in all_drivers:
            st.session_state[f"drv_{d}"] = True

    if col2.button("Clear All Drivers"):
        for d in all_drivers:
            st.session_state[f"drv_{d}"] = False

    cols = st.columns(4)
    selected_drivers = []

    for i, d in enumerate(all_drivers):
        if cols[i % 4].checkbox(d, key=f"drv_{d}"):
            selected_drivers.append(d)

    st.markdown("</div>", unsafe_allow_html=True)

    if selected_drivers:
        tdf = tdf[tdf["ШОФЬОР"].isin(selected_drivers)]
    else:
        tdf = tdf.iloc[0:0]

    # =========================
    # Truck (ВЛЕКАЧ)
    # =========================
    all_tractors = sorted(tdf["ВЛЕКАЧ"].dropna().unique())

    if "trc_keys" not in st.session_state or st.session_state.trc_keys != all_tractors:
        for k in list(st.session_state.keys()):
            if k.startswith("trc_"):
                del st.session_state[k]
        for t in all_tractors:
            st.session_state[f"trc_{t}"] = True
        st.session_state.trc_keys = all_tractors

    st.markdown("""
    <div class="filter-card">
        <div class="filter-title">ВЛЕКАЧ</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    if col1.button("Select All Tractors"):
        for t in all_tractors:
            st.session_state[f"trc_{t}"] = True

    if col2.button("Clear All Tractors"):
        for t in all_tractors:
            st.session_state[f"trc_{t}"] = False

    cols = st.columns(4)
    selected_tractors = []

    for i, t in enumerate(all_tractors):
        if cols[i % 4].checkbox(t, key=f"trc_{t}"):
            selected_tractors.append(t)

    st.markdown("</div>", unsafe_allow_html=True)

    if selected_tractors:
        tdf = tdf[tdf["ВЛЕКАЧ"].isin(selected_tractors)]
    else:
        tdf = tdf.iloc[0:0]

    # =========================
    # KPI (CARDS)
    # =========================
    st.markdown("### Total")
    total_km = tdf["КМ"].sum()
    total_liters = tdf["Л"].sum()
    total_cost = tdf["€_ЦЕНА_ОБЩО"].sum()

    c1, c2, c3 = st.columns(3)

    c1.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total KM</div>
        <div class="metric-value">{round(total_km, 1)}</div>
    </div>
    """, unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Liters</div>
        <div class="metric-value">{round(total_liters, 1)}</div>
    </div>
    """, unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Cost €</div>
        <div class="metric-value">{round(total_cost, 1)}</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # AVERAGES (CARDS)
    # =========================
    st.markdown("### Averages")

    if not tdf.empty:

        avg_liters = tdf["Л"].mean()
        avg_cost = tdf["€_ЦЕНА_ОБЩО"].mean()

        total_liters = tdf["Л"].sum()
        total_cost = tdf["€_ЦЕНА_ОБЩО"].sum()

        cost_per_1000 = (total_cost / total_liters * 1000) if total_liters > 0 else 0

        m1, m2, m3 = st.columns(3)

        m1.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg Transported Liters</div>
            <div class="metric-value">{round(avg_liters, 1)}</div>
        </div>
        """, unsafe_allow_html=True)

        m2.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg Total Cost €</div>
            <div class="metric-value">{round(avg_cost, 2)}</div>
        </div>
        """, unsafe_allow_html=True)

        m3.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Cost per 1000L €</div>
            <div class="metric-value">{round(cost_per_1000, 2)}</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("No data for selected filters")

    # =========================
    # TABLE
    # =========================
    st.markdown("### Transport Data")

    course_count = len(tdf)
    st.markdown(f"**Total Courses: {course_count}**")

    # =========================
    # COLUMN ORDER (CUSTOM)
    # =========================
    desired_order = [
        "ТЪРГОВЕЦ",
        "ВЪЗЛОЖИТЕЛ",
        "КУРС_ДАТА",
        "КУРС",
        "БРОЙ_ОБЕКТИ",
        "ПРЕВОЗВАЧ",
        "ШОФЬОР",
        "ВЛЕКАЧ",
        "ЦИСТЕРНА"
        "КМ",
        "Л",
        "€_ЦЕНА_ОБЩО",
        "€/км",
        "л/км",
        "€/л",
        "ДЕН",
        "МЕСЕЦ",
        "ГОДИНА"

    ]

    # оставя само колоните, които съществуват (safe)
    existing_cols = [col for col in desired_order if col in tdf.columns]

    # добавя останалите колони накрая (ако има)
    remaining_cols = [col for col in tdf.columns if col not in existing_cols]

    tdf = tdf[existing_cols + remaining_cols]

    st.dataframe(
        tdf.sort_values("КУРС_ДАТА", ascending=False),
        use_container_width=True
    )

