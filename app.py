import streamlit as st
import pandas as pd

st.set_page_config(page_title="Транспортен анализ", page_icon="🚛", layout="wide")

st.markdown("""
<style>
.stApp {background: #f5f7fb; color: #17233b;}
.block-container {max-width: 1600px; padding-top: 2rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {background: #10243e;}
[data-testid="stSidebar"] * {color: #f0f5ff;}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] *,
[data-testid="stSidebar"] input {color: #17233b;}
[data-testid="stSidebar"] [data-testid="stDateInput"] input {color: #17233b;}
h1, h2, h3 {color: #17233b; letter-spacing: -0.025em;}
.hero {background: linear-gradient(110deg,#102945,#174a70); border-radius: 20px;
       padding: 28px 34px; color: white; margin-bottom: 22px; box-shadow: 0 12px 28px rgba(18,44,75,.12);}
.hero .eyebrow {font-size: 12px; font-weight: 700; letter-spacing: .15em; color: #8cd5ea;}
.hero h1 {color: #fff; font-size: 32px; margin: 8px 0;}
.hero p {color: #d8e9f4; margin: 0; font-size: 14px;}
.kpi {background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
      padding: 21px 23px; min-height: 127px; box-shadow: 0 5px 14px rgba(17,40,72,.04);}
.kpi-label {font-size: 13px; color: #66758c; font-weight: 600;}
.kpi-value {font-size: 27px; color: #142b49; font-weight: 750; margin-top: 12px; white-space: nowrap;}
.kpi-unit {font-size: 12px; color: #71819a; margin-top: 3px;}
.section-head {font-size: 19px; font-weight: 750; color: #192d49; margin: 30px 0 13px;}
.filter-summary {color: #66758c; margin: 5px 0 20px; font-size: 13px;}
[data-testid="stDataFrame"] {border: 1px solid #e2e8f0; border-radius: 14px; overflow: hidden;}
</style>
""", unsafe_allow_html=True)

# Transport data is the only data source. The course date (not its update date)
# determines the reporting period, including courses edited in later months.
transport_df = pd.read_csv("transport/transport_data.csv")
transport_df.columns = transport_df.columns.str.strip()
transport_df["КУРС_ДАТА"] = pd.to_datetime(transport_df["КУРС_ДАТА"], errors="coerce")
for field in ["КМ", "Л", "ЛИТРИ_1", "ЛИТРИ_2", "€_ЦЕНА_ОБЩО"]:
    transport_df[field] = pd.to_numeric(transport_df[field], errors="coerce")

for field, missing_label in [
    ("ТЪРГОВЕЦ", "НЯМА ТЪРГОВЕЦ"),
    ("ПРЕВОЗВАЧ", "НЯМА ПРЕВОЗВАЧ"),
    ("ШОФЬОР", "НЯМА ШОФЬОР"),
    ("ВЛЕКАЧ", "НЯМА ВЛЕКАЧ"),
]:
    transport_df[field] = transport_df[field].fillna("").astype(str).str.strip()
    transport_df.loc[transport_df[field] == "", field] = missing_label

def safe_ratio(numerator, denominator):
    return numerator.div(denominator.where(denominator.ne(0)))

transport_df["€/км"] = safe_ratio(transport_df["€_ЦЕНА_ОБЩО"], transport_df["КМ"])
transport_df["л/км"] = safe_ratio(transport_df["Л"], transport_df["КМ"])
transport_df["€/л"] = safe_ratio(transport_df["€_ЦЕНА_ОБЩО"], transport_df["Л"])

st.markdown("""
<div class="hero">
<div class="eyebrow">TRANSPORT INTELLIGENCE</div>
<h1>🚛 Транспортен анализ</h1>
<p>Курсове, превозени литри, пробег и транспортни разходи на едно място.</p>
</div>
""", unsafe_allow_html=True)

valid_dates = transport_df["КУРС_ДАТА"].dropna()
if valid_dates.empty:
    st.error("Няма валидни дати на курсове в транспортния файл.")
    st.stop()

min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
with st.sidebar:
    st.header("⚙️ Филтри")
    start_date = st.date_input("От дата", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("До дата", value=max_date, min_value=min_date, max_value=max_date)
    st.caption("Отчетът използва датата на курса, независимо кога записът е редактиран.")

if start_date > end_date:
    st.warning("Началната дата трябва да е преди крайната.")
    st.stop()

# Exclusive next-day bound keeps every course on the chosen end date,
# including timestamps after midnight.
tdf = transport_df.loc[
    (transport_df["КУРС_ДАТА"] >= pd.Timestamp(start_date)) &
    (transport_df["КУРС_ДАТА"] < pd.Timestamp(end_date) + pd.Timedelta(days=1))
].copy()

# Explicit filter controls: users can see their selection, search values, and reset.
# Cascading options reflect selections made above without dropping missing labels.
with st.sidebar:
    st.markdown("### 🔎 Прецизирай резултатите")
    st.caption("По подразбиране се показват всички курсове. Избери конкретни стойности, за да стесниш резултатите.")
    if st.button("↺ Покажи всички", use_container_width=True, help="Изчиства ограниченията по търговец, превозвач, шофьор и влекач."):
        for key in ("ТЪРГОВЕЦ", "ПРЕВОЗВАЧ", "ШОФЬОР", "ВЛЕКАЧ"):
            st.session_state[f"filter_{key}"] = []
        st.rerun()

    filter_fields = [
        ("ТЪРГОВЕЦ", "Търговец", "Кой търговец е организирал курса?"),
        ("ПРЕВОЗВАЧ", "Превозвач", "Коя транспортна фирма е изпълнила курса?"),
        ("ШОФЬОР", "Шофьор", "Кой е управлявал превозното средство?"),
        ("ВЛЕКАЧ", "Влекач", "Кой влекач е използван за курса?"),
    ]
    active_filters = 0
    for field, label, explanation in filter_fields:
        options = sorted(tdf[field].dropna().unique().tolist())
        key = f"filter_{field}"
        # An empty selection means All, even if cascading options change.
        saved = st.session_state.get(key, [])
        st.session_state[key] = [value for value in saved if value in options]
        selected = st.multiselect(
            label,
            options,
            key=key,
            placeholder=f"Всички ({len(options)}) — избери за филтриране",
            help=explanation + " Можеш да търсиш чрез писане. Без избор = всички.",
        )
        if selected:
            tdf = tdf.loc[tdf[field].isin(selected)]
            active_filters += 1
            st.caption(f"✓ Избрани: {len(selected)} от {len(options)}")
        else:
            st.caption(f"Всички {len(options)} стойности са включени")
    st.divider()
    st.caption(f"Активни филтри: {active_filters} от 4 · Намерени курсове: {len(tdf):,}")

def format_number(value, decimals=0):
    return f"{value:,.{decimals}f}".replace(",", " ")

def kpi(label, value, unit=""):
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-unit">{unit}</div></div>',
        unsafe_allow_html=True,
    )

total_liters = tdf["Л"].sum()
total_cost = tdf["€_ЦЕНА_ОБЩО"].sum()
total_km = tdf["КМ"].sum()
count = len(tdf)
st.markdown(
    f'<div class="filter-summary">Период: {start_date:%d.%m.%Y} – {end_date:%d.%m.%Y}'
    f' &nbsp;•&nbsp; {count} курса</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-head">Ключови показатели</div>', unsafe_allow_html=True)
cols = st.columns(4)
with cols[0]:
    kpi("Превозени литри", format_number(total_liters), "л")
with cols[1]:
    kpi("Общ пробег", format_number(total_km, 1), "км")
with cols[2]:
    kpi("Транспортни разходи", format_number(total_cost, 2), "€")
with cols[3]:
    kpi("Брой курсове", format_number(count), "курса")

cols = st.columns(4)
with cols[0]:
    kpi("Средно литри / курс", format_number(total_liters / count, 1) if count else "—", "л")
with cols[1]:
    kpi("Среден разход / курс", format_number(total_cost / count, 2) if count else "—", "€")
with cols[2]:
    kpi("Разход / 1 000 л", format_number(total_cost / total_liters * 1000, 2) if total_liters else "—", "€")
with cols[3]:
    kpi("Допълнителни литри", format_number(tdf["ЛИТРИ_1"].sum() + tdf["ЛИТРИ_2"].sum()), "ЛИТРИ_1 + ЛИТРИ_2")

if tdf.empty:
    st.info("Няма курсове за избраните филтри.")
    st.stop()

st.markdown('<div class="section-head">Тенденция по дати</div>', unsafe_allow_html=True)
daily = (
    tdf.assign(Дата=tdf["КУРС_ДАТА"].dt.date)
    .groupby("Дата", as_index=True)["Л"].sum()
    .rename("Превозени литри")
)
st.bar_chart(daily, use_container_width=True, height=290)

st.markdown('<div class="section-head">Детайли по курсове</div>', unsafe_allow_html=True)
preferred = [
    "КУРС_ДАТА", "ТЪРГОВЕЦ", "ВЪЗЛОЖИТЕЛ", "КУРС", "БРОЙ_ОБЕКТИ",
    "ПРЕВОЗВАЧ", "ШОФЬОР", "ВЛЕКАЧ", "ЦИСТЕРНА", "КМ", "Л",
    "€_ЦЕНА_ОБЩО", "€/км", "л/км", "€/л", "ЛИТРИ_1", "ЛИТРИ_2",
    "ДЕН", "МЕСЕЦ", "ГОДИНА",
]
columns = [c for c in preferred if c in tdf.columns]
table = tdf[columns].sort_values("КУРС_ДАТА", ascending=False)
st.dataframe(table, use_container_width=True, hide_index=True, height=510)
st.download_button(
    "⬇️ Изтегли филтрираните курсове (CSV)",
    table.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"transport_{start_date}_{end_date}.csv",
    mime="text/csv",
)
