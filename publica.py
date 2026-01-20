import mysql.connector
import streamlit as st
import os
import base64
from PyPDF2 import PdfReader
from funcoes_app import exibir_pdf_no_app, conectar_banco

def show():
    PASTA_PDFS = "artigos"  

    if not os.path.exists(PASTA_PDFS):
        os.makedirs(PASTA_PDFS)

    def inserir_artigo(titulo, resumo, abstract, doi, pasta_pdf):
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO artigos (titulo, resumo, abstract, doi, pasta_pdf) VALUES (%s, %s, %s, %s, %s)", (titulo, resumo, abstract, doi, pasta_pdf))
        conn.commit()
        conn.close()

    def buscar_artigos():
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_artigo, titulo, resumo, abstract, doi,  pasta_pdf FROM artigos")
        artigos = cursor.fetchall()
        conn.close()
        return artigos

    def exibir_tabela_com_resumo_e_pdf():
        artigos = buscar_artigos()

        if not artigos:
            st.warning("Nenhum artigo encontrado no banco de dados.")
            return

        margem, col1, col2, col3 = st.columns([0.05, 1, 1, 1])

        with col1:
            st.subheader("Artigos Publicados")
            for idx, artigo in enumerate(artigos):
                st.write(f"**{artigo['id_artigo']} - {artigo['titulo']}**")

                col_res, col_doi = st.columns([2,4])

                with col_res:
                    if st.button("Resumo", key=f"resumo_{artigo['id_artigo']}"):
                        st.session_state['artigo_selecionado'] = artigo
                with col_doi:
                    if artigo.get("doi"):
                        st.markdown(
                            f"""<a href="{artigo['doi']}" target="_blank" style="color: #1f77b4; text-decoration: none;">
                            🔗 Acessar DOI</a>""",
                            unsafe_allow_html=True
                        )
                if idx < len(artigos) - 1:
                    st.markdown("""<hr style="margin-top: 3px; margin-bottom: 2px;">""",unsafe_allow_html=True)

        # Coluna 2: Exibição do Resumo inglês
        with col2:
            st.subheader("Abstract")
            artigo_selecionado = st.session_state.get('artigo_selecionado')

            if artigo_selecionado:
                st.text_area("", artigo_selecionado["abstract"], height=400, disabled=True)

        # Coluna 3: Exibição do Resumo portuguÊs
        with col3:
            st.subheader("Resumo")
            artigo_selecionado = st.session_state.get('artigo_selecionado')

            if artigo_selecionado:
                st.text_area("", artigo_selecionado["resumo"], height=400, disabled=True)

        st.markdown("""<hr style="margin-top: 3px; margin-bottom: 2px;">""",unsafe_allow_html=True)

        if st.session_state.get('modo_edicao', False) and artigo_selecionado:
            st.markdown("---")
            st.subheader("Editar Artigo Selecionado")

            novo_titulo = st.text_input("Título do Artigo", value=artigo_selecionado['titulo'])
            novo_resumo = st.text_area("Resumo", value=artigo_selecionado['resumo'])
            novo_abstract = st.text_area("Abstract", value=artigo_selecionado['abstract'])
            novo_doi = st.text_input("DOI", value=artigo_selecionado['doi'])

            if st.button("Salvar Alterações"):
                conn = conectar_banco()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE artigos 
                    SET titulo = %s, resumo = %s, abstract = %s, doi = %s 
                    WHERE id_artigo = %s
                """, (novo_titulo, novo_resumo, novo_abstract, novo_doi, artigo_selecionado['id_artigo']))
                conn.commit()
                conn.close()
                st.success("Artigo atualizado com sucesso!")
                st.session_state['modo_edicao'] = False


    st.sidebar.title("Gerenciamento de Artigos e Autores")

    if 'menu' not in st.session_state:
        st.session_state['menu'] = 'Artigos Publicados'
    if 'modo_edicao' not in st.session_state:
        st.session_state['modo_edicao'] = False
    if 'artigo_selecionado' not in st.session_state:
        st.session_state['artigo_selecionado'] = None


    if st.sidebar.button("Artigos Publicados"):
        st.session_state['menu'] = "Artigos Publicados"
        st.session_state['modo_edicao'] = False

    if st.sidebar.button("Inserir Artigos"):
        st.session_state['menu'] = "Inserir Artigos"
        st.session_state['modo_edicao'] = False

    if st.sidebar.button("Inserir Autores"):
        st.session_state['menu'] = "Inserir Autores"
        st.session_state['modo_edicao'] = False

    if st.sidebar.button("Relacionar Artigos e Autores"):
        st.session_state['menu'] = "Relacionar Artigos e Autores"
        st.session_state['modo_edicao'] = False

    # Se um artigo estiver selecionado, mostrar opções adicionais
    if st.session_state['artigo_selecionado']:
        st.sidebar.markdown("""<hr style="margin-top: 3px; margin-bottom: 2px;">""",unsafe_allow_html=True)
        
        if st.sidebar.button("Exibir Artigo"):
            artigo_selecionado = st.session_state.get('artigo_selecionado')
            st.session_state['menu'] = "Exibir Artigo"
            caminho_pdf = artigo_selecionado["pasta_pdf"]
            st.subheader(f"{artigo_selecionado['titulo']}")
            exibir_pdf_no_app(caminho_pdf)
        
        if st.sidebar.button("Editar Artigo"):
            st.session_state['modo_edicao'] = True
            st.session_state['menu'] = "Artigos Publicados"

    menu = st.session_state['menu']


################################
    # Artigos Publicados (exibe por padrão ao abrir o app)
    if menu == "Artigos Publicados":
        exibir_tabela_com_resumo_e_pdf()

    elif menu == "Inserir Artigos":
        st.header("Inserir um Novo Artigo")
        titulo = st.text_input("Título do Artigo")
        resumo = st.text_area("Resumo")
        abstract = st.text_area("abstract")
        doi = st.text("doi")
        arquivo_pdf = st.file_uploader("Upload do Arquivo PDF", type=["pdf"])

        if st.button("Salvar Artigo"):
            if titulo and arquivo_pdf:
                caminho_pdf = os.path.join(PASTA_PDFS, arquivo_pdf.name)
                with open(caminho_pdf, "wb") as f:
                    f.write(arquivo_pdf.read())
                
                inserir_artigo(titulo, resumo, abstract, doi, caminho_pdf)
                st.success("Artigo inserido com sucesso!")
            else:
                st.error("Título e o arquivo PDF são obrigatórios.")

    elif menu == "Inserir Autores":
        st.header("Inserir um Novo Autor")
        nome = st.text_input("Nome do Autor")
        link_internet = st.text_input("Link (ex: LinkedIn, Lattes, etc.)")

        if st.button("Salvar Autor"):
            if nome:
                conn = conectar_banco()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO pesquisadores (nome, link_internet) VALUES (%s, %s)", (nome, link_internet))
                conn.commit()
                conn.close()
                st.success("Pesquisador inserido com sucesso!")
            else:
                st.error("O nome do pesquisador é obrigatório.")

    elif menu == "Relacionar Artigos e Autores":
        st.header("Relacionar Artigo a Autor")

        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT id_artigo, titulo FROM artigos")
        artigos = cursor.fetchall()

        cursor.execute("SELECT id_pesquisador, nome FROM pesquisadores")
        autores = cursor.fetchall()
        conn.close()

        artigo_escolhido = st.selectbox("Selecione o Artigo", artigos, format_func=lambda x: f"{x[0]} - {x[1]}")
        autor_escolhido = st.selectbox("Selecione o Autor", autores, format_func=lambda x: f"{x[0]} - {x[1]}")

        if st.button("Relacionar"):
            if artigo_escolhido and autor_escolhido:
                conn = conectar_banco()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO artigos_autores (id_artigo, id_autor) VALUES (%s, %s)", (artigo_escolhido[0], autor_escolhido[0]))
                conn.commit()
                conn.close()
                st.success("Relacionamento criado com sucesso!")