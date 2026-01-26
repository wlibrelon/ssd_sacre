import streamlit as st

def show():
    with st.sidebar:
        st.sidebar.title("Gerenciamento SSD")
        aba1, aba2 = st.tabs(["Otimização Form B", "Otimiza Cenários"])

        with aba1:
            st.subheader("Otimização Form B")
            run_optimization = st.button("Executar Simulação")
            with st.expander("Custos fixos para implantação", expanded=False):
                st.subheader("Custos fixos (Mi R$)")
                FC = {"BAS": st.number_input("Aquífero Bauru (R\$)", value=2.5e6),
                    "GAS": st.number_input("Aquífero Guarani (R\$)", value=5e6),
                    "River Bank Filtration": st.number_input("Custo Fixo River Bank Filtration (R\$)", value=2.2e6)}

                custo_barraginhas = st.number_input("Barraginhas (R\$)", value=5e5)

            with st.expander("Custos variáveis para implantação", expanded=False):
                st.subheader("Custo Variável (Mi R$)")
                VC_unit_base = {"BAS": st.number_input("Aquífero Bauru", value=1251),
                                "GAS": st.number_input("Aquífero Guarani", value=1761),
                                "Batalha River": st.number_input("Batalha River", value=1661),
                                "River Bank Filtration": st.number_input("River Bank Filtration", value=1510)}

            # Capacidades iniciais e incrementais
            with st.expander("Capacidade Inicial", expanded=False):
                st.subheader("Capacidade Inicial (1000 m3/ano)")
                C_initial_base = {"BAS": st.number_input("Aquífero Bauru", value=4700),
                                "GAS": st.number_input("Aquífero Guarani", value=39000),
                                "Batalha River": st.number_input("Batalha River", value=12000),
                                "River Bank Filtration": st.number_input("River Bank Filtration", value=0)}

            with st.expander("Capacidade Adicional", expanded=False):
                st.subheader("Capacidade Adicional (1000 m3/ano)")
                delta_C = {"BAS": st.number_input("Δ Aquífero Bauru", value=500),
                        "GAS": st.number_input("Δ Aquífero Guarani", value=1000),
                        "River Bank Filtration": st.number_input("Δ River Bank Filtration", value=750)}
        

            # Configuração das expansões máximas permitidas
            with st.expander("Expansão máxima", expanded=False):
                st.subheader("Expansão máxima")
                max_expansions = {"BAS": st.slider("Aquífero Bauru", 0, 20, 10),
                                "GAS": st.slider("Aquífero Guarani", 0, 20, 10),
                                "River Bank Filtration": st.slider("River Bank Filtration", 0, 20, 10)}

            #cenários de consumo
            with st.expander("Cenários de consumo", expanded=False):
                st.subheader("Dados populacionais")
                pop0 = st.number_input("População Inicial", value=391740, step=1000, help="Digite a população inicial (ex. 391740)")
                taxa_estag = st.slider("Taxa de Crescimento - Estagnação (% ao ano)", min_value=0.0, max_value=1.0, value=0.005, step=0.005,format="%.4f",help="Defina a taxa anual de crescimento populacional no cenário de estagnação (ex. 0.5%)")
                taxa_tend = st.slider("Taxa de Crescimento - Tendencial (% ao ano)",min_value=0.0, max_value=1.0, value=0.01, step=0.01,format="%.4f",help="Defina a taxa anual de crescimento populacional no cenário tendencial (ex. 1%)")
                taxa_acel = st.slider("Taxa de Crescimento - Acelerada (% ao ano)", min_value=0.0, max_value=1.0, value=0.02, step=0.02,format="%.4f",help="Defina a taxa anual de crescimento populacional no cenário acelerado (ex. 2%)")
                cons_hab = st.number_input("Consumo Médio por Habitante (m³/dia)",value=0.2153, step=0.01, format="%.4f",help="Insira o consumo médio diário por habitante (ex. 0.2153 m³/dia)")

           
        with aba2:
            with st.expander("Ações"):
                st.subheader("Produção de água", divider="gray")
                prod_agua = st.radio(
                    "",
                    ["Poços no SAG área urbana", "Campos de poços SAG na zona rural", "Filtração de margem", "Padrão"],
                    index=3, 
                )

                st.subheader("Infraestrutura", divider="gray")
                infraestrutura = st.radio(
                    "",
                    ["Redução de perdas na ETA", "Redução de perdas na distribuição", "Padrão"],
                    index=2, 
                )

                st.subheader("Disponibilidade de água", divider="gray")
                dispon_agua = st.radio(
                    "",
                    ["Barraginhas", "--", "Fitoremediação", "Padrão"],
                    index=3, 
                )

                st.subheader("Gestão de demanda", divider="gray")
                gestao_deman = st.radio(
                    "",
                    ["Aumento na eficiência na irrigação", "Sistema de reuso domiciliar", "Sistema de reuso idustrial", "Padrão"],
                    index=3, 
                )
            with st.expander("Otimização"):
                st.subheader("Parâmetros de ajuste da otimização", divider="gray")
                st.text_input("Parâmetro x", "Digite o o valor para...")
                st.text_input("Parâmetro y", "Digite o o valor para...")
        
        

