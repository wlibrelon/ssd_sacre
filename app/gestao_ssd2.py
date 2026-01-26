import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from streamlit_option_menu import option_menu
from funcoes_app import conectar_banco, menu_wps

def show():
    """
    Exibição principal para gerenciamento de Work Packages e Projetos 
    com persistência de estado e atualização dinâmica.
    """
    with st.sidebar:
        st.title("Gerenciamento SSD")
        st.subheader("Manutenção de Dados")

        if st.button("Work Packages"):
            st.session_state["menu_selected"] = "work_packages"
            st.session_state["operation"] = None  

        if st.button("Projetos dos WPs"):
            st.session_state["menu_selected"] = "projetos_wp"
            st.session_state["operation"] = None  

    if "menu_selected" not in st.session_state:
        return

    ######################################
    # Gerenciamento de Work Packages
    if st.session_state.get("menu_selected") == "work_packages":
        st.title("Gerenciamento de Work Packages")

        @st.cache_data
        def load_wps():
            try:
                conn = conectar_banco()
                query = "SELECT wp, titulo, descricao, gerente, colaboradores, menu FROM wps ORDER BY wp"
                df = pd.read_sql(query, conn)
                conn.close()
                return df
            except Exception as e:
                st.error(f"Erro ao carregar Work Packages do banco: {e}")
                return pd.DataFrame()

        wps_df = load_wps()

        if wps_df.empty:
            st.warning("⚠️ Nenhum Work Package disponível no banco de dados.")
        else:
            exibir_work_packages(wps_df)

    ######################################
    # Gerenciamento de Projetos dos Work Packages
    elif st.session_state.get("menu_selected") == "projetos_wp":
        st.title("Projetos dos Work Packages")

        @st.cache_data
        def load_wps():
            try:
                conn = conectar_banco()
                query = "SELECT wp, titulo FROM wps ORDER BY wp"
                df = pd.read_sql(query, conn)
                conn.close()
                return df
            except Exception as e:
                st.error(f"Erro ao carregar Work Packages do banco: {e}")
                return pd.DataFrame()

        @st.cache_data
        def load_proj_wps(wp_selecionado):
            try:
                conn = conectar_banco()
                query = "SELECT id_wp, titulo, autor, resumo, objetivos FROM projetos_wps WHERE id_wp = %s"
                df = pd.read_sql_query(query, conn, params=(wp_selecionado,))
                conn.close()
                return df
            except Exception as e:
                st.error(f"Erro ao carregar Projetos dos Work Packages do banco: {e}")
                return pd.DataFrame()

        # Carregar os Work Packages
        wps_df = load_wps()
        if wps_df.empty:
            st.warning("⚠️ Nenhum Work Package encontrado no banco de dados.")
            return

        # Seleção do WP
        wp_selecionado = st.selectbox(
            "Selecione um Work Package para visualizar os projetos:",
            options=wps_df["wp"].tolist(),
            format_func=lambda x: f"WP {x} | {wps_df[wps_df['wp'] == x]['titulo'].values[0]}"
        )

        if wp_selecionado:
            st.session_state["wp_selecionado"] = wp_selecionado

        if "wp_selecionado" in st.session_state:
            projetos_df = load_proj_wps(st.session_state["wp_selecionado"])

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader(f"Projetos no Work Package {st.session_state['wp_selecionado']}")
                if projetos_df.empty:
                    st.warning("⚠️ Nenhum projeto encontrado para este WP.")
                else:
                    st.dataframe(projetos_df, height=400, hide_index=True)

                st.write("Gerenciamento de Projetos:")
                colbtn1, colbtn2, colbtn3 = st.columns(3)
                with colbtn1:
                    if st.button("➕ Incluir Projeto", key="incluir_projeto"):
                        st.session_state["operation_proj"] = "incluir"
                with colbtn2:
                    if st.button("✏️ Alterar Projeto", key="alterar_projeto") and not projetos_df.empty:
                        st.session_state["operation_proj"] = "alterar"
                with colbtn3:
                    if st.button("❌ Excluir Projeto", key="excluir_projeto") and not projetos_df.empty:
                        st.session_state["operation_proj"] = "excluir"

            with col2:
                if "operation_proj" in st.session_state:
                    if st.session_state["operation_proj"] == "incluir":
                        incluir_projeto(wp_selecionado)
                    elif st.session_state["operation_proj"] == "alterar":
                        alterar_projeto(wp_selecionado, projetos_df)
                    elif st.session_state["operation_proj"] == "excluir":
                        excluir_projeto(wp_selecionado, projetos_df)
                        
# ----------------------------------------
def incluir_projeto(wp_selecionado):
    st.write("### Incluir um novo projeto")
    titulo = st.text_input("Título do projeto:")
    autor = st.text_input("Autor:")
    resumo = st.text_area("Resumo:")
    objetivos = st.text_area("Objetivos:")

    if st.button("Salvar Novo Projeto", key="salvar_inclusao"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()
            query = "INSERT INTO projetos_wps (id_wp, titulo, autor, resumo, objetivos) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (wp_selecionado, titulo, autor, resumo, objetivos))
            conn.commit()
            conn.close()

            st.cache_data.clear()
            st.success("✅ Projeto incluído com sucesso!")

        except Exception as e:
            st.error(f"Erro ao incluir projeto: {e}")

# ----------------------------------------
def alterar_projeto(wp_selecionado, projetos_df):
    st.write("### Alterar Projeto Existente")

    projeto_titulo = st.selectbox("Selecione o projeto:", projetos_df["titulo"].tolist())
    projeto = projetos_df[projetos_df["titulo"] == projeto_titulo].iloc[0]

    novo_titulo = st.text_input("Título:", projeto["titulo"])
    novo_autor = st.text_input("Autor:", projeto["autor"])
    novo_resumo = st.text_area("Resumo:", projeto["resumo"])
    novos_objetivos = st.text_area("Objetivos:", projeto["objetivos"])

    if st.button("Salvar Alterações", key="salvar_alteracao"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()
            query = """
                UPDATE projetos_wps SET titulo = %s, autor = %s, resumo = %s, objetivos = %s
                WHERE id_wp = %s AND titulo = %s
            """
            cursor.execute(query, (novo_titulo, novo_autor, novo_resumo, novos_objetivos, wp_selecionado, projeto_titulo))
            conn.commit()
            conn.close()

            st.cache_data.clear()
            st.success("✅ Projeto alterado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao alterar projeto: {e}")

# ----------------------------------------
def excluir_projeto(wp_selecionado, projetos_df):
    st.write("### Excluir Projeto")

    projeto_selecionado = st.selectbox("Selecione o projeto para excluir:", projetos_df["titulo"].tolist())

    if st.button("Confirmar Exclusão", key="confirmar_exclusao"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()
            query = "DELETE FROM projetos_wps WHERE id_wp = %s AND titulo = %s"
            cursor.execute(query, (wp_selecionado, projeto_selecionado))
            conn.commit()
            conn.close()

            st.cache_data.clear()
            st.success("✅ Projeto excluído com sucesso!")
        except Exception as e:
            st.error(f"Erro ao excluir projeto: {e}")


def exibir_work_packages(wps_df):
    """
    Exibe a lista de Work Packages e as opções de gerenciamento (Incluir, Alterar, Excluir)
    em duas colunas.
    """
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Lista de Work Packages")
        st.dataframe(wps_df, height=400, hide_index=True)

        st.write("Gerenciamento de Work Packages:")
        colbtn1, colbtn2, colbtn3 = st.columns([1, 1, 1])

        with colbtn1:
            if st.button("➕ Incluir"):
                st.session_state["wp_action"] = "incluir"
        with colbtn2:
            if st.button("✏️ Alterar"):
                st.session_state["wp_action"] = "alterar"
        with colbtn3:
            if st.button("❌ Excluir"):
                st.session_state["wp_action"] = "excluir"

    with col2:
        if "wp_action" in st.session_state:
            if st.session_state["wp_action"] == "incluir":
                incluir_wp()

            elif st.session_state["wp_action"] == "alterar":
                alterar_wp(wps_df)

            elif st.session_state["wp_action"] == "excluir":
                excluir_wp(wps_df)

def exibir_projetos_wp(proj_wps_df):
    """
    Exibe a lista de projetos Work Packages e as opções de gerenciamento (Incluir, Alterar, Excluir)
    em duas colunas.
    """
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Lista de Projetos do Work Package")
        st.dataframe(proj_wps_df, height=400, hide_index=True)

        st.write("Gerenciamento de Projetos Work Package:")
        colbtn1, colbtn2, colbtn3 = st.columns([1, 1, 1])  

        with colbtn1:
            if st.button("➕ Incluir"):
                st.session_state["wp_action"] = "incluir"
        with colbtn2:
            if st.button("✏️ Alterar"):
                st.session_state["wp_action"] = "alterar"
        with colbtn3:
            if st.button("❌ Excluir"):
                st.session_state["wp_action"] = "excluir"

    with col2:
        if "wp_action" in st.session_state:
            if st.session_state["wp_action"] == "incluir":
                incluir_wp()

            elif st.session_state["wp_action"] == "alterar":
                alterar_wp(wps_df)

            elif st.session_state["wp_action"] == "excluir":
                excluir_wp(wps_df)

############## Funções de Inclusão/Alteração/Exclusão ##############

def incluir_wp():
    """Função para criar um Work Package novo."""
    st.subheader("➕ Incluir Novo Work Package")
    with st.form("form_incluir_wp"):
        wp = st.number_input("Número do WP", min_value=1, step=1)
        titulo = st.text_input("Título")
        descricao = st.text_area("Descrição")
        gerente = st.text_input("Gerente Responsável")
        colaboradores = st.text_input("Colaboradores")
        menu = st.text_input("Texto no Menu")
        salvar = st.form_submit_button("💾 Salvar")

        if salvar:
            try:
                conn = conectar_banco()
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO wps (wp, titulo, descricao, gerente, colaboradores, menu)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (wp, titulo, descricao, gerente, colaboradores, menu)
                )
                conn.commit()
                st.success(f"✅ WP {wp} incluído com sucesso!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro ao incluir Work Package: {e}")
            finally:
                conn.close()


def alterar_wp(wps_df):
    """Função para alterar um Work Package existente."""
    st.subheader("✏️ Alterar Work Package")
    wp_escolhido = st.selectbox("Escolha o WP para alteração:", wps_df["titulo"].tolist())
    wp_atual = wps_df[wps_df["titulo"] == wp_escolhido].iloc[0]

    with st.form("form_alterar_wp"):
        titulo = st.text_input("Título", wp_atual["titulo"])
        descricao = st.text_area("Descrição", wp_atual["descricao"])
        gerente = st.text_input("Gerente", wp_atual["gerente"])
        colaboradores = st.text_input("Colaboradores", wp_atual["colaboradores"])
        salvar = st.form_submit_button("💾 Salvar Alterações")

        if salvar:
            try:
                conn = conectar_banco()
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE wps SET titulo=%s, descricao=%s, gerente=%s,
                    colaboradores=%s WHERE wp=%s
                    """,
                    (titulo, descricao, gerente, colaboradores, wp_escolhido)
                )
                conn.commit()
                st.success(f"✅ WP {wp_escolhido} alterado com sucesso!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro ao alterar Work Package: {e}")
            finally:
                conn.close()


def excluir_wp(wps_df):
    """Função para excluir um Work Package existente."""
    st.subheader("❌ Excluir Work Package")
    wp_escolhido = st.selectbox("Escolha o WP para exclusão:", wps_df["wp"].tolist())

    if st.button("Confirmar Exclusão"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM wps WHERE wp=%s", (wp_escolhido,))
            conn.commit()
            st.success(f"✅ WP {wp_escolhido} excluído com sucesso!")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro ao excluir Work Package: {e}")
        finally:
            conn.close()

