#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dashboard de monitoreo de noticias sobre juventud en Colombia
Métricas: total noticias, noticias de Bogotá, noticias hoy, última semana
Gráfico principal: noticias por categoría temática (violencia, educación, empleo, etc.)
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from config import CATEGORIAS, EXCEL_PATH, TERMINOS_JUVENTUD

# Configuración de la página
st.set_page_config(
    page_title="Monitor Noticias Juventud",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .bogota-highlight {
        font-size: 1.2rem;
        padding: 0.5rem;
        border-radius: 0.3rem;
    }
    .stDataFrame {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def cargar_datos() -> pd.DataFrame:
    """Carga los datos del Excel."""
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame(columns=[
            "fecha", "titulo", "fuente", "tipo_fuente", "categoria",
            "ciudad", "bogota", "url", "resumen"
        ])

    df = pd.read_excel(EXCEL_PATH)
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

    # Asegurar columnas necesarias
    if 'ciudad' not in df.columns:
        df['ciudad'] = "Sin identificar"
    if 'tipo_fuente' not in df.columns:
        df['tipo_fuente'] = "gratuito"
    if 'categoria' not in df.columns:
        df['categoria'] = "Otra"
    if 'bogota' not in df.columns:
        df['bogota'] = df['ciudad'].apply(lambda c: "Sí" if c == "Bogotá" else "No")

    # Reemplazar NaN en resumen por texto vacío
    df['resumen'] = df['resumen'].fillna('')

    return df


def main():
    # Header
    st.markdown(
        '<p class="main-header">Monitor de noticias - Juventud en Colombia</p>',
        unsafe_allow_html=True
    )

    # Cargar datos
    df = cargar_datos()

    if df.empty:
        st.warning("No hay noticias en la base de datos. Ejecuta primero el scraper: `python scraper.py`")
        return

    # ===== SIDEBAR - FILTROS =====
    st.sidebar.header("Filtros")

    # Filtro por fecha
    st.sidebar.subheader("Fecha")
    fecha_min = df['fecha'].min().date() if not df['fecha'].isna().all() else datetime.now().date()
    fecha_max = df['fecha'].max().date() if not df['fecha'].isna().all() else datetime.now().date()

    rango_fecha = st.sidebar.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    # Filtro por categoría
    st.sidebar.subheader("Categoría")
    categorias_disponibles = sorted(df['categoria'].dropna().unique().tolist())
    categorias_seleccionadas = st.sidebar.multiselect(
        "Seleccionar categorías",
        options=categorias_disponibles,
        default=categorias_disponibles
    )

    # Filtro por tipo de fuente
    st.sidebar.subheader("Tipo de fuente")
    tipos_disponibles = sorted(df['tipo_fuente'].dropna().unique().tolist())
    tipos_seleccionados = st.sidebar.multiselect(
        "Seleccionar tipo",
        options=tipos_disponibles,
        default=tipos_disponibles
    )

    # Filtro Bogotá / resto del país
    st.sidebar.subheader("Ubicación")
    opcion_bogota = st.sidebar.radio(
        "Filtrar por ubicación",
        options=["Todas", "Solo Bogotá", "Solo resto del país"],
        index=0
    )

    # Búsqueda libre
    busqueda_libre = st.sidebar.text_input("Buscar en títulos", "")

    # Aplicar filtros
    df_filtrado = df.copy()

    # Filtro de fecha
    if len(rango_fecha) == 2:
        fecha_inicio, fecha_fin = rango_fecha
        df_filtrado = df_filtrado[
            (df_filtrado['fecha'].dt.date >= fecha_inicio) &
            (df_filtrado['fecha'].dt.date <= fecha_fin)
        ]

    # Filtro de categoría
    if categorias_seleccionadas:
        df_filtrado = df_filtrado[df_filtrado['categoria'].isin(categorias_seleccionadas)]

    # Filtro de tipo de fuente
    if tipos_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['tipo_fuente'].isin(tipos_seleccionados)]

    # Filtro Bogotá
    if opcion_bogota == "Solo Bogotá":
        df_filtrado = df_filtrado[df_filtrado['bogota'] == "Sí"]
    elif opcion_bogota == "Solo resto del país":
        df_filtrado = df_filtrado[df_filtrado['bogota'] != "Sí"]

    # Búsqueda libre
    if busqueda_libre:
        df_filtrado = df_filtrado[
            df_filtrado['titulo'].str.lower().str.contains(busqueda_libre.lower(), na=False)
        ]

    # ===== MÉTRICAS PRINCIPALES =====
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    total_noticias = len(df_filtrado)
    noticias_bogota = len(df_filtrado[df_filtrado['bogota'] == "Sí"])
    noticias_hoy = len(df_filtrado[df_filtrado['fecha'].dt.date == datetime.now().date()])
    noticias_semana = len(df_filtrado[
        df_filtrado['fecha'].dt.date >= (datetime.now() - timedelta(days=7)).date()
    ])

    with col1:
        st.metric("Total noticias", total_noticias)

    with col2:
        pct_bogota = f"({round(noticias_bogota/total_noticias*100)}%)" if total_noticias > 0 else ""
        st.metric("Noticias de Bogotá", f"{noticias_bogota} {pct_bogota}")

    with col3:
        st.metric("Noticias hoy", noticias_hoy)

    with col4:
        st.metric("Última semana", noticias_semana)

    # ===== GRÁFICOS =====
    st.markdown("---")

    # Gráfico principal: noticias por categoría
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Noticias por categoría")
        if not df_filtrado.empty:
            noticias_por_cat = df_filtrado['categoria'].value_counts().reset_index()
            noticias_por_cat.columns = ['Categoría', 'Cantidad']

            # Colores por categoría
            colores_cat = {
                'Violencia': '#e74c3c',
                'Seguridad': '#e67e22',
                'Educación': '#2ecc71',
                'Protección': '#9b59b6',
                'Salud': '#3498db',
                'Empleo': '#1abc9c',
                'Política pública': '#f39c12',
                'Cultura y deporte': '#2980b9',
                'Otra': '#95a5a6',
            }

            fig_cat = px.bar(
                noticias_por_cat,
                x='Cantidad',
                y='Categoría',
                orientation='h',
                color='Categoría',
                color_discrete_map=colores_cat,
            )
            fig_cat.update_layout(
                showlegend=False,
                height=400,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No hay datos para mostrar")

    with col_graf2:
        st.subheader("Noticias por día")
        if not df_filtrado.empty:
            noticias_por_dia = df_filtrado.groupby(
                df_filtrado['fecha'].dt.date
            ).size().reset_index()
            noticias_por_dia.columns = ['Fecha', 'Cantidad']

            fig_dias = px.line(
                noticias_por_dia,
                x='Fecha',
                y='Cantidad',
                markers=True
            )
            fig_dias.update_layout(height=400)
            fig_dias.update_traces(
                line_color='#1f77b4',
                marker_size=8
            )
            st.plotly_chart(fig_dias, use_container_width=True)
        else:
            st.info("No hay datos para mostrar")

    # Segunda fila: categorías Bogotá vs resto
    if not df_filtrado.empty:
        st.markdown("---")
        st.subheader("Categorías: Bogotá vs. resto del país")

        df_bogota_cat = df_filtrado.copy()
        df_bogota_cat['ubicacion'] = df_bogota_cat['bogota'].apply(
            lambda x: 'Bogotá' if x == 'Sí' else 'Resto del país'
        )
        cat_cruce = df_bogota_cat.groupby(['categoria', 'ubicacion']).size().reset_index(name='Cantidad')

        fig_cruce = px.bar(
            cat_cruce,
            x='Cantidad',
            y='categoria',
            color='ubicacion',
            orientation='h',
            barmode='group',
            color_discrete_map={'Bogotá': '#e74c3c', 'Resto del país': '#3498db'},
            labels={'categoria': 'Categoría', 'ubicacion': 'Ubicación'}
        )
        fig_cruce.update_layout(
            height=400,
            yaxis={'categoryorder': 'total ascending'},
            legend_title_text=''
        )
        st.plotly_chart(fig_cruce, use_container_width=True)

    # ===== TABLA DE NOTICIAS =====
    st.markdown("---")
    st.subheader("Listado de noticias")

    if not df_filtrado.empty:
        # Columnas a mostrar
        cols_mostrar = ['fecha', 'titulo', 'fuente', 'tipo_fuente', 'categoria', 'bogota', 'url', 'resumen']
        cols_disponibles = [c for c in cols_mostrar if c in df_filtrado.columns]
        df_display = df_filtrado[cols_disponibles].copy()
        df_display['fecha'] = df_display['fecha'].dt.strftime('%Y-%m-%d')
        df_display = df_display.sort_values('fecha', ascending=False)

        # Hacer URLs clickeables
        df_display['url'] = df_display['url'].apply(
            lambda x: f'<a href="{x}" target="_blank">Ver</a>' if pd.notna(x) else ''
        )

        # Renombrar columnas
        nombres = {
            'fecha': 'Fecha', 'titulo': 'Título', 'fuente': 'Fuente',
            'tipo_fuente': 'Tipo', 'categoria': 'Categoría',
            'bogota': 'Bogotá', 'url': 'Link', 'resumen': 'Resumen'
        }
        df_display = df_display.rename(columns=nombres)

        # Mostrar tabla
        st.markdown(
            df_display.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )

        # Descarga
        st.markdown("---")
        df_download = df_filtrado.copy()
        df_download['fecha'] = df_download['fecha'].dt.strftime('%Y-%m-%d')
        csv = df_download.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"noticias_juventud_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No se encontraron noticias con los filtros aplicados")

    # ===== FOOTER =====
    st.markdown("---")
    st.markdown(
        f"<p style='text-align: center; color: gray;'>"
        f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Total en base de datos: {len(df)} noticias</p>",
        unsafe_allow_html=True
    )

    # Botón para refrescar
    if st.sidebar.button("Actualizar datos"):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()
