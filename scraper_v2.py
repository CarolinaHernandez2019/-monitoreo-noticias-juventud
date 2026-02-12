#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper de noticias sobre juventud en Colombia
Monitorea múltiples fuentes de noticias colombianas
"""

import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import CIUDADES_COLOMBIA, EXCEL_PATH, FUENTES, HEADERS, TERMINOS_JUVENTUD


def contiene_terminos_juventud(texto: str) -> bool:
    """Verifica si el texto contiene alguno de los términos de juventud."""
    if not texto:
        return False
    texto_lower = texto.lower()
    return any(termino.lower() in texto_lower for termino in TERMINOS_JUVENTUD)


def detectar_ciudad(texto: str) -> str:
    """Detecta la ciudad mencionada en el texto."""
    if not texto:
        return "Sin identificar"
    texto_lower = texto.lower()

    # Buscar ciudades en orden de especificidad (más específicas primero)
    for ciudad_key, ciudad_nombre in CIUDADES_COLOMBIA.items():
        if ciudad_key in texto_lower:
            if ciudad_nombre != "Colombia":  # Retornar ciudad específica primero
                return ciudad_nombre

    # Si solo encontró "colombia" o nada específico
    if "colombia" in texto_lower:
        return "Colombia"

    return "Sin identificar"


def limpiar_texto(texto: str) -> str:
    """Limpia y normaliza el texto."""
    if not texto:
        return ""
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


def obtener_resumen(texto: str, max_chars: int = 250) -> str:
    """Extrae los primeros caracteres del texto como resumen."""
    texto = limpiar_texto(texto)
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars].rsplit(' ', 1)[0] + "..."


def obtener_tipo_fuente(nombre_fuente: str) -> str:
    """Obtiene el tipo de fuente (gratuito/diario pago) desde la configuración."""
    if nombre_fuente in FUENTES:
        return FUENTES[nombre_fuente].get("tipo", "gratuito")
    return "gratuito"


def cargar_excel_existente() -> pd.DataFrame:
    """Carga el Excel existente o crea uno nuevo."""
    columnas = ["fecha", "titulo", "fuente", "tipo_fuente", "ciudad", "url", "resumen"]

    if os.path.exists(EXCEL_PATH):
        try:
            df = pd.read_excel(EXCEL_PATH)
            # Agregar columna ciudad si no existe
            if 'ciudad' not in df.columns:
                df['ciudad'] = "Sin identificar"
            # Agregar columna tipo_fuente si no existe
            if 'tipo_fuente' not in df.columns:
                df['tipo_fuente'] = df['fuente'].apply(obtener_tipo_fuente)
            print(f"  Cargadas {len(df)} noticias existentes")
            return df
        except Exception as e:
            print(f"  Error al cargar Excel: {e}")

    return pd.DataFrame(columns=columnas)


def guardar_excel(df: pd.DataFrame):
    """Guarda el DataFrame en Excel."""
    os.makedirs(os.path.dirname(EXCEL_PATH), exist_ok=True)
    # Asegurar orden de columnas
    columnas = ["fecha", "titulo", "fuente", "tipo_fuente", "ciudad", "url", "resumen"]
    df = df[columnas]
    df.to_excel(EXCEL_PATH, index=False)
    print(f"\nGuardadas {len(df)} noticias en {EXCEL_PATH}")


def hacer_request(url: str, timeout: int = 15) -> requests.Response | None:
    """Realiza una petición HTTP con manejo de errores."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"    Error en request a {url}: {e}")
        return None


# ============== SCRAPERS POR FUENTE ==============

def scrape_bluradio() -> list[dict]:
    """Scraper para Blu Radio - sección nacional."""
    noticias = []
    url = "https://www.bluradio.com/nacion"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'card|article|item'))

    for art in articulos[:50]:
        try:
            link_tag = art.find('a', href=True)
            if not link_tag:
                continue

            href = link_tag.get('href', '')
            if not href.startswith('http'):
                href = urljoin("https://www.bluradio.com", href)

            titulo_tag = art.find(['h2', 'h3', 'h4']) or link_tag
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''

            resumen_tag = art.find('p')
            resumen = resumen_tag.get_text(strip=True) if resumen_tag else ''

            # FILTRO ESTRICTO: debe contener términos de juventud
            if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                texto_completo = f"{titulo} {resumen}"
                noticias.append({
                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'Blu Radio',
                    'tipo_fuente': obtener_tipo_fuente('Blu Radio'),
                    'ciudad': detectar_ciudad(texto_completo),
                    'url': href,
                    'resumen': obtener_resumen(resumen) if resumen else ''
                })
        except Exception:
            continue

    return noticias


def scrape_caracol() -> list[dict]:
    """Scraper para Noticias Caracol - sección Colombia."""
    noticias = []
    url = "https://www.noticiascaracol.com/colombia"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'card|article|news-item'))

    for art in articulos[:50]:
        try:
            link_tag = art.find('a', href=True)
            if not link_tag:
                continue

            href = link_tag.get('href', '')
            if not href.startswith('http'):
                href = urljoin("https://www.noticiascaracol.com", href)

            titulo_tag = art.find(['h2', 'h3', 'h4', 'span', 'div'], class_=re.compile(r'title|headline'))
            if not titulo_tag:
                titulo_tag = art.find(['h2', 'h3', 'h4']) or link_tag
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''

            resumen_tag = art.find('p')
            resumen = resumen_tag.get_text(strip=True) if resumen_tag else ''

            # FILTRO ESTRICTO
            if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                texto_completo = f"{titulo} {resumen}"
                noticias.append({
                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'Noticias Caracol',
                    'tipo_fuente': obtener_tipo_fuente('Noticias Caracol'),
                    'ciudad': detectar_ciudad(texto_completo),
                    'url': href,
                    'resumen': obtener_resumen(resumen) if resumen else ''
                })
        except Exception:
            continue

    return noticias


def scrape_pulzo() -> list[dict]:
    """Scraper para Pulzo - sección nación."""
    noticias = []
    url = "https://www.pulzo.com/nacion"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'article|card|item'))

    for art in articulos[:50]:
        try:
            link_tag = art.find('a', href=True)
            if not link_tag:
                continue

            href = link_tag.get('href', '')
            if not href.startswith('http'):
                href = urljoin("https://www.pulzo.com", href)

            titulo_tag = art.find(['h2', 'h3', 'h4']) or link_tag
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''

            resumen_tag = art.find('p')
            resumen = resumen_tag.get_text(strip=True) if resumen_tag else ''

            # FILTRO ESTRICTO
            if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                texto_completo = f"{titulo} {resumen}"
                noticias.append({
                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'Pulzo',
                    'tipo_fuente': obtener_tipo_fuente('Pulzo'),
                    'ciudad': detectar_ciudad(texto_completo),
                    'url': href,
                    'resumen': obtener_resumen(resumen) if resumen else ''
                })
        except Exception:
            continue

    return noticias


def scrape_infobae() -> list[dict]:
    """Scraper para Infobae Colombia."""
    noticias = []
    url = "https://www.infobae.com/colombia/"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('a', class_=re.compile(r'feed-list-card|story-card'))
    if not articulos:
        articulos = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'card|article'))

    for art in articulos[:50]:
        try:
            if art.name == 'a':
                href = art.get('href', '')
                titulo_tag = art.find(['h2', 'h3', 'h4', 'span'])
                resumen_tag = art.find('p')
            else:
                link_tag = art.find('a', href=True)
                if not link_tag:
                    continue
                href = link_tag.get('href', '')
                titulo_tag = art.find(['h2', 'h3', 'h4']) or link_tag
                resumen_tag = art.find('p')

            if not href.startswith('http'):
                href = urljoin("https://www.infobae.com", href)

            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''
            resumen = resumen_tag.get_text(strip=True) if resumen_tag else ''

            # FILTRO ESTRICTO
            if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                texto_completo = f"{titulo} {resumen}"
                noticias.append({
                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'Infobae',
                    'tipo_fuente': obtener_tipo_fuente('Infobae'),
                    'ciudad': detectar_ciudad(texto_completo),
                    'url': href,
                    'resumen': obtener_resumen(resumen) if resumen else ''
                })
        except Exception:
            continue

    return noticias


def scrape_alertabogota() -> list[dict]:
    """Scraper para Alerta Bogotá."""
    noticias = []
    url = "https://www.alertabogota.com/"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'post|article|entry'))

    for art in articulos[:50]:
        try:
            link_tag = art.find('a', href=True)
            if not link_tag:
                continue

            href = link_tag.get('href', '')
            if not href.startswith('http'):
                href = urljoin("https://www.alertabogota.com", href)

            titulo_tag = art.find(['h2', 'h3', 'h4']) or link_tag
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''

            resumen_tag = art.find('p')
            resumen = resumen_tag.get_text(strip=True) if resumen_tag else ''

            # FILTRO ESTRICTO
            if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                texto_completo = f"{titulo} {resumen}"
                # Para Alerta Bogotá, default es Bogotá
                ciudad = detectar_ciudad(texto_completo)
                if ciudad == "Sin identificar":
                    ciudad = "Bogotá"
                noticias.append({
                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'Alerta Bogotá',
                    'tipo_fuente': obtener_tipo_fuente('Alerta Bogotá'),
                    'ciudad': ciudad,
                    'url': href,
                    'resumen': obtener_resumen(resumen) if resumen else ''
                })
        except Exception:
            continue

    return noticias


def scrape_redmas() -> list[dict]:
    """Scraper para Red+."""
    noticias = []
    url = "https://redmas.com.co/"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'card|article|post'))

    for art in articulos[:50]:
        try:
            link_tag = art.find('a', href=True)
            if not link_tag:
                continue

            href = link_tag.get('href', '')
            if not href.startswith('http'):
                href = urljoin("https://redmas.com.co", href)

            titulo_tag = art.find(['h2', 'h3', 'h4']) or link_tag
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''

            resumen_tag = art.find('p')
            resumen = resumen_tag.get_text(strip=True) if resumen_tag else ''

            # FILTRO ESTRICTO
            if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                texto_completo = f"{titulo} {resumen}"
                noticias.append({
                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'Red+',
                    'tipo_fuente': obtener_tipo_fuente('Red+'),
                    'ciudad': detectar_ciudad(texto_completo),
                    'url': href,
                    'resumen': obtener_resumen(resumen) if resumen else ''
                })
        except Exception:
            continue

    return noticias


def scrape_diarioadn() -> list[dict]:
    """Scraper para Diario ADN."""
    noticias = []
    url = "https://www.diarioadn.co/"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'card|article|post'))

    for art in articulos[:50]:
        try:
            link_tag = art.find('a', href=True)
            if not link_tag:
                continue

            href = link_tag.get('href', '')
            if not href.startswith('http'):
                href = urljoin("https://www.diarioadn.co", href)

            titulo_tag = art.find(['h2', 'h3', 'h4']) or link_tag
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''

            resumen_tag = art.find('p')
            resumen = resumen_tag.get_text(strip=True) if resumen_tag else ''

            # FILTRO ESTRICTO
            if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                texto_completo = f"{titulo} {resumen}"
                noticias.append({
                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'Diario ADN',
                    'tipo_fuente': obtener_tipo_fuente('Diario ADN'),
                    'ciudad': detectar_ciudad(texto_completo),
                    'url': href,
                    'resumen': obtener_resumen(resumen) if resumen else ''
                })
        except Exception:
            continue

    return noticias


def scrape_eltiempo() -> list[dict]:
    """Scraper para El Tiempo (diario pago) - sección Colombia.
    Extrae títulos y resúmenes visibles en la página de sección,
    sin entrar al contenido completo detrás del paywall.
    """
    noticias = []
    url = "https://www.eltiempo.com/colombia"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')

    # El Tiempo usa <article> con clases c-articulo--basico, c-articulo--detallado, etc.
    articulos = soup.find_all('article', class_=re.compile(r'c-articulo'))

    for art in articulos[:50]:
        try:
            # El título está en <h3 class="c-articulo__titulo"> > <a class="c-articulo__titulo__txt">
            titulo_tag = art.find('a', class_='c-articulo__titulo__txt')
            if not titulo_tag:
                titulo_tag = art.find(['h2', 'h3', 'h4'])
            if not titulo_tag:
                continue

            titulo = titulo_tag.get_text(strip=True)
            href = titulo_tag.get('href', '')
            if not href:
                link_tag = art.find('a', href=True)
                href = link_tag.get('href', '') if link_tag else ''
            if not href:
                continue
            if not href.startswith('http'):
                href = urljoin("https://www.eltiempo.com", href)

            # El resumen está en <p class="c-articulo__resumen"> o dentro de un <a class="c-articulo__resumen-link">
            resumen_tag = art.find('p', class_='c-articulo__resumen')
            if resumen_tag:
                resumen_link = resumen_tag.find('a', class_='c-articulo__resumen-link')
                resumen = resumen_link.get_text(strip=True) if resumen_link else resumen_tag.get_text(strip=True)
            else:
                resumen = ''

            # FILTRO ESTRICTO: debe contener términos de juventud
            if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                texto_completo = f"{titulo} {resumen}"
                noticias.append({
                    'fecha': datetime.now().strftime('%Y-%m-%d'),
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'El Tiempo',
                    'tipo_fuente': obtener_tipo_fuente('El Tiempo'),
                    'ciudad': detectar_ciudad(texto_completo),
                    'url': href,
                    'resumen': obtener_resumen(resumen) if resumen else ''
                })
        except Exception:
            continue

    return noticias


def scrape_elespectador() -> list[dict]:
    """Scraper para El Espectador (diario pago) - sección Colombia.
    Usa el JSON de Fusion.globalContent embebido en la página,
    que contiene todos los artículos con título y descripción completos.
    """
    import json as json_mod

    noticias = []
    url = "https://www.elespectador.com/colombia/"

    response = hacer_request(url)
    if not response:
        return noticias

    # Intentar extraer datos del JSON de Fusion (más confiable que parsear HTML)
    texto_pagina = response.text
    match = re.search(r'Fusion\.globalContent\s*=\s*(\{.*?\});\s*Fusion\.', texto_pagina, re.DOTALL)

    if match:
        try:
            datos_json = json_mod.loads(match.group(1))
            # Los artículos están en content_elements
            elementos = datos_json.get('content_elements', [])

            for elem in elementos[:50]:
                try:
                    titulo = elem.get('headlines', {}).get('basic', '')
                    resumen = elem.get('description', {}).get('basic', '')
                    url_relativa = elem.get('canonical_url', '')

                    if not titulo or not url_relativa:
                        continue

                    href = urljoin("https://www.elespectador.com", url_relativa)

                    # FILTRO ESTRICTO
                    if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                        texto_completo = f"{titulo} {resumen}"
                        noticias.append({
                            'fecha': datetime.now().strftime('%Y-%m-%d'),
                            'titulo': limpiar_texto(titulo),
                            'fuente': 'El Espectador',
                            'tipo_fuente': obtener_tipo_fuente('El Espectador'),
                            'ciudad': detectar_ciudad(texto_completo),
                            'url': href,
                            'resumen': obtener_resumen(resumen) if resumen else ''
                        })
                except Exception:
                    continue
        except json_mod.JSONDecodeError:
            pass

    # Si no se encontró el JSON, se usa HTML como respaldo
    if not noticias:
        soup = BeautifulSoup(texto_pagina, 'lxml')
        # El Espectador usa <div class="Card Card-HomeEE"> y <h2 class="Card-Title">
        cards = soup.find_all('div', class_=re.compile(r'Card-HomeEE'))

        for card in cards[:50]:
            try:
                titulo_tag = card.find('h2', class_=re.compile(r'Card-Title'))
                if not titulo_tag:
                    continue

                link_tag = titulo_tag.find('a', href=True)
                if not link_tag:
                    continue

                titulo = link_tag.get_text(strip=True)
                href = link_tag.get('href', '')
                if not href.startswith('http'):
                    href = urljoin("https://www.elespectador.com", href)

                # El resumen solo aparece en la card principal (Card-Hook)
                hook_tag = card.find('div', class_=re.compile(r'Card-Hook'))
                resumen = ''
                if hook_tag:
                    hook_link = hook_tag.find('a')
                    resumen = hook_link.get_text(strip=True) if hook_link else hook_tag.get_text(strip=True)

                # FILTRO ESTRICTO
                if contiene_terminos_juventud(titulo) or contiene_terminos_juventud(resumen):
                    texto_completo = f"{titulo} {resumen}"
                    noticias.append({
                        'fecha': datetime.now().strftime('%Y-%m-%d'),
                        'titulo': limpiar_texto(titulo),
                        'fuente': 'El Espectador',
                        'tipo_fuente': obtener_tipo_fuente('El Espectador'),
                        'ciudad': detectar_ciudad(texto_completo),
                        'url': href,
                        'resumen': obtener_resumen(resumen) if resumen else ''
                    })
            except Exception:
                continue

    return noticias


def ejecutar_scraping() -> pd.DataFrame:
    """Ejecuta el scraping de todas las fuentes."""
    print("=" * 60)
    print("MONITOREO DE NOTICIAS - JUVENTUD EN COLOMBIA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Cargar noticias existentes
    print("\n[1] Cargando noticias existentes...")
    df_existente = cargar_excel_existente()
    urls_existentes = set(df_existente['url'].tolist()) if not df_existente.empty else set()

    # Lista para nuevas noticias
    nuevas_noticias = []

    # Ejecutar todos los scrapers (incluye diarios pagos: El Tiempo y El Espectador)
    scrapers = [
        ("Blu Radio", scrape_bluradio),
        ("Noticias Caracol", scrape_caracol),
        ("Alerta Bogotá", scrape_alertabogota),
        ("Red+", scrape_redmas),
        ("Pulzo", scrape_pulzo),
        ("Infobae", scrape_infobae),
        ("Diario ADN", scrape_diarioadn),
        ("El Tiempo", scrape_eltiempo),
        ("El Espectador", scrape_elespectador),
    ]

    print("\n[2] Ejecutando scrapers (filtro: términos de juventud)...")
    for nombre, scraper_func in scrapers:
        print(f"\n  Scrapeando {nombre}...")
        try:
            noticias = scraper_func()
            nuevas_count = 0
            for noticia in noticias:
                if noticia['url'] not in urls_existentes:
                    nuevas_noticias.append(noticia)
                    urls_existentes.add(noticia['url'])
                    nuevas_count += 1
            print(f"    Encontradas: {len(noticias)} | Nuevas: {nuevas_count}")
        except Exception as e:
            print(f"    Error: {e}")

        time.sleep(1)

    # Combinar con existentes
    print(f"\n[3] Procesando resultados...")
    print(f"    Noticias nuevas encontradas: {len(nuevas_noticias)}")

    if nuevas_noticias:
        df_nuevas = pd.DataFrame(nuevas_noticias)
        df_final = pd.concat([df_existente, df_nuevas], ignore_index=True)
    else:
        df_final = df_existente

    # Eliminar duplicados por URL
    df_final = df_final.drop_duplicates(subset=['url'], keep='first')

    # Ordenar por fecha descendente
    df_final = df_final.sort_values('fecha', ascending=False)

    # Guardar
    print("\n[4] Guardando Excel...")
    guardar_excel(df_final)

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total noticias en base: {len(df_final)}")
    print(f"Noticias nuevas agregadas: {len(nuevas_noticias)}")
    print(f"Archivo: {EXCEL_PATH}")

    # Mostrar distribución por ciudad
    if not df_final.empty:
        print("\nDistribución por ciudad:")
        for ciudad, count in df_final['ciudad'].value_counts().head(10).items():
            print(f"  {ciudad}: {count}")

    print("=" * 60)

    return df_final


if __name__ == "__main__":
    ejecutar_scraping()
