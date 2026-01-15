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


# =========================
# SIDEBAR
# =========================

st.sidebar.title("⚙️ Menu")
menu = st.sidebar.radio(
    "Navegação",
    ["📦 Precificar", "🖨️ Impressoras", "🧵 Filamentos", "📊 Histórico", "📈 Dashboard"]
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
