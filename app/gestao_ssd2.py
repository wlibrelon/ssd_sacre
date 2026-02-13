import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from streamlit_option_menu import option_menu
from funcoes_app import conectar_banco, menu_wps
import gerenciar_colaboradores as gerenciar_colaboradores
import gerenciar_artigos as gerenciar_artigos
import gerenciar_projetos_wp as gerenciar_projetos_wp

def show():
    """
    Exibição principal para gerenciamento de Work Packages
    com persistência de estado e atualização dinâmica.
    """
    with st.sidebar:
        st.title("Gerenciamento SSD")
        st.subheader("Manutenção de Dados")

        if st.button("Work Packages"):
            st.session_state["menu_selected"] = "work_packages"
            st.session_state["wp_action"] = None  

        if st.button("Projetos dos WPs"):
            st.session_state["menu_selected"] = "projetos_wp"
            st.session_state["proj_action"] = None  

        if st.button("Colaboradores"):
            st.session_state["menu_selected"] = "colaboradores"
            st.session_state["operation"] = None

        if st.button("Gestão de Artigos"):
            st.session_state["menu_selected"] = "gestao_artigos"
            st.session_state["operation"] = None

    if "menu_selected" not in st.session_state:
        return

    if st.session_state.get("menu_selected") == "colaboradores":
        gerenciar_colaboradores.show() 

    if st.session_state.get("menu_selected") == "gestao_artigos":
        gerenciar_artigos.show()

    if st.session_state.get("menu_selected") == "projetos_wp":
        gerenciar_projetos_wp.show()

    ######################################
    # Gerenciamento de Work Packages
    elif st.session_state.get("menu_selected") == "work_packages":
        st.title("Gerenciamento de Work Packages")

        @st.cache_data
        def load_wps():
            try:
                conn = conectar_banco()
                query = """
                    SELECT 
                        w.id_wp,
                        w.wp, 
                        w.titulo, 
                        w.descricao,
                        w.menu,
                        c.nome AS gerente
                    FROM wps w
                    LEFT JOIN colaboradores c ON w.id_gerente = c.id_colaborador
                    ORDER BY w.wp
                """
                df = pd.read_sql(query, conn)
                conn.close()
                return df
            except Exception as e:
                st.error(f"Erro ao carregar Work Packages do banco: {e}")
                return pd.DataFrame()

        wps_df = load_wps()

        if wps_df.empty:
            st.warning("⚠️ Nenhum Work Package disponível no banco de dados.")
            if st.button("➕ Incluir Primeiro Work Package", key="btn_primeiro_wp"):
                st.session_state["wp_action"] = "incluir"
                st.rerun()
        else:
            exibir_work_packages(wps_df)

        # Renderizar operações (FORA das colunas)
        if "wp_action" in st.session_state and st.session_state["wp_action"]:
            st.divider()
            if st.session_state["wp_action"] == "incluir":
                incluir_wp()
            elif st.session_state["wp_action"] == "alterar":
                alterar_wp(wps_df)
            elif st.session_state["wp_action"] == "excluir":
                excluir_wp(wps_df)
            elif st.session_state["wp_action"] == "incluir_colaboradores":
                incluir_colaboradores_wp(wps_df)


# ========== FUNÇÕES DE WORK PACKAGES ==========
def exibir_work_packages(wps_df):
    """
    Exibe a lista de Work Packages e as opções de gerenciamento
    em duas colunas (SEM renderizar operações aqui).
    """
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Lista de Work Packages")
        
        # Exibir apenas as colunas desejadas (incluindo menu)
        wps_display = wps_df[["wp", "titulo", "menu", "gerente"]]
        st.dataframe(wps_display, height=400, hide_index=True)

        st.write("**Gerenciamento de Work Packages:**")
        colbtn1, colbtn2, colbtn3, colbtn4 = st.columns([1, 1, 1, 1])

        with colbtn1:
            if st.button("➕ Incluir", key="btn_incluir_wp"):
                st.session_state["wp_action"] = "incluir"
                st.rerun()
        with colbtn2:
            if st.button("✏️ Alterar", key="btn_alterar_wp"):
                st.session_state["wp_action"] = "alterar"
                st.rerun()
        with colbtn3:
            if st.button("👥 Colaboradores", key="btn_colab_wp"):
                st.session_state["wp_action"] = "incluir_colaboradores"
                st.rerun()
        with colbtn4:
            if st.button("❌ Excluir", key="btn_excluir_wp"):
                st.session_state["wp_action"] = "excluir"
                st.rerun()

    with col2:
        st.subheader("ℹ️ Detalhes do Work Package")
        
        # Selecionar um WP para exibir detalhes
        wp_selecionado = st.selectbox(
            "Selecione um WP para ver detalhes:",
            options=wps_df["id_wp"].tolist(),
            format_func=lambda x: f"WP {wps_df[wps_df['id_wp'] == x]['wp'].values[0]} | {wps_df[wps_df['id_wp'] == x]['titulo'].values[0]}",
            key="select_wp_detalhes"
        )
        
        if wps_df[wps_df["id_wp"] == wp_selecionado].shape[0] > 0:
            wp_info = wps_df[wps_df["id_wp"] == wp_selecionado].iloc[0]
            
            # Exibir descrição
            st.write("**Descrição:**")
            st.write(wp_info["descricao"])
            
            # Exibir menu
            st.write("**Menu:**")
            st.write(wp_info["menu"] if pd.notna(wp_info["menu"]) else "Não definido")
            
            # Exibir lista de colaboradores
            st.write("**Colaboradores:**")
            
            @st.cache_data
            def load_colaboradores_wp(id_wp):
                try:
                    conn = conectar_banco()
                    query = """
                        SELECT 
                            c.nome,
                            c.formacao,
                            c.link_internet
                        FROM lista_colab lc
                        JOIN colaboradores c ON lc.id_colaborador = c.id_colaborador
                        WHERE lc.id_wp = %s
                        ORDER BY c.nome
                    """
                    df = pd.read_sql_query(query, conn, params=(id_wp,))
                    conn.close()
                    return df
                except Exception as e:
                    st.error(f"Erro ao carregar colaboradores do WP: {e}")
                    return pd.DataFrame()
            
            colaboradores_wp = load_colaboradores_wp(wp_selecionado)
            
            if not colaboradores_wp.empty:
                # Exibir tabela com controle de largura
                st.dataframe(
                    colaboradores_wp[["nome", "formacao", "link_internet"]], 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "nome": st.column_config.TextColumn("Nome", width="medium"),
                        "formacao": st.column_config.TextColumn("Formação", width="medium"),
                        "link_internet": st.column_config.LinkColumn("Link", width="small")
                    }
                )
            else:
                st.info("ℹ️ Nenhum colaborador associado a este WP.")

def incluir_wp():
    """Função para criar um Work Package novo."""
    st.subheader("➕ Incluir Novo Work Package")
    
    @st.cache_data
    def load_colaboradores():
        try:
            conn = conectar_banco()
            query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar colaboradores: {e}")
            return pd.DataFrame()
    
    colaboradores_df = load_colaboradores()
    
    with st.form("form_incluir_wp", clear_on_submit=True):
        wp = st.number_input("Número do WP *", min_value=1, step=1)
        titulo = st.text_input("Título *", placeholder="Digite o título")
        descricao = st.text_area("Descrição *", placeholder="Digite a descrição")
        menu = st.text_input("Menu *", placeholder="Digite o nome do menu")
        
        if not colaboradores_df.empty:
            gerente_id = st.selectbox(
                "Gerente Responsável *",
                options=colaboradores_df["id_colaborador"].tolist(),
                format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
                key="select_gerente_incluir"
            )
        else:
            st.warning("⚠️ Nenhum colaborador disponível. Cadastre colaboradores primeiro.")
            gerente_id = None
        
        salvar = st.form_submit_button("💾 Salvar")

        if salvar:
            if not titulo or not descricao or not menu or gerente_id is None:
                st.error("❌ Preencha todos os campos obrigatórios.")
                return
            
            try:
                conn = conectar_banco()
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO wps (wp, titulo, descricao, menu, id_gerente)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (wp, titulo, descricao, menu, gerente_id)
                )
                conn.commit()
                conn.close()
                
                st.success(f"✅ WP {wp} incluído com sucesso!")
                st.cache_data.clear()
                st.session_state["wp_action"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao incluir Work Package: {e}")


def alterar_wp(wps_df):
    """Função para alterar um Work Package existente."""
    st.subheader("✏️ Alterar Work Package")
    
    @st.cache_data
    def load_colaboradores():
        try:
            conn = conectar_banco()
            query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar colaboradores: {e}")
            return pd.DataFrame()
    
    colaboradores_df = load_colaboradores()
    
    wp_escolhido = st.selectbox("Escolha o WP para alteração:", wps_df["titulo"].tolist(), key="select_wp_alterar")
    wp_atual = wps_df[wps_df["titulo"] == wp_escolhido].iloc[0]

    with st.form("form_alterar_wp", clear_on_submit=False):
        titulo = st.text_input("Título", wp_atual["titulo"])
        descricao = st.text_area("Descrição", wp_atual["descricao"])
        menu = st.text_input("Menu", value=wp_atual["menu"] if pd.notna(wp_atual["menu"]) else "")
        
        if not colaboradores_df.empty:
            gerente_id = st.selectbox(
                "Gerente",
                options=colaboradores_df["id_colaborador"].tolist(),
                format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
                key="select_gerente_alterar"
            )
        else:
            gerente_id = None
        
        salvar = st.form_submit_button("💾 Salvar Alterações")

        if salvar:
            try:
                conn = conectar_banco()
                cursor = conn.cursor()

                # Converter valores numpy para tipos Python nativos
                wp_id = int(wp_atual["id_wp"])
                gerente_id_int = int(gerente_id) if gerente_id is not None else None

                cursor.execute(
                    """
                    UPDATE wps SET titulo=%s, descricao=%s, menu=%s, id_gerente=%s
                    WHERE id_wp=%s
                    """,
                    (titulo, descricao, menu, gerente_id_int, wp_id)
                )
                conn.commit()
                conn.close()
                
                st.success(f"✅ WP alterado com sucesso!")
                st.cache_data.clear()
                st.session_state["wp_action"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao alterar Work Package: {e}")

def incluir_colaboradores_wp(wps_df):
    """Função para incluir colaboradores em um Work Package."""
    st.subheader("👥 Incluir Colaboradores no Work Package")
    
    @st.cache_data
    def load_colaboradores():
        try:
            conn = conectar_banco()
            query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar colaboradores: {e}")
            return pd.DataFrame()
    
    @st.cache_data
    def load_colaboradores_wp(id_wp):
        try:
            conn = conectar_banco()
            query = """
                SELECT 
                    lc.id_lista_colab,
                    c.id_colaborador,
                    c.nome
                FROM lista_colab lc
                JOIN colaboradores c ON lc.id_colaborador = c.id_colaborador
                WHERE lc.id_wp = %s
                ORDER BY c.nome
            """
            df = pd.read_sql_query(query, conn, params=(id_wp,))
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar colaboradores do WP: {e}")
            return pd.DataFrame()
    
    colaboradores_df = load_colaboradores()
    
    wp_escolhido = st.selectbox(
        "Escolha o WP:",
        options=wps_df["id_wp"].tolist(),
        format_func=lambda x: f"WP {wps_df[wps_df['id_wp'] == x]['wp'].values[0]} | {wps_df[wps_df['id_wp'] == x]['titulo'].values[0]}",
        key="select_wp_colab"
    )
    
    if wp_escolhido:
        colaboradores_wp = load_colaboradores_wp(wp_escolhido)
        
        st.write(f"**Colaboradores atuais do WP:**")
        if not colaboradores_wp.empty:
            st.dataframe(colaboradores_wp[["nome"]], hide_index=True)
            
            # Opção de remover colaborador
            if st.checkbox("Remover colaborador?", key="check_remover_colab"):
                colab_remover = st.selectbox(
                    "Selecione o colaborador para remover:",
                    options=colaboradores_wp["id_lista_colab"].tolist(),
                    format_func=lambda x: colaboradores_wp[colaboradores_wp["id_lista_colab"] == x]["nome"].values[0],
                    key="select_remover_colab"
                )
                
                if st.button("❌ Remover Colaborador", key="btn_remover_colab"):
                    try:
                        conn = conectar_banco()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM lista_colab WHERE id_lista_colab = %s", (colab_remover,))
                        conn.commit()
                        conn.close()
                        st.success("✅ Colaborador removido com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao remover colaborador: {e}")
        else:
            st.info("ℹ️ Nenhum colaborador associado a este WP ainda.")
        
        st.write("**Adicionar novo colaborador:**")
        if not colaboradores_df.empty:
            novo_colaborador = st.selectbox(
                "Selecione o colaborador:",
                options=colaboradores_df["id_colaborador"].tolist(),
                format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
                key="select_novo_colab"
            )
            
            if st.button("➕ Adicionar Colaborador", key="btn_add_colab"):
                try:
                    conn = conectar_banco()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO lista_colab (id_colaborador, id_wp) VALUES (%s, %s)",
                        (novo_colaborador, wp_escolhido)
                    )
                    conn.commit()
                    conn.close()
                    st.success("✅ Colaborador adicionado com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar colaborador: {e}")
        else:
            st.warning("⚠️ Nenhum colaborador disponível.")


def excluir_wp(wps_df):
    """Função para excluir um Work Package existente."""
    st.subheader("❌ Excluir Work Package")
    
    wp_escolhido = st.selectbox(
        "Escolha o WP para exclusão:",
        options=wps_df["id_wp"].tolist(),
        format_func=lambda x: f"WP {wps_df[wps_df['id_wp'] == x]['wp'].values[0]} | {wps_df[wps_df['id_wp'] == x]['titulo'].values[0]}",
        key="select_wp_excluir"
    )

    st.warning("⚠️ Esta ação é irreversível e removerá todos os dados associados.")
    
    if st.button("Confirmar Exclusão", key="btn_confirmar_excluir_wp"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()

            # Remover colaboradores associados
            cursor.execute("DELETE FROM lista_colab WHERE id_wp = %s", (wp_escolhido,))
            
            # Remover projetos associados
            cursor.execute("DELETE FROM projetos_wps WHERE id_wp = %s", (wp_escolhido,))
            
            # Remover WP
            cursor.execute("DELETE FROM wps WHERE id_wp = %s", (wp_escolhido,))
            
            conn.commit()
            conn.close()
            
            st.success(f"✅ WP excluído com sucesso!")
            st.cache_data.clear()
            st.session_state["wp_action"] = None
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao excluir Work Package: {e}")

# import streamlit as st
# import pandas as pd
# import numpy as np
# import pydeck as pdk
# from streamlit_option_menu import option_menu
# from funcoes_app import conectar_banco, menu_wps
# import gerenciar_colaboradores as gerenciar_colaboradores
# import gerenciar_artigos as gerenciar_artigos

# def show():
#     """
#     Exibição principal para gerenciamento de Work Packages e Projetos 
#     com persistência de estado e atualização dinâmica.
#     """
#     with st.sidebar:
#         st.title("Gerenciamento SSD")
#         st.subheader("Manutenção de Dados")

#         if st.button("Work Packages"):
#             st.session_state["menu_selected"] = "work_packages"
#             st.session_state["wp_action"] = None  

#         if st.button("Projetos dos WPs"):
#             st.session_state["menu_selected"] = "projetos_wp"
#             st.session_state["proj_action"] = None  

#         if st.button("Colaboradores"):
#             st.session_state["menu_selected"] = "colaboradores"
#             st.session_state["operation"] = None

#         if st.button("Gestão de Artigos"):
#             st.session_state["menu_selected"] = "gestao_artigos"
#             st.session_state["operation"] = None

#     if "menu_selected" not in st.session_state:
#         return

#     if st.session_state.get("menu_selected") == "colaboradores":
#         gerenciar_colaboradores.show() 

#     if st.session_state.get("menu_selected") == "gestao_artigos":
#         gerenciar_artigos.show() 

#     ######################################
#     # Gerenciamento de Work Packages
#     elif st.session_state.get("menu_selected") == "work_packages":
#         st.title("Gerenciamento de Work Packages")

#         @st.cache_data
#         def load_wps():
#             try:
#                 conn = conectar_banco()
#                 query = """
#                     SELECT 
#                         w.id_wp,
#                         w.wp, 
#                         w.titulo, 
#                         w.descricao,
#                         w.menu,
#                         c.nome AS gerente
#                     FROM wps w
#                     LEFT JOIN colaboradores c ON w.id_gerente = c.id_colaborador
#                     ORDER BY w.wp
#                 """
#                 df = pd.read_sql(query, conn)
#                 conn.close()
#                 return df
#             except Exception as e:
#                 st.error(f"Erro ao carregar Work Packages do banco: {e}")
#                 return pd.DataFrame()

#         wps_df = load_wps()

#         if wps_df.empty:
#             st.warning("⚠️ Nenhum Work Package disponível no banco de dados.")
#             if st.button("➕ Incluir Primeiro Work Package", key="btn_primeiro_wp"):
#                 st.session_state["wp_action"] = "incluir"
#                 st.rerun()
#         else:
#             exibir_work_packages(wps_df)

#         # Renderizar operações (FORA das colunas)
#         if "wp_action" in st.session_state and st.session_state["wp_action"]:
#             st.divider()
#             if st.session_state["wp_action"] == "incluir":
#                 incluir_wp()
#             elif st.session_state["wp_action"] == "alterar":
#                 alterar_wp(wps_df)
#             elif st.session_state["wp_action"] == "excluir":
#                 excluir_wp(wps_df)
#             elif st.session_state["wp_action"] == "incluir_colaboradores":
#                 incluir_colaboradores_wp(wps_df)

#     ######################################
#     # Gerenciamento de Projetos dos Work Packages
#     elif st.session_state.get("menu_selected") == "projetos_wp":
#         st.title("Projetos dos Work Packages")

#         @st.cache_data
#         def load_wps_list():
#             try:
#                 conn = conectar_banco()
#                 query = "SELECT id_wp, wp, titulo FROM wps ORDER BY wp"
#                 df = pd.read_sql(query, conn)
#                 conn.close()
#                 return df
#             except Exception as e:
#                 st.error(f"Erro ao carregar Work Packages do banco: {e}")
#                 return pd.DataFrame()

#         @st.cache_data
#         def load_proj_wps(id_wp):
#             try:
#                 conn = conectar_banco()
#                 query = """
#                     SELECT 
#                         id_projeto, 
#                         titulo,
#                         c.nome AS autor
#                     FROM projetos_wps p
#                     LEFT JOIN colaboradores c ON p.id_autor = c.id_colaborador
#                     WHERE p.id_wp = %s
#                 """
#                 df = pd.read_sql_query(query, conn, params=(id_wp,))
#                 conn.close()
#                 return df
#             except Exception as e:
#                 st.error(f"Erro ao carregar Projetos dos Work Packages do banco: {e}")
#                 return pd.DataFrame()

#         @st.cache_data
#         def load_proj_detalhes(id_projeto):
#             try:
#                 conn = conectar_banco()
#                 query = """
#                     SELECT 
#                         resumo,
#                         objetivos
#                     FROM projetos_wps
#                     WHERE id_projeto = %s
#                 """
#                 df = pd.read_sql_query(query, conn, params=(id_projeto,))
#                 conn.close()
#                 return df
#             except Exception as e:
#                 st.error(f"Erro ao carregar detalhes do projeto: {e}")
#                 return pd.DataFrame()

#         # Carregar os Work Packages
#         wps_df = load_wps_list()
#         if wps_df.empty:
#             st.warning("⚠️ Nenhum Work Package encontrado no banco de dados.")
#             return

#         # Seleção do WP
#         wp_selecionado = st.selectbox(
#             "Selecione um Work Package para visualizar os projetos:",
#             options=wps_df["id_wp"].tolist(),
#             format_func=lambda x: f"WP {wps_df[wps_df['id_wp'] == x]['wp'].values[0]} | {wps_df[wps_df['id_wp'] == x]['titulo'].values[0]}",
#             key="select_wp_projetos"
#         )

#         if wp_selecionado:
#             st.session_state["wp_selecionado"] = wp_selecionado

#         if "wp_selecionado" in st.session_state:
#             projetos_df = load_proj_wps(st.session_state["wp_selecionado"])

#             col1, col2 = st.columns([1, 1])

#             with col1:
#                 st.subheader(f"Projetos no Work Package {st.session_state['wp_selecionado']}")
#                 if projetos_df.empty:
#                     st.warning("⚠️ Nenhum projeto encontrado para este WP.")
#                     if st.button("➕ Incluir Primeiro Projeto", key="btn_primeiro_proj"):
#                         st.session_state["proj_action"] = "incluir"
#                         st.rerun()
#                 else:
#                     # Exibir apenas titulo e autor (sem resumo e objetivos)
#                     projetos_display = projetos_df[["titulo", "autor"]]
#                     st.dataframe(
#                         projetos_display,
#                         height=400,
#                         hide_index=True,
#                         use_container_width=True,
#                         column_config={
#                             "titulo": st.column_config.TextColumn("Título", width="large"),
#                             "autor": st.column_config.TextColumn("Autor", width="medium")
#                         }
#                     )

#                     st.write("**Gerenciamento de Projetos:**")
#                     colbtn1, colbtn2, colbtn3 = st.columns(3)
#                     with colbtn1:
#                         if st.button("➕ Incluir Projeto", key="btn_incluir_proj"):
#                             st.session_state["proj_action"] = "incluir"
#                             st.rerun()
#                     with colbtn2:
#                         if st.button("✏️ Alterar Projeto", key="btn_alterar_proj"):
#                             st.session_state["proj_action"] = "alterar"
#                             st.rerun()
#                     with colbtn3:
#                         if st.button("❌ Excluir Projeto", key="btn_excluir_proj"):
#                             st.session_state["proj_action"] = "excluir"
#                             st.rerun()

#             with col2:
#                 st.subheader("ℹ️ Detalhes do Projeto")
                
#                 # Selecionar um projeto para exibir detalhes
#                 if not projetos_df.empty:
#                     proj_selecionado = st.selectbox(
#                         "Selecione um projeto para ver detalhes:",
#                         options=projetos_df["id_projeto"].tolist(),
#                         format_func=lambda x: projetos_df[projetos_df["id_projeto"] == x]["titulo"].values[0],
#                         key="select_proj_detalhes"
#                     )
                    
#                     if projetos_df[projetos_df["id_projeto"] == proj_selecionado].shape[0] > 0:
#                         proj_info = projetos_df[projetos_df["id_projeto"] == proj_selecionado].iloc[0]
#                         proj_detalhes = load_proj_detalhes(proj_selecionado)
                        
#                         # Exibir resumo
#                         st.write("**Resumo:**")
#                         if not proj_detalhes.empty:
#                             st.write(proj_detalhes.iloc[0]["resumo"])
                        
#                         # Exibir objetivos
#                         st.write("**Objetivos:**")
#                         if not proj_detalhes.empty:
#                             st.write(proj_detalhes.iloc[0]["objetivos"])
#                 else:
#                     st.info("ℹ️ Selecione um projeto para ver os detalhes.")

#             # Renderizar operações (FORA das colunas)
#             if "proj_action" in st.session_state and st.session_state["proj_action"]:
#                 st.divider()
#                 if st.session_state["proj_action"] == "incluir":
#                     incluir_projeto(st.session_state["wp_selecionado"])
#                 elif st.session_state["proj_action"] == "alterar":
#                     alterar_projeto(st.session_state["wp_selecionado"], projetos_df)
#                 elif st.session_state["proj_action"] == "excluir":
#                     excluir_projeto(st.session_state["wp_selecionado"], projetos_df)

# # ========== FUNÇÕES DE PROJETOS ==========

# def incluir_projeto(id_wp):
#     st.subheader("➕ Incluir um novo projeto")
    
#     @st.cache_data
#     def load_colaboradores():
#         try:
#             conn = conectar_banco()
#             query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
#             df = pd.read_sql(query, conn)
#             conn.close()
#             return df
#         except Exception as e:
#             st.error(f"Erro ao carregar colaboradores: {e}")
#             return pd.DataFrame()
    
#     colaboradores_df = load_colaboradores()
    
#     with st.form("form_incluir_projeto", clear_on_submit=True):
#         titulo = st.text_input("Título do projeto *", placeholder="Digite o título")
        
#         if not colaboradores_df.empty:
#             id_autor = st.selectbox(
#                 "Autor *",
#                 options=colaboradores_df["id_colaborador"].tolist(),
#                 format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
#                 key="select_autor_proj"
#             )
#         else:
#             st.warning("⚠️ Nenhum colaborador disponível.")
#             id_autor = None
        
#         resumo = st.text_area("Resumo *", placeholder="Digite o resumo")
#         objetivos = st.text_area("Objetivos *", placeholder="Digite os objetivos")
        
#         salvar = st.form_submit_button("💾 Salvar Novo Projeto")

#         if salvar:
#             if not titulo or not resumo or not objetivos or id_autor is None:
#                 st.error("❌ Preencha todos os campos obrigatórios.")
#                 return
            
#             try:
#                 conn = conectar_banco()
#                 cursor = conn.cursor()
#                 query = "INSERT INTO projetos_wps (id_wp, titulo, id_autor, resumo, objetivos) VALUES (%s, %s, %s, %s, %s)"
#                 cursor.execute(query, (id_wp, titulo, id_autor, resumo, objetivos))
#                 conn.commit()
#                 conn.close()

#                 st.success("✅ Projeto incluído com sucesso!")
#                 st.cache_data.clear()
#                 st.session_state["proj_action"] = None
#                 st.rerun()

#             except Exception as e:
#                 st.error(f"Erro ao incluir projeto: {e}")


# def alterar_projeto(id_wp, projetos_df):
#     st.subheader("✏️ Alterar Projeto Existente")

#     @st.cache_data
#     def load_colaboradores():
#         try:
#             conn = conectar_banco()
#             query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
#             df = pd.read_sql(query, conn)
#             conn.close()
#             return df
#         except Exception as e:
#             st.error(f"Erro ao carregar colaboradores: {e}")
#             return pd.DataFrame()

#     colaboradores_df = load_colaboradores()

#     projeto_titulo = st.selectbox("Selecione o projeto:", projetos_df["titulo"].tolist(), key="select_proj_alterar")
#     projeto = projetos_df[projetos_df["titulo"] == projeto_titulo].iloc[0]

#     with st.form("form_alterar_projeto", clear_on_submit=False):
#         novo_titulo = st.text_input("Título:", projeto["titulo"])
        
#         if not colaboradores_df.empty:
#             novo_id_autor = st.selectbox(
#                 "Autor:",
#                 options=colaboradores_df["id_colaborador"].tolist(),
#                 format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
#                 index=0,
#                 key="select_autor_alterar"
#             )
#         else:
#             novo_id_autor = None
        
#         novo_resumo = st.text_area("Resumo:", projeto["resumo"])
#         novos_objetivos = st.text_area("Objetivos:", projeto["objetivos"])

#         salvar = st.form_submit_button("💾 Salvar Alterações")

#         if salvar:
#             try:
#                 conn = conectar_banco()
#                 cursor = conn.cursor()
#                 query = """
#                     UPDATE projetos_wps SET titulo = %s, id_autor = %s, resumo = %s, objetivos = %s
#                     WHERE id_wp = %s AND id_projeto = %s
#                 """
#                 cursor.execute(query, (novo_titulo, novo_id_autor, novo_resumo, novos_objetivos, id_wp, projeto["id_projeto"]))
#                 conn.commit()
#                 conn.close()

#                 st.success("✅ Projeto alterado com sucesso!")
#                 st.cache_data.clear()
#                 st.session_state["proj_action"] = None
#                 st.rerun()
#             except Exception as e:
#                 st.error(f"Erro ao alterar projeto: {e}")


# def excluir_projeto(id_wp, projetos_df):
#     st.subheader("❌ Excluir Projeto")

#     projeto_selecionado = st.selectbox("Selecione o projeto para excluir:", projetos_df["titulo"].tolist(), key="select_proj_excluir")
#     projeto = projetos_df[projetos_df["titulo"] == projeto_selecionado].iloc[0]

#     st.warning("⚠️ Esta ação é irreversível.")

#     if st.button("Confirmar Exclusão", key="btn_confirmar_excluir_proj"):
#         try:
#             conn = conectar_banco()
#             cursor = conn.cursor()
#             query = "DELETE FROM projetos_wps WHERE id_wp = %s AND id_projeto = %s"
#             cursor.execute(query, (id_wp, projeto["id_projeto"]))
#             conn.commit()
#             conn.close()

#             st.success("✅ Projeto excluído com sucesso!")
#             st.cache_data.clear()
#             st.session_state["proj_action"] = None
#             st.rerun()
#         except Exception as e:
#             st.error(f"Erro ao excluir projeto: {e}")


# # ========== FUNÇÕES DE WORK PACKAGES ==========
# def exibir_work_packages(wps_df):
#     """
#     Exibe a lista de Work Packages e as opções de gerenciamento
#     em duas colunas (SEM renderizar operações aqui).
#     """
#     col1, col2 = st.columns([1, 1])

#     with col1:
#         st.subheader("📋 Lista de Work Packages")
        
#         # Exibir apenas as colunas desejadas (incluindo menu)
#         wps_display = wps_df[["wp", "titulo", "menu", "gerente"]]
#         st.dataframe(wps_display, height=400, hide_index=True)

#         st.write("**Gerenciamento de Work Packages:**")
#         colbtn1, colbtn2, colbtn3, colbtn4 = st.columns([1, 1, 1, 1])

#         with colbtn1:
#             if st.button("➕ Incluir", key="btn_incluir_wp"):
#                 st.session_state["wp_action"] = "incluir"
#                 st.rerun()
#         with colbtn2:
#             if st.button("✏️ Alterar", key="btn_alterar_wp"):
#                 st.session_state["wp_action"] = "alterar"
#                 st.rerun()
#         with colbtn3:
#             if st.button("👥 Colaboradores", key="btn_colab_wp"):
#                 st.session_state["wp_action"] = "incluir_colaboradores"
#                 st.rerun()
#         with colbtn4:
#             if st.button("❌ Excluir", key="btn_excluir_wp"):
#                 st.session_state["wp_action"] = "excluir"
#                 st.rerun()

#     with col2:
#         st.subheader("ℹ️ Detalhes do Work Package")
        
#         # Selecionar um WP para exibir detalhes
#         wp_selecionado = st.selectbox(
#             "Selecione um WP para ver detalhes:",
#             options=wps_df["id_wp"].tolist(),
#             format_func=lambda x: f"WP {wps_df[wps_df['id_wp'] == x]['wp'].values[0]} | {wps_df[wps_df['id_wp'] == x]['titulo'].values[0]}",
#             key="select_wp_detalhes"
#         )
        
#         if wps_df[wps_df["id_wp"] == wp_selecionado].shape[0] > 0:
#             wp_info = wps_df[wps_df["id_wp"] == wp_selecionado].iloc[0]
            
#             # Exibir descrição
#             st.write("**Descrição:**")
#             st.write(wp_info["descricao"])
            
#             # Exibir menu
#             st.write("**Menu:**")
#             st.write(wp_info["menu"] if pd.notna(wp_info["menu"]) else "Não definido")
            
#             # Exibir lista de colaboradores
#             st.write("**Colaboradores:**")
            
#             @st.cache_data
#             def load_colaboradores_wp(id_wp):
#                 try:
#                     conn = conectar_banco()
#                     query = """
#                         SELECT 
#                             c.nome,
#                             c.formacao,
#                             c.link_internet
#                         FROM lista_colab lc
#                         JOIN colaboradores c ON lc.id_colaborador = c.id_colaborador
#                         WHERE lc.id_wp = %s
#                         ORDER BY c.nome
#                     """
#                     df = pd.read_sql_query(query, conn, params=(id_wp,))
#                     conn.close()
#                     return df
#                 except Exception as e:
#                     st.error(f"Erro ao carregar colaboradores do WP: {e}")
#                     return pd.DataFrame()
            
#             colaboradores_wp = load_colaboradores_wp(wp_selecionado)
            
#             if not colaboradores_wp.empty:
#                 # Exibir tabela com controle de largura
#                 st.dataframe(
#                     colaboradores_wp[["nome", "formacao", "link_internet"]], 
#                     hide_index=True, 
#                     use_container_width=True,
#                     column_config={
#                         "nome": st.column_config.TextColumn("Nome", width="medium"),
#                         "formacao": st.column_config.TextColumn("Formação", width="medium"),
#                         "link_internet": st.column_config.LinkColumn("Link", width="small")
#                     }
#                 )
#             else:
#                 st.info("ℹ️ Nenhum colaborador associado a este WP.")

# def incluir_wp():
#     """Função para criar um Work Package novo."""
#     st.subheader("➕ Incluir Novo Work Package")
    
#     @st.cache_data
#     def load_colaboradores():
#         try:
#             conn = conectar_banco()
#             query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
#             df = pd.read_sql(query, conn)
#             conn.close()
#             return df
#         except Exception as e:
#             st.error(f"Erro ao carregar colaboradores: {e}")
#             return pd.DataFrame()
    
#     colaboradores_df = load_colaboradores()
    
#     with st.form("form_incluir_wp", clear_on_submit=True):
#         wp = st.number_input("Número do WP *", min_value=1, step=1)
#         titulo = st.text_input("Título *", placeholder="Digite o título")
#         descricao = st.text_area("Descrição *", placeholder="Digite a descrição")
#         menu = st.text_input("Menu *", placeholder="Digite o nome do menu")
        
#         if not colaboradores_df.empty:
#             gerente_id = st.selectbox(
#                 "Gerente Responsável *",
#                 options=colaboradores_df["id_colaborador"].tolist(),
#                 format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
#                 key="select_gerente_incluir"
#             )
#         else:
#             st.warning("⚠️ Nenhum colaborador disponível. Cadastre colaboradores primeiro.")
#             gerente_id = None
        
#         salvar = st.form_submit_button("💾 Salvar")

#         if salvar:
#             if not titulo or not descricao or not menu or gerente_id is None:
#                 st.error("❌ Preencha todos os campos obrigatórios.")
#                 return
            
#             try:
#                 conn = conectar_banco()
#                 cursor = conn.cursor()

#                 cursor.execute(
#                     """
#                     INSERT INTO wps (wp, titulo, descricao, menu, id_gerente)
#                     VALUES (%s, %s, %s, %s, %s)
#                     """,
#                     (wp, titulo, descricao, menu, gerente_id)
#                 )
#                 conn.commit()
#                 conn.close()
                
#                 st.success(f"✅ WP {wp} incluído com sucesso!")
#                 st.cache_data.clear()
#                 st.session_state["wp_action"] = None
#                 st.rerun()
#             except Exception as e:
#                 st.error(f"Erro ao incluir Work Package: {e}")


# def alterar_wp(wps_df):
#     """Função para alterar um Work Package existente."""
#     st.subheader("✏️ Alterar Work Package")
    
#     @st.cache_data
#     def load_colaboradores():
#         try:
#             conn = conectar_banco()
#             query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
#             df = pd.read_sql(query, conn)
#             conn.close()
#             return df
#         except Exception as e:
#             st.error(f"Erro ao carregar colaboradores: {e}")
#             return pd.DataFrame()
    
#     colaboradores_df = load_colaboradores()
    
#     wp_escolhido = st.selectbox("Escolha o WP para alteração:", wps_df["titulo"].tolist(), key="select_wp_alterar")
#     wp_atual = wps_df[wps_df["titulo"] == wp_escolhido].iloc[0]

#     with st.form("form_alterar_wp", clear_on_submit=False):
#         titulo = st.text_input("Título", wp_atual["titulo"])
#         descricao = st.text_area("Descrição", wp_atual["descricao"])
#         menu = st.text_input("Menu", value=wp_atual["menu"] if pd.notna(wp_atual["menu"]) else "")
        
#         if not colaboradores_df.empty:
#             gerente_id = st.selectbox(
#                 "Gerente",
#                 options=colaboradores_df["id_colaborador"].tolist(),
#                 format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
#                 key="select_gerente_alterar"
#             )
#         else:
#             gerente_id = None
        
#         salvar = st.form_submit_button("💾 Salvar Alterações")

#         if salvar:
#             try:
#                 conn = conectar_banco()
#                 cursor = conn.cursor()

#                 # Converter valores numpy para tipos Python nativos
#                 wp_id = int(wp_atual["id_wp"])
#                 gerente_id_int = int(gerente_id) if gerente_id is not None else None

#                 cursor.execute(
#                     """
#                     UPDATE wps SET titulo=%s, descricao=%s, menu=%s, id_gerente=%s
#                     WHERE id_wp=%s
#                     """,
#                     (titulo, descricao, menu, gerente_id_int, wp_id)
#                 )
#                 conn.commit()
#                 conn.close()
                
#                 st.success(f"✅ WP alterado com sucesso!")
#                 st.cache_data.clear()
#                 st.session_state["wp_action"] = None
#                 st.rerun()
#             except Exception as e:
#                 st.error(f"Erro ao alterar Work Package: {e}")

# def incluir_colaboradores_wp(wps_df):
#     """Função para incluir colaboradores em um Work Package."""
#     st.subheader("👥 Incluir Colaboradores no Work Package")
    
#     @st.cache_data
#     def load_colaboradores():
#         try:
#             conn = conectar_banco()
#             query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
#             df = pd.read_sql(query, conn)
#             conn.close()
#             return df
#         except Exception as e:
#             st.error(f"Erro ao carregar colaboradores: {e}")
#             return pd.DataFrame()
    
#     @st.cache_data
#     def load_colaboradores_wp(id_wp):
#         try:
#             conn = conectar_banco()
#             query = """
#                 SELECT 
#                     lc.id_lista_colab,
#                     c.id_colaborador,
#                     c.nome
#                 FROM lista_colab lc
#                 JOIN colaboradores c ON lc.id_colaborador = c.id_colaborador
#                 WHERE lc.id_wp = %s
#                 ORDER BY c.nome
#             """
#             df = pd.read_sql_query(query, conn, params=(id_wp,))
#             conn.close()
#             return df
#         except Exception as e:
#             st.error(f"Erro ao carregar colaboradores do WP: {e}")
#             return pd.DataFrame()
    
#     colaboradores_df = load_colaboradores()
    
#     wp_escolhido = st.selectbox(
#         "Escolha o WP:",
#         options=wps_df["id_wp"].tolist(),
#         format_func=lambda x: f"WP {wps_df[wps_df['id_wp'] == x]['wp'].values[0]} | {wps_df[wps_df['id_wp'] == x]['titulo'].values[0]}",
#         key="select_wp_colab"
#     )
    
#     if wp_escolhido:
#         colaboradores_wp = load_colaboradores_wp(wp_escolhido)
        
#         st.write(f"**Colaboradores atuais do WP:**")
#         if not colaboradores_wp.empty:
#             st.dataframe(colaboradores_wp[["nome"]], hide_index=True)
            
#             # Opção de remover colaborador
#             if st.checkbox("Remover colaborador?", key="check_remover_colab"):
#                 colab_remover = st.selectbox(
#                     "Selecione o colaborador para remover:",
#                     options=colaboradores_wp["id_lista_colab"].tolist(),
#                     format_func=lambda x: colaboradores_wp[colaboradores_wp["id_lista_colab"] == x]["nome"].values[0],
#                     key="select_remover_colab"
#                 )
                
#                 if st.button("❌ Remover Colaborador", key="btn_remover_colab"):
#                     try:
#                         conn = conectar_banco()
#                         cursor = conn.cursor()
#                         cursor.execute("DELETE FROM lista_colab WHERE id_lista_colab = %s", (colab_remover,))
#                         conn.commit()
#                         conn.close()
#                         st.success("✅ Colaborador removido com sucesso!")
#                         st.cache_data.clear()
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"Erro ao remover colaborador: {e}")
#         else:
#             st.info("ℹ️ Nenhum colaborador associado a este WP ainda.")
        
#         st.write("**Adicionar novo colaborador:**")
#         if not colaboradores_df.empty:
#             novo_colaborador = st.selectbox(
#                 "Selecione o colaborador:",
#                 options=colaboradores_df["id_colaborador"].tolist(),
#                 format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
#                 key="select_novo_colab"
#             )
            
#             if st.button("➕ Adicionar Colaborador", key="btn_add_colab"):
#                 try:
#                     conn = conectar_banco()
#                     cursor = conn.cursor()
#                     cursor.execute(
#                         "INSERT INTO lista_colab (id_colaborador, id_wp) VALUES (%s, %s)",
#                         (novo_colaborador, wp_escolhido)
#                     )
#                     conn.commit()
#                     conn.close()
#                     st.success("✅ Colaborador adicionado com sucesso!")
#                     st.cache_data.clear()
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Erro ao adicionar colaborador: {e}")
#         else:
#             st.warning("⚠️ Nenhum colaborador disponível.")


# def excluir_wp(wps_df):
#     """Função para excluir um Work Package existente."""
#     st.subheader("❌ Excluir Work Package")
    
#     wp_escolhido = st.selectbox(
#         "Escolha o WP para exclusão:",
#         options=wps_df["id_wp"].tolist(),
#         format_func=lambda x: f"WP {wps_df[wps_df['id_wp'] == x]['wp'].values[0]} | {wps_df[wps_df['id_wp'] == x]['titulo'].values[0]}",
#         key="select_wp_excluir"
#     )

#     st.warning("⚠️ Esta ação é irreversível e removerá todos os dados associados.")
    
#     if st.button("Confirmar Exclusão", key="btn_confirmar_excluir_wp"):
#         try:
#             conn = conectar_banco()
#             cursor = conn.cursor()

#             # Remover colaboradores associados
#             cursor.execute("DELETE FROM lista_colab WHERE id_wp = %s", (wp_escolhido,))
            
#             # Remover projetos associados
#             cursor.execute("DELETE FROM projetos_wps WHERE id_wp = %s", (wp_escolhido,))
            
#             # Remover WP
#             cursor.execute("DELETE FROM wps WHERE id_wp = %s", (wp_escolhido,))
            
#             conn.commit()
#             conn.close()
            
#             st.success(f"✅ WP excluído com sucesso!")
#             st.cache_data.clear()
#             st.session_state["wp_action"] = None
#             st.rerun()
#         except Exception as e:
#             st.error(f"Erro ao excluir Work Package: {e}")
