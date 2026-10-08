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
/* KPI cards: restrained pastel gradients, consistent hierarchy and ample whitespace */
.kpi {position: relative; overflow: hidden; min-height: 152px;
      border-radius: 19px; padding: 21px 22px 19px; margin-bottom: 12px;
      border: 1px solid var(--kpi-border, #dce8f5);
      background: var(--kpi-bg, linear-gradient(135deg,#f8fbff,#eaf3ff));
      box-shadow: 0 6px 22px rgba(30,55,90,.055); transition: transform .2s ease,box-shadow .2s ease;}
.kpi:hover {transform: translateY(-2px); box-shadow: 0 11px 28px rgba(30,55,90,.10);}
.kpi.blue {--kpi-bg: linear-gradient(130deg,#ffffff 0%,#e7f1ff 100%); --kpi-border:#d4e4fc; --kpi-accent:#3574d4;}
.kpi.teal {--kpi-bg: linear-gradient(130deg,#ffffff 0%,#e3f8f4 100%); --kpi-border:#ceeae4; --kpi-accent:#168a7c;}
.kpi.violet {--kpi-bg: linear-gradient(130deg,#ffffff 0%,#f0eaff 100%); --kpi-border:#e1d7f8; --kpi-accent:#7960bb;}
.kpi.amber {--kpi-bg: linear-gradient(130deg,#ffffff 0%,#fff3e2 100%); --kpi-border:#f3e3c8; --kpi-accent:#c48729;}
.kpi-top {display:flex; align-items:center; justify-content:space-between; gap:12px;}
.kpi-label {font-size:13px; color:#50627a; font-weight:650; line-height:1.35;}
.kpi-icon {display:flex; align-items:center; justify-content:center; flex:0 0 38px; height:38px;
           border-radius:12px; color:var(--kpi-accent); background:rgba(255,255,255,.68); font-size:21px;}
.kpi-value {font-size:clamp(21px,2vw,30px); color:#182d49; letter-spacing:-.035em;
            font-weight:780; margin-top:16px; line-height:1.18; overflow-wrap:anywhere; font-variant-numeric:tabular-nums;}
.kpi-unit {font-size:12px; color:#6a7c91; margin-top:6px;}
.kpi:before {content:""; position:absolute; left:0; top:21px; bottom:21px; width:3px;
             background:var(--kpi-accent); border-radius:0 3px 3px 0; opacity:.7;}
@media (prefers-reduced-motion:reduce) {.kpi{transition:none}.kpi:hover{transform:none}}
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

def kpi(label, value, unit="", icon="◈", tone="blue"):
    """Render one accessible KPI tile; tone is controlled by the caller."""
    st.markdown(
        f'<div class="kpi {tone}">'
        f'<div class="kpi-top"><div class="kpi-label">{label}</div>'
        f'<span class="kpi-icon" aria-hidden="true">{icon}</span></div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-unit">{unit}</div></div>',
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
    kpi("Превозени литри", format_number(total_liters), "литра общо", "◉", "blue")
with cols[1]:
    kpi("Общ пробег", format_number(total_km, 1), "километра общо", "↗", "teal")
with cols[2]:
    kpi("Транспортни разходи", format_number(total_cost, 2), "€ общо", "€", "violet")
with cols[3]:
    kpi("Брой курсове", format_number(count), "изпълнени курса", "▤", "amber")

cols = st.columns(4)
with cols[0]:
    kpi("Средно литри / курс", format_number(total_liters / count, 1) if count else "—", "литра на курс", "◉", "teal")
with cols[1]:
    kpi("Среден разход / курс", format_number(total_cost / count, 2) if count else "—", "€ на курс", "€", "violet")
with cols[2]:
    kpi("Разход / 1 000 л", format_number(total_cost / total_liters * 1000, 2) if total_liters else "—", "€ за 1 000 литра", "↗", "amber")
with cols[3]:
    kpi("Допълнителни литри", format_number(tdf["ЛИТРИ_1"].sum() + tdf["ЛИТРИ_2"].sum()), "ЛИТРИ_1 + ЛИТРИ_2", "+", "blue")

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
