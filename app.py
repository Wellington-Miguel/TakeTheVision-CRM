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

# ── Google Sheets Connection ───────────────────────────────────────────────────
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
    """Retorna a worksheet do Google Sheets usando cache de 5 min."""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open(st.secrets["google_sheets"]["sheet_name"])
    ws = spreadsheet.sheet1

    if ws.row_count == 0 or ws.cell(1, 1).value != "id":
        ws.clear()
        ws.append_row(COLUNAS)
    return ws

def load_data():
    try:
        ws = get_sheet()
        return ws.get_all_records()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

def save_row(row: dict):
    ws = get_sheet()
    ws.append_row([row.get(c, "") for c in COLUNAS])

# ── Helpers de Validação e Formatação ──────────────────────────────────────────
def format_cpf(cpf):
    d = re.sub(r"\D", "", cpf)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else cpf

def format_phone(p):
    d = re.sub(r"\D", "", p)
    if len(d) == 11: return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10: return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return p

def valid_cpf(cpf):   
    return len(re.sub(r"\D", "", cpf)) == 11

def valid_email(e):   
    return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", e))

# ── Cabeçalho Clean ────────────────────────────────────────────────────────────
st.title("👁 TAKE THE VISION")
st.subheader("Gestão de Clientes")
st.caption("Armazenamento seguro")

# ── Abas de Navegação ──────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Novo Cadastro", "Lista de Clientes"])

# ══════════════════════════════════════════════════════════
# TAB 1 — FORMULÁRIO DE CADASTRO
# ══════════════════════════════════════════════════════════
with tab1:
    with st.form("form_cadastro", clear_on_submit=True):

        st.write("### Dados Pessoais")
        nome = st.text_input("Nome completo", placeholder="Ex.: Maria da Silva")

        c1, c2 = st.columns(2)
        with c1: 
            cpf = st.text_input("CPF", placeholder="000.000.000-00", max_chars=14)
        with c2: 
            tel = st.text_input("Telefone / WhatsApp", placeholder="(71) 99999-9999", max_chars=15)

        c3, c4 = st.columns(2)
        with c3: 
            email = st.text_input("E-mail", placeholder="cliente@email.com")
        with c4: 
            nasc = st.date_input("Data de Nascimento", value=None,
                                 min_value=date(1920, 1, 1), max_value=date.today(),
                                 format="DD/MM/YYYY")

        end = st.text_input("Endereço", placeholder="Rua, nº, bairro, cidade – UF")

        st.write("### Receita Oftalmológica (Dioptria)")
        c5, c6 = st.columns(2)
        with c5: 
            esf_od = st.number_input("Esférico OD", min_value=-30.0, max_value=30.0, step=0.25, format="%.2f")
        with c6: 
            esf_oe = st.number_input("Esférico OE", min_value=-30.0, max_value=30.0, step=0.25, format="%.2f")

        c7, c8 = st.columns(2)
        with c7: 
            cil_od = st.number_input("Cilíndrico OD", min_value=-10.0, max_value=10.0, step=0.25, format="%.2f")
        with c8: 
            cil_oe = st.number_input("Cilíndrico OE", min_value=-10.0, max_value=10.0, step=0.25, format="%.2f")

        c9, c10 = st.columns(2)
        with c9:  
            adicao = st.number_input("Adição", min_value=0.0, max_value=4.0, step=0.25, format="%.2f")
        with c10: 
            lente = st.selectbox("Tipo de Lente", [
                "— Selecione —", "Monofocal", "Bifocal", "Progressiva",
                "Occupacional", "Lente de Contato", "Outro"
            ])

        ok = st.form_submit_button("Salvar Cadastro")

    if ok:
        errs = []
        if not nome.strip():                  
            errs.append("Nome é obrigatório.")
        if cpf and not valid_cpf(cpf):        
            errs.append("CPF inválido.")
        if email and not valid_email(email):  
            errs.append("E-mail inválido.")
        if lente == "— Selecione —":          
            errs.append("Selecione o tipo de lente.")

        if errs:
            for e in errs: 
                st.error(e)
        else:
            with st.spinner("Salvando dados..."):
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
                    st.cache_resource.clear()   
                    st.success(f"✓ {nome} cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ══════════════════════════════════════════════════════════
# TAB 2 — LISTA DE CLIENTES CADASTRADOS (BUSCA ATUALIZADA)
# ══════════════════════════════════════════════════════════
with tab2:
    # Topo da seção de busca com botão de sincronização alinhado
    c_title, c_refresh = st.columns([4, 1])
    with c_title:
        st.write("### Consultar Clientes")
    with c_refresh:
        if st.button("↺ Atualizar", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

    data = load_data()
    
    if not data:
        st.info("Nenhum cliente cadastrado até o momento.")
    else:
        # Modificação solicitada: Campo focado estritamente na busca por nome
        busca_nome = st.text_input("🔍 Buscar cliente por nome", placeholder="Digite o nome completo ou parte dele...")
        
        # Mapeamento e renomeação de colunas do DataFrame
        df = pd.DataFrame(data).rename(columns={
            "nome": "Nome", "cpf": "CPF", "telefone": "Telefone", "email": "E-mail",
            "nascimento": "Nascimento", "endereco": "Endereço",
            "esf_od": "Esf. OD", "esf_oe": "Esf. OE", "cil_od": "Cil. OD", "cil_oe": "Cil. OE",
            "adicao": "Adição", "tipo_lente": "Lente", "criado_em": "Cadastrado em",
        })
        
        # Aplicação do filtro por nome
        if busca_nome:
            df = df[df["Nome"].str.contains(busca_nome, case=False, na=False)]
            
        # Ordena os clientes em ordem alfabética para facilitar a leitura
        df = df.sort_values(by="Nome")
        
        st.caption(f"Exibindo {len(df)} cliente(s)")
        
        # Exibição otimizada na tabela
        st.dataframe(
            df[["Nome", "CPF", "Telefone", "E-mail", "Nascimento",
                "Esf. OD", "Esf. OE", "Cil. OD", "Cil. OE", "Adição", "Lente", "Cadastrado em"]],
            use_container_width=True, 
            hide_index=True,
        )
        
        # Ações secundárias agrupadas abaixo da tabela
        st.download_button(
            "⬇ Exportar Planilha (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            "clientes_take_the_vision.csv", 
            "text/csv",
        )