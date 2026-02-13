import streamlit as st
import pandas as pd
from funcoes_app import conectar_banco


def show():
    """
    Exibição principal para gerenciamento de Colaboradores
    com persistência de estado e atualização dinâmica.
    """
    st.title("Gerenciamento de Colaboradores")

    @st.cache_data
    def load_colaboradores():
        try:
            conn = conectar_banco()
            query = "SELECT id_colaborador, nome, link_internet, formacao FROM colaboradores ORDER BY nome"
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar Colaboradores do banco: {e}")
            return pd.DataFrame()

    colaboradores_df = load_colaboradores()

    # Se a tabela está vazia
    if colaboradores_df.empty:
        st.warning("⚠️ Nenhum Colaborador disponível no banco de dados.")
        st.info("ℹ️ Clique no botão abaixo para incluir o primeiro colaborador.")
        
        if st.button("➕ Incluir Primeiro Colaborador", key="btn_primeiro_colab"):
            st.session_state["colab_action"] = "incluir"
            st.rerun()
    else:
        # Se há colaboradores, exibir a lista e opções
        exibir_colaboradores(colaboradores_df)

    # Renderizar operações (FORA das colunas)
    if "colab_action" in st.session_state:
        st.divider()
        if st.session_state["colab_action"] == "incluir":
            incluir_colaborador()
        elif st.session_state["colab_action"] == "alterar":
            alterar_colaborador(colaboradores_df)
        elif st.session_state["colab_action"] == "excluir":
            excluir_colaborador(colaboradores_df)


def exibir_colaboradores(colaboradores_df):
    """
    Exibe a lista de Colaboradores e as opções de gerenciamento (Incluir, Alterar, Excluir)
    em duas colunas.
    """
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Lista de Colaboradores")
        st.dataframe(colaboradores_df, height=400, hide_index=True)

        st.write("**Gerenciamento de Colaboradores:**")
        colbtn1, colbtn2, colbtn3 = st.columns([1, 1, 1])

        with colbtn1:
            if st.button("➕ Incluir", key="btn_incluir_colab"):
                st.session_state["colab_action"] = "incluir"
                st.rerun()
        with colbtn2:
            if st.button("✏️ Alterar", key="btn_alterar_colab"):
                st.session_state["colab_action"] = "alterar"
                st.rerun()
        with colbtn3:
            if st.button("❌ Excluir", key="btn_excluir_colab"):
                st.session_state["colab_action"] = "excluir"
                st.rerun()

    with col2:
        st.subheader("ℹ️ Informações")
        st.info(f"Total de colaboradores: {len(colaboradores_df)}")


def incluir_colaborador():
    """Função para criar um Colaborador novo."""
    st.subheader("➕ Incluir Novo Colaborador")
    
    with st.form("form_incluir_colaborador", clear_on_submit=True):
        nome = st.text_input("Nome do Colaborador *", placeholder="Digite o nome completo")
        link_internet = st.text_input("Link Internet (opcional)", placeholder="https://exemplo.com")
        formacao = st.text_input("Formação (opcional)", placeholder="Ex: Engenheiro Ambiental")
        salvar = st.form_submit_button("💾 Salvar Colaborador")

        if salvar:
            if not nome or nome.strip() == "":
                st.error("❌ O nome do colaborador é obrigatório.")
                return
            
            try:
                conn = conectar_banco()
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO colaboradores (nome, link_internet, formacao)
                    VALUES (%s, %s, %s)
                    """,
                    (nome, link_internet if link_internet.strip() else None, formacao if formacao.strip() else None)
                )
                conn.commit()
                conn.close()
                
                st.success(f"✅ Colaborador '{nome}' incluído com sucesso!")
                st.cache_data.clear()
                st.session_state["colab_action"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao incluir Colaborador: {e}")


def alterar_colaborador(colaboradores_df):
    """Função para alterar um Colaborador existente."""
    st.subheader("✏️ Alterar Colaborador")
    
    colab_escolhido = st.selectbox(
        "Escolha o Colaborador para alteração:", 
        colaboradores_df["nome"].tolist(), 
        key="select_alterar_colab"
    )
    colab_atual = colaboradores_df[colaboradores_df["nome"] == colab_escolhido].iloc[0]

    with st.form("form_alterar_colaborador", clear_on_submit=False):
        nome = st.text_input("Nome", colab_atual["nome"])
        link_internet = st.text_input(
            "Link Internet", 
            value=colab_atual["link_internet"] if pd.notna(colab_atual["link_internet"]) else ""
        )
        formacao = st.text_input(
            "Formação", 
            value=colab_atual["formacao"] if pd.notna(colab_atual["formacao"]) else ""
        )
        salvar = st.form_submit_button("💾 Salvar Alterações")

        if salvar:
            if not nome or nome.strip() == "":
                st.error("❌ O nome do colaborador é obrigatório.")
                return
            
            try:
                conn = conectar_banco()
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE colaboradores SET nome=%s, link_internet=%s, formacao=%s
                    WHERE id_colaborador=%s
                    """,
                    (
                        nome, 
                        link_internet if link_internet.strip() else None, 
                        formacao if formacao.strip() else None, 
                        colab_atual["id_colaborador"]
                    )
                )
                conn.commit()
                conn.close()
                
                st.success(f"✅ Colaborador '{colab_escolhido}' alterado com sucesso!")
                st.cache_data.clear()
                st.session_state["colab_action"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao alterar Colaborador: {e}")


def excluir_colaborador(colaboradores_df):
    """Função para excluir um Colaborador existente."""
    st.subheader("❌ Excluir Colaborador")
    
    colab_escolhido = st.selectbox(
        "Escolha o Colaborador para exclusão:", 
        colaboradores_df["nome"].tolist(), 
        key="select_excluir_colab"
    )
    colab_atual = colaboradores_df[colaboradores_df["nome"] == colab_escolhido].iloc[0]

    st.warning(f"⚠️ Tem certeza que deseja excluir '{colab_escolhido}'? Esta ação é irreversível.")
    
    if st.button("Confirmar Exclusão", key="btn_confirmar_excluir"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()

            # Verificar se o colaborador está associado a algum WP como gerente
            cursor.execute("SELECT COUNT(*) FROM wps WHERE id_gerente = %s", (colab_atual["id_colaborador"],))
            wps_count = cursor.fetchone()[0]

            if wps_count > 0:
                st.error(f"❌ Não é possível excluir este colaborador. Ele é gerente de {wps_count} Work Package(s).")
                conn.close()
                return

            # Verificar se o colaborador está associado a algum projeto como autor
            cursor.execute("SELECT COUNT(*) FROM projetos_wps WHERE id_autor = %s", (colab_atual["id_colaborador"],))
            projetos_count = cursor.fetchone()[0]

            if projetos_count > 0:
                st.error(f"❌ Não é possível excluir este colaborador. Ele é autor de {projetos_count} Projeto(s).")
                conn.close()
                return

            # Remover das listas de colaboradores dos WPs
            cursor.execute("DELETE FROM lista_colab WHERE id_colaborador = %s", (colab_atual["id_colaborador"],))

            # Remover o colaborador
            cursor.execute("DELETE FROM colaboradores WHERE id_colaborador = %s", (colab_atual["id_colaborador"],))

            conn.commit()
            conn.close()
            
            st.success(f"✅ Colaborador '{colab_escolhido}' excluído com sucesso!")
            st.cache_data.clear()
            st.session_state["colab_action"] = None
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao excluir Colaborador: {e}")