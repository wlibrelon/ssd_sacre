import streamlit as st
from funcoes_app import exibir_imagem_no_app, conectar_banco 

def show():
    st.header("Projeto SACRE")

    # st.image("images/logo_sacre.png", width=500, use_column_width=True)
    # st.image("images/logo_sacre.png", width=500, use_container_width=True)
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO wps (wp, titulo, descricao, gerente, colaboradores, menu) VALUES (%s, %s, %s, %s, %s, %s)",
        (7, 'titulo', 'descricao', 'gerente', 'colaboradores', 'menu')
    )
    conn.commit()
    conn.close()
    