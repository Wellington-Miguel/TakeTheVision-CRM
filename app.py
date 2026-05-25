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

# ── CSS (identidade visual inalterada) ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background: #000 !important; }
.stApp { background: #000 !important; }

.hero-wrap { text-align: center; padding: 3rem 1rem 2rem; }
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(3rem, 10vw, 6.5rem);
    color: #f5f0ea; letter-spacing: 0.04em; line-height: 0.9; margin: 0;
}
.hero-title span {
    background: conic-gradient(#ff6b6b,#ff9f43,#ffd32a,#0be881,#00d2d3,#54a0ff,#9c88ff,#fd79a8,#ff6b6b);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-eye { display: block; width: 64px; height: 64px; margin: 1rem auto 0.5rem; }
.hero-sub { font-size: 0.7rem; font-weight: 300; letter-spacing: 0.35em; text-transform: uppercase; color: #555; margin-top: 0.5rem; }

.sec-label {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.3rem; letter-spacing: 0.18em;
    color: #f5f0ea; margin: 2.5rem 0 1rem;
    display: flex; align-items: center; gap: 12px;
}
.sec-label::after { content:''; flex:1; height:1px; background: linear-gradient(90deg, rgba(245,240,234,0.4), transparent); }

.stTextInput > label, .stSelectbox > label, .stDateInput > label, .stNumberInput > label {
    color: #555 !important; font-size: 0.7rem !important; font-weight: 500 !important;
    letter-spacing: 0.15em !important; text-transform: uppercase !important;
}

.stTextInput > div > div > input {
    background: #0d0d0d !important; border: 1px solid #222 !important;
    border-radius: 4px !important; color: #f5f0ea !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.95rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #f5f0ea !important; box-shadow: none !important; background: #111 !important;
}
.stNumberInput > div > div > input {
    background: #0d0d0d !important; border: 1px solid #222 !important;
    border-radius: 4px !important; color: #f5f0ea !important;
}
.stSelectbox > div > div {
    background: #0d0d0d !important; border: 1px solid #222 !important;
    border-radius: 4px !important; color: #f5f0ea !important;
}
.stDateInput > div > div > input {
    background: #0d0d0d !important; border: 1px solid #222 !important;
    border-radius: 4px !important; color: #f5f0ea !important;
}

.stButton > button {
    width: 100%; background: #f5f0ea !important; color: #000 !important;
    font-family: 'Bebas Neue', sans-serif !important; font-size: 1.2rem !important;
    letter-spacing: 0.25em !important; border: none !important; border-radius: 4px !important;
    padding: 0.8rem 2rem !important; margin-top: 1.5rem !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #000 !important; color: #f5f0ea !important;
    border: 1px solid #f5f0ea !important; transform: translateY(-1px) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #0d0d0d; border-radius: 4px; border: 1px solid #1a1a1a; padding: 4px; gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Bebas Neue', sans-serif !important; font-size: 1rem !important;
    letter-spacing: 0.2em !important; color: #444 !important; border-radius: 3px !important;
}
.stTabs [aria-selected="true"] { background: #f5f0ea !important; color: #000 !important; }

.stDownloadButton > button {
    background: transparent !important; color: #555 !important; border: 1px solid #222 !important;
    font-size: 0.8rem !important; letter-spacing: 0.1em !important; border-radius: 4px !important;
}
.stDownloadButton > button:hover { color: #f5f0ea !important; border-color: #f5f0ea !important; }

input, textarea, select { color-scheme: dark; }

.stSuccess { background: #0d1a0d !important; border: 1px solid #1a3a1a !important; border-radius: 4px !important; }
.stError   { background: #1a0d0d !important; border: 1px solid #3a1a1a !important; border-radius: 4px !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #000; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── SVG eye ────────────────────────────────────────────────────────────────────
EYE_SVG = """
<svg class="hero-eye" viewBox="0 0 64 40" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="iris" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="#fff"/>
      <stop offset="18%"  stop-color="#fff" stop-opacity="0.9"/>
      <stop offset="28%"  stop-color="#9c88ff"/>
      <stop offset="42%"  stop-color="#54a0ff"/>
      <stop offset="55%"  stop-color="#0be881"/>
      <stop offset="68%"  stop-color="#ffd32a"/>
      <stop offset="80%"  stop-color="#ff9f43"/>
      <stop offset="92%"  stop-color="#ff6b6b"/>
      <stop offset="100%" stop-color="#fd79a8"/>
    </radialGradient>
    <clipPath id="eyeClip"><ellipse cx="32" cy="20" rx="31" ry="18"/></clipPath>
  </defs>
  <ellipse cx="32" cy="20" rx="31" ry="18" fill="#0d0d0d" stroke="#333" stroke-width="0.5"/>
  <circle cx="32" cy="20" r="13" fill="url(#iris)" clip-path="url(#eyeClip)"/>
  <circle cx="32" cy="20" r="5" fill="#000"/>
  <circle cx="36" cy="16" r="2.5" fill="white" opacity="0.6"/>
  <path d="M1 20 Q32 2 63 20" fill="none" stroke="#000" stroke-width="6"/>
  <path d="M1 20 Q32 38 63 20" fill="none" stroke="#000" stroke-width="4"/>
</svg>
"""

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
