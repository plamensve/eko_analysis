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
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

WORKBOOK = Path(__file__).resolve().parent / "data" / "Еко_Списък_фирми.xlsx"
CREATED = "Добавен на"
UPDATED = "Последна промяна"
ROW_COLOR = "Цвят на реда"
COLORS = {
    "Без цвят": "",
    "Червено": "#FFD1D1",
    "Оранжево": "#FFE0B2",
    "Жълто": "#FFF2A8",
    "Зелено": "#C9F2CD",
    "Синьо": "#CFE5FF",
    "Лилаво": "#E4D5FF",
    "Розово": "#FFD4EC",
    "Тюркоазено": "#BDF1EF",
    "Кафяво": "#E2C9B2",
    "Сиво": "#DADFE5",
    "Черно": "#202A37",
    "Бяло": "#FFFFFF",
}


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
    if ROW_COLOR not in df:
        df[ROW_COLOR] = ""
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
    from openpyxl.styles import PatternFill
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
            if ROW_COLOR in frame.columns:
                for row_num, color in enumerate(frame[ROW_COLOR].tolist(), start=startrow + 2):
                    if color in COLORS.values() and color:
                        fill = PatternFill(fill_type="solid", fgColor=color.lstrip("#"))
                        for cell in sheet[row_num]:
                            cell.fill = fill
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

    # Column management is scoped to the selected worksheet only.
    with st.expander("⚙️ Управление на колоните — добавяне и премахване"):
        col_add, col_remove = st.columns(2)
        with col_add:
            st.markdown("**➕ Нова колона**")
            with st.form(f"cards_new_column_{selected}", clear_on_submit=True):
                new_name = st.text_input("Име на колоната", max_chars=100)
                default_value = st.text_input("Начална стойност за всички редове (по избор)")
                add_column = st.form_submit_button("Добави колона", use_container_width=True)
            if add_column:
                new_name = new_name.strip()
                if not new_name:
                    st.error("Въведи име за новата колона.")
                elif new_name.casefold() in {name.casefold() for name in whole.columns}:
                    st.error("Вече съществува колона с това име.")
                else:
                    # Put user columns before the read-only audit timestamps.
                    position = len(whole.columns) - sum(
                        label in whole.columns for label in (CREATED, UPDATED)
                    )
                    whole.insert(position, new_name, default_value)
                    st.session_state.cards_tables[selected] = whole
                    st.session_state.cards_version += 1
                    st.rerun()
        with col_remove:
            st.markdown("**🗑️ Премахване на колона**")
            removable = [name for name in whole.columns if name not in (CREATED, UPDATED, ROW_COLOR)]
            if removable:
                with st.form(f"cards_delete_column_{selected}"):
                    delete_name = st.selectbox("Колона за премахване", removable)
                    confirm_delete = st.checkbox("Потвърждавам изтриването на колоната и всички стойности в нея")
                    delete_column = st.form_submit_button(
                        "Премахни колоната", type="secondary", use_container_width=True
                    )
                if delete_column:
                    if not confirm_delete:
                        st.error("Потвърди изтриването преди да продължиш.")
                    else:
                        st.session_state.cards_tables[selected] = whole.drop(columns=[delete_name])
                        st.session_state.cards_version += 1
                        st.rerun()
            else:
                st.info("Няма потребителски колони за премахване.")
        st.caption("Колоните „Добавен на“ и „Последна промяна“ са защитени. "
                   "Промените засягат само избрания лист и влизат в Excel експорта.")

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
               "Десен бутон върху ред → Оцветяване. "
               "Двоен клик върху клетка → редакция.")
    # Native AG Grid context menus require an Enterprise module. This custom
    # DOM menu uses Community APIs and therefore requires no paid license.
    palette_js = JsCode("""
    function(params) {
        if (!params || !params.node || !params.node.data) return;
        const ev = params.event;
        if (ev && ev.preventDefault) ev.preventDefault();
        document.querySelectorAll('.cards-row-context').forEach(x => x.remove());
        const palette = [
            ['Без цвят',''],['Червено','#FFD1D1'],['Оранжево','#FFE0B2'],
            ['Жълто','#FFF2A8'],['Зелено','#C9F2CD'],['Синьо','#CFE5FF'],
            ['Лилаво','#E4D5FF'],['Розово','#FFD4EC'],['Тюркоазено','#BDF1EF'],
            ['Кафяво','#E2C9B2'],['Сиво','#DADFE5'],['Черно','#202A37'],
            ['Бяло','#FFFFFF']
        ];
        const menu = document.createElement('div');
        menu.className = 'cards-row-context';
        menu.style.cssText = 'position:fixed;z-index:2147483600;background:#102438;' +
            'color:#fff;border:1px solid #47647f;box-shadow:0 12px 30px #0008;' +
            'padding:12px;border-radius:12px;min-width:240px;max-width:270px;';
        const title = document.createElement('div');
        title.textContent = '🎨 Оцветяване на реда';
        title.style.cssText = 'font-size:13px;font-weight:700;margin-bottom:9px;';
        menu.appendChild(title);
        const paletteBox = document.createElement('div');
        paletteBox.style.cssText = 'display:grid;grid-template-columns:repeat(4,1fr);gap:7px;';
        palette.forEach(([name,hex]) => {
            const option = document.createElement('button');
            option.type = 'button';
            option.title = name;
            option.setAttribute('aria-label', name);
            option.style.cssText = 'width:44px;height:34px;border-radius:7px;cursor:pointer;' +
                'border:1px solid #6984a0;background:' + (hex || '#132f46') +
                ';color:' + (hex === '#202A37' || !hex ? '#fff' : '#17233b') + ';';
            option.textContent = hex ? '●' : '×';
            option.onclick = (e) => {
                e.stopPropagation();
                const timestamp = new Date().toISOString();
                params.node.setDataValue('Цвят на реда', hex);
                params.node.setDataValue('Последна промяна', timestamp);
                params.api.refreshCells({rowNodes:[params.node],force:true});
                menu.remove();
            };
            paletteBox.appendChild(option);
        });
        menu.appendChild(paletteBox);
        const note = document.createElement('div');
        note.textContent = 'Посочи квадратче, за да видиш цвета.';
        note.style.cssText = 'font-size:11px;color:#c9d9eb;margin-top:9px;';
        menu.appendChild(note);
        document.body.appendChild(menu);
        const x = ev && ev.clientX !== undefined ? ev.clientX : 30;
        const y = ev && ev.clientY !== undefined ? ev.clientY : 30;
        menu.style.left = Math.max(5, Math.min(x, innerWidth - menu.offsetWidth - 8)) + 'px';
        menu.style.top = Math.max(5, Math.min(y, innerHeight - menu.offsetHeight - 8)) + 'px';
        const close = (event) => {
            if (!menu.contains(event.target)) {
                menu.remove();
                document.removeEventListener('pointerdown', close, true);
            }
        };
        setTimeout(() => document.addEventListener('pointerdown', close, true), 0);
    }
    """)
    row_style_js = JsCode("""
    function(params) {
        const color = (params.data && params.data['Цвят на реда']) || '';
        const allowed = ['#FFD1D1','#FFE0B2','#FFF2A8','#C9F2CD','#CFE5FF',
                         '#E4D5FF','#FFD4EC','#BDF1EF','#E2C9B2','#DADFE5',
                         '#202A37','#FFFFFF'];
        if (allowed.includes(color)) {
            return {backgroundColor:color,
                    color: color === '#202A37' ? '#FFFFFF' : '#17233b'};
        }
        return undefined;
    }
    """)
    display = visible.copy()
    display['_row_id'] = display.index.astype(int)
    grid = GridOptionsBuilder.from_dataframe(display)
    grid.configure_default_column(editable=True, sortable=True, filter=True,
                                  resizable=True, minWidth=135)
    for readonly in (CREATED, UPDATED, ROW_COLOR, '_row_id'):
        grid.configure_column(readonly, editable=False, hide=(readonly in (ROW_COLOR, '_row_id')))
    options = grid.build()
    options['onCellContextMenu'] = palette_js
    options['getRowStyle'] = row_style_js
    options['getRowId'] = JsCode("function(p) {return String(p.data._row_id);}")
    options['suppressContextMenu'] = True
    response = AgGrid(
        display, gridOptions=options, key=f"cards_grid_{selected}_{st.session_state.cards_version}",
        allow_unsafe_jscode=True, enable_enterprise_modules=False,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
        try_to_convert_back_to_original_types=False,
        height=550, theme='streamlit',
    )
    edited = pd.DataFrame(response['data'])
    # Persist by stable source row id, even when the grid is sorted or filtered.
    changes = 0
    if '_row_id' in edited.columns:
        for _, row in edited.iterrows():
            idx = int(row['_row_id'])
            if idx not in whole.index:
                continue
            for col in whole.columns:
                if col in (CREATED, UPDATED) or col not in row:
                    continue
                raw = row[col]
                new_value = '' if pd.isna(raw) else str(raw).strip()
                if 'карт' in col.casefold() and 'номер' in col.casefold():
                    new_value = normalise_card(new_value)
                if new_value != str(whole.at[idx, col]):
                    whole.at[idx, col] = new_value
                    changes += 1
                    whole.at[idx, UPDATED] = datetime.now(
                        ZoneInfo('Europe/Sofia')).isoformat(timespec='seconds')
    if changes:
        st.session_state.cards_tables[selected] = whole

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
                now = datetime.now(ZoneInfo("Europe/Sofia")).isoformat(timespec="seconds")
                row = {**values, CREATED: now, UPDATED: now, ROW_COLOR: ""}
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
