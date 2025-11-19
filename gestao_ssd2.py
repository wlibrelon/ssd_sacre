import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from streamlit_option_menu import option_menu
from funcoes_app import conectar_banco, menu_wps

def show():
    """
    Exibição principal para gerenciamento de Work Packages.
    """
    # Sidebar para seleção
    with st.sidebar:
        st.title("Gerenciamento SSD")
        st.subheader("Manutenção de Dados")

        # Botão para acessar a área de Work Packages
        if st.button("Work Packages"):  # Controle baseado no clique do botão
            st.session_state["menu_selected"] = "work_packages"

        if st.button("Projetos dos WPs"):  # Controle baseado no clique do botão
            st.session_state["menu_selected"] = "Projetos_wp"


    ########################
    # Verifica o estado selecionado no menu para exibir a funcionalidade correta
    if st.session_state.get("menu_selected") == "work_packages":
        # Carregar dados da tabela Work Packages
        @st.cache_data
        def load_wps():
            try:
                conn = conectar_banco()
                query = "SELECT wp, titulo, descricao, gerente, colaboradores, menu FROM wps ORDER BY wp"
                df = pd.read_sql(query, conn)
                conn.close()
                if df.empty:
                    st.warning("⚠️ Nenhum Work Package encontrado no banco de dados.")
                return df
            except Exception as e:
                st.error(f"Erro ao carregar Work Packages do banco: {e}")
                return pd.DataFrame()

        wps_df = load_wps()  # Carrega os dados

        if wps_df.empty:
            st.warning("⚠️ Nenhum Work Package disponível para gerenciamento.")
        else:
            # Passa o DataFrame para a função que exibe os Work Packages
            exibir_work_packages(wps_df)
    else:
        # Tela inicial quando nada foi selecionado
        st.title("Bem-vindo ao Gerenciamento SSD 👋")
        st.write("Escolha uma opção no menu lateral para começar.")


    ############################
    if st.session_state.get("menu_selected") == "projetos_wp":
        # Carregar dados da tabela de projetos dos Work Packages
        @st.cache_data
        def load_proj_wps():
            try:
                conn = conectar_banco()
                query = "SELECT id_wp, titulo, id_autor, resumo, objetivos FROM projetos_wps ORDER BY id_wp"
                df = pd.read_sql(query, conn)
                conn.close()
                if df.empty:
                    st.warning("⚠️ Nenhum Projeto de Work Package encontrado no banco de dados.")
                return df
            except Exception as e:
                st.error(f"Erro ao carregar Projetos Work Packages do banco: {e}")
                return pd.DataFrame()

        proj_wps_df = load_proj_wps()  # Carrega os dados

        if proj_wps_df.empty:
            st.warning("⚠️ Nenhum Projeto de Work Package disponível para gerenciamento.")
        else:
            # Passa o DataFrame para a função que exibe os Work Packages
            exibir_projetos_wp(proj_wps_df)
    else:
        # Tela inicial quando nada foi selecionado
        st.title("Bem-vindo ao Gerenciamento SSD 👋")
        st.write("Escolha uma opção no menu lateral para começar.")
    ###################



def exibir_work_packages(wps_df):
    """
    Exibe a lista de Work Packages e as opções de gerenciamento (Incluir, Alterar, Excluir)
    em duas colunas.
    """
    # Divisão da área principal em duas colunas
    col1, col2 = st.columns([1, 1])  # Duas colunas proporcionais

    # Coluna 1: Tabela e botões de ações
    with col1:
        st.subheader("📋 Lista de Work Packages")
        st.dataframe(wps_df, height=400, hide_index=True)

        # Botões para ações
        st.write("Gerenciamento de Work Packages:")
        colbtn1, colbtn2, colbtn3 = st.columns([1, 1, 1])  # Duas colunas proporcionais

        with colbtn1:
            if st.button("➕ Incluir"):
                st.session_state["wp_action"] = "incluir"
        with colbtn2:
            if st.button("✏️ Alterar"):
                st.session_state["wp_action"] = "alterar"
        with colbtn3:
            if st.button("❌ Excluir"):
                st.session_state["wp_action"] = "excluir"

    # Coluna 2: Formulário de inclusão/alteração e exclusão
    with col2:
        # Controle das ações com base no estado "wp_action"
        if "wp_action" in st.session_state:
            # Operações de inclusão
            if st.session_state["wp_action"] == "incluir":
                incluir_wp()

            # Operações de alteração
            elif st.session_state["wp_action"] == "alterar":
                alterar_wp(wps_df)

            # Operações de exclusão
            elif st.session_state["wp_action"] == "excluir":
                excluir_wp(wps_df)
        else:
            # Orientação inicial caso nenhuma ação tenha sido selecionada
            st.subheader("Selecione uma ação no painel ao lado")
            st.write("Clique em um dos botões disponíveis para começar.")

def incluir_wp():
    """Função para incluir um novo WP"""
    st.subheader("Incluir Novo WP")
    
    with st.form("form_incluir_wp"):
        wp = st.number_input("Número do WP", min_value=1, step=1)
        titulo = st.text_input("Título")
        descricao = st.text_area("Descrição")
        gerente = st.text_input("Gerente Responsável")
        colaboradores = st.text_input("Colaboradores")
        menu = st.text_input("Texto para Menu")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Salvar Novo WP")
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                if 'wp_action' in st.session_state:
                    del st.session_state['wp_action']
                st.rerun()
        
        if submitted:
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                
                # Verificar se WP já existe
                cursor.execute("SELECT COUNT(*) FROM wps WHERE wp = %s", (wp,))
                if cursor.fetchone()[0] > 0:
                    st.error("Este número de WP já existe!")
                    return
                
                # Inserir novo registro
                cursor.execute(
                    """INSERT INTO wps (wp, titulo, descricao, gerente, colaboradores, menu)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (wp, titulo, descricao, gerente, colaboradores, menu)
                )
                conn.commit()
                st.success("✅ WP cadastrado com sucesso!")
                
                # Limpar cache e estado
                st.cache_data.clear()
                if 'wp_action' in st.session_state:
                    del st.session_state['wp_action']
                
                # Atualizar a página após 1 segundo
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"⛔ Erro ao cadastrar WP: {str(e)}")
            finally:
                if conn:
                    conn.close()

def alterar_wp(wps_df):
    """Função para alterar um WP existente"""
    st.subheader("Alterar WP Existente")
    
    if wps_df.empty:
        st.warning("Nenhum WP disponível para edição")
        return
    
    wp_selecionado = st.selectbox(
        "Selecione o WP para alterar:",
        options=wps_df['wp'].tolist(),
        format_func=lambda x: f"WP {x}",
        key="select_alterar_wp"
    )
    
    # Obter dados atuais
    dados_atuais = wps_df[wps_df['wp'] == wp_selecionado].iloc[0]
    
    with st.form("form_alterar_wp"):
        # Campos editáveis (wp não pode ser alterado)
        st.write(f"Editando: WP {wp_selecionado}")
        novo_titulo = st.text_input("Título", value=dados_atuais['titulo'])
        nova_descricao = st.text_area("Descrição", value=dados_atuais['descricao'])
        novo_gerente = st.text_input("Gerente", value=dados_atuais['gerente'])
        novos_colaboradores = st.text_input("Colaboradores", value=dados_atuais['colaboradores'])
        novo_menu = st.text_input("Menu", value=dados_atuais['menu'])
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Salvar Alterações")
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                if 'wp_action' in st.session_state:
                    del st.session_state['wp_action']
                st.rerun()
        
        if submitted:
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                
                cursor.execute(
                    """UPDATE wps SET
                    titulo = %s,
                    descricao = %s,
                    gerente = %s,
                    colaboradores = %s,
                    menu = %s
                    WHERE wp = %s""",
                    (novo_titulo, nova_descricao, novo_gerente,
                     novos_colaboradores, novo_menu, wp_selecionado)
                )
                conn.commit()
                st.success("✅ WP atualizado com sucesso!")
                
                # Limpar cache e estado
                st.cache_data.clear()
                if 'wp_action' in st.session_state:
                    del st.session_state['wp_action']
                
                # Atualizar a página
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"⛔ Erro ao atualizar WP: {str(e)}")
                st.error("Consulta executada:")
                st.code(f"""UPDATE wps SET
                    titulo = '{novo_titulo}',
                    descricao = '{nova_descricao}',
                    gerente = '{novo_gerente}',
                    colaboradores = '{novos_colaboradores}',
                    menu = '{novo_menu}'
                    WHERE wp = {wp_selecionado}""")
            finally:
                if conn:
                    conn.close()                    

def excluir_wp(wps_df):
    """
    Função para excluir um Work Package existente.
    """
    st.subheader("❌ Excluir Work Package")
    
    # Se o DataFrame está vazio, exibe mensagem de alerta
    if wps_df.empty:
        st.warning("⚠️ Nenhum Work Package disponível para exclusão.")
        return

    # Seleção do WP para exclusão
    wp_selecionado = st.selectbox(
        "Selecione o WP para excluir:",
        options=wps_df["wp"].tolist(),  # Certifique-se de que o DataFrame contém a coluna 'wp'
        format_func=lambda x: f"WP {x}",
    )

    # Botão para confirmar a exclusão
    if st.button("Confirmar Exclusão"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM wps WHERE wp = %s", (wp_selecionado,))
            conn.commit()
            st.success(f"✅ Work Package WP {wp_selecionado} foi excluído com sucesso!")
            
            # Limpar cache do DataFrame e reiniciar a tela
            st.cache_data.clear()
            if "wp_action" in st.session_state:
                del st.session_state["wp_action"]
            st.rerun()  # Força a atualização da interface
        except Exception as e:
            st.error(f"Erro ao excluir WP {wp_selecionado}: {e}")
        finally:
            conn.close()



def exibir_projetos_wp(proj_wps_df):
    """
    Exibe a lista de projetos Work Packages e as opções de gerenciamento (Incluir, Alterar, Excluir)
    em duas colunas.
    """
    # Divisão da área principal em duas colunas
    col1, col2 = st.columns([1, 1])  # Duas colunas proporcionais

    # Coluna 1: Tabela e botões de ações
    with col1:
        st.subheader("📋 Lista de Projetos do Work Package")
        st.dataframe(proj_wps_df, height=400, hide_index=True)

        # Botões para ações
        st.write("Gerenciamento de Projetos Work Package:")
        colbtn1, colbtn2, colbtn3 = st.columns([1, 1, 1])  # Duas colunas proporcionais

        with colbtn1:
            if st.button("➕ Incluir"):
                st.session_state["wp_action"] = "incluir"
        with colbtn2:
            if st.button("✏️ Alterar"):
                st.session_state["wp_action"] = "alterar"
        with colbtn3:
            if st.button("❌ Excluir"):
                st.session_state["wp_action"] = "excluir"

    # Coluna 2: Formulário de inclusão/alteração e exclusão
    with col2:
        # Controle das ações com base no estado "wp_action"
        if "wp_action" in st.session_state:
            # Operações de inclusão
            if st.session_state["wp_action"] == "incluir":
                incluir_wp()

            # Operações de alteração
            elif st.session_state["wp_action"] == "alterar":
                alterar_wp(wps_df)

            # Operações de exclusão
            elif st.session_state["wp_action"] == "excluir":
                excluir_wp(wps_df)
        else:
            # Orientação inicial caso nenhuma ação tenha sido selecionada
            st.subheader("Selecione uma ação no painel ao lado")
            st.write("Clique em um dos botões disponíveis para começar.")
