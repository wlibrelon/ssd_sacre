import streamlit as st
import pandas as pd
import pydeck as pdk
import geopandas as gpd

def show():
    # Sidebar content (if needed)
    with st.sidebar:
        st.header("")
        # Add any sidebar controls here if needed
    
    # Main content
    st.header("Limite da Bacia hidrográfica Bauru")
    
    try:
        # Load point data
        chart_data = pd.read_csv('dados/pps_bauru.csv')
        
        # Load GeoJSON polygon
        gdf = gpd.read_file('dados/Bacia_Bauru.json')

        # Calculate center and zoom for the view
        bounds = gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        # Create combined pydeck chart
        combined_layers = [
            # GeoJSON Layer (polygon)
            pdk.Layer(
                "GeoJsonLayer",
                data=gdf.__geo_interface__,
                opacity=0.5,
                stroked=True,
                filled=False,
                get_line_color=[0, 0, 0, 200],      # Cor do contorno
                get_line_width=3,                   # Espessura da linha (ajuste conforme necessário)
                pickable=True,
                line_width_min_pixels=1             # Garante que a linha fique visível mesmo que o zoom mude
            ),
            # Contour Layer
            pdk.Layer(
                "ContourLayer",
                data=chart_data,
                get_position="[lon, lat]",
                get_weight="value",  # Make sure your CSV has a 'value' column
                contours=[{"threshold": 0.1, "color": [255, 0, 0], "strokeWidth": 1}],
                cell_size=1000,
                elevation_scale=10,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            # Scatterplot Layer (points)
            pdk.Layer(
                "ScatterplotLayer",
                data=chart_data,
                get_position="[lon, lat]",
                get_color="[200, 30, 0, 160]",
                get_radius=30,
                pickable=True,
            )
        ]

        # Set initial view state
        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=10,
            pitch=0,
            bearing=0
        )

        # Create and display the combined deck
        st.pydeck_chart(
            pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=view_state,
                layers=combined_layers,
                tooltip={
                    "html": "<b>Latitude:</b> {lat}<br/><b>Longitude:</b> {lon}",
                    "style": {
                        "backgroundColor": "white",
                        "color": "black"
                    }
                }
            )
        )

        # Show the data in expandable sections
        with st.expander("Tabela de poços"):
            st.dataframe(chart_data)

        # with st.expander("Show GeoJSON Polygon Info"):
        #     st.write(gdf)

    except FileNotFoundError as e:
        st.error(f"Erro na leitura do arquivo de dados: {e}")
    except Exception as e:
        st.error(f"Ocorrência do erro: {e}")

if __name__ == "__main__":
    show()