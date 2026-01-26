import mysql.connector
import streamlit as st
import os
import base64
from PyPDF2 import PdfReader

def show():
    # Configurações do banco de dados
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "dbssd@#"
    MYSQL_DB = "db_ssd"
    
    # Função para conectar ao banco de dados
    def conectar_banco():
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        return conn
    
    # Busca os registros da tabela `wps`
    def buscar_reg_wp():
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_wp, wp, titulo, descricao, gerente, colaboradores FROM wps")
        wp = cursor.fetchall()
        conn.close()
        return wp

    reg_wp = buscar_reg_wp()
    
    if not reg_wp:
        st.warning("Nenhum registro encontrado no banco de dados.")
        return

    # Layout principal: margem, tabela e detalhes dos WPs
    margem, col_central, margem_final = st.columns([0.05, 0.9, 0.05])  # Área centralizada

    with col_central:
        st.subheader("Work Packages (WP)")
        st.write("Selecione um Work Package da lista para visualizar seus detalhes:")
        
        # Criar tabela e captar seleção
        wp_ids = [wp["id_wp"] for wp in reg_wp]  # Obtém IDs dos WPs
        wp_titulos = [f'ID {wp["id_wp"]}: {wp["titulo"]}' for wp in reg_wp]  # Exibe títulos numerados
        indice_selecionado = st.selectbox("Selecione o WP:", options=range(len(wp_ids)), format_func=lambda x: wp_titulos[x])
        
        # Identificar o registro selecionado
        wp_selecionado = reg_wp[indice_selecionado]
        
        # Exibição de detalhes do WP
        st.markdown("---")
        st.markdown(f"### {wp_selecionado['titulo']}")
        st.text_area("Descrição", wp_selecionado["descricao"], height=150, disabled=True)
        st.markdown("**Gerente do WP:** " + wp_selecionado["gerente"])
        st.markdown("**Colaboradores:** " + wp_selecionado["colaboradores"])