import streamlit as st
import mysql.connector
import os  
import pandas as pd 
import base64
from funcoes_app import exibir_pdf_no_app, conectar_banco, menu_wps

def buscar_detalhes_wp(wp_id):
    conn = conectar_banco()
    cursor = conn.cursor(dictionary=True)
    # Query SQL para obter os detalhes do WP
    cursor.execute("SELECT id_wp, wp, titulo, descricao, gerente, colaboradores FROM wps WHERE id_wp = %s", (wp_id,))
    wp = cursor.fetchone()
    conn.close()
    return wp

def buscar_colaboradores_wp(wp_id):
    conn = conectar_banco()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id_wp, wp, titulo, descricao, gerente, colaboradores FROM wps WHERE id_wp = %s", (wp_id,))
    wp = cursor.fetchone()
    conn.close()
    return wp

def buscar_projetos_wp(wp_id):
    conn = conectar_banco()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT id_projeto, id_wp, titulo, autor, resumo, objetivos 
        FROM projetos_wps
        WHERE id_wp = %s
    """
    cursor.execute(query, (wp_id,))
    
    projetos_wps = cursor.fetchall()
    
    conn.close()
    return projetos_wps

# Função para exibir os detalhes do WP
def selec_wp(wp_id):
    wp_detalhes = buscar_detalhes_wp(wp_id)
    if wp_detalhes:
        st.markdown(f"""<div style="margin-top: -30px; margin-bottom: 10px; font-size: 28px;"> 
            <strong>{f"WP {wp_id}"f" - {wp_detalhes['titulo']}"} </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""<div style="margin-top: -14px; margin-bottom: 10px; font-size: 22px;"> 
            <strong><u>{f"Descrição"} </div>
            """, unsafe_allow_html=True)

        st.markdown(f""" <div style="margin-top: -15px; margin-bottom: 10px; font-size: 16px;"> 
                {wp_detalhes["descricao"]} </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**📋 Gerente:** {wp_detalhes['gerente']}")
        st.markdown(f"**👥 Colaboradores:** {wp_detalhes['colaboradores']}")
        
        st.markdown("""<hr style="margin-top: -10px; margin-bottom: 5px;">""", unsafe_allow_html=True)
        st.markdown(f"""<div style="margin-top: -14px; margin-bottom: 10px; font-size: 22px;"> 
            <strong><u>{f"Projetos da Equipe"} </div>
            """, unsafe_allow_html=True)

        projetos = buscar_projetos_wp(wp_id)

        for index, projeto in enumerate(projetos):
            vProj = projeto["titulo"]
            st.markdown(f""" <div style="margin-top: -5px; margin-bottom: 10px; font-size: 20px;"> 
                <strong>Título: </strong>{projeto["titulo"]} </div> """, unsafe_allow_html=True)

            st.markdown(f""" <div style="margin-top: -15px; margin-bottom: 10px; font-size: 16px;"> 
                <strong>Autor(a):</strong>{projeto["autor"]} </div> """, unsafe_allow_html=True)

            st.markdown(f""" <div style="margin-top: -15px; margin-bottom: 10px; font-size: 16px;"> 
                <strong>Resumo:</strong></div>""", unsafe_allow_html=True)
            st.markdown(f""" <div style="margin-top: -15px; margin-bottom: 10px; font-size: 16px;"> 
                {projeto["resumo"]} </div>""", unsafe_allow_html=True)

            st.markdown(f""" <div style="margin-top: -15px; margin-bottom: 10px; font-size: 16px;"> 
                <strong>Objetivos:</strong></div>""", unsafe_allow_html=True)
            st.markdown(f""" <div style="margin-top: -15px; margin-bottom: 10px; font-size: 16px;"> 
                {projeto["objetivos"]} </div>""", unsafe_allow_html=True)

            exibir_tabela_projetos(projeto["id_projeto"])
            

            st.markdown("""<hr style="margin-top: -10px; margin-bottom: 5px;">""", unsafe_allow_html=True) #linha separadora
    else:
        st.error("❌ Nenhum Work Package encontrado para o ID fornecido.")


def exibir_tabela_projetos(id_projeto):
    # Busca os dados no banco
    resultados = buscar_resultados_projeto(id_projeto)

    if not resultados.empty:
        st.markdown(
            """
            <div style="margin-top: -5px; margin-bottom: 10px; font-size: 20px;"> 
                <strong>Resultados do projeto</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if "resultados_exibidos" not in st.session_state:
            st.session_state.resultados_exibidos = {}

        # Construção da tabela com botões
        for index, row in resultados.iterrows():
            descricao = row["descricao"]
            nome_arq = row["nome_arq"]
            caminho_arquivo = os.path.join("resultados", nome_arq)  # Pasta de resultados a partir da raiz do projeto

            resultado_key = f"resultado_{id_projeto}_{index}"

            col1, col2 = st.columns([3, 0.5])

            with col1:
                st.markdown(f"**Descrição:** {descricao}")

            botao_text = (
                "❌ Fechar a exibição" if st.session_state.resultados_exibidos.get(resultado_key, False) else "📂 Exibir resultado"
            )

            with col2:
                if st.button(botao_text, key=f"btn_{resultado_key}"):
                    st.session_state.resultados_exibidos[resultado_key] = not st.session_state.resultados_exibidos.get(resultado_key, False)
                    st.rerun()

            if st.session_state.resultados_exibidos.get(resultado_key, False):
                st.markdown("---")

                try:
                    if os.path.exists(caminho_arquivo):
                        # Exibir PDF
                        if caminho_arquivo.lower().endswith('.pdf'):
                            with open(caminho_arquivo, "rb") as f:
                                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" style="border:none;"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        
                        # Exibir imagem
                        elif caminho_arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                            st.image(caminho_arquivo, width=400, use_container_width=True)


                        # Exibir CSV como tabela
                        elif caminho_arquivo.lower().endswith('.csv'):
                            try:
                                try:
                                    df = pd.read_csv(caminho_arquivo, encoding="utf-8")  # Padrão
                                except UnicodeDecodeError:
                                    df = pd.read_csv(caminho_arquivo, encoding="ISO-8859-1")  # Alternativo

                                st.dataframe(df, use_container_width=True)
                            except Exception as e:
                                st.error(f"Erro ao carregar o arquivo CSV: {str(e)}")
                        
                        else:
                            st.warning(f"Formato de arquivo não suportado: {nome_arq}")
                    else:
                        st.error(f"Arquivo não encontrado: {nome_arq}")
                except Exception as e:
                    st.error(f"Erro ao exibir o arquivo: {str(e)}")

                st.markdown("---")
    else:
        st.warning("🔍 Nenhum resultado foi encontrado para este projeto.")

def buscar_resultados_projeto(id_projeto):
    conn = conectar_banco()
    try:
        id_projeto = int(id_projeto)  
        
        query = "SELECT id_projeto, descricao, nome_arq FROM arq_resultados WHERE id_projeto = %s"
        
        with conn.cursor() as cursor:
            cursor.execute(query, (id_projeto,))
            resultados = cursor.fetchall()
            
            colunas = [col[0] for col in cursor.description]
            return pd.DataFrame(resultados, columns=colunas)
            
    except Exception as e:
        print(f"Erro: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def show():
    st.sidebar.title("Resultados das Pesquisas")
    selec_wp(menu_wps())
 

# Chamada da função principal, caso esse arquivo seja executado diretamente
if __name__ == "__main__":
    show()