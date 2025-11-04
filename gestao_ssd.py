import streamlit as st
import pandas as pd
import numpy as np
import datetime
import pydeck as pdk
from streamlit_option_menu import option_menu
from io import StringIO

def show():
    with st.sidebar:
        st.sidebar.title("Gerenciamento SSD")
        uploaded_file = st.file_uploader("Selecione o arquivo para processamento")
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            string_data = stringio.read()
            dataframe = pd.read_csv(uploaded_file)

            meses = st.sidebar.multiselect(
                "Selecione os meses", options=dataframe["Mes"].unique(), default=dataframe["Mes"].unique(),
            )
            anos = st.sidebar.multiselect(
                "Selecione os anos", options=dataframe["Ano"].unique(), default=dataframe["Ano"].unique(),
            )

            df_select = dataframe.query(
                "Mes ==@meses & Ano==@anos"
            )
        btn_map = st.button("Exibir Poços")

        btn_Precip = st.button("Dados de Precipitação")

    if uploaded_file is not None:
        col1, col2 = st.columns([2, 2])

        col1.subheader("Precipitação na bacia do rio Manso", divider="gray")
        col1.dataframe(df_select)
        precip_media = df_select["Precipitacao"].mean()
        precip_max = df_select["Precipitacao"].max()
        precip_min = df_select["Precipitacao"].min()

        col2.subheader("Estatística dos dados", divider="gray")

        col2.subheader(f"Média: {precip_media:.2f}")

        col2.subheader(f"Precipitação Máxima: {precip_max:.2f}")

        col2.subheader(f"Precipitação Mínima: {precip_min:.2f}")

        st.line_chart(df_select, x="Data", y="Precipitacao",x_label="Período", y_label="Precipitação")


    if btn_map:
        # uploaded_file = st.file_uploader("Selecione o arquivo para processamento")
        # if uploaded_file is not None:
        #     bytes_data = uploaded_file.getvalue()
        #     stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        #     string_data = stringio.read()
        #     dataframe = pd.read_csv(uploaded_file)

        # chart_data = pd.DataFrame(
        #     np.random.randn(100, 2) / [50, 50] + [-22.3, -49.07],
        #     columns=["lat", "lon"],
        #      )
        
        chart_data = pd.read_csv('dados/pps_bauru.csv')

        st.pydeck_chart(
            pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(
                    latitude=-22.3,
                    longitude=-49.07,
                    zoom=11,
                    pitch=1,
                ),
                layers=[
                    pdk.Layer(
                        "ContourLayer", # ContourLayer GridLayer HeatmapLayer HexagonLayer ScreenGridLayer
                        data=chart_data,
                        get_position="[lon, lat]",
                        radius=100,
                        elevation_scale=1,
                        elevation_range=[0, 10],
                        pickable=True,
                        extruded=True,
                    ),
                    pdk.Layer(
                        "ScatterplotLayer",  #ArcLayer BitmapLayer ColumnLayer GeoJsonLayer GridCellLayer IconLayer LineLayer PathLayer PointCloudLayer PolygonLayer 
                                            #ScatterplotLayer SolidPolygonLayer TextLayer

                        data=chart_data,
                        get_position="[lon, lat]",
                        get_color="[200, 30, 0, 160]",
                        get_radius=30,
                    ),
                ],
            )
        )
        st.dataframe(chart_data)

        import geopandas as gpd
        gdf = gpd.read_file('dados/Bacia_Bauru.json')

        # Calcula o centro do seu polígono
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        # Estime o zoom ideal (ajuste conforme necessário)
        # Quanto maior a área (diferença max-min), menor o zoom
        extent = max(bounds[2]-bounds[0], bounds[3]-bounds[1])
        # if extent < 1:
        #     zoom = 10
        # elif extent < 5:
        #     zoom = 8
        # elif extent < 10:
        #     zoom = 7
        # elif extent < 50:
        #     zoom = 6
        # else:
        #     zoom = 10

        layer = pdk.Layer(
            "GeoJsonLayer",
            data=gdf.__geo_interface__,
            opacity=0.5,
            stroked=True,
            filled=True,
            get_fill_color=[180, 255, 166, 50],
            get_line_color=[0, 0, 0, 200],
            pickable=True,
        )
        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=10
        )
        deck = pdk.Deck(layers=[layer], initial_view_state=view_state)
        st.pydeck_chart(deck)

        # # Read GeoJSON data into a GeoDataFrame
        # gdf = gpd.read_file('dados/geojs-35-mun.json')
        
        # # Convert the GeoDataFrame to a DataFrame
        # df = pd.DataFrame(gdf)
        # st.dataframe(df)
        # # Create a map with the GeoJSON data
        #st.map(gdf)


    if btn_Precip:
        dataframe = pd.read_csv('dados/Precip_Bacia_Manso_Estacoes.csv')

        estacoes = st.sidebar.multiselect(
            "Selecione as estações", options=dataframe["Estacao"].unique(), default=dataframe["Estacao"].unique(),
        )
        df_select = dataframe.query(
            "Estacao ==@estacoes"
        )
        st.line_chart(df_select, x="Data", y="Precipitacao",x_label="Período", y_label="Precipitação", height=1500)
        # chart = alt.Chart(dfselect).mark_line().encode(
        #     x='Data:T',
        #     y='Precipitacao:Q'
        #     ).properties(
        #         width='container',     # para ocupar toda a largura do container
        #         height=600             # aqui você define a altura desejada
        #     )
        # st.altair_chart(chart, use_container_width=True)

        # st.line_chart(df_select.set_index("Data")["Precipitacao"])
        st.dataframe(df_select, height=300, head=5)

