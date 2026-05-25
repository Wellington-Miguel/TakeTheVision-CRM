import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import re
from datetime import date, datetime

st.set_page_config(
    page_title="Take The Vision",
    page_icon="👁",
    layout="centered",
)


# ── Google Sheets connection ───────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLUNAS = [
    "id", "nome", "cpf", "telefone", "email", "nascimento", "endereco",
    "esf_od", "esf_oe", "cil_od", "cil_oe", "adicao", "tipo_lente", "criado_em",
]

@st.cache_resource(ttl=300)
def get_sheet():
    """Retorna a worksheet. Cache de 5 min para não abrir conexão a cada interação."""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open(st.secrets["google_sheets"]["sheet_name"])
    ws = spreadsheet.sheet1

    # Garante cabeçalho na primeira vez
    if ws.row_count == 0 or ws.cell(1, 1).value != "id":
        ws.clear()
        ws.append_row(COLUNAS)
    return ws

def load_data():
    try:
        ws = get_sheet()
        records = ws.get_all_records()
        return records
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

def save_row(row: dict):
    ws = get_sheet()
    ws.append_row([row.get(c, "") for c in COLUNAS])

# ── Helpers ────────────────────────────────────────────────────────────────────
def format_cpf(cpf):
    d = re.sub(r"\D", "", cpf)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else cpf

def format_phone(p):
    d = re.sub(r"\D", "", p)
    if len(d) == 11: return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10: return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return p

def valid_cpf(cpf):   return len(re.sub(r"\D", "", cpf)) == 11
def valid_email(e):   return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", e))

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-wrap">
    {EYE_SVG}
    <h1 class="hero-title">TAKE THE <span>VISION</span></h1>
    <p class="hero-sub">Gestão de clientes & receitas</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["NOVO CADASTRO", "CLIENTES"])

# ══════════════════════════════════════════════════════════
# TAB 1 — FORMULÁRIO
# ══════════════════════════════════════════════════════════
with tab1:
    with st.form("form", clear_on_submit=True):

        st.markdown('<div class="sec-label">Dados Pessoais</div>', unsafe_allow_html=True)

        nome = st.text_input("Nome completo", placeholder="Ex.: Maria da Silva")

        c1, c2 = st.columns(2)
        with c1: cpf = st.text_input("CPF", placeholder="000.000.000-00", max_chars=14)
        with c2: tel = st.text_input("Telefone / WhatsApp", placeholder="(71) 99999-9999", max_chars=15)

        c3, c4 = st.columns(2)
        with c3: email = st.text_input("E-mail", placeholder="cliente@email.com")
        with c4: nasc  = st.date_input("Data de Nascimento", value=None,
                                        min_value=date(1920,1,1), max_value=date.today(),
                                        format="DD/MM/YYYY")

        end = st.text_input("Endereço", placeholder="Rua, nº, bairro, cidade – UF")

        st.markdown('<div class="sec-label">Receita Oftalmológica</div>', unsafe_allow_html=True)

        c5, c6 = st.columns(2)
        with c5: esf_od = st.number_input("Esférico OD",  min_value=-30.0, max_value=30.0, step=0.25, format="%.2f")
        with c6: esf_oe = st.number_input("Esférico OE",  min_value=-30.0, max_value=30.0, step=0.25, format="%.2f")

        c7, c8 = st.columns(2)
        with c7: cil_od = st.number_input("Cilíndrico OD", min_value=-10.0, max_value=10.0, step=0.25, format="%.2f")
        with c8: cil_oe = st.number_input("Cilíndrico OE", min_value=-10.0, max_value=10.0, step=0.25, format="%.2f")

        c9, c10 = st.columns(2)
        with c9:  adicao = st.number_input("Adição", min_value=0.0, max_value=4.0, step=0.25, format="%.2f")
        with c10: lente  = st.selectbox("Tipo de Lente", [
            "— Selecione —","Monofocal","Bifocal","Progressiva",
            "Occupacional","Lente de Contato","Outro"])

        ok = st.form_submit_button("SALVAR CADASTRO")

    if ok:
        errs = []
        if not nome.strip():                  errs.append("Nome é obrigatório.")
        if cpf and not valid_cpf(cpf):        errs.append("CPF inválido.")
        if email and not valid_email(email):  errs.append("E-mail inválido.")
        if lente == "— Selecione —":          errs.append("Selecione o tipo de lente.")

        if errs:
            for e in errs: st.error(e)
        else:
            with st.spinner("Salvando no Google Sheets..."):
                try:
                    reg = {
                        "id":         datetime.now().strftime("%Y%m%d%H%M%S"),
                        "nome":       nome.strip(),
                        "cpf":        format_cpf(cpf) if cpf else "",
                        "telefone":   format_phone(tel) if tel else "",
                        "email":      email.strip(),
                        "nascimento": nasc.strftime("%d/%m/%Y") if nasc else "",
                        "endereco":   end.strip(),
                        "esf_od":     esf_od, "esf_oe": esf_oe,
                        "cil_od":     cil_od, "cil_oe": cil_oe,
                        "adicao":     adicao, "tipo_lente": lente,
                        "criado_em":  datetime.now().strftime("%d/%m/%Y %H:%M"),
                    }
                    save_row(reg)
                    st.cache_resource.clear()   # força reload na aba Clientes
                    st.success(f"✓  {nome} cadastrado com sucesso.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ══════════════════════════════════════════════════════════
# TAB 2 — LISTA
# ══════════════════════════════════════════════════════════
with tab2:
    if st.button("↺  Atualizar lista"):
        st.cache_resource.clear()

    data = load_data()
    if not data:
        st.markdown('<p style="color:#444;letter-spacing:.1em;font-size:.85rem;">NENHUM CLIENTE CADASTRADO.</p>',
                    unsafe_allow_html=True)
    else:
        busca = st.text_input("Buscar por nome ou CPF", placeholder="Digite para filtrar...")
        df = pd.DataFrame(data).rename(columns={
            "nome":"Nome","cpf":"CPF","telefone":"Telefone","email":"E-mail",
            "nascimento":"Nascimento","endereco":"Endereço",
            "esf_od":"Esf.OD","esf_oe":"Esf.OE","cil_od":"Cil.OD","cil_oe":"Cil.OE",
            "adicao":"Adição","tipo_lente":"Lente","criado_em":"Cadastrado em",
        })
        if busca:
            df = df[
                df["Nome"].str.contains(busca, case=False, na=False) |
                df["CPF"].str.contains(busca, case=False, na=False)
            ]
        st.caption(f"{len(df)} cliente(s)")
        st.dataframe(
            df[["Nome","CPF","Telefone","E-mail","Nascimento",
                "Esf.OD","Esf.OE","Cil.OD","Cil.OE","Adição","Lente","Cadastrado em"]],
            use_container_width=True, hide_index=True,
        )
        st.download_button(
            "⬇ Exportar CSV",
            df.to_csv(index=False).encode("utf-8"),
            "clientes_ttv.csv", "text/csv",
        )
