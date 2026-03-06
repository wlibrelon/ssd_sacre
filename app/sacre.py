import streamlit as st
from streamlit_option_menu import option_menu
import dashboard_quim
import ssd_gerenc
import result_wps
import publica
import gestao_ssd2

st.set_page_config(layout="wide")

# Estilo e ajustes gerais
st.markdown("""
    <style>sou  
        .block-container { padding-top: 1.5rem; padding-left: 0rem; }
        [data-testid="stSidebar"] {background-color: #D3ECF0;}
    </style>
""", unsafe_allow_html=True)

# Layout inicial: Logo e cabeçalho
col1, col2 = st.columns([2, 10])

with col1:
    st.image("images/logo_sacre1.png", width=300)

with col2:
    st.markdown("""
        <style>
            h1 {text-align: center; font-size: 28px !important;}
        </style>
    """, unsafe_allow_html=True)
    st.markdown("<h1>Soluções Integradas de Água para Cidades Resilientes</h1>", unsafe_allow_html=True)

# Menu principal
selected = option_menu(
    menu_title=None, 
    options=["SACRE", "SSD", "Resultados", "Publicação", "Gestão de dados"],
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#0CBFDD"},
        "icon": {"color": "orange", "font-size": "25px"},
        "nav-link": {"font-size": "25px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#505EA5"},
    }
)

st.sidebar.title("...")

if selected == "SACRE":
    st.empty()

elif selected == "SSD":
    st.sidebar.title("Opções SSD")
    # if st.sidebar.button("Otimização"):  
    #     ssd_gerenc.show()
    # if st.sidebar.button("Resultados Dinâmicos"):
    #     dashboard_quim.show()

elif selected == "Resultados":
    result_wps.show()

elif selected == "Publicação":
    publica.show()

elif selected == "Gestão de dados":
    gestao_ssd2.show()