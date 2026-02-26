import streamlit as st
import pandas as pd
import os
from datetime import datetime

# =========================
# CONFIGURAÇÕES
# =========================
st.set_page_config(page_title="Precificador 3D", layout="wide")

ENC = "utf-8-sig"
SEP = ";"

ARQ_IMPRESSORAS = "impressoras.csv"
ARQ_FILAMENTOS = "filamentos.csv"
ARQ_HISTORICO = "historico_precos.csv"
ARQ_VENDAS = "vendas.csv"
ARQ_ENCOMENDAS = "encomendas.csv"

# =========================
# FUNÇÕES UTILITÁRIAS
# =========================

def carregar_csv(arquivo, colunas):
    if os.path.exists(arquivo):
        df = pd.read_csv(arquivo, sep=SEP, encoding=ENC)
        for col in colunas:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=colunas)


def salvar_csv(df, arquivo):
    df.to_csv(arquivo, index=False, sep=SEP, encoding=ENC)

def carregar_vendas():
    colunas = [
        "ID",
        "Data",
        "Nome da Peça",
        "Cor",
        "Cliente",
        "Valor",
        "Forma de Pagamento",
        "Pago",
        "Custo",
        "Lucro"
    ]
    return carregar_csv(ARQ_VENDAS, colunas)

def carregar_encomendas():
    colunas = [
        "ID",
        "Data Registro",
        "Produto",
        "Quantidade",
        "Cores",
        "Prazo Entrega",
        "Link Arquivo",
        "Observacoes",
        "Imagem"
    ]
    return carregar_csv(ARQ_ENCOMENDAS, colunas)


# =========================
# SIDEBAR
# =========================

st.sidebar.title("⚙️ Menu")
menu = st.sidebar.radio(
    "Navegação",
    ["📦 Precificar", "🖨️ Impressoras", "🧵 Filamentos", "📊 Histórico", "📈 Dashboard", "💰 Vendas", "📝 Encomendas"]
)

# =========================
# IMPRESSORAS
# =========================

if menu == "🖨️ Impressoras":
    st.title("🖨️ Cadastro de Impressoras")

    colunas = ["Nome", "Consumo (kW)", "Custo Hora (R$)"]
    df = carregar_csv(ARQ_IMPRESSORAS, colunas)

    with st.form("form_impressoras", clear_on_submit=True):
        nome = st.text_input("Nome da Impressora")
        consumo = st.number_input("Consumo (kW)", min_value=0.0)
        custo_hora = st.number_input("Custo por Hora (R$)", min_value=0.0)

        submitted = st.form_submit_button("Salvar Impressora")

    if submitted:
        df.loc[len(df)] = [nome, consumo, custo_hora]
        salvar_csv(df, ARQ_IMPRESSORAS)
        st.success("Impressora cadastrada com sucesso!")

    st.dataframe(df, use_container_width=True)

# =========================
# FILAMENTOS
# =========================

elif menu == "🧵 Filamentos":
    st.title("🧵 Cadastro de Filamentos")

    colunas = ["Material", "Preço por Kg (R$)"]
    df = carregar_csv(ARQ_FILAMENTOS, colunas)

    with st.form("form_filamentos", clear_on_submit=True):
        material = st.text_input("Material (ex: PLA, PETG)")
        preco = st.number_input("Preço por Kg (R$)", min_value=0.0, step=0.01)

        submitted = st.form_submit_button("Salvar Filamento")

    if submitted:
        material = material.strip()

    if material == "":
        st.error("Informe o nome do material.")
    elif preco <= 0:
        st.error("Informe um preço maior que zero.")
    elif material in df["Material"].values:
        st.warning("Este filamento já está cadastrado.")
    else:
        df.loc[len(df)] = [material, preco]
        salvar_csv(df, ARQ_FILAMENTOS)
        st.success("Filamento cadastrado com sucesso!")


    st.divider()
    st.subheader("Filamentos Cadastrados")
    st.dataframe(df, use_container_width=True)



# =========================
# PRECIFICAÇÃO
# =========================

elif menu == "📦 Precificar":
    st.title("📦 Precificação de Produto")

    df_imp = carregar_csv(
        ARQ_IMPRESSORAS,
        ["Nome", "Consumo (kW)", "Custo Hora (R$)"]
    )

    df_fil = carregar_csv(
        ARQ_FILAMENTOS,
        ["Material", "Preço por Kg (R$)"]
    )

    df_hist = carregar_csv(
        ARQ_HISTORICO,
        [
            "Data",
            "Produto",
            "Impressora",
            "Filamento",
            "Peso (g)",
            "Tempo (h)",
            "Custo Total (R$)",
            "Preço Sugerido (R$)"
        ]
    )

    produto = st.text_input("Nome do Produto")
    impressora = st.selectbox("Impressora", df_imp["Nome"])
    filamento = st.selectbox("Filamento", df_fil["Material"])
    peso = st.number_input("Peso (g)", min_value=0.0)
    tempo = st.number_input("Tempo (h)", min_value=0.0)

    margem = st.number_input(
        "Margem de Lucro (%)",
        min_value=0.0,
        value=200.0,
        step=10.0
    )

    if st.button("Gerar Precificação"):
        custo_hora = float(
            df_imp[df_imp["Nome"] == impressora]["Custo Hora (R$)"].iloc[0]
        )
        preco_kg = float(
            df_fil[df_fil["Material"] == filamento]["Preço por Kg (R$)"].iloc[0]
        )

        custo_material = (peso / 1000) * preco_kg
        custo_maquina = tempo * custo_hora
        custo_total = round(custo_material + custo_maquina, 2)

        preco_sugerido = round(
            custo_total * (1 + margem / 100),
            2
        )

        st.success(f"Custo Total: R$ {custo_total}")
        st.info(f"Preço Sugerido: R$ {preco_sugerido}")

        df_hist.loc[len(df_hist)] = [
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            produto,
            impressora,
            filamento,
            peso,
            tempo,
            custo_total,
            preco_sugerido
        ]

        salvar_csv(df_hist, ARQ_HISTORICO)


# =========================
# HISTÓRICO
# =========================

elif menu == "📊 Histórico":
    st.title("📊 Histórico de Precificações")

    df = carregar_csv(
        ARQ_HISTORICO,
        [
            "Data",
            "Produto",
            "Impressora",
            "Filamento",
            "Peso (g)",
            "Tempo (h)",
            "Custo Total (R$)",
            "Preço Sugerido (R$)"
        ]
    )

    st.dataframe(df, use_container_width=True)

# =========================
# DASHBOARD
# =========================

elif menu == "📈 Dashboard":
    st.title("📈 Dashboard")

    df = carregar_csv(
        ARQ_HISTORICO,
        [
            "Data",
            "Produto",
            "Impressora",
            "Filamento",
            "Peso (g)",
            "Tempo (h)",
            "Custo Total (R$)",
            "Preço Sugerido (R$)"
        ]
    )

    if df.empty:
        st.warning("Nenhum dado disponível.")
    else:
        st.subheader("Preço Médio por Produto")
        st.bar_chart(
            df.groupby("Produto")["Preço Sugerido (R$)"].mean()
        )

# =========================
# VENDAS
# =========================
elif menu == "💰 Vendas":

    st.title("📦 Registro de Vendas")

    df_vendas = carregar_vendas()

    # ---------- SESSION STATE ----------
    if "nome_peca" not in st.session_state:
        st.session_state.nome_peca = ""
    if "cor" not in st.session_state:
        st.session_state.cor = ""
    if "cliente" not in st.session_state:
        st.session_state.cliente = ""
    if "valor" not in st.session_state:
        st.session_state.valor = 0.0
    if "custo" not in st.session_state:
        st.session_state.custo = 0.0

    with st.form("form_venda"):

        data = st.date_input("Data")

        nome_peca = st.text_input(
            "Nome da Peça",
            key="nome_peca"
        )

        cor = st.text_input(
            "Cor da Peça",
            key="cor"
        )

        cliente = st.text_input(
            "Cliente",
            key="cliente"
        )

        valor = st.number_input(
            "Valor (R$)",
            min_value=0.0,
            format="%.2f",
            key="valor"
        )

        custo = st.number_input(
            "Custo (R$)",
            min_value=0.0,
            format="%.2f",
            key="custo"
        )

        forma_pg = st.selectbox(
            "Forma de Pagamento",
            ["Pix", "Dinheiro", "Cartão Crédito", "Cartão Débito"]
        )

        pago = st.selectbox(
            "Está pago?",
            ["Sim", "Não"]
        )

        salvar = st.form_submit_button("Registrar Venda")

    # ---------- VALIDAÇÃO ----------
    if salvar:

        if (
            st.session_state.nome_peca.strip() == "" or
            st.session_state.cor.strip() == "" or
            st.session_state.cliente.strip() == "" or
            st.session_state.valor <= 0 or
            st.session_state.custo < 0
        ):
            st.error("Preencha todos os campos corretamente antes de registrar a venda.")

        else:
            novo_id = len(df_vendas) + 1
            lucro = st.session_state.valor - st.session_state.custo

            nova_venda = {
                "ID": novo_id,
                "Data": data,
                "Nome da Peça": st.session_state.nome_peca,
                "Cor": st.session_state.cor,
                "Cliente": st.session_state.cliente,
                "Valor": st.session_state.valor,
                "Forma de Pagamento": forma_pg,
                "Pago": pago,
                "Custo": st.session_state.custo,
                "Lucro": lucro
            }

            df_vendas = pd.concat(
                [df_vendas, pd.DataFrame([nova_venda])],
                ignore_index=True
            )

            salvar_csv(df_vendas, ARQ_VENDAS)

            st.success("Venda registrada com sucesso!")

            # LIMPA CAMPOS APÓS SALVAR
            st.session_state.nome_peca = ""
            st.session_state.cor = ""
            st.session_state.cliente = ""
            st.session_state.valor = 0.0
            st.session_state.custo = 0.0

    st.subheader("📋 Vendas Registradas")
    st.dataframe(df_vendas, use_container_width=True)

# =========================
# ENCOMENDAS
# =========================
elif menu == "📝 Encomendas":

    st.title("📝 Controle de Encomendas")

    df_enc = carregar_encomendas()

    with st.form("form_encomenda", clear_on_submit=True):

        produto = st.text_input("Nome do Produto")

        quantidade = st.number_input(
            "Quantidade",
            min_value=1,
            step=1
        )

        cores_disponiveis = [
            "Preto", "Branco", "Vermelho", "Azul",
            "Verde", "Amarelo", "Cinza", "Rosa",
            "Laranja", "Roxo"
        ]

        cores = st.multiselect(
            "Selecione as Cores",
            cores_disponiveis
        )

        prazo = st.date_input("Prazo de Entrega")

        link = st.text_input("Link do Arquivo")

        observacoes = st.text_area("Observações")

        imagem = st.file_uploader(
            "Upload de Foto/Print do Produto",
            type=["png", "jpg", "jpeg"]
        )

        salvar = st.form_submit_button("Registrar Encomenda")

    # ---------- VALIDAÇÃO ----------
    if salvar:

        if produto.strip() == "" or len(cores) == 0:
            st.error("Preencha pelo menos o nome do produto e selecione uma cor.")
        else:
            novo_id = len(df_enc) + 1

            nome_imagem = ""
            if imagem is not None:
                nome_imagem = f"imagem_{novo_id}.png"
                with open(nome_imagem, "wb") as f:
                    f.write(imagem.getbuffer())

            nova_encomenda = {
                "ID": novo_id,
                "Data Registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Produto": produto,
                "Quantidade": quantidade,
                "Cores": ", ".join(cores),
                "Prazo Entrega": prazo,
                "Link Arquivo": link,
                "Observacoes": observacoes,
                "Imagem": nome_imagem
            }

            df_enc = pd.concat(
                [df_enc, pd.DataFrame([nova_encomenda])],
                ignore_index=True
            )

            salvar_csv(df_enc, ARQ_ENCOMENDAS)

            st.success("Encomenda registrada com sucesso!")

            st.rerun()

    st.subheader("📋 Encomendas Registradas")
    st.dataframe(df_enc, use_container_width=True)

# python -m streamlit run app_precificador_3d.py
