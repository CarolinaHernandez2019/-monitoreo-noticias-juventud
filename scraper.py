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

import json

from config import (CATEGORIAS, CIUDADES_COLOMBIA, CONTEXTO_JUVENTUD, CSV_PATH,
                    EXCEL_PATH, FUENTES, HEADERS, PAISES_EXCLUIDOS,
                    PAISES_EXCLUIDOS_EXACTOS, PATRONES_EXCLUSION,
                    TERMINOS_AMBIGUOS, TERMINOS_JUVENTUD)


def contiene_terminos_juventud(texto: str) -> bool:
    """Verifica si el texto contiene alguno de los términos de juventud."""
    if not texto:
        return False
    texto_lower = texto.lower()
    url_lower = url.lower()
    return any(termino.lower() in texto_lower for termino in TERMINOS_JUVENTUD)


def contiene_terminos_ambiguos(texto: str) -> bool:
    """Detecta términos amplios que requieren contexto adicional."""
    if not texto:
        return False
    texto_lower = texto.lower()
    return any(termino in texto_lower for termino in TERMINOS_AMBIGUOS)


def tiene_contexto_juventud(texto: str) -> bool:
    """Confirma contexto de juventud cuando el término principal es ambiguo."""
    if not texto:
        return False
    texto_lower = texto.lower()
    return any(contexto in texto_lower for contexto in CONTEXTO_JUVENTUD)


def es_falso_positivo(texto: str, fuente: str = "", url: str = "") -> bool:
    """Descarta coincidencias por contexto deportivo u otros usos no relevantes."""
    texto_lower = (texto or "").lower()
    url_lower = (url or "").lower()
    fuente_lower = (fuente or "").lower()

    contexto = f"{texto_lower} {url_lower} {fuente_lower}"

    if not any(termino in contexto for termino in ("juventud", "juvenil", "estudiantes")):
        return False

    return any(patron in contexto for patron in PATRONES_EXCLUSION)


def es_relevante_para_monitoreo(titulo: str, resumen: str = "", fuente: str = "", url: str = "") -> bool:
    """Aplica un filtro de relevancia con prioridad en precisión."""
    texto = limpiar_texto(f"{titulo} {resumen}")
    if not texto:
        return False

    if es_falso_positivo(texto, fuente, url):
        return False

    if contiene_terminos_juventud(texto):
        return True

    if contiene_terminos_ambiguos(texto):
        return tiene_contexto_juventud(texto)

    return False


def filtrar_dataframe_relevante(df: pd.DataFrame) -> pd.DataFrame:
    """Depura noticias históricas que ya no pasan filtros de relevancia y geografía."""
    if df.empty:
        return df

    mask = df.apply(
        lambda row: (
            es_relevante_para_monitoreo(
                str(row.get("titulo", "")),
                str(row.get("resumen", "")),
                str(row.get("fuente", "")),
                str(row.get("url", "")),
            )
            and es_noticia_colombia(
                f"{row.get('titulo', '')} {row.get('resumen', '')}",
                str(row.get("url", "")),
            )
        ),
        axis=1,
    )
    return df[mask].copy()


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


def contiene_frase(texto: str, termino: str) -> bool:
    """Busca coincidencias por frase completa para evitar falsos positivos."""
    if not texto or not termino:
        return False
    patron = rf'(?<!\w){re.escape(termino.lower())}(?!\w)'
    return re.search(patron, texto.lower()) is not None


def obtener_resumen(texto: str, max_chars: int = 250) -> str:
    """Extrae los primeros caracteres del texto como resumen."""
    texto = limpiar_texto(texto)
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars].rsplit(' ', 1)[0] + "..."


def es_noticia_colombia(texto: str, url: str = "") -> bool:
    """Verifica que la noticia sea de Colombia y no internacional.
    Prioriza notas con foco local y descarta referencias internacionales.
    """
    if not texto:
        return False
    texto_lower = texto.lower()
    url_lower = url.lower()

    # Verificar si menciona algún país/ciudad excluida (subcadena para capturar gentilicios)
    menciona_extranjero = (
        any(pais in texto_lower for pais in PAISES_EXCLUIDOS)
        or any(contiene_frase(texto_lower, pais) for pais in PAISES_EXCLUIDOS_EXACTOS)
    )

    # Señales de foco colombiano
    ciudades_colombianas_especificas = [
        ciudad for ciudad, nombre in CIUDADES_COLOMBIA.items() if nombre != "Colombia"
    ]
    menciona_ciudad_colombiana = any(ciudad in texto_lower for ciudad in ciudades_colombianas_especificas)
    menciona_colombia = "colombia" in texto_lower
    es_fuente_institucional = any(
        dominio in url_lower for dominio in (".gov.co", ".edu.co", ".org.co")
    )

    # Una referencia extranjera descarta la noticia, aunque se publique
    # en un medio colombiano o también mencione una ciudad del país.
    if menciona_extranjero:
        return False

    # Las fuentes institucionales colombianas tienen contexto nacional por
    # definición; las fuentes comerciales necesitan una señal territorial.
    return (
        menciona_ciudad_colombiana
        or menciona_colombia
        or es_fuente_institucional
    )


def clasificar_categoria(texto: str) -> str:
    """Clasifica la noticia en una categoría temática según palabras clave.
    Se asigna la primera categoría cuyas palabras aparezcan en el texto.
    """
    if not texto:
        return "Otra"
    texto_lower = texto.lower()

    for categoria, palabras in CATEGORIAS.items():
        if any(palabra in texto_lower for palabra in palabras):
            return categoria

    return "Otra"


def obtener_tipo_fuente(nombre_fuente: str) -> str:
    """Obtiene el tipo de fuente (gratuito/diario pago) desde la configuración."""
    if nombre_fuente in FUENTES:
        return FUENTES[nombre_fuente].get("tipo", "gratuito")
    return "gratuito"


def cargar_excel_existente() -> pd.DataFrame:
    """Carga el Excel existente o crea uno nuevo."""
    columnas = ["fecha", "titulo", "fuente", "tipo_fuente", "categoria", "ciudad", "bogota", "url", "resumen"]

    if os.path.exists(EXCEL_PATH):
        try:
            df = pd.read_excel(EXCEL_PATH)
            # Agregar columna ciudad si no existe
            if 'ciudad' not in df.columns:
                df['ciudad'] = "Sin identificar"
            # Agregar columna tipo_fuente si no existe
            if 'tipo_fuente' not in df.columns:
                df['tipo_fuente'] = df['fuente'].apply(obtener_tipo_fuente)
            # Agregar columna categoria si no existe
            if 'categoria' not in df.columns:
                df['categoria'] = df.apply(
                    lambda r: clasificar_categoria(f"{r.get('titulo', '')} {r.get('resumen', '')}"), axis=1)
            # Agregar columna bogota si no existe
            if 'bogota' not in df.columns:
                df['bogota'] = df['ciudad'].apply(lambda c: "Sí" if c == "Bogotá" else "No")
            total_antes = len(df)
            df = filtrar_dataframe_relevante(df)
            descartadas = total_antes - len(df)
            if descartadas:
                print(f"  Depuradas {descartadas} noticias históricas no relevantes")
            print(f"  Cargadas {len(df)} noticias existentes")
            return df
        except Exception as e:
            print(f"  Error al cargar Excel: {e}")

    return pd.DataFrame(columns=columnas)


def guardar_excel(df: pd.DataFrame):
    """Guarda el DataFrame en Excel y CSV."""
    os.makedirs(os.path.dirname(EXCEL_PATH), exist_ok=True)
    # Asegurar orden de columnas
    columnas = ["fecha", "titulo", "fuente", "tipo_fuente", "categoria", "ciudad", "bogota", "url", "resumen"]
    df = df[columnas]
    df.to_excel(EXCEL_PATH, index=False)
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    print(f"\nGuardadas {len(df)} noticias en {EXCEL_PATH}")
    print(f"Guardadas {len(df)} noticias en {CSV_PATH}")


def hacer_request(url: str, timeout: int = 15, verify: bool = True) -> requests.Response | None:
    """Realiza una petición HTTP con manejo de errores.
    verify=False para sitios con certificado SSL inválido (ej. integracionsocial.gov.co).
    """
    try:
        if not verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(url, headers=HEADERS, timeout=timeout, verify=verify)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"    Error en request a {url}: {e}")
        return None


def crear_noticia(titulo: str, fuente: str, ciudad: str, url: str, resumen: str) -> dict | None:
    """Crea un dict de noticia con todos los campos, incluyendo categoría y filtro Colombia.
    Retorna None si la noticia no es de Colombia (se descarta).

    Resumen: solo se incluye si el medio lo proporciona en la página de listado.
    Si el resumen es igual al título, se deja vacío para no duplicar información.
    No se hace fetch adicional al artículo para obtener resúmenes.
    """
    texto_completo = f"{titulo} {resumen}"

    if not es_relevante_para_monitoreo(titulo, resumen, fuente, url):
        return None

    # Filtro geográfico: solo noticias de Colombia
    if not es_noticia_colombia(texto_completo, url):
        return None

    ciudad_detectada = ciudad if ciudad != "auto" else detectar_ciudad(texto_completo)
    es_bogota = "Sí" if ciudad_detectada == "Bogotá" else "No"
    categoria = clasificar_categoria(texto_completo)

    return {
        'fecha': datetime.now().strftime('%Y-%m-%d'),
        'titulo': limpiar_texto(titulo),
        'fuente': fuente,
        'tipo_fuente': obtener_tipo_fuente(fuente),
        'categoria': categoria,
        'ciudad': ciudad_detectada,
        'bogota': es_bogota,
        'url': url,
        # Solo se incluye resumen si viene del listado y es diferente al título
        'resumen': obtener_resumen(resumen) if resumen and limpiar_texto(resumen) != limpiar_texto(titulo) else ''
    }


def extraer_json_desde_html(texto_html: str, patron_inicio: str) -> dict | None:
    """Extrae un objeto JSON embebido en el HTML usando conteo de llaves.
    Necesario para sitios que usan Fusion/Arc (El Espectador, Infobae)
    porque el JSON es minificado y el regex non-greedy falla.
    """
    match = re.search(patron_inicio, texto_html)
    if not match:
        return None

    inicio_json = match.end()
    # Buscar el inicio del objeto JSON
    pos_llave = texto_html.find('{', inicio_json - 1)
    if pos_llave == -1:
        return None

    # Contar llaves para encontrar el cierre correcto
    contador = 0
    for i in range(pos_llave, len(texto_html)):
        if texto_html[i] == '{':
            contador += 1
        elif texto_html[i] == '}':
            contador -= 1
            if contador == 0:
                try:
                    return json.loads(texto_html[pos_llave:i + 1])
                except json.JSONDecodeError:
                    return None
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

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Blu Radio', href):
                noticia = crear_noticia(titulo, 'Blu Radio', 'auto', href, resumen)
                if noticia:
                    noticias.append(noticia)
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

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Noticias Caracol', href):
                noticia = crear_noticia(titulo, 'Noticias Caracol', 'auto', href, resumen)
                if noticia:
                    noticias.append(noticia)
        except Exception:
            continue

    return noticias


def scrape_pulzo() -> list[dict]:
    """Scraper para Pulzo - sección nación.
    Pulzo usa a.link-title como enlaces a artículos con h3 dentro.
    Se filtran los autores (parent class container-autor-openingMain o href con /autor/).
    """
    noticias = []
    url = "https://www.pulzo.com/nacion"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')

    # Buscar todos los enlaces con clase link-title (contienen los títulos)
    enlaces_titulo = soup.find_all('a', class_='link-title')

    for enlace in enlaces_titulo[:50]:
        try:
            href = enlace.get('href', '')

            # Filtrar enlaces de autor (contienen /autor/ en la URL)
            if '/autor/' in href or not href:
                continue

            # Filtrar por clase del padre (los autores tienen container-autor-openingMain)
            parent_classes = enlace.parent.get('class', []) if enlace.parent else []
            if 'container-autor-openingMain' in parent_classes:
                continue

            if not href.startswith('http'):
                href = urljoin("https://www.pulzo.com", href)

            # El título está en el h3 dentro del enlace
            h3 = enlace.find('h3')
            titulo = h3.get_text(strip=True) if h3 else enlace.get_text(strip=True)

            if not titulo or len(titulo) < 10:
                continue

            # Pulzo no tiene resumen en las tarjetas
            resumen = titulo

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Pulzo', href):
                noticia = crear_noticia(titulo, 'Pulzo', 'auto', href, resumen)
                if noticia:
                    noticias.append(noticia)
        except Exception:
            continue

    return noticias


def scrape_infobae() -> list[dict]:
    """Scraper para Infobae Colombia.
    Infobae es una SPA que carga contenido por JavaScript.
    Se usa el feed RSS que tiene ~100 artículos recientes con títulos limpios.
    """
    noticias = []
    url_rss = "https://www.infobae.com/arc/outboundfeeds/rss/"

    response = hacer_request(url_rss)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'xml')
    items = soup.find_all('item')

    for item in items[:100]:
        try:
            titulo_tag = item.find('title')
            link_tag = item.find('link')
            desc_tag = item.find('description')

            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''
            href = link_tag.get_text(strip=True) if link_tag else ''
            resumen = desc_tag.get_text(strip=True) if desc_tag else ''

            if not titulo or not href:
                continue

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Infobae', href):
                noticia = crear_noticia(titulo, 'Infobae', 'auto', href, resumen)
                if noticia:
                    noticias.append(noticia)
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

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Alerta Bogotá', href):
                texto_completo = f"{titulo} {resumen}"
                ciudad = detectar_ciudad(texto_completo)
                if ciudad == "Sin identificar":
                    ciudad = "Bogotá"
                noticia = crear_noticia(titulo, 'Alerta Bogotá', ciudad, href, resumen)
                if noticia:
                    noticias.append(noticia)
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

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Red+', href):
                noticia = crear_noticia(titulo, 'Red+', 'auto', href, resumen)
                if noticia:
                    noticias.append(noticia)
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

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Diario ADN', href):
                noticia = crear_noticia(titulo, 'Diario ADN', 'auto', href, resumen)
                if noticia:
                    noticias.append(noticia)
        except Exception:
            continue

    return noticias


def scrape_eltiempo() -> list[dict]:
    """Scraper para El Tiempo (diario pago) - sección Colombia.
    El Tiempo usa Marfeel (renderiza todo con JavaScript).
    Los artículos están disponibles como JSON-LD (schema.org) en el HTML inicial.
    """
    noticias = []
    url = "https://www.eltiempo.com/colombia"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')

    # Extraer artículos del JSON-LD (datos estructurados para SEO)
    scripts_jsonld = soup.find_all('script', type='application/ld+json')

    for script in scripts_jsonld:
        try:
            if not script.string:
                continue
            datos = json.loads(script.string)

            # Puede ser un solo artículo o una lista
            if isinstance(datos, list):
                articulos = datos
            else:
                articulos = [datos]

            for articulo in articulos:
                tipo = articulo.get('@type', '')
                # Solo artículos de noticias
                if tipo not in ('ReportageNewsArticle', 'NewsArticle', 'Article'):
                    continue

                titulo = articulo.get('headline', '')
                href = articulo.get('url', '')
                resumen = articulo.get('description', '')

                if not titulo or not href:
                    continue

                # FILTRO: términos de juventud + Colombia
                if es_relevante_para_monitoreo(titulo, resumen, 'El Tiempo', href):
                    noticia = crear_noticia(titulo, 'El Tiempo', 'auto', href, resumen)
                    if noticia:
                        noticias.append(noticia)
        except (json.JSONDecodeError, TypeError):
            continue

    return noticias


def scrape_elespectador() -> list[dict]:
    """Scraper para El Espectador (diario pago) - sección Colombia.
    Usa el JSON de Fusion.globalContent embebido en la página.
    El JSON está minificado y sin espacios (Fusion.globalContent={...}),
    por eso se usa conteo de llaves en vez de regex non-greedy.
    """
    noticias = []
    url = "https://www.elespectador.com/colombia/"

    response = hacer_request(url)
    if not response:
        return noticias

    texto_pagina = response.text

    # Extraer JSON de Fusion.globalContent con conteo de llaves
    datos_json = extraer_json_desde_html(texto_pagina, r'Fusion\.globalContent\s*=\s*')

    if datos_json:
        elementos = datos_json.get('content_elements', [])

        for elem in elementos[:50]:
            try:
                titulo = elem.get('headlines', {}).get('basic', '')
                resumen = elem.get('description', {}).get('basic', '')
                url_relativa = elem.get('canonical_url', '')

                if not titulo or not url_relativa:
                    continue

                href = urljoin("https://www.elespectador.com", url_relativa)

                # FILTRO: términos de juventud + Colombia
                if es_relevante_para_monitoreo(titulo, resumen, 'El Espectador', href):
                    noticia = crear_noticia(titulo, 'El Espectador', 'auto', href, resumen)
                    if noticia:
                        noticias.append(noticia)
            except Exception:
                continue

    return noticias


def scrape_sdis_juventud() -> list[dict]:
    """Scraper para la sección de noticias de juventud de la SDIS.
    Sitio Joomla que muestra artículos completos inline (sin URL individual por artículo).
    Se genera una URL única con hash del título para deduplicación.
    No se filtra por términos de juventud: toda la sección es de juventud.
    Ciudad siempre Bogotá. Fecha real tomada del tag <time>.
    """
    noticias = []
    url_base = "https://www.integracionsocial.gov.co/index.php/noticias/94-noticias-juventud"

    # Scrapear primeras 2 páginas (20 artículos, ~1 mes de publicaciones)
    for inicio in [0, 10]:
        url = url_base if inicio == 0 else f"{url_base}?start={inicio}"

        response = hacer_request(url, verify=False)
        if not response:
            continue

        soup = BeautifulSoup(response.text, 'lxml')
        articulos = soup.find_all('article')

        for art in articulos:
            try:
                # Título
                h2 = art.find('h2')
                if not h2:
                    continue
                titulo = h2.get_text(strip=True)
                if not titulo or len(titulo) < 10:
                    continue

                # Fecha real de publicación
                time_tag = art.find('time')
                if time_tag and time_tag.get('datetime'):
                    try:
                        dt = datetime.fromisoformat(time_tag['datetime'].replace('+00:00', '+00:00'))
                        fecha = dt.strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        fecha = datetime.now().strftime('%Y-%m-%d')
                else:
                    fecha = datetime.now().strftime('%Y-%m-%d')

                # Resumen: primeros párrafos del artículo
                parrafos = art.find_all('p')
                textos = [p.get_text(strip=True) for p in parrafos if len(p.get_text(strip=True)) > 30]
                resumen_texto = ' '.join(textos[:2]) if textos else ''

                # URL única: hash del título normalizado como fragmento
                titulo_normalizado = re.sub(r'\s+', ' ', titulo).strip().lower()
                hash_id = hashlib.md5(titulo_normalizado.encode('utf-8')).hexdigest()[:10]
                href = f"{url_base}#{hash_id}"

                # Crear noticia (ciudad fija Bogotá, sin filtro de términos)
                categoria = clasificar_categoria(f"{titulo} {resumen_texto}")

                noticia = {
                    'fecha': fecha,
                    'titulo': limpiar_texto(titulo),
                    'fuente': 'SDIS - Juventud',
                    'tipo_fuente': obtener_tipo_fuente('SDIS - Juventud'),
                    'categoria': categoria,
                    'ciudad': 'Bogotá',
                    'bogota': 'Sí',
                    'url': href,
                    'resumen': obtener_resumen(resumen_texto) if resumen_texto else '',
                }
                noticias.append(noticia)
            except Exception:
                continue

        time.sleep(1)

    return noticias


def scrape_rss_wordpress(url_feed: str, nombre_fuente: str) -> list[dict]:
    """Scraper genérico para feeds RSS de WordPress.
    Funciona con La Silla Vacía, Las2orillas, La Nota Económica y similares.
    """
    noticias = []

    response = hacer_request(url_feed)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'xml')
    items = soup.find_all('item')

    for item in items[:50]:
        try:
            titulo_tag = item.find('title')
            link_tag = item.find('link')
            desc_tag = item.find('description')

            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''
            href = link_tag.get_text(strip=True) if link_tag else ''
            resumen = ''
            if desc_tag:
                # Limpiar HTML del resumen RSS
                desc_html = desc_tag.get_text(strip=True)
                desc_soup = BeautifulSoup(desc_html, 'lxml')
                resumen = desc_soup.get_text(strip=True)

            if not titulo or not href:
                continue

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, nombre_fuente, href):
                noticia = crear_noticia(titulo, nombre_fuente, 'auto', href, resumen)
                if noticia:
                    noticias.append(noticia)
        except Exception:
            continue

    return noticias


def scrape_lasillavacia() -> list[dict]:
    """Scraper para La Silla Vacía - vía RSS (WordPress)."""
    return scrape_rss_wordpress("https://www.lasillavacia.com/feed/", "La Silla Vacía")


def scrape_las2orillas() -> list[dict]:
    """Scraper para Las2orillas - vía RSS (WordPress)."""
    return scrape_rss_wordpress("https://www.las2orillas.co/feed/", "Las2orillas")


def scrape_lanotaeconomica() -> list[dict]:
    """Scraper para La Nota Económica - vía RSS (WordPress)."""
    return scrape_rss_wordpress("https://lanotaeconomica.com.co/feed/", "La Nota Económica")


def scrape_portafolio() -> list[dict]:
    """Scraper para Portafolio - sección economía.
    Usa atributos data-* en los <article> (data-name, data-publicacion).
    """
    noticias = []
    url = "https://www.portafolio.co/economia"

    response = hacer_request(url)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('article')

    for art in articulos[:50]:
        try:
            # Título desde data-name o desde el h3
            titulo = art.get('data-name', '')
            if not titulo:
                h3 = art.find(['h2', 'h3'])
                titulo = h3.get_text(strip=True) if h3 else ''

            if not titulo:
                continue

            # URL desde el enlace dentro del artículo
            link_tag = art.find('a', href=True)
            if not link_tag:
                continue
            href = link_tag.get('href', '')
            if not href.startswith('http'):
                href = urljoin("https://www.portafolio.co", href)

            resumen = titulo  # Portafolio no tiene resumen en el listado

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Portafolio', href):
                noticia = crear_noticia(titulo, 'Portafolio', 'auto', href, resumen)
                if noticia:
                    noticias.append(noticia)
        except Exception:
            continue

    return noticias


def scrape_prosperidad_social() -> list[dict]:
    """Scraper para Prosperidad Social - sección noticias.
    Sitio WordPress (GeneratePress) con <article> estándar.
    """
    noticias = []
    url = "https://prosperidadsocial.gov.co/noticias/"

    response = hacer_request(url, verify=False)
    if not response:
        return noticias

    soup = BeautifulSoup(response.text, 'lxml')
    articulos = soup.find_all('article')

    for art in articulos[:20]:
        try:
            # Título
            h2 = art.find('h2', class_='entry-title')
            if not h2:
                continue
            link_tag = h2.find('a', href=True)
            if not link_tag:
                continue

            titulo = link_tag.get_text(strip=True)
            href = link_tag.get('href', '')

            if not titulo or not href:
                continue

            # Resumen
            resumen_div = art.find('div', class_='entry-summary')
            resumen = ''
            if resumen_div:
                p = resumen_div.find('p')
                resumen = p.get_text(strip=True) if p else resumen_div.get_text(strip=True)

            # FILTRO: términos de juventud + Colombia
            if es_relevante_para_monitoreo(titulo, resumen, 'Prosperidad Social', href):
                noticia = crear_noticia(titulo, 'Prosperidad Social', 'Bogotá', href, resumen)
                if noticia:
                    noticias.append(noticia)
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
        ("SDIS - Juventud", scrape_sdis_juventud),
        ("La Silla Vacía", scrape_lasillavacia),
        ("Las2orillas", scrape_las2orillas),
        ("La Nota Económica", scrape_lanotaeconomica),
        ("Portafolio", scrape_portafolio),
        ("Prosperidad Social", scrape_prosperidad_social),
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

    # Normalizar columna fecha (el Excel carga datetime, los nuevos datos son string)
    df_final['fecha'] = pd.to_datetime(df_final['fecha'], errors='coerce').dt.strftime('%Y-%m-%d')

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
