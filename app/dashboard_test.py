import streamlit as st
import pandas as pd
import plotly.express as px
from funcoes_app import conectar_banco
from pyproj import Transformer
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Função para carregar dados com cache
@st.cache_data(ttl=600)
def carregar_dados(query):
    conexao = conectar_banco()
    try:
        df = pd.read_sql_query(query, conexao)
        return df
    finally:
        conexao.close()

# Função para obter query de relacionamento
def obter_relacionamento_dados():
    query = """
    SELECT 
        rq.id_resultado,
        rq.tipo_resultado,
        rq.nome_amostra,
        rq.data AS data_resultado,
        rq.parametro,
        rq.simbolo,
        rq.unidade,
        rq.resultado,
        rq.erro,
        rq.lab,
        rq.obs,
        rq.profund_inicial_solo,
        rq.profund_final_solo,
        pm.cod_ponto,
        pm.latitude,
        pm.longitude,
        cm.cod_Campanha,
        cm.tipo_Campanha
    FROM 
        resultados_quim AS rq
    LEFT JOIN 
        pontos_monitorados AS pm ON rq.id_ponto = pm.id_ponto
    LEFT JOIN 
        Campanhas AS cm ON rq.id_campanha = cm.id_campanha
    """
    return query

# Função para converter UTM 23S para lat/long (EPSG:4326)
# def converter_utm_para_latlong(df, x_col='coord_x', y_col='coord_y'):
#     transformer = Transformer.from_crs("epsg:32723", "epsg:4326")  # UTM 23S para WGS84
#     df = df.copy()
#     valid_mask = (df[x_col].notna()) & (df[y_col].notna()) & (df[x_col] > 0) & (df[y_col] > 0)
#     if valid_mask.any():
#         lat, lon = transformer.transform(df.loc[valid_mask, y_col], df.loc[valid_mask, x_col])  # Ordem: y (Northing), x (Easting)
#         df.loc[valid_mask, 'latitude'] = lat
#         df.loc[valid_mask, 'longitude'] = lon
#     return df

# Configuração da página
st.set_page_config(page_title="Dashboard de Resultados Químicos", layout="wide")

# Carregar dados
query = obter_relacionamento_dados()
dados = carregar_dados(query)

# Filtros no sidebar
tipo_result = st.sidebar.multiselect(
    "Tipo de Resultado",
    options=dados["tipo_resultado"].unique(),
    default=dados["tipo_resultado"].unique()
)

cod_ponto = st.sidebar.multiselect(
    "Código do Ponto",
    options=dados["cod_ponto"].unique(),
    default=dados["cod_ponto"].unique()
)

# Filtrar dados
df_filter = dados[
    (dados["tipo_resultado"].isin(tipo_result)) &
    (dados["cod_ponto"].isin(cod_ponto))
]

# Converter UTM para lat/long
# df_filter = converter_utm_para_latlong(df_filter)

# Verificar se há dados filtrados
if df_filter.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
else:
    # Exibir dados filtrados
    st.dataframe(df_filter)

    # Gráficos
    graf = px.bar(df_filter, x="tipo_resultado", color="cod_ponto", y="resultado",
                  title="Resultados por Tipo e Ponto", labels={"resultado": "Resultado"})
    graf_pt_monit = px.bar(df_filter, x="cod_ponto", color="tipo_resultado", y="resultado",
                           title="Resultados por Ponto de Monitoramento", labels={"resultado": "Resultado"})

    # Tabs para Mapa e Gráficos
    tab1, tab2, tab3 = st.tabs(["Mapa", "Gráficos", "teste"])

    with tab1:
        df_points = df_filter.drop_duplicates(subset=['cod_ponto'])

        # Remover rows com nulls em latitude/longitude
        df_map = df_points.dropna(subset=['latitude', 'longitude'])

        # Depuração: Mostrar número de pontos válidos e amostra
        st.write(f"Número de pontos únicos válidos para plotar: {len(df_map)}")

        # Carregar shapefile e calcular default_center do centro do polígono
        shapefile_path = "D:/SACRE/SSD/mapas/Base da área de estudo/area de estudo-4326.shp"
        default_center = [-23.55, -46.63]  # Fallback em SP
        bounds = None
        gdf = None
        try:
            gdf = gpd.read_file(shapefile_path)
            gdf = gdf.to_crs("EPSG:4326")
            
            # Calcular centro do polígono (média dos centroids)
            centroids = gdf.geometry.centroid
            center_lat = centroids.y.mean()
            center_lon = centroids.x.mean()
            default_center = [center_lat, center_lon]
            
            # Calcular bounds do shapefile
            bounds = gdf.total_bounds  # [min_lon, min_lat, max_lon, max_lat]
            
            st.write(f"Centro calculado do shapefile: lat={center_lat:.4f}, lon={center_lon:.4f}")
        except Exception as e:
            st.warning(f"Erro ao carregar shapefile ou calcular centro: {e}. Usando fallback em SP.")

        # Criar mapa folium com default_center calculado
        m = folium.Map(location=default_center, zoom_start=20)
        # political_countries_url = ("d:/SACRE/SSD/mapas/Base da área de estudo/Area_Estudo.geojsonl.json")
        # m = folium.Map(location=default_center, zoom_start=20, tiles="cartodb positron")
        # folium.GeoJson(political_countries_url).add_to(m)

        # Adicionar polígono do shapefile (se carregado)
        if gdf is not None:
            folium.GeoJson(
                gdf,
                style_function=lambda feature: {
                    'fillColor': 'blue',
                    'color': 'darkblue',
                    'weight': 0.4,
                    'fillOpacity': 0.2
                }
            ).add_to(m)

        # Adicionar pontos como marcadores e expandir bounds
        if not df_map.empty:
            for _, row in df_map.iterrows():
                popup_text = f"Cod Ponto: {row['cod_ponto']}<br>Tipo Resultado: {row.get('tipo_resultado', 'N/A')}"
                folium.Marker(
                    location=[row['longitude'], row['latitude']],
                    popup=popup_text,
                    tooltip=row['cod_ponto'],
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
            
            # Expandir bounds para incluir pontos
            points_bounds = [df_map['longitude'].min(), df_map['latitude'].min(), df_map['longitude'].max(), df_map['latitude'].max()]
            if bounds is None:
                bounds = points_bounds
            else:
                bounds = [
                    min(bounds[0], points_bounds[0]), min(bounds[1], points_bounds[1]),
                    max(bounds[2], points_bounds[2]), max(bounds[3], points_bounds[3])
                ]

        # Se houver bounds, ajustar o mapa para fit (foco automático na área)
        if bounds is not None:
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])  # Ordem: [[min_lat, min_lon], [max_lat, max_lon]]

        # Renderizar o mapa único no Streamlit
        st_folium(m, width=2000, height=800, returned_objects=[])

    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(graf)
        with col2:
            st.plotly_chart(graf_pt_monit)
    
    with tab3:
        df = pd.DataFrame(
            [
                {"command": "st.selectbox", "rating": 4, "is_widget": True},
                {"command": "st.balloons", "rating": 5, "is_widget": False},
                {"command": "st.time_input", "rating": 3, "is_widget": True},
            ]
        )
        edited_df = st.data_editor(df)

        favorite_command = edited_df.loc[edited_df["rating"].idxmax()]["command"]
        st.markdown(f"Your favorite command is **{favorite_command}** 🎈")
