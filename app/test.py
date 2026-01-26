import streamlit as st
from streamlit_option_menu import option_menu
import dashboard_quim
import projeto_sacre
import ssd_gerenc
import result_wps
import publica
import gestao_ssd
import gestao_ssd2

### SACRE Application
st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
        .block-container {
            padding-left: 0rem;
        }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 10]) 

with col1:
    st.image("images/logo_sacre1.png", width=300)

with col2:
    st.markdown("""
    <style>  h1 {text-align: center; font-size: 28px !important;}</style>
    """, unsafe_allow_html=True)

    st.markdown("<h1>Soluções Integradas de Água para Cidades Resilientes</h1>",unsafe_allow_html=True)

selected = option_menu(
    menu_title=None, 
    options=["SACRE", "SSD", "Resultados","Publicação", "Gestão"],
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#0CBFDD"},
        "icon": {"color": "orange", "font-size": "25px"}, 
        "nav-link": {"font-size": "25px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#505EA5"},
    }
)
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {background-color: #D3ECF0;}
    </style>
    """,
    unsafe_allow_html=True 
)

with st.sidebar:
    st.sidebar.title("")  #

# Renderize a página correta de acordo com a seleção
if selected == "SACRE":
    dashboard_quim.show()
    # projeto_sacre.show()
elif selected == "SSD":
    ssd_gerenc.show()
elif selected == "Resultados":
    result_wps.show()
elif selected == "Publicação":
     publica.show()
elif selected == "Gestão":
    gestao_ssd2.show()

