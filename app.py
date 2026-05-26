import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import re
from datetime import date, datetime

# ── CONFIGURAÇÃO DA PÁGINA ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Take The Vision",
    page_icon="👁",
    layout="wide",
)

# ── SISTEMA DE AUTENTICAÇÃO (LOGIN) ──────────────────────────────────────────
def check_password():
    """Retorna True se o utilizador inseriu as credenciais corretas."""
    def password_entered():
        if (
            st.session_state["username"] == st.secrets["credentials"]["username"]
            and st.session_state["password"] == st.secrets["credentials"]["password"]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown('<div class="hero-wrap"><h1 class="hero-title">TAKE THE VISION</h1></div>', unsafe_allow_html=True)
        st.subheader("Acesso Restrito")
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", key="password")
        st.button("Entrar", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.markdown('<div class="hero-wrap"><h1 class="hero-title">TAKE THE VISION</h1></div>', unsafe_allow_html=True)
        st.subheader("Acesso Restrito")
        st.text_input("Utilizador", key="username")
        st.text_input("Senha", type="password", key="password")
        st.button("Entrar", on_click=password_entered)
        st.error("❌ Usuário ou senha incorretos.")
        return False
    else:
        return True

# ── LISTA DE ESTADOS BRASILEIROS ─────────────────────────────────────────────
ESTADOS_BR = [
    "", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ",
    "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]

# O resto do sistema só roda se passar na barreira do login
if check_password():
    # Botão Discreto de Logout no Topo
    col_space, col_logout = st.columns([4, 1])
    with col_logout:
        if st.button("Sair", use_container_width=True):
            del st.session_state["password_correct"]
            st.rerun()

    # ── GOOGLE SHEETS CONNECTION ───────────────────────────────────────────────
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Estrutura oficial de colunas (28 campos)
    COLUNAS = [
        "id", "nome", "genero", "cpf", "telefone", "email", "nascimento",
        "rua", "estado", "cidade",
        "esf_od", "esf_oe", "cil_od", "cil_oe", "eixo_od", "eixo_oe",
        "dnp_od", "dnp_oe", "co_od", "co_oe", "adicao", "tipo_lente",
        "tipo_produto", "data_compra", "valor_compra",
        "criado_em"
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

        primeira_linha = ws.row_values(1) if ws.row_count > 0 else []
        if not primeira_linha or len(primeira_linha) != len(COLUNAS):
            if ws.row_count == 0:
                ws.append_row(COLUNAS)
            else:
                for i, col in enumerate(COLUNAS, start=1):
                    ws.update_cell(1, i, col)
        return ws

    def load_data():
        try:
            ws = get_sheet()
            return ws.get_all_records(expected_headers=COLUNAS)
        except Exception as e:
            st.error(f"Erro ao carregar dados da planilha: {e}")
            return []

    def save_row(row: dict):
        ws = get_sheet()
        ws.append_row([row.get(c, "") for c in COLUNAS])

    # ── HELPERS DE VALIDAÇÃO E FORMATAÇÃO ──────────────────────────────────────
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

    # ── CABEÇALHO DO PAINEL ────────────────────────────────────────────────────
    st.title("👁 TAKE THE VISION")
    st.subheader("Gestão de Clientes")
    st.caption("Painel Autenticado de Forma Segura")

    # ── ABAS DE NAVEGAÇÃO ──────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["Novo Cadastro", "Lista de Clientes"])

    # ══════════════════════════════════════════════════════════
    # TAB 1 — FORMULÁRIO DE CADASTRO
    # ══════════════════════════════════════════════════════════
    with tab1:
        with st.form("form_cadastro", clear_on_submit=True):

            # ── DADOS PESSOAIS ────────────────────────────────
            st.write("### Dados Pessoais")
            nome = st.text_input("Nome completo", placeholder="Ex.: Maria da Silva")

            c1, c2 = st.columns(2)
            with c1: cpf = st.text_input("CPF", placeholder="000.000.000-00", max_chars=14)
            with c2: tel = st.text_input("Telefone / WhatsApp", placeholder="(71) 99999-9999", max_chars=15)

            c3, c4 = st.columns(2)
            with c3: email = st.text_input("E-mail", placeholder="cliente@email.com")
            with c4: nasc = st.date_input(
                "Data de Nascimento", value=None,
                min_value=date(1920, 1, 1), max_value=date.today(),
                format="DD/MM/YYYY"
            )

            c_gen, _ = st.columns(2)
            with c_gen:
                genero = st.selectbox(
                    "Gênero",
                    options=[
                        "",
                        "Homem Cisgênero",
                        "Mulher Cisgênero",
                        "Homem Transgênero",
                        "Mulher Transgênero",
                        "Não-Binário",
                        "Bigênero",
                    ]
                )

            # ── LOCALIZAÇÃO (RUA / CIDADE / ESTADO) ──────────
            st.write("### Localização")
            rua = st.text_input("Rua / Endereço", placeholder="Ex.: Rua das Flores, 123, Bairro")

            c_est, c_cid = st.columns(2)
            with c_est:
                estado = st.selectbox("Estado (UF)", options=ESTADOS_BR)
            with c_cid:
                cidade = st.text_input("Cidade", placeholder="Ex.: Salvador")

            # ── RECEITA OFTALMOLÓGICA ─────────────────────────
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
            with c_dnp_od: dnp_od = st.number_input("DNP OD (mm)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f", help="Distância Nasopupilar - Olho Direito")
            with c_dnp_oe: dnp_oe = st.number_input("DNP OE (mm)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f", help="Distância Nasopupilar - Olho Esquerdo")

            c_co_od, c_co_oe = st.columns(2)
            with c_co_od: co_od = st.number_input("CO OD (mm)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f", help="Centro Óptico - Olho Direito")
            with c_co_oe: co_oe = st.number_input("CO OE (mm)", min_value=0.0, max_value=50.0, step=0.5, format="%.1f", help="Centro Óptico - Olho Esquerdo")

            c9, c10 = st.columns(2)
            with c9: adicao = st.number_input("Adição", min_value=0.0, max_value=4.0, step=0.25, format="%.2f")
            with c10: lente = st.text_input("Tipo de Lente", placeholder="Ex.: Policarbonato Antirreflexo")

            # ── DADOS DA COMPRA ───────────────────────────────
            st.write("### Dados da Compra")

            c_tp, c_dc = st.columns(2)
            with c_tp:
                tipo_produto = st.selectbox(
                    "Tipo de Produto",
                    options=["", "Grau", "Solar"]
                )
            with c_dc:
                data_compra = st.date_input(
                    "Data da Compra",
                    value=date.today(),
                    min_value=date(2000, 1, 1),
                    max_value=date.today(),
                    format="DD/MM/YYYY"
                )

            c_val, _ = st.columns(2)
            with c_val:
                valor_compra = st.number_input(
                    "Valor da Compra (R$)",
                    min_value=0.0,
                    max_value=100000.0,
                    step=0.01,
                    format="%.2f"
                )

            ok = st.form_submit_button("Salvar Cadastro")

        if ok:
            errs = []
            if not nome.strip(): errs.append("Nome é obrigatório.")
            if cpf and not valid_cpf(cpf): errs.append("CPF inválido.")
            if email and not valid_email(email): errs.append("E-mail inválido.")
            if not estado: errs.append("Estado é obrigatório.")
            if not cidade.strip(): errs.append("Cidade é obrigatória.")

            if errs:
                for e in errs: st.error(e)
            else:
                with st.spinner("A guardar dados..."):
                    try:
                        reg = {
                            "id":           datetime.now().strftime("%Y%m%d%H%M%S"),
                            "nome":         nome.strip(),
                            "genero":       genero,
                            "cpf":          format_cpf(cpf) if cpf else "",
                            "telefone":     format_phone(tel) if tel else "",
                            "email":        email.strip(),
                            "nascimento":   nasc.strftime("%d/%m/%Y") if nasc else "",
                            "rua":          rua.strip(),
                            "estado":       estado,
                            "cidade":       cidade.strip(),
                            "esf_od":       esf_od,     "esf_oe":  esf_oe,
                            "cil_od":       cil_od,     "cil_oe":  cil_oe,
                            "eixo_od":      int(eixo_od), "eixo_oe": int(eixo_oe),
                            "dnp_od":       dnp_od,     "dnp_oe":  dnp_oe,
                            "co_od":        co_od,      "co_oe":   co_oe,
                            "adicao":       adicao,
                            "tipo_lente":   lente.strip() if lente else "",
                            "tipo_produto": tipo_produto,
                            "data_compra":  data_compra.strftime("%d/%m/%Y") if data_compra else "",
                            "valor_compra": f"{valor_compra:.2f}",
                            "criado_em":    datetime.now().strftime("%d/%m/%Y %H:%M"),
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
        col_title, col_refresh = st.columns([6, 1])
        with col_title: st.write("### Consultar Clientes")
        with col_refresh:
            if st.button("↺ Atualizar", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()

        data = load_data()

        # ── FILTROS ───────────────────────────────────────────
        busca = st.text_input("🔍 Buscar por nome, CPF ou cidade", placeholder="Digite para filtrar...")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_produto = st.selectbox("Tipo de Produto", options=["Todos", "Grau", "Solar"])
        with col_f2:
            filtro_genero = st.selectbox("Gênero", options=[
                "Todos", "Homem Cisgênero", "Mulher Cisgênero",
                "Homem Transgênero", "Mulher Transgênero",
                "Não-Binário", "Bigênero"
            ])
        with col_f3:
            filtro_estado = st.selectbox("Estado (UF)", options=["Todos"] + [e for e in ESTADOS_BR if e])

        col_f4, col_f5 = st.columns(2)
        with col_f4:
            filtro_data_ini = st.date_input(
                "Data da Compra — De", value=None,
                min_value=date(2000, 1, 1), max_value=date.today(),
                format="DD/MM/YYYY",
            )
        with col_f5:
            filtro_data_fim = st.date_input(
                "Data da Compra — Até", value=None,
                min_value=date(2000, 1, 1), max_value=date.today(),
                format="DD/MM/YYYY",
            )

        if not data:
            st.info("Nenhum cliente cadastrado na base de dados.")
        else:
            df = pd.DataFrame(data).rename(columns={
                "nome":         "Nome",
                "genero":       "Gênero",
                "cpf":          "CPF",
                "telefone":     "Telefone",
                "email":        "E-mail",
                "nascimento":   "Nascimento",
                "rua":          "Rua / Endereço",
                "estado":       "Estado",
                "cidade":       "Cidade",
                "esf_od":       "Esf. OD",   "esf_oe":  "Esf. OE",
                "cil_od":       "Cil. OD",   "cil_oe":  "Cil. OE",
                "eixo_od":      "Eixo OD",   "eixo_oe": "Eixo OE",
                "dnp_od":       "DNP OD",    "dnp_oe":  "DNP OE",
                "co_od":        "CO OD",     "co_oe":   "CO OE",
                "adicao":       "Adição",
                "tipo_lente":   "Lente",
                "tipo_produto": "Produto",
                "data_compra":  "Data Compra",
                "valor_compra": "Valor (R$)",
                "criado_em":    "Cadastrado em",
            })

            # Aplicar filtros
            if busca:
                df = df[
                    df["Nome"].str.contains(busca, case=False, na=False) |
                    df["CPF"].str.contains(busca, case=False, na=False) |
                    df["Cidade"].str.contains(busca, case=False, na=False)
                ]
            if filtro_produto != "Todos":
                df = df[df["Produto"].str.contains(filtro_produto, case=False, na=False)]
            if filtro_genero != "Todos":
                df = df[df["Gênero"].str.contains(filtro_genero, case=False, na=False)]
            if filtro_estado != "Todos":
                df = df[df["Estado"] == filtro_estado]
            if filtro_data_ini or filtro_data_fim:
                def parse_date(s):
                    try:
                        return datetime.strptime(str(s), "%d/%m/%Y").date()
                    except Exception:
                        return None
                df["_dt"] = df["Data Compra"].apply(parse_date)
                if filtro_data_ini:
                    df = df[df["_dt"].apply(lambda d: d >= filtro_data_ini if d else False)]
                if filtro_data_fim:
                    df = df[df["_dt"].apply(lambda d: d <= filtro_data_fim if d else False)]
                df = df.drop(columns=["_dt"])

            df = df.sort_values(by="Nome")

            if df.empty:
                st.warning("Nenhum cliente encontrado com os filtros aplicados.")
            else:
                # ── MÉTRICAS RÁPIDAS ──────────────────────────────
                total = len(df)
                try:
                    valor_total = df["Valor (R$)"].apply(
                        lambda x: float(str(x).replace(",", ".")) if x not in ("", None) else 0.0
                    ).sum()
                    ticket_medio = valor_total / total if total > 0 else 0.0
                except Exception:
                    valor_total = ticket_medio = 0.0

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total de clientes", total)
                m2.metric("Faturamento filtrado", f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                m3.metric("Ticket médio", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                grau_count = df[df["Produto"].str.lower() == "grau"].shape[0]
                solar_count = df[df["Produto"].str.lower() == "solar"].shape[0]
                m4.metric("Grau / Solar", f"{grau_count} / {solar_count}")

                st.divider()
                st.caption(f"Exibindo {total} cliente(s)")

                # ── TABELA PRINCIPAL ──────────────────────────────
                # Separar em dois grupos de colunas para melhor legibilidade
                st.write("**Dados Pessoais & Compra**")
                st.dataframe(
                    df[[
                        "Nome", "Gênero", "CPF", "Telefone", "E-mail",
                        "Nascimento", "Estado", "Cidade",
                        "Produto", "Data Compra", "Valor (R$)", "Cadastrado em"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Nome":          st.column_config.TextColumn(width="medium"),
                        "Gênero":        st.column_config.TextColumn(width="medium"),
                        "CPF":           st.column_config.TextColumn(width="small"),
                        "Telefone":      st.column_config.TextColumn(width="small"),
                        "E-mail":        st.column_config.TextColumn(width="medium"),
                        "Nascimento":    st.column_config.TextColumn(width="small"),
                        "Estado":        st.column_config.TextColumn(width="small"),
                        "Cidade":        st.column_config.TextColumn(width="small"),
                        "Produto":       st.column_config.TextColumn(width="small"),
                        "Data Compra":   st.column_config.TextColumn(width="small"),
                        "Valor (R$)":    st.column_config.TextColumn(width="small"),
                        "Cadastrado em": st.column_config.TextColumn(width="small"),
                    },
                )

                st.write("**Receita Oftalmológica**")
                st.dataframe(
                    df[[
                        "Nome",
                        "Esf. OD", "Esf. OE",
                        "Cil. OD", "Eixo OD",
                        "Cil. OE", "Eixo OE",
                        "DNP OD", "DNP OE",
                        "CO OD",  "CO OE",
                        "Adição", "Lente",
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Nome": st.column_config.TextColumn(width="medium"),
                    },
                )

                st.divider()
                st.download_button(
                    "⬇ Exportar Planilha Completa (CSV)",
                    df[[
                        "Nome", "Gênero", "CPF", "Telefone", "E-mail", "Nascimento",
                        "Rua / Endereço", "Estado", "Cidade",
                        "Esf. OD", "Esf. OE", "Cil. OD", "Eixo OD", "Cil. OE", "Eixo OE",
                        "DNP OD", "DNP OE", "CO OD", "CO OE", "Adição", "Lente",
                        "Produto", "Data Compra", "Valor (R$)", "Cadastrado em"
                    ]].to_csv(index=False).encode("utf-8"),
                    "clientes_take_the_vision.csv",
                    "text/csv",
                )
