"""Editable register for the complete, private fuel-card workbook.

Edits are session-scoped until the updated Excel is downloaded. For durable
storage upload the exported workbook into the app again (or use an external DB).
Never commit the workbook or a secrets file containing card PINs to public Git.
"""
import base64
import hashlib
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

WORKBOOK = Path(__file__).resolve().parent / "data" / "Еко_Списък_фирми.xlsx"
CREATED = "Добавен на"
UPDATED = "Последна промяна"


@st.cache_data(show_spinner=False)
def parse_workbook(raw: bytes) -> dict:
    return pd.read_excel(BytesIO(raw), sheet_name=None, header=None,
                         dtype=str, keep_default_na=False)


def normalise_card(value):
    """Remove a leading dot/bullet and Excel's decimal .0, not actual digits."""
    value = "" if value is None else str(value).strip()
    value = value.lstrip("•·. ").strip()
    if value.endswith(".0") and value[:-2].isdigit():
        value = value[:-2]
    return value


def table_from_sheet(raw, name):
    header_row = 1 if name == "Еко карти" else 0
    if len(raw) <= header_row:
        return pd.DataFrame(), None, []
    legend = raw.iloc[0].tolist() if header_row else None
    used, labels = set(), []
    for i, col in enumerate(raw.iloc[header_row].tolist()):
        label = str(col).strip() or f"Колона {i + 1}"
        original, number = label, 2
        while label in used:
            label = f"{original} ({number})"
            number += 1
        used.add(label)
        labels.append(label)
    df = raw.iloc[header_row + 1:].copy()
    df.columns = labels
    df = df.loc[df.apply(lambda col: col.astype(str).str.strip().ne("")).any(axis=1)]
    df = df.fillna("").astype(str).reset_index(drop=True)
    for col in df.columns:
        if "номер" in col.casefold() and "карт" in col.casefold():
            df[col] = df[col].map(normalise_card)
    if CREATED not in df:
        df[CREATED] = ""
    if UPDATED not in df:
        df[UPDATED] = ""
    return df, legend, labels


def company_column(df):
    if df.empty and len(df.columns) == 0:
        return None
    for name in df.columns:
        lower = name.casefold().strip()
        if lower in ("пуснати карти за издаване списък", "надпис на карта"):
            return name
    for name in df.columns:
        if "фирма" in name.casefold() or "надпис" in name.casefold():
            return name
    return None


def workbook_bytes(tables, meta):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for name, frame in tables.items():
            legend, original_cols = meta[name]
            if legend is not None:
                pd.DataFrame([legend]).to_excel(
                    writer, sheet_name=name, index=False, header=False)
                startrow = 1
            else:
                startrow = 0
            if frame.empty and not original_cols:
                pd.DataFrame().to_excel(writer, sheet_name=name, index=False,
                                        header=False, startrow=startrow)
            else:
                frame.to_excel(writer, sheet_name=name, index=False, startrow=startrow)
            sheet = writer.sheets[name]
            sheet.freeze_panes = f"A{startrow + 2}"
            sheet.auto_filter.ref = f"A{startrow + 1}:{sheet.cell(sheet.max_row, sheet.max_column).coordinate}"
            for column in sheet.columns:
                letter = column[0].column_letter
                max_len = max((len(str(cell.value or "")) for cell in list(column)[:150]), default=12)
                sheet.column_dimensions[letter].width = min(max(14, max_len + 2), 44)
                for cell in column:
                    if cell.column <= len(original_cols) and "карт" in str(sheet.cell(startrow + 1, cell.column).value or "").casefold():
                        cell.number_format = "@"
    return out.getvalue()


def load_source():
    try:
        encoded = st.secrets.get("CARDS_WORKBOOK_B64")
    except (FileNotFoundError, KeyError):
        encoded = None
    source = None
    if encoded:
        try:
            source = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            st.error("Невалиден CARDS_WORKBOOK_B64 в Streamlit Secrets.")
            return None
    elif WORKBOOK.is_file():
        source = WORKBOOK.read_bytes()
    # An uploaded newer workbook always overrides the configured initial copy.
    uploaded = st.file_uploader(
        "Зареди нова версия на регистъра (Excel)",
        type=["xlsx"], key="cards_replace_workbook",
        help="Използвай експортирания Excel, за да продължиш работата със запазени промени.")
    if uploaded is not None:
        source = uploaded.getvalue()
    return source


def render_cards():
    st.markdown("""
    <section class="hero">
      <div class="hero-top"><span class="hero-mark">▤</span> COMPANY REGISTER / ГОРИВНИ КАРТИ</div>
      <h1>Фирми и горивни карти</h1>
      <p>Редакция, филтриране, сортиране и Excel експорт на списъците.</p>
    </section>
    """, unsafe_allow_html=True)

    source = load_source()
    if not source:
        st.info("Добавете Excel файла или настройте CARDS_WORKBOOK_B64 в Streamlit Secrets.")
        return
    source_hash = hashlib.sha256(source).hexdigest()
    if st.session_state.get("cards_source_hash") != source_hash:
        try:
            original = parse_workbook(source)
            tables, meta = {}, {}
            for name, raw in original.items():
                frame, legend, labels = table_from_sheet(raw, name)
                tables[name] = frame
                meta[name] = (legend, labels)
        except Exception as exc:
            st.error(f"Невъзможно зареждане на файла: {exc}")
            return
        st.session_state.cards_source_hash = source_hash
        st.session_state.cards_tables = tables
        st.session_state.cards_meta = meta
        st.session_state.cards_version = 0

    tables = st.session_state.cards_tables
    st.warning("Промените се пазят в текущата сесия. За трайно съхранение "
               "изтеглете актуализирания Excel и при следващото отваряне го заредете отново. "
               "Streamlit Secrets не се актуализира автоматично.")
    selected = st.selectbox("Горивна верига / лист", list(tables), key="cards_sheet")
    whole = tables[selected]
    if not len(whole.columns):
        st.info("В този лист няма таблица с колони.")
        return

    company = company_column(whole)
    left, middle, right = st.columns([2, 2, 1])
    with left:
        companies = sorted(str(v) for v in whole[company].unique() if str(v).strip()) if company else []
        chosen = st.multiselect("Филтър по фирми", companies, key=f"cards_companies_{selected}",
                                placeholder="Всички фирми") if company else []
    with middle:
        searchable = st.text_input("Търсене във всички колони", key=f"cards_search_{selected}",
                                   placeholder="Име, карта, МПС…")
    with right:
        ordering = st.selectbox("Подреждане", ["По оригинален ред", "Фирма А–Я", "Фирма Я–А"],
                                key=f"cards_order_{selected}", disabled=company is None)

    visible = whole.copy()
    if chosen and company:
        visible = visible.loc[visible[company].isin(chosen)]
    if searchable.strip():
        visible = visible.loc[visible.apply(
            lambda column: column.astype(str).str.contains(
                searchable.strip(), case=False, regex=False, na=False)).any(axis=1)]
    if company and ordering != "По оригинален ред":
        visible = visible.sort_values(company, ascending=ordering == "Фирма А–Я",
                                     kind="stable", key=lambda col: col.str.casefold())

    st.caption(f"Показани {len(visible)} от {len(whole)} записа. "
               "Двоен клик върху клетка за редакция. Промените се прилагат веднага в текущата сесия.")
    # The stable original index preserves row identity across sort/filter operations.
    edited = st.data_editor(
        visible, key=f"cards_editor_{selected}_{st.session_state.cards_version}",
        hide_index=True, use_container_width=True, height=550,
        num_rows="fixed", disabled=[CREATED, UPDATED],
        column_config={
            CREATED: st.column_config.TextColumn(CREATED, help="Дата на добавяне; старите записи нямат известна дата"),
            UPDATED: st.column_config.TextColumn(UPDATED, help="Дата на последната промяна"),
        },
    )
    editable_cols = [c for c in whole if c not in (CREATED, UPDATED)]
    changes = 0
    for index in visible.index:
        for col in editable_cols:
            new_value = str(edited.at[index, col] or "").strip()
            if "карт" in col.casefold() and "номер" in col.casefold():
                new_value = normalise_card(new_value)
            if new_value != str(whole.at[index, col]):
                whole.at[index, col] = new_value
                changes += 1
                whole.at[index, UPDATED] = datetime.now().astimezone().isoformat(timespec="seconds")
    if changes:
        st.session_state.cards_tables[selected] = whole
        st.toast(f"Записани {changes} промени в текущата сесия.")

    with st.expander("➕ Добави нов ред"):
        st.caption("Новият ред се добавя към избрания лист.")
        with st.form(f"cards_add_{selected}"):
            values = {}
            for col in editable_cols:
                values[col] = st.text_input(col, key=f"cards_add_field_{selected}_{col}")
            submitted = st.form_submit_button("Добави ред")
        if submitted:
            if not any(x.strip() for x in values.values()):
                st.warning("Попълнете поне едно поле.")
            else:
                now = datetime.now().astimezone().isoformat(timespec="seconds")
                row = {**values, CREATED: now, UPDATED: now}
                st.session_state.cards_tables[selected] = pd.concat(
                    [whole, pd.DataFrame([row])], ignore_index=True)
                st.session_state.cards_version += 1
                st.rerun()

    st.divider()
    full = workbook_bytes(st.session_state.cards_tables, st.session_state.cards_meta)
    st.download_button("⬇️ Изтегли целия редактиран Excel (всички листове)",
                       data=full, file_name="gorivni_karti_aktualizirani.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="cards_export_all")
    st.caption("Историческите дати на първоначално добавяне не съществуват в стария Excel. "
               "Не ги попълваме със случайни стойности. "
               "Файлът може да съдържа ПИН кодове — пазете го в защитено хранилище.")
