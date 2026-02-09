# gerenciar_artigos.py

import streamlit as st
import pandas as pd
from funcoes_app import conectar_banco
import pathlib
import os

# --- Configurações Globais ---
PDF_DIRECTORY = "pdfs_artigos"

# --- Funções Auxiliares de Carregamento de Dados ---

@st.cache_data
def load_pdfs_disponiveis():
    """Carrega lista de arquivos PDF disponíveis no diretório"""
    pdf_paths = []
    try:
        base_path = pathlib.Path(PDF_DIRECTORY)
        base_path.mkdir(parents=True, exist_ok=True)
        for item in base_path.iterdir():
            if item.is_file() and item.suffix.lower() == '.pdf':
                pdf_paths.append(str(item))
    except OSError as e:
        st.error(f"Erro ao acessar diretório de PDFs: {e}")
    return pdf_paths

@st.cache_data
def load_artigos():
    """Carrega todos os artigos"""
    try:
        conn = conectar_banco()
        query = """
            SELECT id_Artigo, titulo, tipo, id_projeto, resumo, abstract, doi, pasta_pdf
            FROM artigos ORDER BY id_Artigo DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar artigos: {e}")
        return pd.DataFrame()

@st.cache_data
def load_projetos():
    """Carrega lista de projetos"""
    try:
        conn = conectar_banco()
        query = "SELECT id_projeto, titulo FROM projetos_wps ORDER BY titulo"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {e}")
        return pd.DataFrame()

@st.cache_data
def load_colaboradores():
    """Carrega lista de colaboradores"""
    try:
        conn = conectar_banco()
        query = "SELECT id_colaborador, nome FROM colaboradores ORDER BY nome"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar colaboradores: {e}")
        return pd.DataFrame()

# --- Funções de Exibição e Interação ---

def exibir_tabela_artigos_autores(artigos_df, colaboradores_df, projetos_df):
    """Exibe tabela formatada com layout solicitado"""
    
    # Cabeçalho da Tabela (Colunas ajustadas: 2, 1.5, 2.5)
    c1, c2, c3 = st.columns([3, 1.5, 0.8])
    with c1: st.write("**Artigo**")
    with c2: st.write("**Autores**")
    with c3: st.write("**Gestão e Comandos**")
    # st.markdown("---")
    st.markdown("""
    <style>
        hr {margin: 0.25rem 0 !important;}
    </style>
    <hr>
    """, unsafe_allow_html=True)


    # Iterar sobre artigos
    for idx, row in artigos_df.iterrows():
        id_artigo = row['id_Artigo']
        titulo = row['titulo']
        tipo = row['tipo']

        c1, c2, c3 = st.columns([3, 1.5, 0.8])

        # COLUNA 1: Artigo, Tipo e Botão Selecionar
        with c1:
            st.write(f"**{id_artigo}** - {titulo}")
            st.caption(f"Tipo: {tipo}")

            if st.button("👥 Selecionar Autores", key=f"btn_sel_{id_artigo}"):
                st.session_state['artigo_selecionado_id'] = id_artigo
                st.rerun()

        # COLUNA 2: Lista de Autores (largura reduzida)
        with c2:
            autores_df = pd.read_sql_query(
                "SELECT c.nome FROM artigos_autores aa JOIN colaboradores c ON aa.id_autor = c.id_colaborador WHERE aa.id_artigo = %s ORDER BY c.nome",
                conectar_banco(), params=(id_artigo,)
            )
            if not autores_df.empty:
                for autor in autores_df['nome'].tolist():
                    st.caption(f"• {autor}")
            else:
                st.caption("*Sem autores*")

        # COLUNA 3: Comandos de Gestão
        with c3:
            # Se este artigo estiver selecionado para gerenciar autores
            if st.session_state.get('artigo_selecionado_id') == id_artigo:
                with st.container(border=True):
                    st.write("**:blue[Gerenciar Autores]**")
                    gerenciar_autores_inline(id_artigo, colaboradores_df)
            
            # Botões de Alterar e Excluir
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✏️ Alterar", key=f"btn_alt_{id_artigo}", use_container_width=True):
                    st.session_state['artigo_action'] = "alterar"
                    st.session_state['artigo_alvo'] = id_artigo
                    st.rerun()
            # with col_b:
                if st.button("🗑️ Excluir", key=f"btn_exc_{id_artigo}", use_container_width=True):
                    st.session_state['artigo_action'] = "excluir"
                    st.session_state['artigo_alvo'] = id_artigo
                    st.rerun()

        st.markdown("---")

def gerenciar_autores_inline(id_artigo, colaboradores_df):
    """Gerencia autores diretamente na coluna 3"""
    autores_atuais_df = pd.read_sql_query(
        "SELECT id_autor FROM artigos_autores WHERE id_artigo = %s",
        conectar_banco(), params=(id_artigo,)
    )
    autores_atuais = autores_atuais_df["id_autor"].tolist()
    
    novos_autores = st.multiselect(
        "Autores:",
        options=colaboradores_df["id_colaborador"].tolist(),
        default=autores_atuais,
        format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"] == x]["nome"].values[0],
        key=f"multi_aut_{id_artigo}",
        label_visibility="collapsed",
        placeholder="Selecione os autores..." 
    )
    
    c_salvar, c_cancel = st.columns(2)
    if c_salvar.button("💾 Salvar", key=f"save_aut_{id_artigo}", use_container_width=True):
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM artigos_autores WHERE id_artigo = %s", (id_artigo,))
        for id_autor in novos_autores:
            cursor.execute("INSERT INTO artigos_autores (id_artigo, id_autor) VALUES (%s, %s)", (id_artigo, id_autor))
        conn.commit()
        conn.close()
        st.success("Atualizado!")
        st.session_state['artigo_selecionado_id'] = None
        st.rerun()
        
    if c_cancel.button("❌ Fechar", key=f"cancel_aut_{id_artigo}", use_container_width=True):
        st.session_state['artigo_selecionado_id'] = None
        st.rerun()

# --- Formulários de Ação ---

def form_incluir(projetos_df, colaboradores_df):
    st.info("➕ **Novo Artigo**")
    pdfs = load_pdfs_disponiveis()
    pdf_nomes = [pathlib.Path(p).name for p in pdfs]
    pdf_map = {pathlib.Path(p).name: p for p in pdfs}

    with st.form("form_incluir"):
        titulo = st.text_input("Título *")
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo *", ["SACRE", "Referência"])
        proj = c2.selectbox("Projeto", [None] + projetos_df["id_projeto"].tolist(), 
                          format_func=lambda x: "Nenhum" if x is None else f"{x} - {projetos_df[projetos_df['id_projeto']==x]['titulo'].values[0]}")
        
        pdf_sel = st.selectbox("Arquivo PDF", [None] + pdf_nomes)
        resumo = st.text_area("Resumo")
        abstract = st.text_area("Abstract")
        doi = st.text_input("DOI")
        autores = st.multiselect("Autores Iniciais", colaboradores_df["id_colaborador"].tolist(), 
                               format_func=lambda x: colaboradores_df[colaboradores_df["id_colaborador"]==x]["nome"].values[0])
        
        if st.form_submit_button("💾 Criar Artigo", use_container_width=True):
            if not titulo: return st.error("Título obrigatório")
            conn = conectar_banco()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO artigos (titulo, tipo, id_projeto, resumo, abstract, doi, pasta_pdf) 
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""", 
                           (titulo, tipo, proj, resumo, abstract, doi, pdf_map.get(pdf_sel)))
            new_id = cursor.lastrowid
            for aut in autores:
                cursor.execute("INSERT INTO artigos_autores (id_artigo, id_autor) VALUES (%s,%s)", (new_id, aut))
            conn.commit()
            conn.close()
            st.success("Criado!")
            st.session_state['artigo_action'] = None
            st.rerun()

def form_alterar(id_artigo, projetos_df):
    st.info(f"✏️ **Editando Artigo {id_artigo}**")
    conn = conectar_banco()
    artigo = pd.read_sql_query("SELECT * FROM artigos WHERE id_Artigo = %s", conn, params=(id_artigo,)).iloc[0]
    conn.close()

    pdfs = load_pdfs_disponiveis()
    pdf_nomes = [pathlib.Path(p).name for p in pdfs]
    pdf_map = {pathlib.Path(p).name: p for p in pdfs}
    curr_pdf = pathlib.Path(artigo['pasta_pdf']).name if artigo['pasta_pdf'] else None
    
    idx_pdf = 0
    if curr_pdf in pdf_nomes: idx_pdf = pdf_nomes.index(curr_pdf) + 1

    with st.form("form_alterar"):
        titulo = st.text_input("Título", value=artigo['titulo'])
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["SACRE", "Referência"], index=0 if artigo['tipo']=="SACRE" else 1)
        
        proj_idx = 0
        if artigo['id_projeto'] in projetos_df['id_projeto'].tolist():
            proj_idx = projetos_df['id_projeto'].tolist().index(artigo['id_projeto']) + 1
            
        proj = c2.selectbox("Projeto", [None] + projetos_df["id_projeto"].tolist(), index=proj_idx,
                          format_func=lambda x: "Nenhum" if x is None else f"{x}")

        pdf_sel = st.selectbox("PDF", [None] + pdf_nomes, index=idx_pdf)
        resumo = st.text_area("Resumo", value=artigo['resumo'] or "")
        abstract = st.text_area("Abstract", value=artigo['abstract'] or "")
        doi = st.text_input("DOI", value=artigo['doi'] or "")
        
        if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
            conn = conectar_banco()
            cursor = conn.cursor()
            cursor.execute("""UPDATE artigos SET titulo=%s, tipo=%s, id_projeto=%s, resumo=%s, abstract=%s, doi=%s, pasta_pdf=%s 
                           WHERE id_Artigo=%s""", 
                           (titulo, tipo, proj, resumo, abstract, doi, pdf_map.get(pdf_sel), id_artigo))
            conn.commit()
            conn.close()
            st.success("Alterado!")
            st.session_state['artigo_action'] = None
            st.rerun()

def form_excluir(id_artigo):
    st.error(f"❌ **Excluir Artigo {id_artigo}?**")
    st.warning("Esta ação removerá o artigo e todos os vínculos com autores.")
    
    c1, c2 = st.columns(2)
    if c1.button("Sim, Excluir Definitivamente", use_container_width=True):
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM artigos_autores WHERE id_artigo=%s", (id_artigo,))
        cursor.execute("DELETE FROM artigos WHERE id_Artigo=%s", (id_artigo,))
        conn.commit()
        conn.close()
        st.success("Excluído!")
        st.session_state['artigo_action'] = None
        st.rerun()
        
    if c2.button("Cancelar", use_container_width=True):
        st.session_state['artigo_action'] = None
        st.rerun()

# --- MAIN ---

def show():
    st.title("Gestão de Artigos")
    
    # Inicialização de Estado
    if 'artigo_action' not in st.session_state: st.session_state['artigo_action'] = None
    if 'artigo_alvo' not in st.session_state: st.session_state['artigo_alvo'] = None
    if 'artigo_selecionado_id' not in st.session_state: st.session_state['artigo_selecionado_id'] = None

    # Dados
    artigos = load_artigos()
    projetos = load_projetos()
    colabs = load_colaboradores()

    # Botão de Inclusão no Topo (Coluna 3)
    c1, c2, c3 = st.columns([3, 1.5, 0.8])
    with c3:
        if st.button("➕ Novo Artigo", use_container_width=True):
            st.session_state['artigo_action'] = "incluir"
            st.session_state['artigo_selecionado_id'] = None
            st.rerun()

    # Renderizar Formulários de Ação (se ativos)
    if st.session_state['artigo_action'] == "incluir":
        st.divider()
        form_incluir(projetos, colabs)
        if st.button("Cancelar Inclusão"): 
            st.session_state['artigo_action'] = None
            st.rerun()
        st.divider()
    elif st.session_state['artigo_action'] == "alterar":
        st.divider()
        form_alterar(st.session_state['artigo_alvo'], projetos)
        if st.button("Cancelar Edição"):
            st.session_state['artigo_action'] = None
            st.rerun()
        st.divider()
    elif st.session_state['artigo_action'] == "excluir":
        st.divider()
        form_excluir(st.session_state['artigo_alvo'])
        st.divider()

    # Tabela Principal
    if not artigos.empty:
        exibir_tabela_artigos_autores(artigos, colabs, projetos)
    else:
        st.warning("Nenhum artigo encontrado.")