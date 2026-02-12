#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dashboard de Monitoreo de Noticias sobre Juventud en Colombia
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from config import EXCEL_PATH, TERMINOS_JUVENTUD

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
    .stDataFrame {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def cargar_datos() -> pd.DataFrame:
    """Carga los datos del Excel."""
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame(columns=["fecha", "titulo", "fuente", "ciudad", "url", "resumen"])

    df = pd.read_excel(EXCEL_PATH)
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    # Asegurar que exista columna ciudad
    if 'ciudad' not in df.columns:
        df['ciudad'] = "Sin identificar"
    return df


def filtrar_por_termino(df: pd.DataFrame, termino: str) -> pd.DataFrame:
    """Filtra noticias que contienen un término específico."""
    if not termino:
        return df

    termino_lower = termino.lower()
    mask = (
        df['titulo'].str.lower().str.contains(termino_lower, na=False) |
        df['resumen'].fillna('').str.lower().str.contains(termino_lower, na=False)
    )
    return df[mask]


def main():
    # Header
    st.markdown('<p class="main-header">📰 Monitor de Noticias - Juventud en Colombia</p>', unsafe_allow_html=True)

    # Cargar datos
    df = cargar_datos()

    if df.empty:
        st.warning("No hay noticias en la base de datos. Ejecuta primero el scraper: `python scraper.py`")
        return

    # ===== SIDEBAR - FILTROS =====
    st.sidebar.header("🔍 Filtros")

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

    # Filtro por ciudad
    st.sidebar.subheader("Ciudad")
    ciudades_disponibles = sorted(df['ciudad'].dropna().unique().tolist())
    ciudades_seleccionadas = st.sidebar.multiselect(
        "Seleccionar ciudades",
        options=ciudades_disponibles,
        default=ciudades_disponibles
    )

    # Filtro por fuente
    st.sidebar.subheader("Fuente")
    fuentes_disponibles = sorted(df['fuente'].unique().tolist())
    fuentes_seleccionadas = st.sidebar.multiselect(
        "Seleccionar fuentes",
        options=fuentes_disponibles,
        default=fuentes_disponibles
    )

    # Filtro por término
    st.sidebar.subheader("Término de búsqueda")
    termino_busqueda = st.sidebar.selectbox(
        "Filtrar por término",
        options=["Todos"] + TERMINOS_JUVENTUD
    )

    # Búsqueda libre
    busqueda_libre = st.sidebar.text_input("🔎 Buscar en títulos", "")

    # Aplicar filtros
    df_filtrado = df.copy()

    # Filtro de fecha
    if len(rango_fecha) == 2:
        fecha_inicio, fecha_fin = rango_fecha
        df_filtrado = df_filtrado[
            (df_filtrado['fecha'].dt.date >= fecha_inicio) &
            (df_filtrado['fecha'].dt.date <= fecha_fin)
        ]

    # Filtro de ciudades
    if ciudades_seleccionadas:
        df_filtrado = df_filtrado[df_filtrado['ciudad'].isin(ciudades_seleccionadas)]

    # Filtro de fuentes
    if fuentes_seleccionadas:
        df_filtrado = df_filtrado[df_filtrado['fuente'].isin(fuentes_seleccionadas)]

    # Filtro por término
    if termino_busqueda != "Todos":
        df_filtrado = filtrar_por_termino(df_filtrado, termino_busqueda)

    # Búsqueda libre
    if busqueda_libre:
        df_filtrado = df_filtrado[
            df_filtrado['titulo'].str.lower().str.contains(busqueda_libre.lower(), na=False)
        ]

    # ===== MÉTRICAS =====
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📊 Total Noticias", len(df_filtrado))

    with col2:
        st.metric("📰 Fuentes Activas", df_filtrado['fuente'].nunique())

    with col3:
        st.metric("🏙️ Ciudades", df_filtrado['ciudad'].nunique())

    with col4:
        noticias_hoy = len(df_filtrado[df_filtrado['fecha'].dt.date == datetime.now().date()])
        st.metric("📅 Noticias Hoy", noticias_hoy)

    with col5:
        noticias_semana = len(df_filtrado[
            df_filtrado['fecha'].dt.date >= (datetime.now() - timedelta(days=7)).date()
        ])
        st.metric("📆 Última Semana", noticias_semana)

    # ===== GRÁFICOS =====
    st.markdown("---")
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("📊 Noticias por Fuente")
        if not df_filtrado.empty:
            noticias_por_fuente = df_filtrado['fuente'].value_counts().reset_index()
            noticias_por_fuente.columns = ['Fuente', 'Cantidad']

            fig_fuentes = px.bar(
                noticias_por_fuente,
                x='Fuente',
                y='Cantidad',
                color='Cantidad',
                color_continuous_scale='Blues'
            )
            fig_fuentes.update_layout(
                showlegend=False,
                xaxis_tickangle=-45,
                height=400
            )
            st.plotly_chart(fig_fuentes, use_container_width=True)
        else:
            st.info("No hay datos para mostrar")

    with col_graf2:
        st.subheader("🏙️ Noticias por Ciudad")
        if not df_filtrado.empty:
            noticias_por_ciudad = df_filtrado['ciudad'].value_counts().reset_index()
            noticias_por_ciudad.columns = ['Ciudad', 'Cantidad']

            fig_ciudades = px.pie(
                noticias_por_ciudad,
                values='Cantidad',
                names='Ciudad',
                hole=0.4
            )
            fig_ciudades.update_layout(height=400)
            st.plotly_chart(fig_ciudades, use_container_width=True)
        else:
            st.info("No hay datos para mostrar")

    # Segunda fila de gráficos
    col_graf3, col_graf4 = st.columns(2)

    with col_graf3:
        st.subheader("📈 Noticias por Día")
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
            fig_dias.update_layout(height=350)
            fig_dias.update_traces(
                line_color='#1f77b4',
                marker_size=8
            )
            st.plotly_chart(fig_dias, use_container_width=True)
        else:
            st.info("No hay datos para mostrar")

    with col_graf4:
        st.subheader("🏷️ Términos más Frecuentes")
        if not df_filtrado.empty:
            conteo_terminos = {}
            for termino in TERMINOS_JUVENTUD:
                conteo = len(filtrar_por_termino(df_filtrado, termino))
                if conteo > 0:
                    conteo_terminos[termino] = conteo

            if conteo_terminos:
                df_terminos = pd.DataFrame({
                    'Término': list(conteo_terminos.keys()),
                    'Menciones': list(conteo_terminos.values())
                }).sort_values('Menciones', ascending=True).tail(10)

                fig_terminos = px.bar(
                    df_terminos,
                    x='Menciones',
                    y='Término',
                    orientation='h',
                    color='Menciones',
                    color_continuous_scale='Viridis'
                )
                fig_terminos.update_layout(
                    showlegend=False,
                    height=350
                )
                st.plotly_chart(fig_terminos, use_container_width=True)

    # ===== TABLA DE NOTICIAS =====
    st.markdown("---")
    st.subheader("📋 Listado de Noticias")

    if not df_filtrado.empty:
        # Preparar tabla para mostrar
        df_display = df_filtrado[['fecha', 'titulo', 'fuente', 'ciudad', 'url', 'resumen']].copy()
        df_display['fecha'] = df_display['fecha'].dt.strftime('%Y-%m-%d')
        df_display = df_display.sort_values('fecha', ascending=False)

        # Hacer URLs clickeables
        df_display['url'] = df_display['url'].apply(
            lambda x: f'<a href="{x}" target="_blank">Ver</a>' if pd.notna(x) else ''
        )

        # Renombrar columnas para mostrar
        df_display.columns = ['Fecha', 'Título', 'Fuente', 'Ciudad', 'Link', 'Resumen']

        # Mostrar tabla con HTML
        st.markdown(
            df_display.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )

        # Opción de descarga
        st.markdown("---")
        col_desc1, col_desc2 = st.columns([1, 4])
        with col_desc1:
            # Preparar CSV para descarga
            df_download = df_filtrado.copy()
            df_download['fecha'] = df_download['fecha'].dt.strftime('%Y-%m-%d')
            csv = df_download.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV",
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

    # Botón para refrescar datos
    if st.sidebar.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()
