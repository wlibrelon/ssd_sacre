## instalar pacotes não-nativos no colab
#!pip install ortools

# SSD - Otimização por ações (OR-Tools / pywraplp)
# ABORDAGEM B: atingir a meta de produção W (boost sobre baseline)

from ortools.linear_solver import pywraplp

from typing import Dict, List
import numpy as np
import pandas as pd
import time

import matplotlib.pyplot as plt
import seaborn as sns

# ========== 1) HELPERS DE SÉRIES SINTÉTICAS / HIDROLOGIA ==========

## gera uma série mensal de custo unitário com crescimento anual convertido para taxa mensal e sazonalidade senoidal
def _unit_cost_series(base: float,
                      T: int,
                      annual_growth: float = 0.0,
                      seasonal_amp: float = 0.0) -> np.ndarray:
    """
    Fórmula (para cada mês t):
        custo_t = base * (1 + g_m)^t * [ 1 + seasonal_amp * sin(2π*(t mod 12)/12 - π/2) ]

    Onde:
      g_m = ((1 + annual_growth)^(1/12)) - 1  → conversão de taxa anual para mensal composta.
      O termo senoidal oscila entre (1 - seasonal_amp) e (1 + seasonal_amp).
      A defasagem de -π/2 faz a série começar no ponto mínimo (valendo 1 - seasonal_amp)
      e atingir o pico por volta de 6 meses depois, repetindo a cada 12 meses.

    Observação: 
      - Recomenda-se 0 ≤ seasonal_amp < 1 para manter o fator sazonal sempre positivo.
    """
    # converte taxa anual -> taxa mensal composta (sem aproximar por dividir por 12)
    g_m = (1.0 + annual_growth)**(1/12) - 1.0

    # período temporal mensal: 0,1,2,...,T-1
    t = np.arange(T)

    # componente sazonal: período de 12 meses, começando na parte baixa da curva (-π/2)
    saz = 1.0 + seasonal_amp * np.sin(2*np.pi*(t % 12)/12.0 - np.pi/2.0)

    # custo base * tendência composta * sazonalidade
    return base * ((1.0 + g_m) ** t) * saz

## cria uma série diária sintética de vazões com sazonalidade, anos secos/normal e ruído aleatório, retornando um DataFrame com data e vazao_m3s
def gerar_vazao_diaria(
    n_anos: int = 25,
    T: int = 365,
    data_inicio: str = "2025-01-01",
    expoente_normal: int = 2,
    expoente_seca: int = 6,
    fase: int = 30,
    ruido_sd: float = 0.25,
    q_max_min: tuple = (2, 7),
    q_min_min: tuple = (0.2, 0.5),
    tendencia_cheia: tuple = (1.0, 1.5),
    tendencia_seca: tuple = (1.0, 0.5),
    frac_seca: float = 0.5,
    seed: int = 10,
    f_pico: float | None = None,
    f_min: float | None = None,
) -> pd.DataFrame:
    """
    Gera uma série **diária** sintética de vazões (m³/s) com:
      • sazonalidade “clima monsônico como diz o Ricardo kkkk” (meio ano chuvoso, meio ano seco — seno truncado em 0);
      • mistura de “anos secos” e “anos normais” (controlada por `frac_seca`);
      • tendência interanual independente para picos (`tendencia_cheia`) e vazões mínimas (`tendencia_seca`);
      • aleatoriedade diária;
      • fatores multiplicativos opcionais (`f_pico`, `f_min`) para simular ações que alterem pico e base.

    Para cada ano i:
      q_max_i = U(q_max_min) * tendencia_cheia[i] * f_pico
      q_min_i = U(q_min_min) * tendencia_seca[i]  * f_min
      saz_t   = max(0, sin(π*(t - fase)/T))
      expo_i  = expoente_seca se i < n_anos*frac_seca, senão expoente_normal
      vazao_t = clip( q_min_i + (q_max_i - q_min_i) * saz_t^expo_i + N(0,ruido_sd),
                      q_min_i, q_max_i )

    Retorna DataFrame com colunas:
      - 'data' (freq diária) e
      - 'vazao_m3s' (float, m³/s).
    """

    # semente para reprodutibilidade
    rng = np.random.RandomState(seed)

    # eixo temporal diário
    datas = pd.date_range(data_inicio, periods=T * n_anos, freq="D")

    # sorteia, por ano, pico e base (sem tendência ainda)
    q_max_anos_base = rng.uniform(q_max_min[0], q_max_min[1], n_anos)  # picos anuais
    q_min_anos_base = rng.uniform(q_min_min[0], q_min_min[1], n_anos)  # vazões de base

    # aplica tendências interanuais (linhas retas entre os extremos fornecidos)
    fator_cheia = np.linspace(tendencia_cheia[0], tendencia_cheia[1], n_anos)
    fator_seca  = np.linspace(tendencia_seca[0],  tendencia_seca[1],  n_anos)

    # fatores extras (ex.: efeitos de ações); se não informados, neutros (=1)
    if f_pico is None:
        f_pico = 1.0
    if f_min is None:
        f_min = 1.0

    # vetor final de vazões
    vazao = np.zeros(T * n_anos, dtype=float)

    for i in range(n_anos):
        idx0, idx1 = i * T, (i + 1) * T
        tt = np.arange(T)  # dias do ano

        # define as vazões máxima e mínima anual já com tendências e fatores
        q_max = q_max_anos_base[i] * fator_cheia[i] * f_pico
        q_min = q_min_anos_base[i] * fator_seca[i]  * f_min

        # sazonalidade: valores negativos do seno são zerados (estação seca)
        saz = np.sin(np.pi * (tt - fase) / T)
        saz[saz < 0] = 0.0

        # anos inicialmente marcados como "secos" usam expoente maior (pico mais curto)
        expo = expoente_seca if i < int(n_anos * frac_seca) else expoente_normal

        # curva determinística do ano (entre q_min e q_max)
        base_ano = q_min + (q_max - q_min) * (saz ** expo)

        # ruído diário (sd em unidades de m³/s)
        ruido = rng.normal(0.0, ruido_sd, T)

        # aplica ruído e garante que permanece no intervalo [q_min, q_max]
        v_ano = np.clip(base_ano + ruido, q_min, q_max)

        # grava no vetor completo
        vazao[idx0:idx1] = v_ano

    return pd.DataFrame({"data": datas, "vazao_m3s": vazao})

## agrega a vazão diária por mês, aplica restrições de captação/outorga/jusante e converte para capacidade em mil m³/mês
def processa_vazao_mensal(
    df_daily: pd.DataFrame,
    vazao_capt_montante: float = 0.2,
    vazao_outorga: float = 0.347,
    vazao_liberada_jusante: float = 0.0,
    janela: str = "2025-01-01/2049-12-31"
) -> pd.DataFrame:

    """
    Agrega uma série diária de vazões (m³/s) para o nível mensal e calcula a
    vazão captável sob restrições simples de montante, jusante e outorga => regra de captação!

    Pipeline:
      1) Agrupa por ano/mês e tira a média mensal de 'vazao_m3s';
      2) Calcula a vazão disponível: max(0, vazao_mensal - captação a montante - liberação a jusante);
      3) Aplica teto de outorga: min(vazão disponível, vazão outorgada);
      4) Converte m³/s → (mil m³/mês) usando 86400 * (365/12) / 1000 (média de 30,4167 dias/mês);
      5) (Opcional) Recorta pelo intervalo 'janela';

    Observações:
      - A conversão assume mês médio (365/12 dias);
      - Todas as vazões de entrada (parâmetros) estão em m³/s;
      - A função não altera 'df_daily' (copia interna).

    Parâmetros
    ----------
    df_daily : pd.DataFrame
        DataFrame com colunas:
          - 'data' (datetime64[ns])
          - 'vazao_m3s' (float, em m³/s).
    vazao_capt_montante : float, padrão 0.2
        Vazão (m³/s) já captada a montante (descontada antes de avaliar disponibilidade).
    vazao_outorga : float, padrão 0.347
        Teto outorgado de captação (m³/s).
    vazao_liberada_jusante : float, padrão 0.0
        Vazão (m³/s) a manter/liberar a jusante (descontada da disponibilidade).
    janela : str, padrão '2025-01-01/2049-12-31'
        Intervalo temporal para recorte do resultado, no formato 'YYYY-MM-DD/YYYY-MM-DD'.

    Retorno
    -------
    pd.DataFrame com colunas:
      - 'data'                       : primeiro dia de cada mês (timestamp)
      - 'vazao_m3s'                  : média mensal da série diária (m³/s)
      - 'vazao_disponivel_m3s'       : max(0, vazao_m3s - montante - jusante) (m³/s)
      - 'vazao_captada_m3s'          : min(vazao_disponivel_m3s, vazao_outorga) (m³/s)
      - 'vazao_captada_1000m3mes'    : vazão captada convertida para mil m³/mês

    """

    # Trabalha em cópia para não alterar o DataFrame original
    df = df_daily.copy()

    # Quebra em ano/mês para agregação mensal
    df["ano"] = df["data"].dt.year
    df["mes"] = df["data"].dt.month

    # Média mensal (m³/s) da série diária
    mens = df.groupby(["ano", "mes"])["vazao_m3s"].mean().reset_index()

    # Timestamp do "1º dia do mês" para cada linha mensal (serve como marcador temporal)
    mens["data"] = pd.to_datetime(mens["ano"].astype(str) + "-" + mens["mes"].astype(str) + "-01")

    # Disponibilidade mensal após reservar montante e jusante (não negativa)
    mens["vazao_disponivel_m3s"] = np.maximum(
        0.0,
        mens["vazao_m3s"] - vazao_capt_montante - vazao_liberada_jusante
    )

    # Aplica teto de outorga na captação
    mens["vazao_captada_m3s"] = np.minimum(mens["vazao_disponivel_m3s"], vazao_outorga)

    # Converte m³/s → mil m³/mês (assumindo mês médio de 365/12 dias)
    mens["vazao_captada_1000m3mes"] = mens["vazao_captada_m3s"] * 86400 * (365 / 12) / 1000

    # Seleciona apenas as colunas finais de interesse
    mens = mens[
        ["data", "vazao_m3s", "vazao_disponivel_m3s", "vazao_captada_m3s", "vazao_captada_1000m3mes"]
    ]

    # Recorte temporal opcional
    if janela:
        inicio, fim = janela.split("/")
        mens = mens.query("data >= @inicio and data <= @fim").reset_index(drop=True)

    return mens

# ========== 2) PREP DE PARÂMETROS POR MANANCIAL/AÇÃO (BAS, BATALHA, GAS) ==========

## monta o pacote de parâmetros do manancial  BAS (metadados, capacidades base/incrementais, custos, CAPEX, Operação fixo) para o otimizador
def prepare_BAS_params_A(
    start_date: str = "2025-01-01",
    years: int = 25,
    decision_points=np.arange(0, 300, 6),   # meses de decisão (ex.: a cada 6 meses)
    lead_time_months: int = 11,             # tempo (meses) entre decisão e entrada em operação
    base_capacity_1000m3m: float = 4700/12, # capacidade base contínua (mil m³/mês)
    add_BAS_1000m3m: float = 500/12,        # incremento por módulo de BAS (mil m³/mês)
    add_RBF_1000m3m: float = 750/12,        # incremento por módulo de RBF (mil m³/mês)
    max_BAS: int = 15,                      # teto de módulos de BAS
    max_RBF: int = 15,                      # teto de módulos de RBF
    VC0_BAS: float = 1.60 * 1000,           # custo variável inicial BAS (R$/mil m³)
    VC0_RBF: float = 1.70 * 1000,           # custo variável inicial RBF (R$/mil m³)
    growth_BAS_annual: float = 0.02,        # crescimento anual do VC BAS
    growth_RBF_annual: float = 0.02,        # crescimento anual do VC RBF
    seasonal_amp: float = 0.0,              # amplitude sazonal (0 = sem sazonalidade no VC)
    fixed_opex_per_module_BAS: float = 1e4, # OPEX fixo/mês por módulo BAS (R$)
    fixed_opex_per_module_RBF: float = 1e4  # OPEX fixo/mês por módulo RBF (R$)
) -> Dict:
    """
    Gera o pacote de parâmetros da fonte BAS para o otimizador baseado em ações.

    O que monta:
      - Séries mensais de custo variável (vc_t) para BAS e RBF com crescimento anual
        (convertido para taxa mensal) e sazonalidade senoidal (opcional).
      - Capacidade base contínua do sistema (cap_base_t) e incremento por módulo
        (cap_add_per_module) para cada ação.
      - Metadados (horizonte, data de início) e limites (máx. de módulos).
      - Campos auxiliares para escalonamento:
          • max_add_per_decision : teto de módulos que podem ser adicionados em um ponto de decisão
          • ramp_per_month : rampa máxima de ativação por mês (Δ módulos/mês)

    Unidades principais
      - Vazões/capacidades: mil m³/mês.
      - Custos variáveis:  R$/mil m³.
      - OPEX fixo: R$/mês por módulo.

    Retorna
      Um dicionário no formato esperado pelo otimizador
    """

    # Horizonte em meses
    T = years * 12

    # Séries de custo variável com crescimento anual → taxa mensal e sazonalidade opcional
    vc_bas = _unit_cost_series(VC0_BAS, T, growth_BAS_annual, seasonal_amp).astype(float)
    vc_rbf = _unit_cost_series(VC0_RBF, T, growth_RBF_annual, seasonal_amp).astype(float)

    return {
        "meta": {
            "horizon_months": int(T),
            "start_date": pd.to_datetime(start_date),
        },
        # Módulos iniciais
        "M0": {"BAS": 0, "RBF": 0},

        # Especificação das ações controláveis
        "actions": {
            # ── Ação 1: BAS_URB ─────────────────────────────────────────────────────
            "BAS_URB": {
                # Em quais meses posso decidir instalar (índices base 0: mês 0, 6, 12, ...)
                "decision_points": list(decision_points),

                # Lead time (meses) da decisão até a capacidade entrar no balanço
                "lead_time_months": int(lead_time_months),

                # Teto total de módulos ao longo do horizonte
                "max_modules": int(max_BAS),

                # Capacidade base recorrente (mil m³/mês)
                "cap_base_t": np.full(T, base_capacity_1000m3m, dtype=float),

                # Ganho de capacidade por módulo (constante no tempo)
                "cap_add_per_module": float(add_BAS_1000m3m),

                # Custo variável por unidade produzida (R$/mil m³) por mês
                "vc_t": vc_bas,

                # CAPEX por módulo (R$) descontado na data de decisão (no solver)
                "capex_per_module": 3e6,

                # OPEX fixo mensal por módulo ativo (R$/mês)
                "fixed_om_cost_per_module_t": np.full(T, float(fixed_opex_per_module_BAS), dtype=float),

                # Instalação gradual
                "max_add_per_decision": 2,
                "ramp_per_month": 2,
            },

            # ── Ação 2: RBF ────────────────────────────────────────────────────────
            "RBF": {
                "decision_points": list(decision_points),
                "lead_time_months": int(lead_time_months),
                "max_modules": int(max_RBF),

                # RBF não tem base própria; entra só via módulos
                "cap_base_t": np.zeros(T, dtype=float),

                # Incremento por módulo (mil m³/mês)
                "cap_add_per_module": float(add_RBF_1000m3m),

                # Custo variável mensal (R$/mil m³)
                "vc_t": vc_rbf,

                # CAPEX por módulo (R$)
                "capex_per_module": 2.2e6,

                # OPEX fixo mensal por módulo ativo (R$/mês)
                "fixed_om_cost_per_module_t": np.full(T, float(fixed_opex_per_module_RBF), dtype=float),

                # Instalação gradual
                "max_add_per_decision": 2,
                "ramp_per_month": 2,
            },
        },
    }

## gera vazões base e com ações (barragem/reservatório), calcula os incrementos mensais de captação e compõe o pacote do manancial Batalha
def prepare_BATALHA_params_A(
    years: int = 25,
    start_date: str = "2025-01-01",
    decision_points=np.arange(0, 300, 6),     # meses (índices base 0) em que a decisão é permitida
    lead_time_months: int = 11,               # defasagem decisão→operação (meses)

    # --- Geração hidrológica sintética (nível diário) ---
    n_anos: int = 25,                          # anos de série diária a gerar
    Tday: int = 365,                           # dias por ano da série sintética
    expoente_normal: int = 2,                  # “largura” do pico em anos normais (menor = pico mais largo)
    expoente_seca: int = 6,                    # “largura” do pico em anos secos (maior = pico mais agudo)
    fase: int = 30,                            # deslocamento do pico sazonal (em dias)
    ruido_sd: float = 0.25,                    # desvio-padrão do ruído diário
    q_max_min=(2, 7),                          # sorteio anual do máximo [mín, máx]
    q_min_min=(0.2, 0.5),                      # sorteio anual do mínimo [mín, máx]
    tendencia_cheia=(1.0, 1.5),                # tendência (crescimento) no máximo ao longo dos anos
    tendencia_seca=(1.0, 0.5),                 # tendência (decrescimento) no mínimo ao longo dos anos
    frac_seca: float = 0.5,                    # fração inicial dos anos tratados como “secos”
    seed: int = 10,                            # semente

    # --- Regras de captação / outorga / jusante ---
    vazao_capt_montante: float = 0.2,          # (m³/s) tomada a montante (reduz a disponível local)
    vazao_outorga: float = 0.347,              # (m³/s) limite concedido (outorga)
    vazao_liberada_jusante: float = 0.0,       # (m³/s) exigência mínima a jusante

    # --- Custos variáveis (rio) ---
    VC0_river: float = 1.66 * 1000,            # R$/mil m³ (mês 0)
    growth_river_annual: float = 0.01,         # crescimento anual do VC do rio
    seasonal_amp: float = 0.05,                # sazonalidade do VC (0 = sem)

    # --- Efeitos das obras (fatores sobre o ciclo sazonal) ---
    barr_f_pico: float = 0.7,                  # barragem: reduz picos (multiplica pico)
    barr_f_min: float = 1.30,                  # barragem: eleva vales
    CAPEX_BARR: float = 5e5,                   # CAPEX por “módulo” (barragem)
    max_BARR: int = 1,                         # teto de módulos (0/1, binário)

    res_f_pico: float = 0.6,                   # reservatório: reduz picos
    res_f_min: float = 1.50,                   # reservatório: eleva vales
    CAPEX_RES: float = 2e6,                    # CAPEX por “módulo” (reservatório)
    max_RES: int = 1,                          # teto de módulos (0/1, binário)

    fixed_om_per_module_BARR: float = 0.0,     # OPEX fixo/mês da barragem (R$)
    fixed_om_per_module_RES: float  = 0.0      # OPEX fixo/mês do reservatório (R$)
) -> Dict:
    """
    Constrói o pacote do manancial Batalha (rio) para o otimizador, com:
      1) Série diária sintética de vazões → agregação mensal (capacidade base do rio).
      2) Efeitos de BARR (barraginhas) e RES (reservatório) aplicados sobre a hidrologia,
         gerando incrementos mensais `cap_add_per_module_t` específicos para cada obra.
      3) Uma ação BARRxRES que modela explicitamente a interação quando AMBAS
         as obras existem, usando um teto conjunto (`combo_cap_t`) via ligação lógica AND.

    Unidades:
      - Vazões/capacidades: mil m³/mês.
      - Custos variáveis:   R$/mil m³.
      - OPEX fixo:          R$/mês por “módulo”.

    Políticas de instalação - escalonamento:
      - max_add_per_decision: nº máx. de módulos adicionáveis em UM ponto de decisão.
      - ramp_per_month:       rampa máx. de ativação por mês (Δ módulos/mês).

    Retorna um dicionário no formato esperado pelo otimizador, contendo:
      meta, M0 e actions = {RIVER, BARR, RES, BARRxRES}.
    """

    # 1) Série diária base (sem obras) e agregação mensal → capacidade base do rio
    daily_base = gerar_vazao_diaria(
        n_anos=n_anos, T=Tday, data_inicio=start_date,
        expoente_normal=expoente_normal, expoente_seca=expoente_seca,
        fase=fase, ruido_sd=ruido_sd,
        q_max_min=q_max_min, q_min_min=q_min_min,
        tendencia_cheia=tendencia_cheia, tendencia_seca=tendencia_seca,
        frac_seca=frac_seca, seed=seed
    )
    janela = f"{start_date}/{(pd.to_datetime(start_date) + pd.DateOffset(years=years, months=-1)).strftime('%Y-%m-%d')}"
    mens_base = processa_vazao_mensal(
        daily_base, vazao_capt_montante, vazao_outorga, vazao_liberada_jusante, janela=janela
    )
    cap_base_t = mens_base["vazao_captada_1000m3mes"].to_numpy(dtype=float)
    Tm = len(cap_base_t)

    # 2) Séries diárias com cada obra isolada (aplica fatores f_pico / f_min) → incrementos mensais
    daily_barr = gerar_vazao_diaria(
        n_anos=n_anos, T=Tday, data_inicio=start_date,
        expoente_normal=expoente_normal, expoente_seca=expoente_seca,
        fase=fase, ruido_sd=ruido_sd,
        q_max_min=q_max_min, q_min_min=q_min_min,
        tendencia_cheia=tendencia_cheia, tendencia_seca=tendencia_seca,
        frac_seca=frac_seca, seed=seed,
        f_pico=barr_f_pico, f_min=barr_f_min
    )
    daily_res = gerar_vazao_diaria(
        n_anos=n_anos, T=Tday, data_inicio=start_date,
        expoente_normal=expoente_normal, expoente_seca=expoente_seca,
        fase=fase, ruido_sd=ruido_sd,
        q_max_min=q_max_min, q_min_min=q_min_min,
        tendencia_cheia=tendencia_cheia, tendencia_seca=tendencia_seca,
        frac_seca=frac_seca, seed=seed,
        f_pico=res_f_pico, f_min=res_f_min
    )
    mens_barr = processa_vazao_mensal(
        daily_barr, vazao_capt_montante, vazao_outorga, vazao_liberada_jusante, janela=janela
    )
    mens_res = processa_vazao_mensal(
        daily_res, vazao_capt_montante, vazao_outorga, vazao_liberada_jusante, janela=janela
    )

    # Incrementos mensais gerados por cada obra isoladamente
    inc_barr_t = (mens_barr["vazao_captada_1000m3mes"] - mens_base["vazao_captada_1000m3mes"]).to_numpy(float)
    inc_res_t  = (mens_res ["vazao_captada_1000m3mes"] - mens_base["vazao_captada_1000m3mes"]).to_numpy(float)

    # 3) Série com AMBAS as obras ao mesmo tempo
    daily_combo = gerar_vazao_diaria(
        n_anos=n_anos, T=Tday, data_inicio=start_date,
        expoente_normal=expoente_normal, expoente_seca=expoente_seca,
        fase=fase, ruido_sd=ruido_sd,
        q_max_min=q_max_min, q_min_min=q_min_min,
        tendencia_cheia=tendencia_cheia, tendencia_seca=tendencia_seca,
        frac_seca=frac_seca, seed=seed,
        f_pico=barr_f_pico * res_f_pico,   # aplica ambos os efeitos nos picos
        f_min =barr_f_min  * res_f_min     # aplica ambos os efeitos nos vales
    )
    mens_combo  = processa_vazao_mensal(
        daily_combo, vazao_capt_montante, vazao_outorga, vazao_liberada_jusante, janela=janela
    )
    cap_combo_t = mens_combo["vazao_captada_1000m3mes"].to_numpy(float)

    # Sinergia = ganho com ambos – (ganho com barraginhas + ganho com reservatório)
    inc_combo_t   = cap_combo_t - cap_base_t
    inc_inter_raw = inc_combo_t - inc_barr_t - inc_res_t
    inc_inter_pos = np.maximum(inc_inter_raw, 0.0)  # só soma a sinergia sinergia (>0)

    # 4) Custo variável do rio (com crescimento anual e sazonalidade opcional)
    vc_river = _unit_cost_series(VC0_river, Tm, growth_river_annual, seasonal_amp).astype(float)

    # 5) Pacote final no formato do otimizador
    return {
        "meta": {
            "horizon_months": Tm,
            "start_date": pd.to_datetime(start_date),
        },
        "M0": {"RIVER": 0, "BARR": 0, "RES": 0, "BARRxRES": 0},

        "actions": {
            # ── Ação: RIVER (capacidade base variável no tempo, sem módulos) ──
            "RIVER": {
                "decision_points": list(decision_points),
                "lead_time_months": int(lead_time_months),
                "max_modules": 0,                            # não instala “módulos” no rio
                "cap_base_t": cap_base_t,                   # capacidade base mensal (mil m³/mês)
                "cap_add_per_module": 0.0,                  # sem incremento por módulo
                "vc_t": vc_river,
                "capex_per_module": 0.0,
                "fixed_om_cost_per_module_t": np.zeros(Tm, dtype=float),

                # Políticas de operação/instalação (mantidos para interface homogênea)
                "max_add_per_decision": 2,
                "ramp_per_month": 2,
            },

            # ── Ação: BARR (barragem) ──
            "BARR": {
                "decision_points": list(decision_points),
                "lead_time_months": int(lead_time_months),
                "max_modules": int(max_BARR),
                "cap_base_t": np.zeros(Tm, dtype=float),    # só incrementa (não tem base própria)
                "cap_add_per_module": 0.0,
                "cap_add_per_module_t": inc_barr_t,         # incremento mensal (mil m³/mês)
                "vc_t": vc_river,                           # mesmo VC do rio
                "capex_per_module": float(CAPEX_BARR),
                "fixed_om_cost_per_module_t": np.full(Tm, float(fixed_om_per_module_BARR), dtype=float),

                "max_add_per_decision": 2,
                "ramp_per_month": 2,
            },

            # ── Ação: RES (reservatório) ──
            "RES": {
                "decision_points": list(decision_points),
                "lead_time_months": int(lead_time_months),
                "max_modules": int(max_RES),
                "cap_base_t": np.zeros(Tm, dtype=float),
                "cap_add_per_module": 0.0,
                "cap_add_per_module_t": inc_res_t,          # incremento mensal (mil m³/mês)
                "vc_t": vc_river,
                "capex_per_module": float(CAPEX_RES),
                "fixed_om_cost_per_module_t": np.full(Tm, float(fixed_om_per_module_RES), dtype=float),

                "max_add_per_decision": 2,
                "ramp_per_month": 2,
            },

            # ── Ação: BARRxRES (interação entre as ações - preciso melhorar aqui!!! - ativada por AND) ──
            "BARRxRES": {
                "decision_points": [],                      # não decide diretamente
                "lead_time_months": 0,
                "max_modules": 1,                           # ativada/desativada pela ação AND
                "cap_base_t": np.zeros(Tm, dtype=float),
                "cap_add_per_module": 0.0,
                "cap_add_per_module_t": inc_inter_pos,      # só a sinergia (>0)
                "vc_t": vc_river,
                "capex_per_module": 0.0,
                "fixed_om_cost_per_module_t": np.zeros(Tm, dtype=float),

                # (meta) serve apenas p/ manter interface consistente
                "max_add_per_decision": 2,
                "ramp_per_month": 2,

                # Dados para o solver:
                "and_gate_of": ["BARR", "RES"],             # ativa se (BARR AND RES)
                "combo_cap_t": cap_combo_t.tolist()         # teto da soma quando ambos ativos
            },
        },
    }

## define o pacote do manancial GAS (URB, WF, e item de injeção), com capacidades, limites de módulos, CAPEX/OPEX e séries de custo
def prepare_GAS_params_A(
    start_date: str = "2025-01-01",
    years: int = 25,
    decision_points=np.arange(0, 300, 6),         # meses (índices base 0) em que a decisão é permitida
    lead_time_months: int = 11,                   # defasagem decisão→operação (meses)

    # --- capacidades e limites ---
    base_capacity_1000m3m: float = 39000/12,      # base mensal do SAG (mil m³/mês)
    add_URB_1000m3m: float = 1000/12,             # incremento por módulo URB
    add_WF_1000m3m: float = 3000/12,              # incremento por módulo WF
    max_URB: int = 5,
    max_WF: int = 2,

    # --- custos variáveis (R$/mil m³) ---
    VC0_URB: float = 1.76 * 1000,                 # custo base URB no mês 0
    VC0_WF:  float = 1.70 * 1000,                 # custo base WF no mês 0
    growth_URB_annual: float = 0.003,              # crescimento anual URB (aqui é baixo, pq já é computado pelo rebaixamento)
    growth_WF_annual:  float = 0.001,              # crescimento anual WF (aqui é baixo, pq já é computado pelo rebaixamento)
    seasonal_amp: float = 0.0,                    # sazonalidade (0 = sem)

    # --- injeção (não gera capacidade, afeta rebaixamento) ---
    CAPEX_INJ_onetime: float = 5e6,
    CAPEX_INJ_recurring_per_month: float = 5e4,
    max_INJ: int = 1,
    inj_fixed_opex_delta: float = 0.0,            # ajuste fino de OPEX fixo da INJ

    # --- modelo de rebaixamento por fonte (aqui estou melhorando!!!)---
    drawdown_config: dict | None = None,
) -> Dict:
    """
    Constrói o pacote da fonte GAS para o otimizador, com ações:
      • GAS_URB (poços urbanos) e GAS_WF (wellfield): geram capacidade e têm custo variável.
      • GAS_INJ (injeção): não gera capacidade, mas reduz rebaixamento d_t via modelo dinâmico.

    (Rebaixamento opcional)
      Se `meta["drawdown_model"]` estiver presente, o solver aplicará:
        d_t = ρ·d_{t-1} + Σ_j k_j·x_{j,t} − k_inj·a_{inj,t}
      e custo adicional:  α_j · (x_{j,t} * d_t)
      com linearização de w_{j,t} = x_{j,t}·d_t.
      Unidades típicas: x em mil m³/mês, d em metros.

    Unidades:
      - Capacidades: mil m³/mês.
      - Custos variáveis: R$/mil m³.
      - OPEX fixo (INJ): R$/mês por módulo.
      - CAPEX: R$ por módulo.

    Rampas de decisão
      - max_add_per_decision: nº máximo de módulos que podem ser adicionados em um único ponto de decisão.
      - ramp_per_month: rampa de ativação por mês (Δ módulos/mês).

    Retorna um dicionário {meta, M0, actions} no formato esperado pelo otimizador.
    """

    # Horizonte em meses
    T = years * 12

    # Séries de custo variável (crescimento anual → mensal + sazonalidade senoidal)
    vc_urb = _unit_cost_series(VC0_URB, T, growth_URB_annual, seasonal_amp).astype(float)
    vc_wf  = _unit_cost_series(VC0_WF,  T, growth_WF_annual,  seasonal_amp).astype(float)

    # Modelo de drawdown (aqui vai ser afinado com base no modelo de fluxo!!!)
    # Dicionário base
    default_drawdown = {
        "rho": 0.85,          # persistência mensal (↑ aproxima d_t)
        "d0": 200,            # rebaixamento inicial
        "d_max": 400,        # teto de d_t
        # Sensibilidades (x em mil m³/mês)
        "k_urb": 1.5e-4,      # impacto de URB sobre d_t
        "k_wf":  5e-5,      # impacto de WF sobre d_t (≈40% do URB)
        "k_inj": 0.20,        # efeito redutor por módulo de INJ
        # Custo adicional proporcional ao produto x*d:
        "alpha_cost_urb": 2.0,
        "alpha_cost_wf":  0.5,
        # Mapeamentos p/ o solver reconhecer onde aplicar k_j e α_j:
        "inj_action": "GAS_INJ",
        "applies_to": ["GAS_URB", "GAS_WF"],
    }
    ddm = dict(drawdown_config) if isinstance(drawdown_config, dict) and drawdown_config else default_drawdown

    # Metadados (inclui drawdown_model que o solver vai ler)
    meta = {
        "horizon_months": int(T),
        "start_date": pd.to_datetime(start_date),
        "drawdown_model": ddm,
    }

    # Pacote de ações no formato do otimizador
    return {
        "meta": meta,
        "M0": {"GAS_URB": 0, "GAS_WF": 0, "GAS_INJ": 0},
        "actions": {
            # ── Ação: GAS_URB (poços urbanos) ──
            "GAS_URB": {
                "decision_points": list(decision_points),
                "lead_time_months": int(lead_time_months),
                "max_modules": int(max_URB),
                "cap_base_t": np.full(T, float(base_capacity_1000m3m), dtype=float),
                "cap_add_per_module": float(add_URB_1000m3m),
                "vc_t": vc_urb,                     # custo base; efeito d_t entra via α·(x*d)
                "capex_per_module": 5e6,
                "fixed_om_cost_per_module_t": np.zeros(T, dtype=float),

                # Políticas de rampa / teto por decisão (usadas pelo solver)
                "max_add_per_decision": 2,
                "ramp_per_month": 2,
            },

            # ── Ação: GAS_WF (campo de poços) ──
            "GAS_WF": {
                "decision_points": list(decision_points),
                "lead_time_months": int(lead_time_months),
                "max_modules": int(max_WF),
                "cap_base_t": np.zeros(T, dtype=float),
                "cap_add_per_module": float(add_WF_1000m3m),
                "vc_t": vc_wf,
                "capex_per_module": 50e6,
                "fixed_om_cost_per_module_t": np.zeros(T, dtype=float),

                "max_add_per_decision": 2,
                "ramp_per_month": 2,
            },

            # ── Ação: GAS_INJ (injeção) ──
            # Não gera capacidade, mas reduz d_t; tem CAPEX pontual e OPEX fixo mensal (custo recorrente).
            "GAS_INJ": {
                "decision_points": list(decision_points),
                "lead_time_months": int(lead_time_months),
                "max_modules": int(max_INJ),
                "cap_base_t": np.zeros(T, dtype=float),
                "cap_add_per_module": 0.0,                   # sem capacidade adicional
                "vc_t": np.zeros(T, dtype=float),            # sem custo variável
                "capex_per_module": float(CAPEX_INJ_onetime),
                "fixed_om_cost_per_module_t": np.full(
                    T, float(CAPEX_INJ_recurring_per_month + inj_fixed_opex_delta), dtype=float
                ),

                "max_add_per_decision": 2,
                "ramp_per_month": 2,
            },
        },
    }

## constrói um dicionário de pacotes por fonte (BAS, Batalha, GAS) conforme flags e horizonte/datas informados
def build_paramsA_by_source(
    include_BAS: bool = True,
    include_BATALHA: bool = True,
    include_GAS: bool = True,
    start_date: str = "2025-01-01",
    years: int = 25,
    # >>> repassa config de rebaixamento para o GAS (opcional)
    drawdown_config_gas: dict | None = None,
) -> Dict[str, Dict]:
    """
    Monta um dicionário de pacotes de parâmetros por fonte hídrica para o otimizador.

    O que faz:
      - Chama as funções que constroem  cada fonte (BAS, Batalha, GAS).
      - Respeita *flags* de inclusão para compor apenas as fontes desejadas (por ex. tentar um cenário sem um manancial)
      - Propaga `start_date` e `years` para todas as fontes, garantindo horizonte comum.
      - Encaminha `drawdown_config_gas` para o pacote do GAS (se fornecido), permitindo
        calibrar rebaixamento/α/k diretamente no setup.

    Observações:
      - O formato retornado é { "BAS": {...}, "Batalha": {...}, "GAS": {...} } apenas
        para as fontes incluídas.

    Parâmetros:
      include_BAS, include_BATALHA, include_GAS : toggles de inclusão de cada fonte.
      start_date  : data inicial do horizonte (YYYY-MM-DD).
      years       : duração do horizonte (em anos).
      drawdown_config_gas : dict opcional para sobrescrever o modelo de rebaixamento do SAG

    Retorna:
      out : Dict[str, Dict] com as entradas presentes apenas para as fontes ativadas.
            Cada valor é um pacote de parâmetros no formato esperado pelo otimizador.
    """
    out: Dict[str, Dict] = {}

    if include_BAS:
        out["BAS"] = prepare_BAS_params_A(
            start_date=start_date, years=years
        )

    if include_BATALHA:
        out["Batalha"] = prepare_BATALHA_params_A(
            start_date=start_date, years=years
        )

    if include_GAS:
        out["GAS"] = prepare_GAS_params_A(
            start_date=start_date, years=years,
            drawdown_config=drawdown_config_gas
        )

    return out

# ========== 3) NORMALIZAÇÃO & UTILITÁRIOS DO PACOTE "ACTIONS" ==========
def infer_T(p: dict, default_T: int = 300) -> int:
    """
    Infere T (horizonte em meses) de um pacote de parâmetros.
    Ordem de preferência:
      1) meta.horizon_months > 0
      2) menor comprimento entre séries nas ações (cap_base_t, vc_t, fixed_om_cost_per_module_t
      3) default_T
    Usa "min" nas séries para ser conservador quando houver comprimentos distintos.
    """
    # 1) meta
    meta = (p or {}).get("meta", {}) or {}
    hm = meta.get("horizon_months", None)
    if isinstance(hm, (int, np.integer)) and hm > 0:
        return int(hm)

    # 2) séries nas ações
    actions = (p or {}).get("actions", {}) or {}
    lengths = []
    for a in actions.values():
        for k in ("cap_base_t", "vc_t", "fixed_om_cost_per_module_t"):
            arr = a.get(k, None)
            if isinstance(arr, (list, tuple, np.ndarray)):
                n = len(arr)
                if n > 0:
                    lengths.append(int(n))
    if lengths:
        return int(min(lengths))

    # 3) fallback
    return int(default_T)

## normaliza um pacote de ações para comprimento T, preenchendo valores padrão e limpando/validando segmentos exógenos
def normalize_actions_package(pA, default_T=300):
    """
    Normaliza um pacote de ações para um horizonte T consistente.

    O que faz:
      1) Descobre T com `infer_T` (meta.horizon_months ou menor comprimento das séries).
      2) Garante que meta.horizon_months == T.
      3) Para cada ação:
         - Preenche defaults: decision_points, lead_time_months, max_modules, cap_add_per_module, capex_per_module.
         - Normaliza arrays para tamanho T: cap_base_t, vc_t, fixed_om_cost_per_module_t.
         - (Opcional) Trunca/preenche cap_add_per_module_t para T.
         - Mantém intactas chaves extras (max_add_per_decision, ramp_per_month, and_gate_of, combo_cap_t)
      4) Anexa `p["T"] = T` para acesso rápido.


    Parâmetros:
      pA : dict do pacote bruto (como retornado pelos *prepare_*).
      default_T : fallback de T caso não seja possível inferir.

    Retorna:
      dict normalizado com meta.horizon_months == T, arrays np.ndarray float32/64 de comprimento T e campo auxiliar "T".
    """
    p = dict(pA)
    meta = dict(p.get("meta", {}) or {})
    T = infer_T(p, default_T=default_T)
    meta["horizon_months"] = int(T)
    p["meta"] = meta

    actions_in = dict(p.get("actions", {}) or {})
    actions_out = {}
    for name, a0 in actions_in.items():
        a = dict(a0 or {})

        # Defaults de chaves escalares
        a.setdefault("decision_points", [0])
        a.setdefault("lead_time_months", 0)
        a.setdefault("max_modules", 0)
        a.setdefault("cap_add_per_module", 0.0)
        a.setdefault("capex_per_module", 0.0)

        # Normalizador de arrays para tamanho T (preenche com "default" quando faltar)
        def _norm_arr(key, default=0.0):
            arr = a.get(key, None)
            if arr is None:
                a[key] = np.full(T, float(default), dtype=float)
            else:
                arr = np.asarray(arr, dtype=float)
                if arr.size < T:
                    z = np.full(T, float(default), dtype=float)
                    z[:arr.size] = arr
                    arr = z
                a[key] = arr[:T]

        _norm_arr("cap_base_t", 0.0)
        _norm_arr("vc_t", 0.0)
        _norm_arr("fixed_om_cost_per_module_t", 0.0)

        # Série incremental opcional (por mês) — se existir, normaliza/trunca
        if "cap_add_per_module_t" in a and isinstance(a["cap_add_per_module_t"], (list, tuple, np.ndarray)):
            arr = np.asarray(a["cap_add_per_module_t"], dtype=float)
            if arr.size < T:
                z = np.zeros(T, dtype=float)
                z[:arr.size] = arr
                arr = z
            a["cap_add_per_module_t"] = arr[:T]

        # Chaves não listadas acima são preservadas (ramp, limites por decisão, AND, etc.)
        actions_out[name] = a

    p["actions"] = actions_out
    p["T"] = int(T)
    return p

## calcula a capacidade base no primeiro mês somando cap_base_t[0] e os módulos iniciais M0 vezes cap_add_per_module
def base_capacity_at(pA: dict, t: int = 0) -> float:
    """
    Calcula a capacidade "base" disponível em um mês t (0-based) para um pacote.

    O que conta:
      - Soma cap_base_t[t] de todas as ações.
      - Adiciona M0[a] * cap_add_per_module (módulos já existentes no início).

    Parâmetros:
      pA : pacote (dict) de uma fonte (ex.: BAS/GAS/Batalha).
      t  : índice do mês (0 para o primeiro mês).

    Retorna:
      cap : float com a capacidade total base no mês t (mesma unidade das séries, p.ex. mil m³/mês).
    """
    M0   = (pA or {}).get("M0", {}) or {}
    acts = (pA or {}).get("actions", {}) or {}
    cap = 0.0
    for a, spec in acts.items():
        cap_base = spec.get("cap_base_t", None)
        if isinstance(cap_base, (list, tuple, np.ndarray)) and len(cap_base) > t:
            cap += float(cap_base[t])
        cap_add = float(spec.get("cap_add_per_module", 0.0))
        cap += float(M0.get(a, 0)) * cap_add
    return cap

## computa a entrega inicial agregada entre fontes com/sem perdas aplicando a perda inicial λ₀
def baseline_delivery_from_paramsA(params_by_source, fontes_com_perda, niveis_reducao_perda):
    """
    Calcula a entrega inicial (mês 0) agregada entre fontes com/sem perdas.

    Lógica:
      - Para cada fonte s, pega a capacidade base no t=0 (via base_capacity_at).
      - Se s ∈ fontes_com_perda, aplica λo (perda inicial) sobre essa parte.
      - Retorna cap_sem_perda + cap_com_perda*(1 - λo).

    Parâmetros:
      params_by_source : dict {fonte -> pacote}, p.ex. {"BAS": {...}, "GAS": {...}}
      fontes_com_perda : conjunto de fontes às quais se aplica a perda (ex.: {"Batalha","GAS"}).
      niveis_reducao_perda : dict {nível -> (lambda, custo PV acumulado)}; usa-se apenas lambda do nível 0.

    Retorna:
      float : entrega inicial agregada (t=0) já considerando a perda λo nas fontes marcadas.
    """
    lam0 = float(niveis_reducao_perda[0][0])
    cap_sem, cap_com = 0.0, 0.0
    for s, pA in params_by_source.items():
        q1 = base_capacity_at(pA, t=0)
        if s in fontes_com_perda:
            cap_com += q1
        else:
            cap_sem += q1
    return cap_sem + cap_com * (1.0 - lam0)


def gerar_niveis_de_perda(perda_atual, perda_minima_viavel, custo_total_reducao, passo=0.02):
    assert 0 <= perda_minima_viavel <= perda_atual <= 1
    assert passo > 0
    niveis = {0: (round(perda_atual, 4), 0.0)}
    delta = round(perda_atual - perda_minima_viavel, 4)
    if delta <= 0:
        return niveis
    n_int = int(delta / passo)
    reducoes = [passo] * max(n_int, 0)
    resto = round(delta - sum(reducoes), 4)
    if resto > 1e-6:
        if n_int > 0:
            reducoes[-1] += resto
        else:
            reducoes.append(resto)
    perda = perda_atual
    custo_acum = 0.0
    for i, r in enumerate(reducoes):
        custo_acum += custo_total_reducao * (r / delta)
        perda = max(0.0, perda - r)
        niveis[i + 1] = (round(perda, 4), round(custo_acum, 2))
    return niveis

def build_W_series(C0, n, w_inc, meses_constantes=12):
        W = []
        for t in range(1, n + 1):
            if t <= meses_constantes:
                W.append(C0)
            else:
                frac = (t - meses_constantes) / max(1, (n - meses_constantes))
                W.append(C0 * (1 + w_inc * frac))
        return W

# ========== 4) OTIMIZADOR ==========
def optimize_by_actions(
    strategy_W,
    params_by_source,
    fontes_com_perda,
    niveis_reducao_perda,
    discount_rate,
    lead_time_loss=11,
    verbose=False,
    timelimit_ms=60000000,
    solver_name="SCIP",
    enable_solver_output=True,
    soft_W_first_L_months=True,
    soft_W_months=None,
    force_soft_W_all_months=False,
    soft_deficit_penalty=None
):
    """
    Resolve um problema de planejamento mensal de água (T meses) via MIP (OR-Tools),
    minimizando VPL(CAPEX + OPEX + penalidades) para cumprir metas mensais de entrega W[t].

    Visão geral do otimizador
    ---------------------
    • Ações (por fonte): cada ação j tem decisões de instalação (y_add[j,m]), módulos ativos por mês
      (a_act[j,t]) e produção (x_act[j,t]). A produção respeita capacidades base e incrementais.

    • Lead time de ação: uma decisão tomada em “mês de decisão m” só vira módulo ativo após “lead”.

    • Limites: (i) teto de módulos total por ação; (ii) teto por decisão (max_add_per_decision);
      (iii) rampa mensal de ativação (ramp_per_month), limitando o quanto a_act pode crescer de t–1 para t.

    • Perdas de distribuição: níveis discretos com λ (percentual de perda) e custo PV acumulado.
      O nível escolhido no mês t (através de z[ell,t]) afeta a entrega efetiva das fontes “com perda”
      após um lead específico (lead_time_loss).

    • Portas lógicas (AND) BARR×RES: quando “BARRxRES” é ativo, aplica-se teto conjunto (combo_cap_t)
      e lógica a_act_AND <= a_act_BARR e a_act_AND <= a_act_RES, etc.

    • Drawdown (teste para o GAS!): se meta.drawdown_model estiver presente, cria-se uma dinâmica
      d_t = ρ·d_{t-1} + Σ_j k_j·x_{j,t} − k_inj·a_inj,t com custo adicional α_j·(x_{j,t}·d_t),
      linearizado por envelopes de McCormick (w_{j,t} = x_{j,t}·d_t).

    Função objetivo
    ---------------
    min  Σ_t DF[t]·[ Σ_{j}( vc_j[t]·x_{j,t} + FOM_j[t]·a_{j,t} )
                     + Σ_{m∈DP_j} capex_j·y_{j,m} (descontado no m+1)
                     + Σ_{j∈draw} α_j·w_{j,t} ]
         + CAPEX(perdas) em forma telescópica
         + penalidade de déficit “soft” nas metas W[t] conforme configuração.

    Principais restrições
    ---------------------
    (A) Ativação/limites:
        • Σ_k y_add[j,k] ≤ max_modules_j
        • y_add[j,k] ≤ max_add_per_decision_j (teto por decisão)
        • a_{j,t} = Σ decisões efetivas até t (considerando lead)
        • a_{j,t} − a_{j,t−1} ≤ ramp_per_month_j  (rampa de crescimento mensal)
        • Lógica AND para ações compostas (ex.: BARRxRES)
    (B) Capacidade:
        • x_{j,t} ≤ cap_base_{j,t} + a_{j,t}·cap_add_j  (ou cap_add_per_module_t se temporal)
    (B+) Teto conjunto BARR×RES:
        • x_RIVER + x_BARR + x_RES + x_AND ≤ combo_cap_t + M·a_AND
    (DD) Drawdown:
        • Dinâmica de d_t e envelopes de McCormick para w_{j,t} = x_{j,t}·d_t
    (C–E) Perdas:
        • Soma das fontes com perda → x_total_perda_t
        • Seleção monotônica de níveis (z[ell,t]), cooldown e lead das perdas
        • x_entregue_perda_t ↔ x_total_perda_t e z[ell,·]
    (F) Meta W:
        • Σ fontes_sem_perda x_{j,t} + x_entregue_perda_t + d_soft_t ≥ W[t]
          (d_soft_t presente somente nos meses configurados como “soft”).

    Parâmetros
    ----------
    strategy_W : array-like de tamanho T
        Série-alvo W[t] (1000 m³/mês). Deve ter o mesmo T inferido do pacote.
    params_by_source : dict {fonte -> pacote_normalizado}
        Pacotes montados por “prepare_*” e normalizados por `normalize_actions_package`.
        Cada ação pode conter:
          - decision_points (lista de meses 0-based),
          - lead_time_months,
          - max_modules,
          - cap_base_t (array T),
          - cap_add_per_module (escalar) OU cap_add_per_module_t (array T),
          - vc_t (array T), capex_per_module (escalar),
          - fixed_om_cost_per_module_t (array T),
          - (opcional) and_gate_of, combo_cap_t, max_add_per_decision, ramp_per_month.
    fontes_com_perda : set[str]
        Conjunto das fontes às quais os níveis de perdas se aplicam.
    niveis_reducao_perda : dict {ell -> (lambda, pv_acumulado)}
        λ (0–1) do nível de redução de perdas e custo PV acumulado até esse nível.
    discount_rate : float
        Taxa de desconto por mês (ex.: 0.05/12).
    lead_time_loss : int (default=11)
        Lead (meses) para a efetivação do nível de perda escolhido.
    verbose : bool
        Imprime auditorias/diagnósticos extras.
    timelimit_ms : int
        Tempo máximo de solver (ms).
    solver_name : str
        “SCIP”, “CBC”, etc. (passa ao OR-Tools).
    enable_solver_output : bool
        Liga/desliga o log do solver.
    soft_W_first_L_months : bool
        Se True, trata as metas W dos primeiros L meses como “soft” com penalidade.
        L é o máximo entre leads das ações e `lead_time_loss`, a menos que `soft_W_months` defina outro valor.
    soft_W_months : int | None
        Se informado, fixa L = soft_W_months (sobrepõe a inferência automática).
    force_soft_W_all_months : bool
        Se True, todas as metas W são “soft”.
    soft_deficit_penalty : float | None
        Penalidade por unidade de d_soft_t. Se None, é calibrada automaticamente
        (≈100× o maior custo variável observado).
    max_add_per_decision : int
        Teto de módulos que podem ser aprovados em uma mesma decisão (m). Se ausente, usa max_modules.
    ramp_per_month : int
        Teto de variação mensal de módulos ativos (a_{j,t} − a_{j,t−1} ≤ ramp_per_month).
        Se ausente, usa max_modules (rampa “solta”).

    Retorno
    -------
    dict com:
      status : str  (“Optimal” | “Feasible” | “Infeasible”)
      vpl_custo_total : float
          VPL de CAPEX + OPEX (exclui penalidade de folga).
      vpl_custo_total_com_folga : float
          Objetivo total do solver (inclui penalidade de folga).
      vpl_capex : float
          CAPEX total: módulos + perdas.
      vpl_opex : float
          OPEX total (variável + fixo).
      vpl_soft_penalty : float
          Soma descontada das penalidades d_soft.
      capex_breakdown : dict
          {"perdas": ..., "check_diff_obj": ...} – verificação de consistência do objetivo.
      delivered_capacity : dict {t -> float}
          Entrega efetiva (já aplicando perdas conforme lead).
      series_by_action : dict {fonte -> {ação -> {"x_t": [...], "a_t": [...]}}}
          Séries mensais de produção e módulos ativos por ação.
      drawdown_series : dict (se houver drawdown)
          {"fonte": {"d_t": [...], "w_xd": {acao: [...]} } }
      investment_details : dict
          Plano por fonte (adds por decisão), níveis de perda escolhidos e timeline.
      actions_installations : dict
          {fonte->{acao->{t_impl: delta_mod}}} com os eventos de implantação.
      install_events : list[dict]
          Lista tabular de eventos {"Fonte","Acao","Periodo","Delta"}.

    Unidades e convenções
    ---------------------
    • Volumes/fluxos em 1000 m³/mês.
    • Custos variáveis em R$/1000 m³; CAPEX/FOM em R$.
    • Tempos: t = 1..T (internamente, decisões usam meses 0-based nos DP).
    • Desconto: DF[t] = 1/(1+discount_rate)^t.
    """

    S = list(params_by_source.keys())

    # 1) Horizonte & W
    T_candidates = [infer_T(params_by_source[s]) for s in S]
    T_valid = [t for t in T_candidates if isinstance(t, (int, np.integer)) and t > 0]
    if not T_valid:
        raise ValueError("Nenhum T válido em params_by_source (meta.horizon_months).")
    T = int(np.nanmin(T_valid))
    periods = list(range(1, T + 1))

    W_vec = np.asarray(strategy_W, dtype=float)
    if len(W_vec) != T:
        raise ValueError(f"strategy_W tem tamanho {len(W_vec)} e T={T}.")

    # L (meses de folga penalizada)
    if soft_W_first_L_months:
        lead_actions_max = 0
        for s2 in S:
            actions_s = (params_by_source[s2].get("actions", {}) or {})
            for ainfo in actions_s.values():
                lead_actions_max = max(lead_actions_max, int(ainfo.get("lead_time_months", 0)))
        lead_actions_max = max(lead_actions_max, int(lead_time_loss or 0))
        if soft_W_months is not None:
            lead_actions_max = int(soft_W_months)
    else:
        lead_actions_max = 0

    # 2) Diagnóstico leve
    t0_diag = time.perf_counter()
    print("\n[diagnóstico-estimativa Ações]")
    approx_x = 0
    approx_int = 0
    for s in S:
        ps = params_by_source[s]
        actions = ps.get("actions", {}) or {}
        n_tech = len(actions)
        dp_count = sum(len(a.get("decision_points", [])) for a in actions.values())
        approx_int += dp_count
        approx_x += n_tech * T
        print(f"  - {s:10s}: techs={n_tech}, decisões={dp_count}")
    print(f"  Vars x≈{approx_x:,}   Vars inteiras≈{approx_int:,}")
    print(f"[tempo] estimativa levou {time.perf_counter()-t0_diag:.3f}s\n")

    # 3) Solver
    solver = pywraplp.Solver.CreateSolver(solver_name) or pywraplp.Solver.CreateSolver("SCIP")
    if timelimit_ms is not None:
        solver.SetTimeLimit(int(timelimit_ms))
    if enable_solver_output:
        try:
            solver.EnableOutput()
        except Exception:
            pass

    # ---------- VARIÁVEIS ----------
    y_add = {}
    a_act = {}
    x_act = {}

    tech_info = {}
    for s in S:
        ps = params_by_source[s]
        actions = ps.get("actions", {}) or {}

        for j, a in actions.items():
            DP = list(a.get("decision_points", []))
            is_and = isinstance(a.get("and_gate_of", None), (list, tuple)) and len(a["and_gate_of"]) == 2

            max_per_dec = int(a.get("max_add_per_decision", int(a.get("max_modules", 0))))
            ramp_pm     = int(a.get("ramp_per_month",       int(a.get("max_modules", 0))))

            if not DP and not is_and:
                raise ValueError(f"{s}/{j}: 'decision_points' vazio.")

            lead = int(a.get("lead_time_months", 0))
            max_mod = int(a.get("max_modules", 0))
            cap_add = float(a.get("cap_add_per_module", 0.0))

            cap_add_t = a.get("cap_add_per_module_t", None)
            if isinstance(cap_add_t, (list, tuple, np.ndarray)):
                cap_add_t = np.asarray(cap_add_t, dtype=float)[:T]
            else:
                cap_add_t = None

            cap_base = np.asarray(a.get("cap_base_t", np.zeros(T)), dtype=float)[:T]
            vc_t     = np.asarray(a.get("vc_t",       np.zeros(T)), dtype=float)[:T]
            capex_per_module = float(a.get("capex_per_module", 0.0))
            fixed_om = np.asarray(a.get("fixed_om_cost_per_module_t", np.zeros(T)), dtype=float)[:T]

            combo_cap_t = a.get("combo_cap_t", None)
            if isinstance(combo_cap_t, (list, tuple, np.ndarray)):
                combo_cap_t = np.asarray(combo_cap_t, dtype=float)[:T]
            else:
                combo_cap_t = None

            tech_info[(s, j)] = {
                "DP": DP, "lead": lead, "max_mod": max_mod,
                "cap_add": cap_add, "cap_add_t": cap_add_t,
                "cap_base": cap_base, "vc_t": vc_t,
                "capex_per_module": capex_per_module, "fixed_om": fixed_om,
                "is_and": is_and,
                "and_of": tuple(a.get("and_gate_of", [])) if is_and else None,
                "combo_cap_t": combo_cap_t,
                "max_per_dec": max_per_dec,
                "ramp": ramp_pm
            }

            if not is_and:
                for k, m in enumerate(DP):
                    ub = tech_info[(s, j)]["max_per_dec"]  # <<< NOVO
                    y_add[(s, j, k)] = solver.IntVar(0, ub, f"y_add__{s}__{j}__m{m}")

            for t in periods:
                a_act[(s, j, t)] = solver.IntVar(0, max_mod, f"a_act__{s}__{j}__t{t}")
                x_act[(s, j, t)] = solver.NumVar(0.0, solver.infinity(), f"x__{s}__{j}__t{t}")

    # >>> REBAIXAMENTO DO GAS (teste): ler config por fonte (merge seguro, por nome de ação)
    draw_models = {}  # s -> config
    for s in S:
        meta_s = (params_by_source[s].get("meta", {}) or {})
        dm = meta_s.get("drawdown_model", None)
        if not isinstance(dm, dict):
            continue

        defaults = {
            "rho": 0.95, "d0": 0.0, "d_max": 40.0,
            "k_urb": 3e-5, "k_wf": 1.5e-5, "k_inj": 0.5,
            "inj_action": "GAS_INJ",
            "applies_to": ["GAS_URB", "GAS_WF"],
            "alpha_cost_urb": 8.0, "alpha_cost_wf": 5.0,
        }
        cfg = {**defaults, **dm}

        applies_to = list(cfg["applies_to"])
        inj_name   = cfg["inj_action"]

        ok = all((s, j) in tech_info for j in applies_to) and ((s, inj_name) in tech_info)
        if not ok:
            continue

        # α_j por ação (aceita alpha_cost como dict direto; senão, deduz pelos nomes)
        if isinstance(cfg.get("alpha_cost"), dict):
            alpha_cost = {j: float(cfg["alpha_cost"].get(j, 0.0)) for j in applies_to}
        else:
            alpha_cost = {}
            for j in applies_to:
                if "URB" in j:
                    alpha_cost[j] = float(cfg["alpha_cost_urb"])
                elif "WF" in j:
                    alpha_cost[j] = float(cfg["alpha_cost_wf"])
                else:
                    alpha_cost[j] = 0.0

        # k por ação (evita depender da ordem de applies_to)
        k_by_action = {}
        for j in applies_to:
            if "URB" in j:
                k_by_action[j] = float(cfg["k_urb"])
            elif "WF" in j:
                k_by_action[j] = float(cfg["k_wf"])
            else:
                k_by_action[j] = 0.0

        draw_models[s] = {
            "rho":  float(cfg["rho"]),
            "d0":   float(cfg["d0"]),
            "dmax": float(cfg["d_max"]),
            "k_by_action": k_by_action,
            "k_inj": float(cfg["k_inj"]),
            "alpha_cost": alpha_cost,
            "applies_to": applies_to,
            "inj": inj_name,
            "vars": {}
        }

    # >>> DRAW DOWN: criar variáveis d_t e w_{j,t}
    for s, cfg in draw_models.items():
        d_vars = {}
        w_vars = {j: {} for j in cfg["applies_to"]}
        for t in periods:
            d_vars[t] = solver.NumVar(0.0, cfg["dmax"], f"d_draw__{s}__t{t}")
            for j in cfg["applies_to"]:
                w_vars[j][t] = solver.NumVar(0.0, solver.infinity(), f"w_xd__{s}__{j}__t{t}")
        cfg["vars"]["d"] = d_vars
        cfg["vars"]["w"] = w_vars

    # Perdas
    LMAX = max(niveis_reducao_perda.keys())
    z = {(ell,t): solver.BoolVar(f"z_loss_{ell}_t{t}") for ell in niveis_reducao_perda for t in periods}
    s_lvl = {t: solver.IntVar(0, LMAX, f"s_level_t{t}") for t in periods}
    u_upg = {t: solver.BoolVar(f"u_upgrade_t{t}") for t in periods if t >= 2}
    x_total_perda    = {t: solver.NumVar(0.0, solver.infinity(), f"x_total_perda_t{t}") for t in periods}
    x_entregue_perda = {t: solver.NumVar(0.0, solver.infinity(), f"x_entregue_perda_t{t}") for t in periods}

    # Folgas
    d_soft = {}
    def get_dsoft(tt: int):
        v = d_soft.get(tt)
        if v is None:
            try:
                v = solver.LookupVariableOrNull(f"d_soft_t{tt}")
            except Exception:
                v = None
            if v is None:
                v = solver.NumVar(0.0, solver.infinity(), f"d_soft_t{tt}")
            d_soft[tt] = v
        return v

    # ---------- OBJETIVO ----------
    obj = solver.Objective(); obj.SetMinimization()
    DF = {t: 1.0 / ((1.0 + discount_rate) ** t) for t in periods}

    # Penalidade déficit soft
    if soft_deficit_penalty is None:
        max_vc = 0.0
        for s2 in params_by_source:
            actions_s = params_by_source[s2]["actions"]
            for ainfo in actions_s.values():
                vc = ainfo.get("vc_t", None)
                if vc is not None and len(vc) > 0:
                    max_vc = max(max_vc, float(np.max(vc)))
        soft_deficit_penalty = 100.0 * (max_vc if max_vc > 0 else 1.0)

    for t in periods:
        if (t <= lead_actions_max) or force_soft_W_all_months:
            obj.SetCoefficient(get_dsoft(t), soft_deficit_penalty * DF[t])

    # OPEX + fixo + CAPEX módulos
    for (s, j), info in tech_info.items():
        vc_t = info["vc_t"]; fixed_om = info["fixed_om"]
        for t in periods:
            obj.SetCoefficient(x_act[(s, j, t)], float(vc_t[t-1]) * DF[t])
            cfix = float(fixed_om[t-1])
            if abs(cfix) > 0:
                obj.SetCoefficient(a_act[(s, j, t)], cfix * DF[t])
        capex_mod = float(info["capex_per_module"])
        if abs(capex_mod) > 0 and len(info["DP"]) > 0:
            for k, m in enumerate(info["DP"]):
                t_disc = int(m) + 1
                if 1 <= t_disc <= T:
                    obj.SetCoefficient(y_add[(s, j, k)], capex_mod * DF[t_disc])

    # >>> DRAW DOWN: custo α_j * w_{j,t}
    for s, cfg in draw_models.items():
        w = cfg["vars"]["w"]
        alpha = cfg["alpha_cost"]
        for j in cfg["applies_to"]:
            a_j = float(alpha.get(j, 0.0))
            if abs(a_j) < 1e-12:
                continue
            for t in periods:
                obj.SetCoefficient(w[j][t], a_j * DF[t])

    # CAPEX perdas
    for ell, (_, pv_acum) in niveis_reducao_perda.items():
        if pv_acum == 0:
            continue
        for t in periods:
            df_t  = DF[t]
            df_tp = DF[t+1] if t < T else 0.0
            obj.SetCoefficient(z[(ell,t)], pv_acum * (df_t - df_tp))

    # ---------- RESTRIÇÕES ----------
    # (A) Ativos por mês + limite total
    for (s, j), info in tech_info.items():
        if info.get("is_and", False):
            a1, a2 = info["and_of"]
            for t in periods:
                # y ≤ a1
                ct1 = solver.Constraint(-solver.infinity(), 0, f"and_le1__{s}__{j}__t{t}")
                ct1.SetCoefficient(a_act[(s, j, t)], 1)
                ct1.SetCoefficient(a_act[(s, a1, t)], -1)
                # y ≤ a2
                ct2 = solver.Constraint(-solver.infinity(), 0, f"and_le2__{s}__{j}__t{t}")
                ct2.SetCoefficient(a_act[(s, j, t)], 1)
                ct2.SetCoefficient(a_act[(s, a2, t)], -1)
                # y ≥ a1 + a2 − 1
                ct3 = solver.Constraint(-1, solver.infinity(), f"and_lb__{s}__{j}__t{t}")
                ct3.SetCoefficient(a_act[(s, j, t)], 1)
                ct3.SetCoefficient(a_act[(s, a1, t)], -1)
                ct3.SetCoefficient(a_act[(s, a2, t)], -1)
            continue

        DP         = info["DP"]
        lead       = int(info["lead"])
        max_mod    = int(info["max_mod"])
        # >>> NOVO: parâmetros (com defaults seguros)
        max_per_dec = int(info.get("max_per_dec", max_mod))   # teto por decisão
        ramp_pm     = int(info.get("ramp",       max_mod))    # rampa mensal

        # Limite total de módulos (soma de todas as decisões) ≤ max_mod
        ct_tot = solver.Constraint(0, max_mod, f"max_mod__{s}__{j}")
        for k in range(len(DP)):
            ct_tot.SetCoefficient(y_add[(s, j, k)], 1)
            # >>> NOVO: teto por decisão (se não quis usar UB no IntVar)
            ct_dec = solver.Constraint(-solver.infinity(), float(max_per_dec),
                                    f"max_per_dec__{s}__{j}__m{DP[k]}")
            ct_dec.SetCoefficient(y_add[(s, j, k)], 1)

        # Vínculo de ativação com lead: a_t = Σ decisões já efetivadas
        for t in periods:
            ct = solver.Constraint(0, 0, f"act_link__{s}__{j}__t{t}")
            ct.SetCoefficient(a_act[(s, j, t)], 1)
            for k, m in enumerate(DP):
                if (m + lead) <= (t - 1):
                    ct.SetCoefficient(y_add[(s, j, k)], -1)

        # >>> NOVO: rampa mensal — só pode aumentar até 'ramp_pm' por mês
        if ramp_pm > 0:
            for t in periods[1:]:
                ct_ramp = solver.Constraint(-solver.infinity(), float(ramp_pm),
                                            f"ramp__{s}__{j}__t{t}")
                ct_ramp.SetCoefficient(a_act[(s, j, t)],   1.0)
                ct_ramp.SetCoefficient(a_act[(s, j, t-1)], -1.0)

    # (B) Capacidade: x_act ≤ cap_base + cap_add * a_act (+cap_add_t)
    for (s, j), info in tech_info.items():
        cap_base = info["cap_base"]; cap_add  = info["cap_add"]; cap_add_t = info.get("cap_add_t", None)
        for t in periods:
            ct = solver.Constraint(-np.inf, float(cap_base[t-1]), f"cap_base__{s}__{j}__t{t}")
            ct.SetCoefficient(x_act[(s, j, t)], 1)
            if cap_add_t is not None:
                ct.SetCoefficient(a_act[(s, j, t)], -float(cap_add_t[t-1]))
            elif abs(cap_add) > 0:
                ct.SetCoefficient(a_act[(s, j, t)], -float(cap_add))

    # (B+') Teto conjunto BARR×RES quando ambos ativos
    for (s, j), info in tech_info.items():
        if not info.get("is_and", False):
            continue
        a1, a2 = info["and_of"]
        combo_cap_t = info.get("combo_cap_t", None)
        if combo_cap_t is None:
            continue

        info_R  = tech_info.get((s, "RIVER"))
        info_B  = tech_info.get((s, a1))
        info_Rs = tech_info.get((s, a2))
        for t in periods:
            def ub(info_k):
                if info_k is None: return 0.0
                cap_b = float(info_k["cap_base"][t-1])
                cap_t = info_k.get("cap_add_t", None)
                if cap_t is not None:
                    return cap_b + float(info_k["max_mod"]) * float(cap_t[t-1])
                else:
                    return cap_b + float(info_k["max_mod"]) * float(info_k["cap_add"])
            M_combo_t = ub(info_R) + ub(info_B) + ub(info_Rs) + ub(info)
            ct_combo = solver.Constraint(-solver.infinity(),
                                         float(combo_cap_t[t-1]) + M_combo_t,
                                         f"combo_cap__{s}__t{t}")
            if (s, "RIVER", t) in x_act: ct_combo.SetCoefficient(x_act[(s, "RIVER", t)], 1)
            if (s, a1,      t) in x_act: ct_combo.SetCoefficient(x_act[(s, a1,      t)], 1)
            if (s, a2,      t) in x_act: ct_combo.SetCoefficient(x_act[(s, a2,      t)], 1)
            if (s, j,       t) in x_act: ct_combo.SetCoefficient(x_act[(s, j,       t)], 1)
            if (s, j,       t) in a_act: ct_combo.SetCoefficient(a_act[(s, j, t)], M_combo_t)

    # >>> REBAIXAMENTO (teste para o SAG, ainda quero mexer e entender como vai interagir com o modelo): dinâmica d_t
    def _ub_cap(info_k, t):
        if info_k is None: return 0.0
        cap_b = float(info_k["cap_base"][t-1])
        cap_t = info_k.get("cap_add_t", None)
        if cap_t is not None:
            return cap_b + float(info_k["max_mod"]) * float(cap_t[t-1])
        else:
            return cap_b + float(info_k["max_mod"]) * float(info_k["cap_add"])

    for s, cfg in draw_models.items():
        d   = cfg["vars"]["d"]
        rho = cfg["rho"]; d0 = cfg["d0"]
        j_inj = cfg["inj"]
        for t in periods:
            if t == 1:
                rhs = rho * d0
                ct = solver.Constraint(rhs, rhs, f"ddyn__{s}__t{t}")
                ct.SetCoefficient(d[t], 1.0)
                for j in cfg["applies_to"]:
                    ct.SetCoefficient(x_act[(s, j, t)], -cfg["k_by_action"][j])
                ct.SetCoefficient(a_act[(s, j_inj, t)],  cfg["k_inj"])
            else:
                ct = solver.Constraint(0.0, 0.0, f"ddyn__{s}__t{t}")
                ct.SetCoefficient(d[t], 1.0)
                ct.SetCoefficient(d[t-1], -rho)
                for j in cfg["applies_to"]:
                    ct.SetCoefficient(x_act[(s, j, t)], -cfg["k_by_action"][j])
                ct.SetCoefficient(a_act[(s, j_inj, t)],  cfg["k_inj"])

    # >>> Rebaixamento: McCormick de w = x*d (x>=0, d>=0) (como rebaixmento é uma variável e vazão captada também, isso torna o problema não linear, por isso tive que buscar uma solução de McCormick, que introduz uma variável auxiliar como o produto entre x e d)
    for s, cfg in draw_models.items():
        d   = cfg["vars"]["d"]
        w   = cfg["vars"]["w"]
        Ud  = cfg["dmax"]
        for j in cfg["applies_to"]:
            info_j = tech_info[(s, j)]
            for t in periods:
                Ux = _ub_cap(info_j, t)
                ct1 = solver.Constraint(-solver.infinity(), 0.0, f"mcc1__{s}__{j}__t{t}")
                ct1.SetCoefficient(w[j][t], 1.0)
                ct1.SetCoefficient(x_act[(s, j, t)], -Ud)
                ct2 = solver.Constraint(-solver.infinity(), 0.0, f"mcc2__{s}__{j}__t{t}")
                ct2.SetCoefficient(w[j][t], 1.0)
                ct2.SetCoefficient(d[t], -Ux)
                ct3 = solver.Constraint(-Ux*Ud, solver.infinity(), f"mcc_lb__{s}__{j}__t{t}")
                ct3.SetCoefficient(w[j][t], 1.0)
                ct3.SetCoefficient(x_act[(s, j, t)], -Ud)
                ct3.SetCoefficient(d[t], -Ux)

    # (C) Soma p/ perdas por mês → x_total_perda
    for t in periods:
        ct_sum_perda = solver.Constraint(0, 0, f"sum_perda_t{t}")
        ct_sum_perda.SetCoefficient(x_total_perda[t], 1)
        for (s2, j2) in tech_info.keys():
            if s2 in fontes_com_perda:
                ct_sum_perda.SetCoefficient(x_act[(s2, j2, t)], -1)

    # (D) Perdas – seleção/monotonicidade/cooldown
    for t in periods:
        ct_one = solver.Constraint(1, 1, f"one_loss_level_t{t}")
        for ell in niveis_reducao_perda:
            ct_one.SetCoefficient(z[(ell,t)], 1)
        ct_s = solver.Constraint(0, 0, f"def_s_t{t}")
        ct_s.SetCoefficient(s_lvl[t], 1)
        for ell in niveis_reducao_perda:
            ct_s.SetCoefficient(z[(ell,t)], -ell)

    for t in periods[:-1]:
        ct_mon = solver.Constraint(0, solver.infinity(), f"monotonic_t{t}")
        ct_mon.SetCoefficient(s_lvl[t+1], 1)
        ct_mon.SetCoefficient(s_lvl[t], -1)

    if T >= 2:
        LMAX = max(niveis_reducao_perda.keys())
        for t in range(2, T+1):
            ct_lb = solver.Constraint(0, solver.infinity(), f"upg_lb_t{t}")
            ct_lb.SetCoefficient(s_lvl[t], 1)
            ct_lb.SetCoefficient(s_lvl[t-1], -1)
            ct_lb.SetCoefficient(u_upg[t], -1)
            ct_ub = solver.Constraint(-solver.infinity(), 0, f"upg_ub_t{t}")
            ct_ub.SetCoefficient(s_lvl[t], 1)
            ct_ub.SetCoefficient(s_lvl[t-1], -1)
            ct_ub.SetCoefficient(u_upg[t], -LMAX)
        for start in range(2, T+1):
            end = min(T, start + lead_time_loss - 1)
            ct_cool = solver.Constraint(-solver.infinity(), 1, f"cooldown_{start}")
            for k in range(start, end+1):
                if k in u_upg:
                    ct_cool.SetCoefficient(u_upg[k], 1)

    # (E) Ligação perdas: x_total_perda → x_entregue_perda
    lambda0 = float(niveis_reducao_perda[0][0])
    cap_perda_max = 0.0
    for t in periods:
        cap_t = 0.0
        for (s2, j2), info2 in tech_info.items():
            if s2 not in fontes_com_perda:
                continue
            cap_t += float(info2["cap_base"][t-1])
            if info2.get("cap_add_t") is not None:
                cap_t += float(info2["max_mod"]) * float(info2["cap_add_t"][t-1])
            else:
                cap_t += float(info2["max_mod"]) * float(info2["cap_add"])
        cap_perda_max = max(cap_perda_max, cap_t)
    M = max(1.0, 2.0 * cap_perda_max)

    for t in periods:
        if t <= lead_time_loss:
            lam_max = max(float(v[0]) for v in niveis_reducao_perda.values())
            ct_init_le = solver.Constraint(-solver.infinity(), 0, f"loss_link_init_le_t{t}")
            ct_init_le.SetCoefficient(x_entregue_perda[t], 1)
            ct_init_le.SetCoefficient(x_total_perda[t], -(1.0 - lambda0))
            ct_init_ge = solver.Constraint(-solver.infinity(), 0, f"loss_link_init_ge_t{t}")
            ct_init_ge.SetCoefficient(x_entregue_perda[t], -1)
            ct_init_ge.SetCoefficient(x_total_perda[t],  (1.0 - lam_max))
        else:
            t_eff = t - lead_time_loss
            for ell, (lam, _) in niveis_reducao_perda.items():
                f = 1.0 - float(lam)
                ct1 = solver.Constraint(-solver.infinity(), M, f"loss_le_t{t}_ell{ell}")
                ct1.SetCoefficient(x_entregue_perda[t], 1)
                ct1.SetCoefficient(x_total_perda[t], -f)
                ct1.SetCoefficient(z[(ell,t_eff)], M)
                ct2 = solver.Constraint(-solver.infinity(), M, f"loss_ge_t{t}_ell{ell}")
                ct2.SetCoefficient(x_entregue_perda[t], -1)
                ct2.SetCoefficient(x_total_perda[t],  f)
                ct2.SetCoefficient(z[(ell,t_eff)], M)

    # (F) Meta W (≥ W[t])
    for t in periods:
        if (t <= lead_actions_max) or force_soft_W_all_months:
            ct_W = solver.Constraint(float(W_vec[t-1]), solver.infinity(), f"target_W_soft_t{t}")
            ct_W.SetCoefficient(get_dsoft(t), 1.0)
        else:
            ct_W = solver.Constraint(float(W_vec[t-1]), solver.infinity(), f"target_W_t{t}")

        for s2 in S:
            if s2 in fontes_com_perda:
                continue
            actions_s = params_by_source[s2]["actions"]
            for j2 in actions_s.keys():
                ct_W.SetCoefficient(x_act[(s2, j2, t)], 1)

        ct_W.SetCoefficient(x_entregue_perda[t], 1)

    print(f"[modelo] vars={solver.NumVariables():,}   cons={solver.NumConstraints():,}")

    # ---------- SOLVER ----------
    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        try:
            lam_min = min(float(v[0]) for v in niveis_reducao_perda.values())
            max_cap_sem_perda = {t: 0.0 for t in periods}
            max_cap_com_perda = {t: 0.0 for t in periods}

            for (s2, j2), info2 in tech_info.items():
                for t in periods:
                    cap_b = float(info2["cap_base"][t-1])
                    if info2.get("cap_add_t") is not None:
                        cap_b += float(info2["max_mod"]) * float(info2["cap_add_t"][t-1])
                    else:
                        cap_b += float(info2["max_mod"]) * float(info2["cap_add"])
                    if s2 in fontes_com_perda:
                        max_cap_com_perda[t] += cap_b
                    else:
                        max_cap_sem_perda[t] += cap_b

            slack = {}
            for t in periods:
                lam_eff = lambda0 if t <= lead_time_loss else lam_min
                max_ent = max_cap_sem_perda[t] + (1.0 - lam_eff) * max_cap_com_perda[t]
                slack[t] = max_ent - float(W_vec[t-1])
            worst_t = min(slack, key=slack.get)
            print("[debug-W] min slack (upper-bound):", f"t={worst_t}  slack={slack[worst_t]:.2f}")
        except Exception:
            pass

        return {"status": "Infeasible", "vpl_custo_total": float("inf"),
                "vpl_capex": float("nan"), "vpl_opex": float("nan"),
                "delivered_capacity": None, "investment_details": None}

    obj_total = solver.Objective().Value()

    # "Auditoria" de folgas (um teste de sanidade)
    soft_used = {t: (d_soft[t].solution_value() if t in d_soft else 0.0) for t in periods}
    if any(v > 1e-6 for v in soft_used.values()):
        print("[soft-W] Folgas (1000 m³):", {t: round(v, 2) for t, v in soft_used.items() if v > 1e-6})

    # Instalações & CAPEX
    DF = {t: 1.0 / ((1.0 + discount_rate) ** t) for t in periods}
    action_plan = {}
    actions_installations = {}
    install_events = []
    vpl_capex_modulos = 0.0

    for (s, j), info in tech_info.items():
        DP = info["DP"]; lead = int(info["lead"]); capex_mod = float(info["capex_per_module"])
        plan_rows = []; cum = 0.0
        for k, m in enumerate(DP):
            add_val = y_add.get((s, j, k), None)
            add_val = add_val.solution_value() if add_val is not None else 0.0
            if add_val > 1e-9:
                add_int = int(round(add_val))
                t_disc = int(m) + 1
                if 1 <= t_disc <= T and abs(capex_mod) > 0:
                    vpl_capex_modulos += DF[t_disc] * capex_mod * add_val
                t_impl = int(m) + lead + 1
                if 1 <= t_impl <= T:
                    actions_installations.setdefault(s, {}).setdefault(j, {})
                    actions_installations[s][j][t_impl] = actions_installations[s][j].get(t_impl, 0) + add_int
                    install_events.append({"Fonte": s, "Acao": j, "Periodo": int(t_impl), "Delta": add_int})
                plan_rows.append((int(m), add_int))
                cum += add_val
        action_plan.setdefault(s, {})[j] = {"adds_by_decision_month": plan_rows,
                                            "total_modules": int(round(cum))}

    # OPEX (variável + fixo)
    vpl_opex = 0.0
    for (s, j), info in tech_info.items():
        vc_t = info["vc_t"]; fixed_om = info["fixed_om"]
        for t in periods:
            q = x_act[(s, j, t)].solution_value()
            if q > 0:
                vpl_opex += DF[t] * float(vc_t[t-1]) * q
            a = a_act[(s, j, t)].solution_value()
            if a > 0:
                vpl_opex += DF[t] * float(fixed_om[t-1]) * a

    # CAPEX perdas
    custo_nivel = {ell: v[1] for ell, v in niveis_reducao_perda.items()}
    chosen_level = {}; capex_perdas = 0.0; prev_cost = 0.0
    for t in periods:
        chosen = 0
        for ell in niveis_reducao_perda:
            if z[(ell,t)].solution_value() > 0.5:
                chosen = ell; break
        chosen_level[t] = chosen
        cur_cost = custo_nivel[chosen]
        delta = cur_cost - prev_cost
        if delta > 1e-12:
            capex_perdas += DF[t] * delta
        prev_cost = cur_cost

    vpl_capex = vpl_capex_modulos + capex_perdas

    # Penalidade de folga (em VPL): somar só onde criamos d_soft
    vpl_soft_penalty = 0.0
    for t in periods:
        if t in d_soft:
            vpl_soft_penalty += DF[t] * float(soft_deficit_penalty) * d_soft[t].solution_value()

    # Custo total SEM a penalidade de folga (para leitura clara)
    vpl_custo_total_sem_folga = vpl_capex + vpl_opex

    # Entregas
    delivered_capacity = {}
    for t in periods:
        q_sem = 0.0; q_com = 0.0
        for (s2, j2) in tech_info.keys():
            val = x_act[(s2, j2, t)].solution_value()
            if s2 in fontes_com_perda: q_com += val
            else:                      q_sem += val
        if t <= lead_time_loss:
            lam = float(niveis_reducao_perda[0][0])
        else:
            t_eff = t - lead_time_loss
            lam = None
            for ell in niveis_reducao_perda:
                if z[(ell,t_eff)].solution_value() > 0.5:
                    lam = float(niveis_reducao_perda[ell][0]); break
            if lam is None:
                lam = float(niveis_reducao_perda[0][0])
        delivered_capacity[t] = q_sem + q_com * (1.0 - lam)

    # Séries x_t e a_t por ação
    series_by_action = {}
    for (s2, j2) in tech_info.keys():
        series_by_action.setdefault(s2, {})
        series_by_action[s2][j2] = {
            "x_t": [x_act[(s2, j2, t)].solution_value() for t in periods],
            "a_t": [a_act[(s2, j2, t)].solution_value() for t in periods],
        }

    # Séries de drawdown (se houver)
    drawdown_series = {}
    for s2, cfg in draw_models.items():
        d  = cfg["vars"]["d"]
        w  = cfg["vars"]["w"]
        drawdown_series[s2] = {
            "d_t": [d[t].solution_value() for t in periods],
            "w_xd": { j: [w[j][t].solution_value() for t in periods]
                      for j in cfg["applies_to"] }
        }

    # Auditoria objetivo
    gap_obj = abs((vpl_capex + vpl_opex) - obj_total)
    if verbose and gap_obj > max(1e-6 * abs(obj_total), 1e-3):
        print(f"[WARN] Auditoria: (CAPEX+OPEX) ≠ objetivo: gap={gap_obj:.6f}")

    investment_details = {
        "acoes_por_fonte": action_plan,
        "perdas": [f"Per. {t}: nível {chosen_level[t]}" for t in periods],
        "timeline": install_events
    }

    return {
        "status": "Optimal" if status == pywraplp.Solver.OPTIMAL else "Feasible",
        "vpl_custo_total": vpl_custo_total_sem_folga,
        "vpl_custo_total_com_folga": obj_total,
        "vpl_capex": vpl_capex,
        "vpl_opex": vpl_opex,
        "vpl_soft_penalty": vpl_soft_penalty,
        "capex_breakdown": {
            "perdas": capex_perdas,
            "check_diff_obj": abs((vpl_capex + vpl_opex + vpl_soft_penalty) - obj_total)
        },
        "delivered_capacity": delivered_capacity,
        "series_by_action": series_by_action,
        "drawdown_series": drawdown_series,
        "investment_details": investment_details,
        "actions_installations": actions_installations,
        "install_events": install_events
    }

# ========== 5) DRIVER (roda a otimização em loop por estratégia e junta em gráficos [alguns novos!! para uma checagem geral de como está funcionando]) ==========
if __name__ == "__main__":

    # (1) Monta params
    paramsA_by_source = build_paramsA_by_source(
        start_date="2025-01-01", years=25
    )
    params_by_source = {
        "BAS": normalize_actions_package(paramsA_by_source["BAS"]),
        "Batalha": normalize_actions_package(paramsA_by_source["Batalha"]),
        "GAS": normalize_actions_package(paramsA_by_source["GAS"]),
    }
    print(params_by_source["BAS"])
    print('################')

    # (2) Perdas (níveis)
    perda_atual_custom = 0.40
    perda_minima_viavel_custom = 0.25
    custo_total_reducao_custom = 3 * 66.21 * 10**6
    niveis_reducao_perda = gerar_niveis_de_perda(
        perda_atual_custom, perda_minima_viavel_custom, custo_total_reducao_custom, passo=0.03
    )
    LEAD_TIME_LOSS = 6
    discount_rate = 0.05 / 12
    fontes_com_perda = {"Batalha", "GAS"}

    # (3) Horizonte comum + baseline entregue
    T_list = []
    for s in params_by_source:
        Ti = infer_T(params_by_source[s], default_T=0)
        if isinstance(Ti, (int, np.integer)) and Ti > 0:
            T_list.append(int(Ti))
    T = min(T_list)
    periods = np.arange(1, T + 1)
    print("Horizontes detectados:", {s: infer_T(params_by_source[s], default_T=0) for s in params_by_source})

    C0_entregue = baseline_delivery_from_paramsA(params_by_source, fontes_com_perda, niveis_reducao_perda)

    # (4) Programas W
    w1, w2, w3 = 0.10, 0.25, 0.50
    meses_constantes = 13
    W_programs = {
        "W0 (Base)": [C0_entregue] * T,
        f"W1 (Leve {100 * w1:.0f}%)": build_W_series(C0_entregue, T, w1, meses_constantes),
        f"W2 (Moderada {100 * w2:.0f}%)": build_W_series(C0_entregue, T, w2, meses_constantes),
        f"W3 (Elevada {100 * w3:.0f}%)": build_W_series(C0_entregue, T, w3, meses_constantes),
    }

    # (5) Cenários de demanda (para avaliar déficit ex-post)
    pop0 = 391740
    taxa_estag = 0.005 / 12
    taxa_tend = 0.01 / 12
    taxa_acel = 0.02 / 12
    consumo_m3pcd = 215.3 / 1000  # m³/capita/dia
    dias_mes_medio = 30.4
    scenarios_demanda = {
        "estagnação": {t: (pop0 * (1 + taxa_estag) ** t) * consumo_m3pcd * dias_mes_medio / 1000 for t in range(1, T + 1)},
        "crescimento tendencial": {t: (pop0 * (1 + taxa_tend) ** t) * consumo_m3pcd * dias_mes_medio / 1000 for t in range(1, T + 1)},
        "crescimento acelerado": {t: (pop0 * (1 + taxa_acel) ** t) * consumo_m3pcd * dias_mes_medio / 1000 for t in range(1, T + 1)},
    }

    # (6) Rodadas por W (prints primeiro)
    final_results = []
    timeline_events = []
    series_data = []
    delivered_rows = []   # série efetiva (pós-perdas) por estratégia
    eff_rows = []         # VC efetivo por ação/tempo/estratégia

    print("Iniciando a avaliação das estratégias…")
    for name, W in W_programs.items():
        print(f"\n--- Otimizando: {name} ---")
        opt_result = optimize_by_actions(
            strategy_W=W,
            params_by_source=params_by_source,
            fontes_com_perda=fontes_com_perda,
            niveis_reducao_perda=niveis_reducao_perda,
            discount_rate=discount_rate,
            lead_time_loss=LEAD_TIME_LOSS,
            verbose=False,
            timelimit_ms=3000000, ######## <============= MEXER AQUI PARA MUDAR O TEMPO DE EXEXCUÇÃO!
            solver_name="SCIP",
            force_soft_W_all_months=False,
            soft_deficit_penalty=1e9,
            enable_solver_output=False,
        )

        if opt_result["status"] not in ("Optimal", "Feasible"):
            print(f"  > Não foi possível encontrar um plano viável ({opt_result['status']}).")
            continue

        # Séries por ação (para o gráfico de "vazão extraída")
        sba = opt_result.get("series_by_action", {})
        for fonte, acts in sba.items():
            for acao, series in acts.items():
                for t, val in enumerate(series["x_t"], 1):
                    series_data.append(
                        {
                            "Estratégia": name,
                            "Fonte": fonte,
                            "Ação": acao,
                            "Período": t,
                            "Vazão Extraída (mil m³/mês)": val,
                        }
                    )

        # Total efetivo (pós-perdas) desta estratégia
        capacity_plan = opt_result["delivered_capacity"]
        for t, qeff in capacity_plan.items():
            delivered_rows.append({
                "Estratégia": name,
                "Período": int(t),
                "Vazão Efetiva (mil m³/mês)": float(qeff),
            })

        # VC efetivo por ação/tempo (inclui drawdown quando houver)
        draw = opt_result.get("drawdown_series", {})
        for fonte, acts in sba.items():
            pack = params_by_source[fonte]["actions"]
            ddm = (params_by_source[fonte].get("meta", {}) or {}).get("drawdown_model", None)
            has_dd = isinstance(ddm, dict) and fonte in draw

            alpha_by_action = {}
            if has_dd:
                applies = list(ddm.get("applies_to", []))
                if isinstance(ddm.get("alpha_cost"), dict):
                    for j in applies:
                        alpha_by_action[j] = float(ddm["alpha_cost"].get(j, 0.0))
                else:
                    a_urb = float(ddm.get("alpha_cost_urb", 0.0))
                    a_wf  = float(ddm.get("alpha_cost_wf",  0.0))
                    for j in applies:
                        if "URB" in j:
                            alpha_by_action[j] = a_urb
                        elif "WF" in j:
                            alpha_by_action[j] = a_wf
                        else:
                            alpha_by_action[j] = 0.0
                d_t = np.asarray(draw[fonte]["d_t"], dtype=float)
            else:
                d_t = None

            for acao, series in acts.items():
                vc_base = np.asarray(pack[acao]["vc_t"], dtype=float)
                x_ser   = np.asarray(series["x_t"], dtype=float)
                if has_dd and acao in (ddm.get("applies_to", []) or []):
                    w_map = draw[fonte]["w_xd"].get(acao, None)
                    w_ser = np.asarray(w_map, dtype=float) if w_map is not None else None
                    alpha = float(alpha_by_action.get(acao, 0.0))
                else:
                    w_ser = None
                    alpha = 0.0

                T_here = len(x_ser)
                for t in range(1, T_here+1):
                    vc_t  = float(vc_base[t-1])
                    if d_t is not None and acao in (ddm.get("applies_to", []) or []):
                        vc_eff = vc_t + alpha * float(d_t[t-1])
                        if w_ser is not None and x_ser[t-1] > 0:
                            vc_real = (vc_t * x_ser[t-1] + alpha * w_ser[t-1]) / x_ser[t-1]
                        else:
                            vc_real = np.nan
                    else:
                        vc_eff = vc_t
                        vc_real = vc_t if x_ser[t-1] > 0 else np.nan

                    eff_rows.append({
                        "Estratégia": name,
                        "Fonte": fonte,
                        "Ação": acao,
                        "Período": t,
                        "VC_base (R$/mil m³)": vc_t,
                        "d_t (m)": (float(d_t[t-1]) if d_t is not None else 0.0),
                        "alpha": alpha,
                        "VC_efetivo (R$/mil m³)": vc_eff,
                        "VC_realizado (R$/mil m³)": vc_real,
                        "x_t (mil m³/mês)": float(x_ser[t-1]),
                    })

        vpl_cost = opt_result["vpl_custo_total"]
        vpl_capex = opt_result["vpl_capex"]
        vpl_opex = opt_result["vpl_opex"]
        cap_perdas = opt_result.get("capex_breakdown", {}).get("perdas", 0.0)
        cap_infra = vpl_capex - cap_perdas

        print(f"  > VPL Custo Total: {vpl_cost/1e6:.2f} R$ mi")
        print(f"    CAPEX (perdas): {cap_perdas/1e6:.2f} R$ mi | CAPEX (infra): {cap_infra/1e6:.2f} R$ mi")

        # Eventos de instalação (timeline)
        for ev in opt_result.get("install_events", []):
            timeline_events.append(
                {
                    "Estratégia": name,
                    "Período": ev["Periodo"],
                    "Ação Implementada": f"{ev['Fonte']}: {ev['Acao']} +{ev['Delta']}",
                }
            )

        # Déficit por cenário (ex-post)
        capacity_plan = opt_result["delivered_capacity"]
        for scen_name, scen_demand in scenarios_demanda.items():
            total_deficit = 0.0
            for t in periods:
                total_deficit += max(0.0, scen_demand[t] - capacity_plan[t])
            final_results.append(
                {
                    "Estratégia (W)": name,
                    "Cenário de Demanda": scen_name,
                    "VPL Custo Total (R$ mi)": vpl_cost / 1e6,
                    "VPL CAPEX (R$ mi)": vpl_capex / 1e6,
                    "VPL OPEX (R$ mi)": vpl_opex / 1e6,
                    "Déficit Total (mil m³)": total_deficit,
                }
            )

    # ===== Prints consolidados =====
    if final_results:
        df_final = pd.DataFrame(final_results).round(2)
        print("\n" + "=" * 80)
        print(" Trade-off Custo vs. Déficit por Estratégia/Cenário ")
        print("=" * 80)
        print(df_final.to_string(index=False))
        print("=" * 80 + "\n")
    else:
        print("Nenhum resultado viável para o gráfico de trade-off.")

    if timeline_events:
        df_timeline = pd.DataFrame(timeline_events).sort_values(["Estratégia", "Período"])
        print("\n" + "=" * 80)
        print(" Resumo das Ações de Investimento por Período ")
        print("=" * 80)
        print(df_timeline.to_string(index=False))
        print("=" * 80 + "\n")
    else:
        print("Nenhuma ação de investimento registrada.")

    # ===== Gráficos (após todos os prints) =====
    # 1) Trade-off custo vs. déficit
    if final_results:
        plt.style.use("seaborn-v0_8-whitegrid")
        g = sns.relplot(
            data=df_final,
            x="Déficit Total (mil m³)",
            y="VPL Custo Total (R$ mi)",
            hue="Estratégia (W)",
            style="Cenário de Demanda",
            s=130,
            height=7,
            aspect=1.3,
            palette="viridis",
            edgecolor="w",
            alpha=0.85,
            legend="full",
        )
        for scenario in df_final["Cenário de Demanda"].unique():
            scenario_data = (
                df_final[df_final["Cenário de Demanda"] == scenario]
                .sort_values("VPL Custo Total (R$ mi)")
            )
            g.ax.plot(
                scenario_data["Déficit Total (mil m³)"],
                scenario_data["VPL Custo Total (R$ mi)"],
                color="grey",
                linestyle="--",
                zorder=0,
            )
        g.ax.axvline(x=0, linestyle="--", color="red", linewidth=1.2)
        g.ax.text(
            0,
            g.ax.get_ylim()[1],
            "Déficit = 0",
            color="red",
            ha="right",
            va="top",
            rotation=90,
            fontsize=10,
        )
        g.fig.suptitle("Trade-off: Custo vs. Déficit por Estratégia", y=1.02, fontsize=16)
        g.set_axis_labels("Déficit Total (milhares de m³)", "Custo: VPL Total (R$ mi)", fontsize=12)
        if g._legend is not None:
            g._legend.set_title("Legenda")
        plt.tight_layout()
        plt.show()

    # 2) Timeline de instalações (investimentos)
    if timeline_events:
        plt.style.use("seaborn-v0_8-whitegrid")
        g_timeline = sns.catplot(
            data=df_timeline,
            x="Período",
            y="Ação Implementada",
            col="Estratégia",
            kind="strip",
            height=3,
            aspect=2,
            col_wrap=1,
            hue="Ação Implementada",
            s=15,
            jitter=0,
            sharey=False,
        )
        g_timeline.fig.suptitle("Linha do Tempo dos Investimentos por Estratégia", y=1.03, fontsize=18)
        g_timeline.set_axis_labels("Período de Implementação (mês)", "Ação de Investimento")
        g_timeline.set_titles("Estratégia: {col_name}")
        g_timeline.fig.tight_layout(rect=[0, 0, 1, 0.96])
        plt.show()

    # 3) Metas W vs. Demanda (facet por estratégia x cenário)
    if final_results:
        meta_data = []
        for name, W_values in W_programs.items():
            for t, value in enumerate(W_values, 1):
                meta_data.append({"Estratégia": name, "Período": t, "Valor": value, "Tipo": "Meta de Entrega (W)"})
        df_metas = pd.DataFrame(meta_data)

        demand_data = []
        for scen_name, demand_values in scenarios_demanda.items():
            for t, value in demand_values.items():
                demand_data.append({"Cenário de Demanda": scen_name, "Período": t, "Valor": value, "Tipo": "Demanda"})
        df_demand = pd.DataFrame(demand_data)

        estrategias_unicas = df_metas[["Estratégia"]].drop_duplicates()
        cenarios_unicos = df_demand[["Cenário de Demanda"]].drop_duplicates()
        df_grid_base = estrategias_unicas.merge(cenarios_unicos, how="cross")

        df_plot_metas = pd.merge(df_grid_base, df_metas, on="Estratégia")
        df_plot_demanda = pd.merge(df_grid_base, df_demand, on="Cenário de Demanda")
        df_final_plot = pd.concat([df_plot_metas, df_plot_demanda])

        plt.style.use("seaborn-v0_8-whitegrid")
        palette = {"Meta de Entrega (W)": "royalblue", "Demanda": "orangered"}

        g = sns.FacetGrid(
            df_final_plot,
            row="Estratégia",
            col="Cenário de Demanda",
            row_order=list(W_programs.keys()),
            col_order=list(scenarios_demanda.keys()),
            height=2.5,
            aspect=2.2,
            margin_titles=True,
            hue="Tipo",
            palette=palette,
        )
        g.map_dataframe(
            sns.lineplot,
            x="Período",
            y="Valor",
            style="Tipo",
            dashes={"Meta de Entrega (W)": "", "Demanda": (4, 2)},
            linewidth=2,
            legend=False,
        )
        g.set_axis_labels("Período (meses)", "Volume de Água\n(1000 m³/ano)")
        g.set_titles(col_template="{col_name}", row_template="{row_name}")
        handles = [h for h in g._legend_data.values()]
        labels = [l for l in g._legend_data.keys()]
        g.fig.legend(
            handles=handles,
            labels=labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.98),
            ncol=len(labels),
            frameon=False,
            title="Séries:",
        )
        g.fig.tight_layout(rect=[0, 0, 1, 0.92])
        plt.show()

    # 3b) Total produzido × Total efetivo × Meta (por estratégia)
    if series_data and delivered_rows:
        df_series_all = pd.DataFrame(series_data)
        df_prod_total = (
            df_series_all.groupby(['Estratégia','Período'])['Vazão Extraída (mil m³/mês)']
                         .sum().reset_index()
                         .rename(columns={'Vazão Extraída (mil m³/mês)':'Valor'})
        )
        df_prod_total['Série'] = 'Total produzido (bruto)'

        df_deliv_total = pd.DataFrame(delivered_rows).rename(
            columns={'Vazão Efetiva (mil m³/mês)':'Valor'}
        )
        df_deliv_total['Série'] = 'Total efetivo (pós-perdas)'

        meta_rows = []
        for estrat, W_vals in W_programs.items():
            for t, v in enumerate(W_vals, 1):
                meta_rows.append({"Estratégia": estrat, "Período": t, "Valor": float(v), "Série": "Meta W"})
        df_meta_total = pd.DataFrame(meta_rows)

        df_compare = pd.concat([df_prod_total, df_deliv_total, df_meta_total], ignore_index=True)

        plt.style.use("seaborn-v0_8-whitegrid")
        g_comp = sns.FacetGrid(
            df_compare, row='Estratégia', hue='Série',
            sharey=False, height=2.6, aspect=2.0, margin_titles=True
        )
        g_comp.map_dataframe(sns.lineplot, x='Período', y='Valor')

        # === legenda fora do grid ===
        # pega handles/labels do 1º eixo
        first_ax = g_comp.axes.flat[0] if hasattr(g_comp, "axes") else g_comp.ax
        handles, labels = first_ax.get_legend_handles_labels()
        if g_comp._legend is not None:
            g_comp._legend.remove()
        g_comp.fig.legend(
            handles, labels,
            loc="upper center", bbox_to_anchor=(0.5, 1.02),
            ncol=len(labels), frameon=True, title="Séries"
        )

        g_comp.set_axis_labels("Período (meses)", "Volume (mil m³/mês)")
        g_comp.fig.suptitle("Total produzido × Total efetivo × Meta (por estratégia)", y=1.05, fontsize=16, weight="bold")
        g_comp.fig.subplots_adjust(top=0.86)  # abre espaço para a legenda/supertítulo
        plt.show()

    # 4) Produção (vazão extraída) por ação — timelines + linha de TOTAL por estratégia
    if series_data:
        df_series = pd.DataFrame(series_data)

        df_total = (df_series
            .groupby(["Estratégia", "Período"], as_index=False)["Vazão Extraída (mil m³/mês)"]
            .sum()
            .rename(columns={"Vazão Extraída (mil m³/mês)": "Vazão Total (mil m³/mês)"})
        )

        plt.style.use("seaborn-v0_8-whitegrid")
        g = sns.FacetGrid(
            df_series, row="Estratégia", hue="Ação",
            aspect=2.0, height=2.5, sharey=False, margin_titles=True
        )
        g.map_dataframe(sns.lineplot, x="Período", y="Vazão Extraída (mil m³/mês)")
        g.set_axis_labels("Período (meses)", "Vazão (mil m³/mês)")
        g.fig.subplots_adjust(top=0.90)
        g.fig.suptitle("Produção de Água por Ação — Timeline de Cada Estratégia", fontsize=16, weight="bold")

        axes = g.axes.flat if hasattr(g, "axes") else [g.ax]
        estrategias = list(df_series["Estratégia"].drop_duplicates())
        for ax, estr in zip(axes, estrategias):
            dados = df_total[df_total["Estratégia"] == estr].sort_values("Período")
            ax.plot(
                dados["Período"], dados["Vazão Total (mil m³/mês)"],
                linestyle="--", linewidth=2.0, color="black", label="Total (soma das ações)"
            )

        g.add_legend(title="Ação")  # cria rótulos das ações
        axes = g.axes.flat if hasattr(g, "axes") else [g.ax]
        first_ax = axes[0]
        handles, labels = first_ax.get_legend_handles_labels()

        # adiciona o "Total (soma das ações)" se ainda não existir
        if "Total (soma das ações)" not in labels:
            handles.append(plt.Line2D([0],[0], linestyle="--", linewidth=2.0, color="black"))
            labels.append("Total (soma das ações)")

        if g._legend is not None:
            g._legend.remove()
        g.fig.legend(
            handles, labels,
            loc="lower center", bbox_to_anchor=(0.5, -0.02),
            ncol=min(5, len(labels)), frameon=True, fontsize=9, title="Legenda"
        )
        g.fig.subplots_adjust(bottom=0.22, top=0.88)
        plt.show()

        # 5) Custo variável efetivo por ação (diagnóstico)
        df_eff = pd.DataFrame(eff_rows)
        df_eff_plot = df_eff.copy()

        plt.style.use("seaborn-v0_8-whitegrid")
        g_eff = sns.FacetGrid(
            df_eff_plot,
            row="Estratégia", col="Fonte", hue="Ação",
            sharey=False, height=2.6, aspect=1.9, margin_titles=True
        )
        g_eff = sns.FacetGrid(
            df_eff_plot, row="Estratégia", col="Fonte", hue="Ação",
            sharey=False, height=2.6, aspect=1.9, margin_titles=True
        )
        g_eff.map_dataframe(sns.lineplot, x="Período", y="VC_efetivo (R$/mil m³)")

        # === legenda consolidada fora ===
        first_ax = g_eff.axes.flat[0] if hasattr(g_eff, "axes") else g_eff.ax
        handles, labels = first_ax.get_legend_handles_labels()
        if g_eff._legend is not None:
            g_eff._legend.remove()
        g_eff.fig.legend(
            handles, labels,
            loc="upper center", bbox_to_anchor=(0.5, 1.02),
            ncol=min(6, len(labels)), frameon=True, title="Ação"
        )

        g_eff.set_axis_labels("Período (meses)", "VC efetivo (R$/mil m³)")
        g_eff.fig.suptitle("Custo Variável Efetivo por Ação (inclui efeito do rebaixamento no GAS)", y=1.06, fontsize=16, weight="bold")
        g_eff.fig.subplots_adjust(top=0.84)
        plt.show()