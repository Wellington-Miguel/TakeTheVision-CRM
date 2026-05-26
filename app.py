import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import re
from datetime import date, datetime

# Configuração da página limpa e profissional
st.set_page_config(
    page_title="Take The Vision",
    page_icon="👁",
    layout="centered",
)

# ── SISTEMA DE AUTENTICAÇÃO (LOGIN) ──────────────────────────────────────────
def check_password():
    """Retorna True se o usuário inseriu as credenciais corretas."""
    def password_entered():
        """Verifica se as credenciais digitadas batem com o secrets."""
        if (
            st.session_state["username"] == st.secrets["credentials"]["username"]
            and st.session_state["password"] == st.secrets["credentials"]["password"]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Remove a senha da memória por segurança
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("👁 TAKE THE VISION")
        st.subheader("Acesso Restrito")
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", key="password")
        st.button("Entrar", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.title("👁 TAKE THE VISION")
        st.subheader("Acesso Restrito")
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", key="password")
        st.button("Entrar", on_click=password_entered)
        st.error("❌ Usuário ou senha incorretos.")
        return False
    else:
        return True

# Se a verificação falhar, o script para aqui e não carrega o resto do app
if check_password():

    # ── Botão de Logout no topo da página de forma discreta ───────────────────
    col_space, col_logout = st.columns([4, 1])
    with col_logout:
        if st.button("Sair (Logout)", use_container_width=True):
            del st.session_state["password_correct"]
            st.rerun()

    # ── Google Sheets Connection ───────────────────────────────────────────────
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    COLUNAS = [
        "id", "nome", "cpf", "telefone", "email", "nascimento", "endereco",
        "esf_od", "esf_oe", "cil_od", "cil_oe", "eixo_od", "eixo_oe", 
        "dnp_od", "dnp_oe", "co_od", "co_oe", "adicao", "tipo_lente", "criado_em"
    ]

    @st.cache_resource(ttl=300)
    def get_sheet():
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

    # FUNÇÃO ATUALIZADA: Blindada contra cabeçalhos fantasmas ou vazios no Sheets
    def load_data():
        try:
            ws = get_sheet()
            # Força o gspread a usar estritamente a nossa lista COLUNAS como chaves.
            # Isso ignora qualquer coluna em branco à direita que gerava o erro.
            return ws.get_all_records(expected_headers=COLUNAS)
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return []

    def save_row(row: dict):
        ws = get_sheet()
        ws.append_row([row.get(c, "") for c in COLUNAS])

    # ── Helpers de Validação e Formatação ──────────────────────────────────────
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

    # ── Cabeçalho Clean ────────────────────────────────────────────────────────
    st.title("👁 TAKE THE VISION")
    st.subheader("Gestão de Clientes")
    st.caption("Painel Autenticado de Forma Segura")

    # ── Abas de Navegação ──────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["Novo Cadastro", "Lista de Clientes"])

    # ══════════════════════════════════════════════════════════
    # TAB 1 — FORMULÁRIO DE CADASTRO
    # ══════════════════════════════════════════════════════════
    with tab1:
        with st.form("form_cadastro", clear_on_submit=True):
            st.write("### Dados Pessoais")
            nome = st.text_input("Nome completo", placeholder="Ex.: Maria da Silva")

            c1, c2 = st.columns(2)
            with c1: cpf = st.text_input("CPF", placeholder="000.000.000-00", max_chars=14)
            with c2: tel = st.text_input("Telefone / WhatsApp", placeholder="(71) 99999-9999", max_chars=15)

            c3, c4 = st.columns(2)
            with c3: email = st.text_input("E-mail", placeholder="cliente@email.com")
            with c4: nasc = st.date_input("Data de Nascimento", value=None,
                                         min_value=date(1920, 1, 1), max_value=date.today(),
                                         format="DD/MM/YYYY")

            end = st.text_input("Endereço", placeholder="Rua, nº, bairro, cidade – UF")

            st.write("### Receita Oftalmológica (Dioptria)")
            c5, c6 = st.columns(2)
            with c5: esf_od = st.number_input("Esférico OD", min_value=-30.0, max_value=30.0, step=0.25, format="%.2f")
            with c6: esf_oe = st.number_input("Esférico OE", min_value=-30.0, max_value=30.0, step=0.25, format="%.2f")

            c_cil_od, c_eixo_od = st.columns(2)
            with c_cil_od: cil_od = st.number_input("Cilíndrico OD", min_value=-10.0, max_value=10.0, step=0.25, format="%.2f")
            with c_eixo_od: eixo_od = st.number_input("Eixo OD (°)", min_value=0, max_value=180, step=1, value=0)

            c_cil_oe, c_eixo_oe = st.columns(2)
            with c_cil_oe: cil_oe = st.number_input("Cilíndrico OE", min_value=-10.0, max_value=10.0, step=0.25, format="%.2f")
            with c_eixo_oe: eixo_oe = st.number_input("Eixo OE (°)", min_value=0, max_value=180, step=1, value=0)

            c_dnp_od, c_dnp_oe = st.columns(2)
            with c_dnp_od: dnp_od = st.number_input("DNP OD (mm)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f")
            with c_dnp_oe: dnp_oe = st.number_input("DNP OE (mm)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f")

            c_co_od, c_co_oe = st.columns(2)
            with c_co_od: co_od = st.number_input("CO OD (mm)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f")
            with c_co_oe: co_oe = st.number_input("CO OE (mm)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f")

            c9, c10 = st.columns(2)
            with c9: adicao = st.number_input("Adição", min_value=0.0, max_value=4.0, step=0.25, format="%.2f")
            with c10: lente = st.text_input("Tipo de Lente", placeholder="Ex.: Policarbonato Antirreflexo")

            ok = st.form_submit_button("Salvar Cadastro")

        if ok:
            errs = []
            if not nome.strip(): errs.append("Nome é obrigatório.")
            if cpf and not valid_cpf(cpf): errs.append("CPF inválido.")
            if email and not valid_email(email): errs.append("E-mail inválido.")

            if errs:
                for e in errs: st.error(e)
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
                            "eixo_od":    int(eixo_od), "eixo_oe": int(eixo_oe),
                            "dnp_od":     dnp_od, "dnp_oe": dnp_oe,
                            "co_od":      co_od, "co_oe": co_oe,
                            "adicao":     adicao, "tipo_lente": lente.strip() if lente else "",
                            "criado_em":  datetime.now().strftime("%d/%m/%Y %H:%M"),
                        }
                        save_row(reg)
                        st.cache_resource.clear()   
                        st.success(f"✓ {nome} cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # ══════════════════════════════════════════════════════════
    # TAB 2 — LISTA DE CLIENTES CADASTRADOS
    # ══════════════════════════════════════════════════════════
    with tab2:
        col_title, col_refresh = st.columns([4, 1])
        with col_title: st.write("### Consultar Clientes")
        with col_refresh:
            if st.button("↺ Atualizar", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()

        data = load_data()
        busca_nome = st.text_input("🔍 Buscar cliente por nome", placeholder="Digite o nome completo ou parte dele...")
        
        if not data:
            st.info("Nenhum cliente cadastrado na base de dados geral.")
        else:
            df = pd.DataFrame(data).rename(columns={
                "nome": "Nome", "cpf": "CPF", "telefone": "Telefone", "email": "E-mail",
                "nascimento": "Nascimento", "endereco": "Endereço",
                "esf_od": "Esf. OD", "esf_oe": "Esf. OE", "cil_od": "Cil. OD", "cil_oe": "Cil. OE",
                "eixo_od": "Eixo OD", "eixo_oe": "Eixo OE",
                "dnp_od": "DNP OD", "dnp_oe": "DNP OE", "co_od": "CO OD", "co_oe": "CO OE",
                "adicao": "Adição", "tipo_lente": "Lente", "criado_em": "Cadastrado em",
            })
            
            if busca_nome:
                df = df[df["Nome"].str.contains(busca_nome, case=False, na=False)]
                
            df = df.sort_values(by="Nome")
            
            if df.empty:
                st.warning(f"Nenhum cliente encontrado com o nome '{busca_nome}'.")
            else:
                st.caption(f"Exibindo {len(df)} cliente(s)")
                st.dataframe(
                    df[["Nome", "CPF", "Telefone", "E-mail", "Nascimento",
                        "Esf. OD", "Esf. OE", "Cil. OD", "Eixo OD", "Cil. OE", "Eixo OE", 
                        "DNP OD", "DNP OE", "CO OD", "CO OE", "Adição", "Lente", "Cadastrado em"]],
                    use_container_width=True, 
                    hide_index=True,
                )
                st.download_button(
                    "⬇ Exportar Planilha (CSV)",
                    df.to_csv(index=False).encode("utf-8"),
                    "clientes_take_the_vision.csv", "text/csv",
                )