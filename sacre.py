import streamlit as st
from streamlit_option_menu import option_menu
import projeto_sacre
import ssd_gerenc
import repositorio
import gestao_ssd
import publica
import requests


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
    st.image("images/logo_sacre.png", width=300)

with col2:
    st.write("")


selected = option_menu(
    menu_title=None, 
    options=["SACRE", "SSD", "Repositório","Publicação", "Gestão SSD"],
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
    projeto_sacre.show()
elif selected == "SSD":
    ssd_gerenc.show()
elif selected == "Repositório":
    repositorio.show()
elif selected == "Publicação":
     publica.show()
elif selected == "Gestão SSD":
    gestao_ssd.show()