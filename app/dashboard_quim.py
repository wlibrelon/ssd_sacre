# import streamlit as st
# import pandas as pd
# import mysql.connector
# import matplotlib.pyplot as plt
# import seaborn as sns
# from funcoes_app import conectar_banco


# # Função para carregar dados do banco
# def carregar_dados(query):
#     conexao = conectar_banco()
#     try:
#         df = pd.read_sql(query, conexao)
#         return df
#     finally:
#         conexao.close()

# # Configuração principal do Streamlit
# st.title("Dashboard de Resultados Químicos")
# st.sidebar.title("Filtros do Dashboard")

# # Configurar os filtros no sidebar
# tipo_resultado = st.sidebar.multiselect("Tipo de Resultado", options=["Solos", "Águas", "Outros"], default=["Solos"])
# parametros = st.sidebar.text_input("Parâmetro (Digite para Filtrar, ex: pH, N, etc.)")
# intervalo_data = st.sidebar.date_input("Intervalo de Data", [])

# # Construir a query SQL com base nos filtros
# query = "SELECT * FROM resultados_quim WHERE 1=1"
# if tipo_resultado:
#     tipos = "', '".join(tipo_resultado)
#     query += f" AND tipo_resultado IN ('{tipos}')"
# if parametros:
#     query += f" AND parametro LIKE '%{parametros}%'"
# if len(intervalo_data) == 2:  # Verifica se o intervalo foi fornecido
#     data_inicio, data_fim = intervalo_data
#     query += f" AND data BETWEEN '{data_inicio}' AND '{data_fim}'"

# # Carregar dados com base na query
# dados = carregar_dados(query)

# # Mostrar os dados filtrados como tabela
# st.subheader("Tabela de Resultados Filtrados")
# st.dataframe(dados)

# # Verificar se há dados para exibir gráficos
# if not dados.empty:
#     # **Gráficos**

#     # 1. Gráfico de barras: Contagem por Tipo de Resultado
#     st.subheader("Gráfico de Barras por Tipo de Resultado")
#     fig, ax = plt.subplots()
#     sns.countplot(data=dados, x="tipo_resultado", palette="viridis", ax=ax)
#     ax.set_title("Distribuição por Tipo de Resultado")
#     ax.set_xlabel("Tipo de Resultado")
#     ax.set_ylabel("Contagem")
#     st.pyplot(fig)

#     # 2. Gráfico de linha: Evolução temporal do Resultado
#     st.subheader("Evolução Temporal dos Resultados")
#     if "data" in dados.columns and not dados["data"].isnull().values.all():
#         dados['data'] = pd.to_datetime(dados['data'])
#         dados = dados.sort_values(by="data")
#         fig, ax = plt.subplots(figsize=(10, 5))
#         for parametro in dados["parametro"].unique():
#             subset = dados[dados["parametro"] == parametro]
#             ax.plot(subset["data"], subset["resultado"], label=parametro)
#         ax.set_title("Evolução Temporal dos Resultados por Parâmetro")
#         ax.set_xlabel("Data")
#         ax.set_ylabel("Resultado")
#         ax.legend()
#         st.pyplot(fig)

#     # 3. Gráfico de dispersão: Resultado vs Profundidade
#     st.subheader("Gráfico de Dispersão: Resultado vs Profundidade")
#     if "profund_inicial_solo" in dados.columns and "profund_final_solo" in dados.columns:
#         fig, ax = plt.subplots()
#         sns.scatterplot(
#             data=dados,
#             x="profund_inicial_solo",
#             y="resultado",
#             hue="parametro",
#             palette="deep",
#             ax=ax
#         )
#         ax.set_title("Resultado vs Profundidade Inicial do Solo")
#         ax.set_xlabel("Profundidade Inicial (cm)")
#         ax.set_ylabel("Resultado")
#         st.pyplot(fig)
# else:
#     st.warning("Nenhum dado encontrado com os filtros aplicados.")

import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns
from funcoes_app import conectar_banco

# Encapsular a lógica principal em uma função `show`
def show():
    # Função para carregar dados do banco
    @st.cache_data(ttl=600)  # Cache para evitar recarregamento desnecessário em cada interação
    def carregar_dados(query):
        conexao = conectar_banco()
        try:
            df = pd.read_sql(query, conexao)
            return df
        finally:
            conexao.close()

    # Configuração principal do Streamlit
    st.title("Dashboard de Resultados Químicos")
    st.sidebar.title("Filtros do Dashboard")

    # Filtros no sidebar: Tipo de Resultado
    tipo_resultado = st.sidebar.multiselect(
        "Tipo de Resultado", 
        options=["Solo", "Agua", "Outros"], 
        default=["Solo"], 
        key="filtro_tipo_resultado"
    )

    # Filtros no sidebar: Parâmetros
    parametros = st.sidebar.text_input(
        "Parâmetro (Digite para Filtrar, ex: pH, N, etc.)", 
        key="filtro_parametros"
    )

    # Filtros no sidebar: Intervalo de Data
    intervalo_data = st.sidebar.date_input(
        "Intervalo de Data", 
        key="filtro_intervalo_data"
    )

    # Construir a query SQL com base nos filtros
    query = "SELECT * FROM resultados_quim WHERE 1=1"

    # Filtro: Tipo de Resultado
    if tipo_resultado:
        tipos = "', '".join(tipo_resultado)
        query += f" AND tipo_resultado IN ('{tipos}')"

    # Filtro: Parâmetros
    if parametros:
        query += f" AND parametro LIKE '%{parametros}%'"

    # Filtro: Intervalo de Data
    if isinstance(intervalo_data, list) and len(intervalo_data) == 2:  # Verifica se é um intervalo (lista com 2 valores)
        data_inicio, data_fim = intervalo_data
        query += f" AND data BETWEEN '{data_inicio}' AND '{data_fim}'"
    elif isinstance(intervalo_data, pd.Timestamp):  # Trata caso seja uma única data
        query += f" AND data = '{intervalo_data}'"

    # Carregar dados com base na query
    dados = carregar_dados(query)

    # Mostrar os dados filtrados como tabela
    st.subheader("Tabela de Resultados Filtrados")
    if not dados.empty:
        st.dataframe(dados)
    else:
        st.warning("Nenhum dado encontrado com os filtros aplicados.")
        return  # Parar execução se não houver dados para gráficos

    # **Gráficos**

    # 1. Gráfico de Barras por Tipo de Resultado
    st.subheader("Gráfico de Barras por Tipo de Resultado")
    fig, ax = plt.subplots()
    sns.countplot(data=dados, x="tipo_resultado", palette="viridis", ax=ax)
    ax.set_title("Distribuição por Tipo de Resultado")
    ax.set_xlabel("Tipo de Resultado")
    ax.set_ylabel("Contagem")
    st.pyplot(fig)

    # 2. Gráfico de Linha: Evolução Temporal do Resultado
    st.subheader("Evolução Temporal dos Resultados")
    if "data" in dados.columns and dados["data"].notnull().all():
        dados['data'] = pd.to_datetime(dados['data'])
        dados = dados.sort_values(by="data")
        fig, ax = plt.subplots(figsize=(10, 5))
        for parametro in dados["parametro"].unique():
            subset = dados[dados["parametro"] == parametro]
            ax.plot(subset["data"], subset["resultado"], label=parametro)
        ax.set_title("Evolução Temporal dos Resultados por Parâmetro")
        ax.set_xlabel("Data")
        ax.set_ylabel("Resultado")
        ax.legend()
        st.pyplot(fig)

    # 3. Gráfico de Dispersão: Resultado vs Profundidade Inicial
    st.subheader("Gráfico de Dispersão: Resultado vs Profundidade")
    if "profund_inicial_solo" in dados.columns and "profund_final_solo" in dados.columns:
        fig, ax = plt.subplots()
        sns.scatterplot(
            data=dados,
            x="profund_inicial_solo",
            y="resultado",
            hue="parametro",
            palette="deep",
            ax=ax
        )
        ax.set_title("Resultado vs Profundidade Inicial do Solo")
        ax.set_xlabel("Profundidade Inicial (cm)")
        ax.set_ylabel("Resultado")
        st.pyplot(fig)