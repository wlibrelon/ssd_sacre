import streamlit as st
import pandas as pd
import numpy as np
import datetime
import pydeck as pdk
from streamlit_option_menu import option_menu
from io import StringIO
from funcoes_app import exibir_pdf_no_app, conectar_banco, menu_wps

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
                cursor.execute("SELECT COUNT(*) FROM wps WHERE wp = ?", (wp,))
                if cursor.fetchone()[0] > 0:
                    st.error("Este número de WP já existe!")
                    return
                
                # Inserir novo registro
                cursor.execute(
                    """INSERT INTO wps (wp, titulo, descricao, gerente, colaboradores, menu)
                    VALUES (?, ?, ?, ?, ?, ?)""",
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

def show():
    # Sidebar com login
    with st.sidebar:
        st.title("Gerenciamento SSD")
        st.subheader("Manutenção de Dados")
        btn_wp = st.button("Work Packages")

    # Layout de colunas
    col1, col2 = st.columns([10, 10]) 

    with col1:
        st.subheader("Work Packages")
        
        # Carregar dados da tabela WPs
        @st.cache_data
        def load_wps():
            conn = conectar_banco()
            query = "SELECT wp, titulo, descricao, gerente, colaboradores, menu FROM wps ORDER BY wp"
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        
        df_wps = load_wps()
        
        # Exibir tabela com paginação
        st.dataframe(df_wps, height=400, hide_index=True)

        # Botões de gerenciamento
        st.write("")  # Espaçamento
        btn_container = st.container()
        with btn_container:
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("➕ Incluir", use_container_width=True):
                    st.session_state['wp_action'] = 'incluir'
            with col_btn2:
                if st.button("✏️ Alterar", use_container_width=True):
                    st.session_state['wp_action'] = 'alterar'
            with col_btn3:
                if st.button("❌ Excluir", use_container_width=True):
                    st.session_state['wp_action'] = 'excluir'

        # Lógica para cada ação (será exibida na coluna 2)
        if 'wp_action' in st.session_state:
            if st.session_state['wp_action'] == 'incluir':
                with col2:
                    st.subheader("Incluir Novo WP")
                    with st.form("form_incluir"):
                        wp = st.number_input("WP (Número)", min_value=1)
                        titulo = st.text_input("Título")
                        descricao = st.text_area("Descrição")
                        gerente = st.text_input("Gerente Responsável")
                        colaboradores = st.text_input("Colaboradores")
                        menu = st.text_input("Texto do Menu")
                        
                        if st.form_submit_button("Salvar"):
                            st.write("Salvando novo WP...")
                            try:
                                # incluir_wp(wp, titulo, descricao, gerente, colaboradores, menu)
                                conn = conectar_banco()
                                cursor = conn.cursor()
                                cursor.execute(
                                    "INSERT INTO wps (wp, titulo, descricao, gerente, colaboradores, menu) " \
                                    "VALUES (%s, %s, %s, %s, %s, %s)",
                                    (wp, titulo, descricao, gerente, colaboradores, menu)
                                )
                                conn.commit()
                                st.success("WP cadastrado com sucesso!")
                                st.cache_data.clear()  # Limpa cache para recarregar dados
                            except Exception as e:
                                st.error(f"Erro ao cadastrar: {e}")
                            finally:
                                del st.session_state['wp_action']
            
            elif st.session_state['wp_action'] == 'alterar':
                with col2:
                    st.subheader("Alterar WP")
                    wp_selecionado = st.selectbox(
                        "Selecione o WP para alterar.",
                        options=df_wps['wp'].tolist()
                    )
                    dados_wp = df_wps[df_wps['wp'] == wp_selecionado].iloc[0]
                    
                    with st.form("form_alterar"):
                        novo_titulo = st.text_input("Título", value=dados_wp['titulo'])
                        nova_descricao = st.text_area("Descrição", value=dados_wp['descricao'])
                        novo_gerente = st.text_input("Gerente Responsável", value=dados_wp['gerente'])
                        novos_colaboradores = st.text_input("Colaboradores", value=dados_wp['colaboradores'])
                        novo_menu = st.text_input("Texto do Menu", value=dados_wp['menu'])
                        
                        if st.form_submit_button("Atualizar"):
                            try:
                                st.write("atualizando WP...")
                                conn = conectar_banco()
                                cursor = conn.cursor()
                                cursor.execute(
                                    """UPDATE wps SET 
                                    titulo = %s, descricao = %s, gerente = %s, 
                                    colaboradores = %s, menu = %s
                                    WHERE wp = %s""",
                                    (novo_titulo, nova_descricao, novo_gerente, 
                                     novos_colaboradores, novo_menu, wp_selecionado)
                                )
                                conn.commit()
                                st.success("WP atualizado com sucesso!")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error(f"Erro ao atualizar: {e}")
                            finally:
                                if conn:
                                    conn.close()
                                del st.session_state['wp_action']
            
            elif st.session_state['wp_action'] == 'excluir':
                with col2:
                    st.subheader("Excluir WP")
                    wp_selecionado = st.selectbox(
                        "Selecione o WP para excluir",
                        options=df_wps['wp'].tolist()
                    )
                    
                    if st.button("Confirmar Exclusão"):
                        try:
                            conn = conectar_banco()
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM wps WHERE wp = %s",
                                (wp_selecionado,)
                            )
                            conn.commit()
                            st.success("WP excluído com sucesso!")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")
                        finally:
                            if conn:
                                conn.close()
                            del st.session_state['wp_action']

