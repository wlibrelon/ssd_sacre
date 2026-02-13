import streamlit as st
import pandas as pd
from funcoes_app import conectar_banco


def show():
    """
    Módulo de gerenciamento de Projetos dos Work Packages
    """
    st.title("Projetos dos Work Packages")

    @st.cache_data
    def load_wps_list():
        try:
            conn = conectar_banco()
            query = "SELECT id_wp, wp, titulo FROM wps ORDER BY wp"
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar Work Packages do banco: {e}")
            return pd.DataFrame()

    @st.cache_data
    def load_proj_wps(id_wp):
        try:
            conn = conectar_banco()
            query = """
                SELECT 
                    id_projeto, 
                    titulo,
                    c.nome AS autor
                FROM projetos_wps p
                LEFT JOIN colaboradores c ON p.id_autor = c.id_colaborador
                WHERE p.id_wp = %s
            """
            df = pd.read_sql_query(query, conn, params=(id_wp,))
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar Projetos dos Work Packages do banco: {e}")
            return pd.DataFrame()

    @st.cache_data
    def load_proj_detalhes(id_projeto):
        try:
            conn = conectar_banco()
            query = """
                SELECT 
                    resumo,
                    objetivos
                FROM projetos_wps
                WHERE id_projeto = %s
            """
            df = pd.read_sql_query(query, conn, params=(id_projeto,))
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar detalhes do projeto: {e}")
            return pd.DataFrame()

    @st.cache_data
    def load_resultados_projeto(id_projeto):
        """Carrega resultados do projeto"""
        try:
            conn = conectar_banco()
            query = """
                SELECT 
                    id_arq_res,
                    id_projeto,
                    descricao,
                    nome_arq
                FROM arq_resultados
                WHERE id_projeto = %s
                ORDER BY descricao
            """
            df = pd.read_sql_query(query, conn, params=(id_projeto,))
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar resultados do projeto: {e}")
            return pd.DataFrame()

    # Carregar os Work Packages
    wps_df = load_wps_list()
    if wps_df.empty:
        st.warning("⚠️ Nenhum Work Package encontrado no banco de dados.")
        return

    # Seleção do WP
    wp_selecionado = st.selectbox(
        "Selecione um Work Package para visualizar os projetos:",
        options=wps_df["id_wp"].tolist(),
        format_func=lambda x: f"WP {wps_df[wps_df['id_wp'] == x]['wp'].values[0]} | {wps_df[wps_df['id_wp'] == x]['titulo'].values[0]}",
        key="select_wp_projetos"
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
                if st.button("➕ Incluir Primeiro Projeto", key="btn_primeiro_proj"):
                    st.session_state["proj_action"] = "incluir"
                    st.rerun()
            else:
                # Exibir apenas titulo e autor (sem resumo e objetivos)
                projetos_display = projetos_df[["titulo", "autor"]]
                st.dataframe(
                    projetos_display,
                    height=400,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "titulo": st.column_config.TextColumn("Título", width="large"),
                        "autor": st.column_config.TextColumn("Autor", width="medium")
                    }
                )

                st.write("**Gerenciamento de Projetos:**")
                colbtn1, colbtn2, colbtn3 = st.columns(3)
                with colbtn1:
                    if st.button("➕ Incluir Projeto", key="btn_incluir_proj"):
                        st.session_state["proj_action"] = "incluir"
                        st.rerun()
                with colbtn2:
                    if st.button("✏️ Alterar Projeto", key="btn_alterar_proj"):
                        st.session_state["proj_action"] = "alterar"
                        st.rerun()
                with colbtn3:
                    if st.button("❌ Excluir Projeto", key="btn_excluir_proj"):
                        st.session_state["proj_action"] = "excluir"
                        st.rerun()

        with col2:
            st.subheader("ℹ️ Detalhes do Projeto")
            
            # Selecionar um projeto para exibir detalhes
            if not projetos_df.empty:
                proj_selecionado = st.selectbox(
                    "Selecione um projeto para ver detalhes:",
                    options=projetos_df["id_projeto"].tolist(),
                    format_func=lambda x: projetos_df[projetos_df["id_projeto"] == x]["titulo"].values[0],
                    key="select_proj_detalhes"
                )
                
                if projetos_df[projetos_df["id_projeto"] == proj_selecionado].shape[0] > 0:
                    proj_info = projetos_df[projetos_df["id_projeto"] == proj_selecionado].iloc[0]
                    proj_detalhes = load_proj_detalhes(proj_selecionado)
                    
                    # Exibir resumo
                    st.write("**Resumo:**")
                    if not proj_detalhes.empty:
                        st.write(proj_detalhes.iloc[0]["resumo"])
                    
                    # Exibir objetivos
                    st.write("**Objetivos:**")
                    if not proj_detalhes.empty:
                        st.write(proj_detalhes.iloc[0]["objetivos"])
                    
                    # Separador
                    st.markdown("---")
                    
                    # Seção de Resultados do Projeto
                    st.write("**📊 Resultados do Projeto:**")
                    
                    resultados_df = load_resultados_projeto(int(proj_selecionado))
                    
                    if not resultados_df.empty:
                        # Exibir tabela de resultados
                        st.dataframe(
                            resultados_df[["descricao", "nome_arq"]],
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "descricao": st.column_config.TextColumn("Descrição", width="large"),
                                "nome_arq": st.column_config.TextColumn("Nome do Arquivo", width="medium")
                            }
                        )
                        
                        # Botões de ação para resultados
                        st.write("**Gerenciamento de Resultados:**")
                        colres1, colres2, colres3 = st.columns(3)
                        
                        with colres1:
                            if st.button("➕ Incluir Resultado", key="btn_incluir_resultado"):
                                st.session_state["resultado_action"] = "incluir"
                                st.session_state["proj_selecionado_resultado"] = int(proj_selecionado)
                                st.rerun()
                        
                        with colres2:
                            if st.button("✏️ Alterar Resultado", key="btn_alterar_resultado"):
                                st.session_state["resultado_action"] = "alterar"
                                st.session_state["proj_selecionado_resultado"] = int(proj_selecionado)
                                st.rerun()
                        
                        with colres3:
                            if st.button("❌ Excluir Resultado", key="btn_excluir_resultado"):
                                st.session_state["resultado_action"] = "excluir"
                                st.session_state["proj_selecionado_resultado"] = int(proj_selecionado)
                                st.rerun()
                    else:
                        st.info("ℹ️ Nenhum resultado encontrado para este projeto.")
                        if st.button("➕ Incluir Primeiro Resultado", key="btn_primeiro_resultado"):
                            st.session_state["resultado_action"] = "incluir"
                            st.session_state["proj_selecionado_resultado"] = int(proj_selecionado)
                            st.rerun()
            else:
                st.info("ℹ️ Selecione um projeto para ver os detalhes.")

        # Renderizar operações de projetos (FORA das colunas)
        if "proj_action" in st.session_state and st.session_state["proj_action"]:
            st.divider()
            if st.session_state["proj_action"] == "incluir":
                incluir_projeto(st.session_state["wp_selecionado"])
            elif st.session_state["proj_action"] == "alterar":
                alterar_projeto(st.session_state["wp_selecionado"], projetos_df)
            elif st.session_state["proj_action"] == "excluir":
                excluir_projeto(st.session_state["wp_selecionado"], projetos_df)

        # Renderizar operações de resultados (FORA das colunas)
        if "resultado_action" in st.session_state and st.session_state["resultado_action"]:
            st.divider()
            proj_id = st.session_state.get("proj_selecionado_resultado")
            if st.session_state["resultado_action"] == "incluir":
                incluir_resultado(proj_id)
            elif st.session_state["resultado_action"] == "alterar":
                resultados_df = load_resultados_projeto(proj_id)
                alterar_resultado(proj_id, resultados_df)
            elif st.session_state["resultado_action"] == "excluir":
                resultados_df = load_resultados_projeto(proj_id)
                excluir_resultado(proj_id, resultados_df)


# ========== FUNÇÕES DE PROJETOS ==========

def incluir_projeto(id_wp):
    st.subheader("➕ Incluir um novo projeto")
    
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
    
    with st.form("form_incluir_projeto", clear_on_submit=True):
        titulo = st.text_input("Título do projeto *", placeholder="Digite o título")
        
        if not colaboradores_df.empty:
            id_autor = st.selectbox(
                "Autor *",
                options=colaboradores_df["id_colaborador"].tolist(),
                format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
                key="select_autor_proj"
            )
        else:
            st.warning("⚠️ Nenhum colaborador disponível.")
            id_autor = None
        
        resumo = st.text_area("Resumo *", placeholder="Digite o resumo")
        objetivos = st.text_area("Objetivos *", placeholder="Digite os objetivos")
        
        salvar = st.form_submit_button("💾 Salvar Novo Projeto")

        if salvar:
            if not titulo or not resumo or not objetivos or id_autor is None:
                st.error("❌ Preencha todos os campos obrigatórios.")
                return
            
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                query = "INSERT INTO projetos_wps (id_wp, titulo, id_autor, resumo, objetivos) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (id_wp, titulo, id_autor, resumo, objetivos))
                conn.commit()
                conn.close()

                st.success("✅ Projeto incluído com sucesso!")
                st.cache_data.clear()
                st.session_state["proj_action"] = None
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao incluir projeto: {e}")


def alterar_projeto(id_wp, projetos_df):
    st.subheader("✏️ Alterar Projeto Existente")

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
    def load_proj_completo(id_projeto):
        """Carrega todos os dados do projeto incluindo resumo e objetivos"""
        try:
            conn = conectar_banco()
            query = """
                SELECT 
                    id_projeto,
                    titulo,
                    id_autor,
                    resumo,
                    objetivos
                FROM projetos_wps
                WHERE id_projeto = %s
            """
            df = pd.read_sql_query(query, conn, params=(id_projeto,))
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados completos do projeto: {e}")
            return pd.DataFrame()

    colaboradores_df = load_colaboradores()

    projeto_titulo = st.selectbox("Selecione o projeto:", projetos_df["titulo"].tolist(), key="select_proj_alterar")
    projeto = projetos_df[projetos_df["titulo"] == projeto_titulo].iloc[0]
    
    # Carregar dados completos do projeto
    projeto_completo_df = load_proj_completo(int(projeto["id_projeto"]))
    
    if projeto_completo_df.empty:
        st.error("Projeto não encontrado.")
        return
    
    projeto_completo = projeto_completo_df.iloc[0]

    with st.form("form_alterar_projeto", clear_on_submit=False):
        novo_titulo = st.text_input("Título:", projeto_completo["titulo"])
        
        if not colaboradores_df.empty:
            novo_id_autor = st.selectbox(
                "Autor:",
                options=colaboradores_df["id_colaborador"].tolist(),
                format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
                index=0,
                key="select_autor_alterar"
            )
        else:
            novo_id_autor = None
        
        novo_resumo = st.text_area("Resumo:", value=projeto_completo["resumo"] if pd.notna(projeto_completo["resumo"]) else "")
        novos_objetivos = st.text_area("Objetivos:", value=projeto_completo["objetivos"] if pd.notna(projeto_completo["objetivos"]) else "")

        salvar = st.form_submit_button("💾 Salvar Alterações")

        if salvar:
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                query = """
                    UPDATE projetos_wps SET titulo = %s, id_autor = %s, resumo = %s, objetivos = %s
                    WHERE id_wp = %s AND id_projeto = %s
                """
                cursor.execute(query, (novo_titulo, novo_id_autor, novo_resumo, novos_objetivos, id_wp, int(projeto_completo["id_projeto"])))
                conn.commit()
                conn.close()

                st.success("✅ Projeto alterado com sucesso!")
                st.cache_data.clear()
                st.session_state["proj_action"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao alterar projeto: {e}")


def excluir_projeto(id_wp, projetos_df):
    st.subheader("❌ Excluir Projeto")

    projeto_selecionado = st.selectbox("Selecione o projeto para excluir:", projetos_df["titulo"].tolist(), key="select_proj_excluir")
    projeto = projetos_df[projetos_df["titulo"] == projeto_selecionado].iloc[0]

    st.warning("⚠️ Esta ação é irreversível.")

    if st.button("Confirmar Exclusão", key="btn_confirmar_excluir_proj"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()
            query = "DELETE FROM projetos_wps WHERE id_wp = %s AND id_projeto = %s"
            cursor.execute(query, (id_wp, int(projeto["id_projeto"])))
            conn.commit()
            conn.close()

            st.success("✅ Projeto excluído com sucesso!")
            st.cache_data.clear()
            st.session_state["proj_action"] = None
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao excluir projeto: {e}")


# ========== FUNÇÕES DE RESULTADOS ==========

def incluir_resultado(id_projeto):
    """Função para incluir um novo resultado"""
    st.subheader("➕ Incluir Novo Resultado")
    
    with st.form("form_incluir_resultado", clear_on_submit=True):
        descricao = st.text_input("Descrição *", placeholder="Digite a descrição do resultado")
        nome_arq = st.text_input("Nome do Arquivo *", placeholder="Ex: resultado.pdf")
        
        salvar = st.form_submit_button("💾 Salvar Resultado")

        if salvar:
            if not descricao or not nome_arq:
                st.error("❌ Preencha todos os campos obrigatórios.")
                return
            
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                query = "INSERT INTO arq_resultados (id_projeto, descricao, nome_arq) VALUES (%s, %s, %s)"
                cursor.execute(query, (id_projeto, descricao, nome_arq))
                conn.commit()
                conn.close()

                st.success("✅ Resultado incluído com sucesso!")
                st.cache_data.clear()
                st.session_state["resultado_action"] = None
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao incluir resultado: {e}")


def alterar_resultado(id_projeto, resultados_df):
    """Função para alterar um resultado existente"""
    st.subheader("✏️ Alterar Resultado Existente")
    
    if resultados_df.empty:
        st.warning("⚠️ Nenhum resultado disponível para alteração.")
        return
    
    resultado_selecionado = st.selectbox(
        "Selecione o resultado para alteração:",
        options=resultados_df["id_arq_res"].tolist(),
        format_func=lambda x: resultados_df[resultados_df["id_arq_res"] == x]["descricao"].values[0],
        key="select_resultado_alterar"
    )
    
    resultado = resultados_df[resultados_df["id_arq_res"] == resultado_selecionado].iloc[0]

    with st.form("form_alterar_resultado", clear_on_submit=False):
        nova_descricao = st.text_input("Descrição:", value=resultado["descricao"])
        novo_nome_arq = st.text_input("Nome do Arquivo:", value=resultado["nome_arq"])
        
        salvar = st.form_submit_button("💾 Salvar Alterações")

        if salvar:
            if not nova_descricao or not novo_nome_arq:
                st.error("❌ Preencha todos os campos obrigatórios.")
                return
            
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                query = """
                    UPDATE arq_resultados 
                    SET descricao = %s, nome_arq = %s
                    WHERE id_arq_res = %s AND id_projeto = %s
                """
                cursor.execute(query, (nova_descricao, novo_nome_arq, int(resultado_selecionado), id_projeto))
                conn.commit()
                conn.close()

                st.success("✅ Resultado alterado com sucesso!")
                st.cache_data.clear()
                st.session_state["resultado_action"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao alterar resultado: {e}")


def excluir_resultado(id_projeto, resultados_df):
    """Função para excluir um resultado existente"""
    st.subheader("❌ Excluir Resultado")
    
    if resultados_df.empty:
        st.warning("⚠️ Nenhum resultado disponível para exclusão.")
        return
    
    resultado_selecionado = st.selectbox(
        "Selecione o resultado para exclusão:",
        options=resultados_df["id_arq_res"].tolist(),
        format_func=lambda x: resultados_df[resultados_df["id_arq_res"] == x]["descricao"].values[0],
        key="select_resultado_excluir"
    )
    
    resultado = resultados_df[resultados_df["id_arq_res"] == resultado_selecionado].iloc[0]
    
    if st.button("Confirmar Exclusão", key="btn_confirmar_excluir_resultado"):
        try:
            conn = conectar_banco()
            cursor = conn.cursor()
            query = "DELETE FROM arq_resultados WHERE id_arq_res = %s AND id_projeto = %s"
            cursor.execute(query, (int(resultado_selecionado), id_projeto))
            conn.commit()
            conn.close()

            st.success("✅ Resultado excluído com sucesso!")
            st.cache_data.clear()
            st.session_state["resultado_action"] = None
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao excluir resultado: {e}")