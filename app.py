import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from html import escape
from io import BytesIO

st.set_page_config(page_title="Транспортен анализ", page_icon="🚛", layout="wide")

st.markdown("""
<style>
.stApp {background: #f5f7fb; color: #17233b;}
[data-testid="stHeader"] {
    background:linear-gradient(110deg,#050a12 0%,#0b1b2c 60%,#122f40 100%);
    border-bottom:1px solid #35516a;box-shadow:0 3px 14px rgba(0,0,0,.22);}
[data-testid="stHeader"] button,
[data-testid="stHeader"] button p,
[data-testid="stHeader"] a,
[data-testid="stHeader"] [data-testid="stIconMaterial"],
[data-testid="stHeader"] [data-testid="stIconEmoji"],
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapsedControl"] [data-testid="stIconMaterial"] {
    color:#f0f6ff !important;opacity:1;}
[data-testid="stHeader"] button svg,
[data-testid="stSidebarCollapsedControl"] button svg {color:#f0f6ff;fill:currentColor;}
[data-testid="stHeader"] button svg [stroke]:not([stroke="none"]),
[data-testid="stSidebarCollapsedControl"] button svg [stroke]:not([stroke="none"]) {
    stroke:currentColor;}
[data-testid="stHeader"] button,
[data-testid="stSidebarCollapsedControl"] button {
    background:rgba(38,70,95,.65);border:1px solid #46637c;border-radius:9px;}
[data-testid="stHeader"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:hover {
    background:#294d68;border-color:#8eb9d8;}
[data-testid="stHeader"] button:focus-visible,
[data-testid="stSidebarCollapsedControl"] button:focus-visible {
    outline:2px solid #a5d5f3;outline-offset:2px;}

.block-container {max-width: 1600px; padding-top: 5.5rem; padding-bottom: 3rem;}
/* Consistent, accessible filter panel; scoped to the sidebar only. */
[data-testid="stSidebar"] {
    background:linear-gradient(155deg,#10243f 0%,#183e60 54%,#23607d 100%);
    border-right:1px solid #52758d;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background:transparent;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color:#f4f8ff;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color:#bed2e5;
    font-size:12px;
    line-height:1.55;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
    display:flex;
    align-items:center;
    gap:6px;
    min-height:22px;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    font-size:13px;
    font-weight:650;
    line-height:1.4;
}
/* Streamlit's SVG help icon varied between versions; keep its native
   tooltip behavior and draw a legible, deterministic white question mark. */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] [data-testid="stTooltipIcon"] {
    position:relative;
    display:inline-flex !important;
    align-items:center;
    justify-content:center;
    flex:0 0 19px;
    width:19px !important;
    height:19px !important;
    padding:0 !important;
    margin-left:3px;
    box-sizing:border-box;
    color:#fff !important;
    border:1.5px solid #fff !important;
    border-radius:50% !important;
    background:rgba(9,30,52,.35) !important;
    opacity:1 !important;
    cursor:help;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] [data-testid="stTooltipIcon"] svg,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] [data-testid="stTooltipIcon"] [data-testid="stIconMaterial"] {
    opacity:0 !important;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] [data-testid="stTooltipIcon"]::after {
    content:"?";
    position:absolute;
    inset:0;
    display:flex;
    align-items:center;
    justify-content:center;
    font-family:Arial,Helvetica,sans-serif;
    font-size:12px;
    font-weight:800;
    line-height:1;
    color:#fff;
    pointer-events:none;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] [data-testid="stTooltipIcon"]:focus-visible {
    outline:2px solid #b4e1ff;
    outline-offset:3px;
}
/* Light fields on the dark surface: readable dates and selected tags. */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background:#f3f7fd !important;
    border-color:#b6c7d9 !important;
    border-radius:10px !important;
    box-shadow:none !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    color:#193650 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color:#274965 !important;
    fill:currentColor;
}
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] {
    background:#2f70c8 !important;
    border-radius:6px;
}
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] *,
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] {
    color:#fff !important;
}
[data-testid="stSidebar"] input::placeholder {
    color:#70839c !important;
    opacity:1;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within,
[data-testid="stSidebar"] [data-baseweb="input"]:focus-within {
    border-color:#7bbde9 !important;
    box-shadow:0 0 0 2px rgba(123,189,233,.25) !important;
}
/* Rely on Streamlit's own stretch-width button layout. Only theme colors,
   borders and focus states are customized to avoid a collapsed button box. */
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background:linear-gradient(115deg,#28516d,#34768d);
    border:1px solid #5988a5;
    border-radius:10px;
    color:#fff;
}
[data-testid="stSidebar"] [data-testid="stButton"] button p,
[data-testid="stSidebar"] [data-testid="stButton"] button svg {
    color:#fff;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background:linear-gradient(115deg,#316786,#4388a0);
    border-color:#a6d5f0;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:focus-visible {
    outline:2px solid #c3e9ff;
    outline-offset:2px;
}
[data-testid="stSidebar"] hr { border-color:#456680; }
h1, h2, h3 {color: #17233b; letter-spacing: -0.025em;}
.hero {position:relative;overflow:hidden;background:linear-gradient(112deg,#10243f 0%,#173f63 61%,#23627e 100%);
       border:1px solid rgba(255,255,255,.16);border-radius:22px;padding:32px 38px;
       margin-bottom:24px;box-shadow:0 16px 36px rgba(15,42,69,.15);}
.hero:after {content:"";position:absolute;width:350px;height:350px;right:-80px;top:-220px;
       border:1px solid rgba(183,222,244,.20);border-radius:50%;box-shadow:0 0 0 65px rgba(181,225,245,.04);}
.hero-top {display:flex;align-items:center;gap:10px;color:#a5d5ed;font-size:11px;
       font-weight:750;letter-spacing:.16em;text-transform:uppercase;position:relative;z-index:1;}
.hero-mark {display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;
       border-radius:9px;background:rgba(163,216,239,.14);border:1px solid rgba(204,235,249,.22);
       color:#c9eafa;font-size:15px;letter-spacing:0;}
.hero h1 {position:relative;z-index:1;color:#fff;font-size:clamp(28px,3vw,40px);
       line-height:1.15;font-weight:770;letter-spacing:-.035em;margin:17px 0 12px;}
.hero p {position:relative;z-index:1;color:#d3e1ee;margin:0;font-size:14px;line-height:1.6;max-width:680px;}
.hero-footer {position:relative;z-index:1;display:flex;gap:10px;flex-wrap:wrap;margin-top:22px;}
.hero-chip {font-size:11px;font-weight:650;color:#d5eaf4;border:1px solid rgba(206,232,243,.21);
       background:rgba(255,255,255,.065);padding:7px 11px;border-radius:30px;}
@media(max-width:700px){.hero{padding:26px 22px;}.hero:after{display:none;}}
/* KPI cards: restrained pastel gradients, consistent hierarchy and ample whitespace */
.kpi {position: relative; overflow: hidden; box-sizing: border-box; min-height: 194px; height: 100%;
      border-radius: 19px; padding: 21px 22px 19px; margin-bottom: 12px;
      border: 1px solid var(--kpi-border, #dce8f5);
      background: var(--kpi-bg, linear-gradient(135deg,#f8fbff,#eaf3ff));
      box-shadow: 0 6px 22px rgba(30,55,90,.055); transition: transform .2s ease,box-shadow .2s ease;}
.kpi:hover {transform: translateY(-2px); box-shadow: 0 11px 28px rgba(30,55,90,.10);}
/* Stretch each KPI to the tallest card within its own row. */
[data-testid="stHorizontalBlock"]:has(.kpi) {align-items:stretch;}
[data-testid="stColumn"]:has(.kpi) > [data-testid="stVerticalBlock"] {height:100%;}
[data-testid="stColumn"]:has(.kpi) [data-testid="stElementContainer"]:has(.kpi),
[data-testid="stColumn"]:has(.kpi) [data-testid="stMarkdown"],
[data-testid="stColumn"]:has(.kpi) [data-testid="stMarkdownContainer"] {height:100%;}

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
.liters-split {display:grid;grid-template-columns:1fr 1fr;margin-top:16px;}
.liters-part {min-width:0;padding-right:12px;}
.liters-part + .liters-part {border-left:1px solid #c2d6ef;padding-left:16px;padding-right:0;}
.liters-value {color:#182d49;font-size:clamp(20px,1.6vw,27px);font-weight:780;
    line-height:1.2;margin-top:7px;overflow-wrap:anywhere;font-variant-numeric:tabular-nums;}

.kpi:before {content:""; position:absolute; left:0; top:21px; bottom:21px; width:3px;
             background:var(--kpi-accent); border-radius:0 3px 3px 0; opacity:.7;}
@media (prefers-reduced-motion:reduce) {.kpi{transition:none}.kpi:hover{transform:none}}
.section-head {font-size: 19px; font-weight: 750; color: #192d49; margin: 30px 0 13px;}
.filter-summary {color: #66758c; margin: 5px 0 20px; font-size: 13px;}
.chart-period {display:inline-block;margin:-3px 0 12px;padding:9px 14px;
    background:#eaf2fd;border:1px solid #d4e4f7;border-radius:10px;
    color:#29486a;font-size:13px;font-weight:500;}
.chart-period strong {font-weight:750;color:#173955;}
.chart-filter-context {display:flex;flex-wrap:wrap;gap:8px;margin:15px 0 20px;}
.chart-chip {display:inline-block;background:linear-gradient(125deg,#fff,#f0f5fc);
  border:1px solid #dae5f3;border-radius:999px;padding:8px 12px;
  font-size:12px;line-height:1.4;color:#36516e;}
.chart-chip strong {color:#173955;}

[data-testid="stDataFrame"] {border: 1px solid #e2e8f0; border-radius: 14px; overflow: hidden;}
</style>
""", unsafe_allow_html=True)

# Main navigation lives below the global theme, above both page contents.
tab_analysis, tab_cards = st.tabs(["📊 Транспортен анализ", "💳 Списък фирми и карти"])

with tab_analysis:
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
    <section class="hero" aria-label="Транспортен анализ">
      <div class="hero-top"><span class="hero-mark">↗</span> OPERATIONS OVERVIEW <span style="opacity:.45">/</span> ТРАНСПОРТ</div>
      <h1>Транспортен анализ</h1>
      <p>Централизирана информация за курсовете, превозените количества, пробега и транспортните разходи.</p>
      <div class="hero-footer">
        <span class="hero-chip">◉ Актуални данни от курсовете</span>
        <span class="hero-chip">↗ Анализ по избран период</span>
      </div>
    </section>
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
        st.caption("Без избор = всички. По подразбиране е избран търговец Vesela Nikolova.")
        if st.button("↺ Покажи всички", width="stretch", key="transport_reset_filters"):
            for key in ("ТЪРГОВЕЦ", "ПРЕВОЗВАЧ", "ШОФЬОР", "ВЛЕКАЧ"):
                st.session_state[f"filter_{key}"] = []
            st.rerun()

        # Only initialize on the first load: later user selections and "Покажи всички"
        # remain authoritative, including an intentionally empty (all) selection.
        if "filter_ТЪРГОВЕЦ" not in st.session_state:
            st.session_state["filter_ТЪРГОВЕЦ"] = ["Vesela Nikolova"]

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
        kpi("Общ пробег / км", format_number(total_km, 1), "километра общо", "↗", "teal")
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
        st.markdown(
            '<div class="kpi blue">'
            '<div class="kpi-top"><div class="kpi-label">Допълнителни литри</div>'
            '<span class="kpi-icon" aria-hidden="true">+</span></div>'
            '<div class="liters-split">'
            '<div class="liters-part"><div class="kpi-label">Литри 1</div>'
            f'<div class="liters-value">{format_number(tdf["ЛИТРИ_1"].sum())}</div>'
            '<div class="kpi-unit">литра</div></div>'
            '<div class="liters-part"><div class="kpi-label">Литри 2</div>'
            f'<div class="liters-value">{format_number(tdf["ЛИТРИ_2"].sum())}</div>'
            '<div class="kpi-unit">литра</div></div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

    if tdf.empty:
        st.info("Няма курсове за избраните филтри.")
        st.stop()

    # The chart always uses the fully filtered tdf, just like the KPI cards and table.
    st.markdown('<div class="section-head">Дневна тенденция на транспорта</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="chart-period">📅 Отчетен период: '
        f'<strong>{start_date:%d.%m.%Y} – {end_date:%d.%m.%Y}</strong></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Всяка колона представя общите данни за един ден. "
        "Стойностите се преизчисляват автоматично при промяна на периода, "
        "търговеца, превозвача, шофьора или влекача."
    )

    def chart_filter_summary(field):
        selection = st.session_state.get(f"filter_{field}", [])
        if not selection:
            return "Всички"
        return selection[0] if len(selection) == 1 else f"{len(selection)} избрани"

    filter_descriptions = [
        ("Период", f"{start_date:%d.%m.%Y} – {end_date:%d.%m.%Y}"),
        ("Търговец", chart_filter_summary("ТЪРГОВЕЦ")),
        ("Превозвач", chart_filter_summary("ПРЕВОЗВАЧ")),
        ("Шофьор", chart_filter_summary("ШОФЬОР")),
        ("Влекач", chart_filter_summary("ВЛЕКАЧ")),
    ]
    chips = "".join(
        f'<span class="chart-chip"><strong>{escape(label)}:</strong> '
        f'{escape(value)}</span>'
        for label, value in filter_descriptions
    )
    st.markdown(f'<div class="chart-filter-context">{chips}</div>', unsafe_allow_html=True)

    daily = (
        tdf.assign(Дата=tdf["КУРС_ДАТА"].dt.normalize())
        .groupby("Дата", as_index=False)
        .agg(
            литри=("Л", "sum"),
            курсове=("КУРС_ДАТА", "size"),
            километри=("КМ", "sum"),
            разход=("€_ЦЕНА_ОБЩО", "sum"),
        )
        .sort_values("Дата")
    )
    active_days = len(daily)
    average_liters = total_liters / active_days if active_days else 0
    peak = daily.loc[daily["литри"].idxmax()] if active_days else None

    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Превозени литри", f"{format_number(total_liters)} л")
    with summary_cols[1]:
        st.metric("Дни с курсове", format_number(active_days))
    with summary_cols[2]:
        st.metric("Средно на активен ден", f"{format_number(average_liters)} л")
    with summary_cols[3]:
        st.metric(
            "Най-натоварен ден",
            peak["Дата"].strftime("%d.%m.%Y") if peak is not None else "—",
            f"{format_number(peak['литри'])} л" if peak is not None else None,
            delta_color="off",
        )

    metric_options = {
        "Превозени литри": ("литри", "л", "#4596df"),
        "Брой курсове": ("курсове", "курса", "#258d80"),
        "Пробег": ("километри", "км", "#8169c6"),
        "Транспортни разходи": ("разход", "€", "#cc903f"),
    }
    metric_name = st.segmented_control(
        "Показател на графиката",
        list(metric_options),
        default="Превозени литри",
        selection_mode="single",
        key="transport_daily_metric",
        help="Избери показател. Графиката запазва текущия период и всички активни филтри.",
        width="stretch",
    )
    metric_name = metric_name or "Превозени литри"
    metric_explanations = {
        "Превозени литри": "Общо превозени литри за всеки ден.",
        "Брой курсове": "Брой изпълнени курсове за всеки ден.",
        "Пробег": "Общ пробег в километри за всеки ден.",
        "Транспортни разходи": "Общи транспортни разходи в евро за всеки ден.",
    }
    st.caption(metric_explanations[metric_name] + " Показани са само курсовете, включени в текущите филтри.")

    metric_field, metric_unit, bar_color = metric_options[metric_name]

    fig = go.Figure()
    fig.add_bar(
        x=daily["Дата"],
        y=daily[metric_field],
        marker_color=bar_color,
        width=0.82 * 24 * 60 * 60 * 1000,  # 82% of one calendar day on a date axis
        marker_line_width=0,
        customdata=daily[["литри", "курсове", "километри", "разход"]].to_numpy(),
        hovertemplate=(
            "<b>%{x|%d.%m.%Y}</b><br>"
            "Превозени литри: %{customdata[0]:,.0f} л<br>"
            "Курсове: %{customdata[1]:,.0f}<br>"
            "Пробег: %{customdata[2]:,.1f} км<br>"
            "Транспортни разходи: %{customdata[3]:,.2f} €"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        dragmode="pan",
        template="plotly_dark",
        height=380,
        margin=dict(l=14, r=20, t=16, b=20),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(family="Arial, sans-serif", color="#f0f5ff", size=12),
        showlegend=False,
        bargap=0.12,
        hoverlabel=dict(bgcolor="#172c45", font_color="#ffffff"),
        xaxis=dict(
            title=None,
            type="date",
            tickformat="%d.%m",
            tickangle=0,
            showgrid=False,
            showline=True,
            linecolor="#526781",
            range=[pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1)],
        ),
        yaxis=dict(
            title=f"{metric_name} ({metric_unit})",
            rangemode="tozero",
            tickformat=",~s",
            showgrid=True,
            gridcolor="#3a3a3a",
            gridwidth=1,
            zeroline=False,
        ),
    )
    st.plotly_chart(fig, use_container_width=True, theme=None, config={"displaylogo": False, "scrollZoom": True})

    st.caption(
        f"За периода има {active_days} дни с курсове от общо "
        f"{(end_date - start_date).days + 1} календарни дни. "
        "Дните без курсове остават без колона; това не означава липсващи данни."
    )
    with st.expander("ℹ️ Как да четете графиката?"):
        st.markdown(
            "- **Всяка колона** показва сумата за избраната дата и показател.\\n"
            "- **Посочете колона с мишката**, за да видите литри, брой курсове, километри и разходи.\\n"
            "- **Сменете показателя** над графиката, за да сравните натоварване и разходи.\\n"
            "- **Филтрите отляво** влияят едновременно върху графиката, картите и таблицата.\\n"
            "- **Активен ден** означава ден с поне един курс за текущите филтри."
        )

    st.markdown('<div class="section-head">Детайли по курсове</div>', unsafe_allow_html=True)
    preferred = [
        "КУРС_ДАТА", "ТЪРГОВЕЦ", "ВЪЗЛОЖИТЕЛ", "КУРС", "БРОЙ_ОБЕКТИ",
        "ПРЕВОЗВАЧ", "ШОФЬОР", "ВЛЕКАЧ", "ЦИСТЕРНА", "КМ", "Л",
        "€_ЦЕНА_ОБЩО", "€/км", "л/км", "€/л", "ЛИТРИ_1", "ЛИТРИ_2",
        "ДЕН", "МЕСЕЦ", "ГОДИНА",
    ]
    columns = [c for c in preferred if c in tdf.columns]
    table = tdf[columns].sort_values("КУРС_ДАТА", ascending=False)
    # Render a scoped dark table so both headers and cells use the same palette.
    display_table = table.copy()
    display_table["КУРС_ДАТА"] = display_table["КУРС_ДАТА"].dt.strftime("%d.%m.%Y")
    st.html(
        '<style>'
        '.course-details {max-height:510px;overflow:auto;background:#000000;'
        'border:1px solid #444444;border-radius:14px;}'
        '.course-details {scrollbar-width:auto;scrollbar-color:#315b77 #080f1b;'
        'scrollbar-gutter:stable;}'
        '.course-details::-webkit-scrollbar {width:18px;height:18px;}'
        '.course-details::-webkit-scrollbar-track {background:linear-gradient(180deg,#050a12,#102638);border-radius:9px;}'
        '.course-details::-webkit-scrollbar-thumb {background:linear-gradient(180deg,#315b77,#17364e);border:3px solid #080f1b;'
        'border-radius:9px;min-height:48px;min-width:48px;}'
        '.course-details::-webkit-scrollbar-thumb:hover {background:linear-gradient(180deg,#477c9d,#245773);}'
        '.course-details::-webkit-scrollbar-corner {background:linear-gradient(180deg,#050a12,#102638);}'
        '.course-details table {width:100%;border-collapse:separate;border-spacing:0;'
        'font-size:14px;color:#ffffff;}'
        '.course-details th {position:sticky;top:0;z-index:1;background:linear-gradient(180deg,#050a12,#102638);'
        'color:#ffffff;text-align:left;font-weight:700;white-space:nowrap;}'
        '.course-details th,.course-details td {padding:12px 15px;'
        'border-bottom:1px solid #303030;}'
        '.course-details td {background:#000000;color:#ffffff;white-space:nowrap;}'
        '.course-details tbody tr:nth-child(even) td {background:#111111;}'
        '.course-details tbody tr:hover td {background:#292929;}'
        '.course-details th {background:linear-gradient(135deg,#070d19 0%,#122b45 55%,#173c4d 100%);font-size:14px;letter-spacing:.02em;'
        'padding-top:16px;padding-bottom:16px;border-bottom:2px solid #ffffff;}'
        '.course-details th:not(:last-child) {border-right:1px solid #ffffff;}'
        '.course-details td:not(:last-child) {border-right:1px solid rgba(255,255,255,.55);}'

        '</style>'
        '<div class="course-details" role="region" aria-label="Детайли по курсове" tabindex="0">'
        + display_table.to_html(index=False, escape=True, border=0, na_rep="—")
        + '</div>'
    )

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl", datetime_format="DD.MM.YYYY") as writer:
        table.to_excel(writer, index=False, sheet_name="Курсове")
        sheet = writer.sheets["Курсове"]
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions

    st.download_button(
        "⬇️ Изтегли филтрираните курсове (Excel)",
        excel_buffer.getvalue(),
        file_name=f"transport_{start_date}_{end_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


with tab_cards:
    from cards_view import render_cards
    render_cards()
