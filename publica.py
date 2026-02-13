import mysql.connector
import streamlit as st
import os
import base64
from PyPDF2 import PdfReader
from funcoes_app import exibir_pdf_no_app, conectar_banco


def show():
    PASTA_PDFS = "pdfs_artigos"  

    if not os.path.exists(PASTA_PDFS):
        os.makedirs(PASTA_PDFS)

    def buscar_artigos_por_tipo(tipo):
        """Busca artigos filtrados por tipo"""
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_Artigo, Titulo, Resumo, Abstract, doi, Pasta_PDF, Tipo FROM artigos WHERE Tipo = %s ORDER BY id_Artigo DESC",
            (tipo,)
        )
        artigos = cursor.fetchall()
        conn.close()
        return artigos

    def exibir_tabela_com_resumo_e_pdf(tipo_filtro):
        """Exibe tabela de artigos filtrados por tipo"""
        artigos = buscar_artigos_por_tipo(tipo_filtro)

        if not artigos:
            st.warning(f"Nenhum artigo do tipo '{tipo_filtro}' encontrado no banco de dados.")
            return

        margem, col1, col2, col3 = st.columns([0.05, 1, 1, 1])

        with col1:
            st.subheader(f"Artigos - {tipo_filtro}")
            for idx, artigo in enumerate(artigos):
                st.write(f"**{artigo['id_Artigo']} - {artigo['Titulo']}**")

                col_res, col_pdf, col_doi = st.columns([1.5, 1.5, 2])

                with col_res:
                    if st.button("Resumo", key=f"resumo_{artigo['id_Artigo']}"):
                        st.session_state['artigo_selecionado'] = artigo

                with col_pdf:
                    if st.button("📄 Exibir", key=f"exibir_{artigo['id_Artigo']}"):
                        st.session_state['artigo_selecionado'] = artigo
                        st.session_state['exibir_pdf'] = True

                with col_doi:
                    if artigo.get("doi"):
                        st.markdown(
                            f"""<a href="https://doi.org/{artigo['doi']}" target="_blank" style="color: #1f77b4; text-decoration: none;">
                            🔗 Acessar DOI</a>""",
                            unsafe_allow_html=True
                        )
                
                if idx < len(artigos) - 1:
                    st.markdown("""<hr style="margin-top: 3px; margin-bottom: 2px;">""", unsafe_allow_html=True)

        # Coluna 2: Exibição do Abstract (inglês)
        with col2:
            st.subheader("Abstract")
            artigo_selecionado = st.session_state.get('artigo_selecionado')

            if artigo_selecionado:
                st.text_area("", artigo_selecionado["Abstract"], height=400, disabled=True, key="abstract_display")
            else:
                st.info("Selecione um artigo para ver o abstract")

        # Coluna 3: Exibição do Resumo (português)
        with col3:
            st.subheader("Resumo")
            artigo_selecionado = st.session_state.get('artigo_selecionado')

            if artigo_selecionado:
                st.text_area("", artigo_selecionado["Resumo"], height=400, disabled=True, key="resumo_display")
            else:
                st.info("Selecione um artigo para ver o resumo")

        st.markdown("""<hr style="margin-top: 3px; margin-bottom: 2px;">""", unsafe_allow_html=True)

        # Exibir PDF se solicitado
        artigo_selecionado = st.session_state.get('artigo_selecionado')
        if st.session_state.get('exibir_pdf', False) and artigo_selecionado:
            st.markdown("---")
            st.subheader(f"📄 {artigo_selecionado['Titulo']}")
            caminho_pdf = artigo_selecionado["Pasta_PDF"]
            if os.path.exists(caminho_pdf):
                exibir_pdf_no_app(caminho_pdf)
            else:
                st.error(f"Arquivo PDF não encontrado: {caminho_pdf}")

    # Inicializar session_state
    if 'tipo_selecionado' not in st.session_state:
        st.session_state['tipo_selecionado'] = 'SACRE'
    if 'artigo_selecionado' not in st.session_state:
        st.session_state['artigo_selecionado'] = None
    if 'exibir_pdf' not in st.session_state:
        st.session_state['exibir_pdf'] = False

    # Sidebar com botões um abaixo do outro
    st.sidebar.title("Filtrar Artigos")
    
    if st.sidebar.button("📚 Artigos SACRE", key="btn_sacre", use_container_width=True):
        st.session_state['tipo_selecionado'] = 'SACRE'
        st.session_state['artigo_selecionado'] = None
        st.session_state['exibir_pdf'] = False
        st.rerun()
    
    if st.sidebar.button("📖 Artigos de Referência", key="btn_referencia", use_container_width=True):
        st.session_state['tipo_selecionado'] = 'Referência'
        st.session_state['artigo_selecionado'] = None
        st.session_state['exibir_pdf'] = False
        st.rerun()

    # Título principal
    st.title("Artigos e Publicações")

    # Exibir artigos filtrados
    exibir_tabela_com_resumo_e_pdf(st.session_state['tipo_selecionado'])