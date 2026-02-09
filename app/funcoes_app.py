import base64
import mysql.connector
import streamlit as st
import os

# Função para exibir PDF
def exibir_pdf_no_app(caminho_pdf, altura=1000):
    """Exibe o PDF renderizado na tela, usando a largura máxima do navegador."""
    with open(caminho_pdf, "rb") as pdf_file:
        base64_pdf = base64.b64encode(pdf_file.read()).decode("utf-8")
        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{altura}" type="application/pdf"></iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)

def exibir_imagem_no_app(caminho_imagem, largura="auto"):
    """
    Exibe uma imagem na área principal do app, usando st.image().
    
    Args:
        caminho_imagem (str): Caminho para o arquivo de imagem.
        largura (str ou int): Largura da exibição (como "auto" ou um valor em pixels, ex.: 600).
    """
    # Exibir a imagem diretamente com Streamlit
    st.image(caminho_imagem, use_column_width=(largura == "auto"))

# Função para conectar ao banco de dados
def conectar_banco():
    # Configurações do banco de dados
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="dbssd@#",
        database="ssd_db"
    )
    return conn

def menu_wps():
    # Conectar ao banco de dados
    conn = conectar_banco()
    cursor = conn.cursor()

    # Obter os WPs disponíveis
    cursor.execute("SELECT wp, menu FROM wps")
    wps_df = cursor.fetchall()
    wps_df = [{"wp": row[0], "menu": row[1]} for row in wps_df]

    # Converter para DataFrame para facilitar a manipulação
    import pandas as pd
    wps_df = pd.DataFrame(wps_df)

    # Criar uma lista de opções para o selectbox
    wp_options = wps_df['menu'].tolist()

    # Adicionar um selectbox na sidebar para escolher o WP
    selected_menu = st.sidebar.selectbox(
        "Escolha o Work Package:",
        options=wp_options,
        index=0  # Seleciona o primeiro item por padrão
    )

    # Obter o valor wp correspondente à opção selecionada
    selected_wp = wps_df[wps_df['menu'] == selected_menu]['wp'].values[0]
    
    return(int(selected_wp))
