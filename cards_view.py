"""Company/card register viewer. The uploaded workbook is never changed."""
from io import BytesIO
import base64
from pathlib import Path

import pandas as pd
import streamlit as st

WORKBOOK = Path(__file__).resolve().parent / "data" / "Еко_Списък_фирми.xlsx"


@st.cache_data(show_spinner=False)
def parse_workbook(raw: bytes) -> dict:
    return pd.read_excel(BytesIO(raw), sheet_name=None, header=None, dtype=str, keep_default_na=False)


def render_cards():
    st.markdown("""
    <section class="hero">
      <div class="hero-top"><span class="hero-mark">▤</span> COMPANY REGISTER / ГОРИВНИ КАРТИ</div>
      <h1>Списък фирми и карти</h1>
      <p>Преглед и търсене в оригиналните списъци по горивни вериги. Изберете лист за подробности.</p>
    </section>
    """, unsafe_allow_html=True)

    source = None
    # Store the original workbook privately rather than committing card PINs.
    try:
        encoded = st.secrets.get("CARDS_WORKBOOK_B64")
    except (FileNotFoundError, KeyError):
        encoded = None
    if encoded:
        try:
            source = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            st.error("Невалидно съдържание на CARDS_WORKBOOK_B64 в Streamlit Secrets.")
            return
    elif WORKBOOK.is_file():
        source = WORKBOOK.read_bytes()
    if source is None:
        st.info("За да заредите списъка, изберете Excel файла „Еко_Списък_фирми.xlsx“. "
                "За постоянно зареждане го добавете в Streamlit Secrets под ключ CARDS_WORKBOOK_B64.")
        upload = st.file_uploader("Excel файл със списъците", type=["xlsx"], key="cards_workbook")
        if upload is None:
            return
        source = upload.getvalue()

    try:
        sheets = parse_workbook(source)
    except Exception as exc:
        st.error(f"Файлът не може да бъде прочетен: {exc}")
        return

    names = list(sheets)
    sheet_name = st.selectbox("Списък / горивна верига", names, key="cards_sheet")
    raw = sheets[sheet_name].copy()
    # The EKO sheet has a legend row followed by the real header.
    header_row = 1 if sheet_name == "Еко карти" else 0
    if len(raw) <= header_row:
        st.info("В този лист няма данни.")
        return

    labels = []
    used = set()
    for i, label in enumerate(raw.iloc[header_row].tolist(), 1):
        label = str(label).strip() or f"Колона {i}"
        original = label
        n = 2
        while label in used:
            label = f"{original} ({n})"
            n += 1
        labels.append(label)
        used.add(label)

    df = raw.iloc[header_row + 1:].copy()
    df.columns = labels
    df = df.loc[df.astype(str).apply(lambda col: col.str.strip().ne("")).any(axis=1)]
    df = df.reset_index(drop=True)
    search = st.text_input("Търси по фирма, регистрационен номер, карта или друг текст",
                           placeholder="Въведете име, номер или друга стойност…",
                           key="cards_search")
    if search.strip():
        mask = df.astype(str).apply(
            lambda c: c.str.contains(search.strip(), case=False, regex=False, na=False)
        ).any(axis=1)
        df = df.loc[mask].copy()

    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.metric("Намерени записи", len(df))
    with col_b:
        st.caption(f"Източник: {sheet_name} · {len(sheets)} листа в работната книга · "
                   "търсенето обхваща всички колони")
    st.dataframe(df, hide_index=True, use_container_width=True, height=550)
    st.caption('Файлът може да съдържа номера на карти и ПИН кодове. Ограничете достъпа до приложението.')
    st.download_button(
        "⬇️ Изтегли показаните записи (CSV)",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="cards_filtered.csv",
        mime="text/csv",
        key="cards_export",
    )
