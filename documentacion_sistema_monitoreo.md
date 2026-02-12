# Sistema de monitoreo de noticias sobre juventud en Colombia

## Qué es este sistema

Es un sistema automatizado que revisa diariamente las principales páginas de noticias de Colombia y recopila las noticias que mencionan temas de juventud (jóvenes, adolescentes, niños, colegios, etc.). Los resultados se guardan en un archivo Excel y se pueden consultar en un dashboard visual con filtros.

El objetivo es que el equipo de SDIS tenga un panorama actualizado de lo que se publica en medios sobre juventud en Colombia, sin tener que revisar manualmente cada medio todos los días.

---

## Estructura del proyecto

```
Monitoreo noticias juventud/
  config.py              --> Configuración: términos de búsqueda, fuentes, ciudades
  scraper.py             --> El programa que recoge las noticias de cada medio
  dashboard.py           --> La interfaz visual para consultar las noticias
  ejecutar_scraper.bat   --> Archivo para ejecutar el scraper con doble clic en Windows
  requirements.txt       --> Lista de librerías necesarias (Python)
  data/
    noticias.xlsx        --> Base de datos con todas las noticias recolectadas
  .github/workflows/
    scraper.yml          --> Configuración para que se ejecute automáticamente en GitHub
  logs/                  --> Carpeta donde se guardan los registros de ejecución
```

---

## Cómo funciona paso a paso

### 1. El scraper recoge noticias (scraper.py)

Cuando se ejecuta `scraper.py`, el sistema hace lo siguiente:

1. **Carga las noticias existentes** del archivo Excel (para no duplicar)
2. **Visita cada medio de noticias** configurado en `config.py`
3. **Lee los títulos y resúmenes** de las noticias en cada página
4. **Filtra solo las noticias que mencionan temas de juventud** usando los términos definidos en `config.py`
5. **Detecta la ciudad** mencionada en cada noticia
6. **Marca el tipo de fuente** (gratuito o diario pago)
7. **Guarda todo en el Excel** sin borrar las noticias anteriores

### 2. El dashboard muestra los resultados (dashboard.py)

El dashboard es una página web local que permite:

- Ver todas las noticias recolectadas en una tabla
- Filtrar por fecha, ciudad, fuente, tipo de fuente (gratuito/diario pago) y términos
- Ver gráficos de distribución por fuente, ciudad, día y términos frecuentes
- Descargar los datos filtrados en CSV
- Buscar texto libre en los títulos

---

## Fuentes de noticias configuradas

### Fuentes gratuitas (acceso libre)
| Fuente | Sección que se revisa |
|---|---|
| Blu Radio | Nacional |
| Noticias Caracol | Colombia |
| Alerta Bogotá | Página principal |
| Red+ | Página principal |
| Pulzo | Nacional |
| Infobae | Colombia |
| Diario ADN | Página principal |

### Diarios pagos (tienen paywall)
| Fuente | Sección que se revisa | Nota |
|---|---|---|
| El Tiempo | Colombia | Solo se recogen títulos y resúmenes visibles (no entra al contenido pago) |
| El Espectador | Colombia | Usa datos JSON embebidos en la página para mayor precisión |

La etiqueta "diario pago" aparece en el Excel y en el dashboard para que el equipo sepa cuándo una noticia viene de un medio con suscripción. Esto es relevante porque si se quiere leer la noticia completa, puede requerir acceso pago.

---

## Términos de búsqueda (filtro de juventud)

El sistema solo guarda noticias que contengan al menos uno de estos términos en el título o resumen:

- juventud, jóvenes, jovenes
- adolescentes, adolescencia
- menor de edad, menores de edad
- pandillas, idipron
- plataformas juveniles
- primera infancia, niños, niñas, infancia
- juvenil, juveniles
- estudiantes, colegios, escolar

Se pueden agregar o quitar términos editando la lista `TERMINOS_JUVENTUD` en `config.py`.

---

## Cómo ejecutar el sistema

### Opción 1: Ejecutar el scraper manualmente
1. Abrir una terminal en la carpeta del proyecto
2. Ejecutar: `python scraper.py`
3. Esperar a que termine (toma unos 2-3 minutos)
4. Los resultados se guardan en `data/noticias.xlsx`

### Opción 2: Doble clic en Windows
1. Hacer doble clic en `ejecutar_scraper.bat`
2. Se ejecuta el scraper y se guarda un registro en `logs/`

### Opción 3: Ejecución automática con GitHub Actions
- Si el proyecto está en GitHub, el scraper se ejecuta automáticamente todos los días a las 7:00 AM (hora Colombia)
- Los resultados se guardan automáticamente en el repositorio

### Ver el dashboard
1. Abrir una terminal en la carpeta del proyecto
2. Ejecutar: `streamlit run dashboard.py`
3. Se abre una página web local en el navegador
4. Usar los filtros del panel izquierdo para explorar las noticias

---

## Problemas conocidos y limitaciones

### Títulos y resúmenes incorrectos
Algunas noticias pueden aparecer con título o resumen incorrecto. Esto ocurre porque:

- **La estructura HTML de los sitios cambia sin aviso.** Cada medio organiza su página web de forma diferente, y cuando hacen rediseños o cambios, el scraper puede capturar texto de navegación, publicidad o widgets en lugar del título real.
- **Algunos artículos no tienen resumen visible.** En esos casos, el campo resumen queda vacío o con texto irrelevante.
- **Es una limitación inherente del web scraping** (leer información directamente del HTML de las páginas).

**Qué hacer si se detectan muchos errores en una fuente:**
Se debe revisar la estructura HTML actual de esa fuente y ajustar la función de scraping correspondiente en `scraper.py`. Cada medio tiene su propia función (por ejemplo, `scrape_bluradio()`, `scrape_eltiempo()`, etc.).

### Diarios pagos
El Tiempo y El Espectador tienen paywall. El sistema solo recoge lo visible en las páginas de sección (títulos y resúmenes que se muestran antes de pagar). No accede al contenido completo del artículo.

### Ejecución automática
Para que la ejecución automática con GitHub Actions funcione, el proyecto debe estar subido a GitHub y el workflow debe estar habilitado en el repositorio.

---

## Estructura de datos (columnas del Excel)

| Columna | Descripción |
|---|---|
| fecha | Fecha en que se recolectó la noticia (AAAA-MM-DD) |
| titulo | Título de la noticia |
| fuente | Medio de comunicación (Blu Radio, El Tiempo, etc.) |
| tipo_fuente | Si el medio es "gratuito" o "diario pago" |
| ciudad | Ciudad mencionada en la noticia (o "Sin identificar") |
| url | Enlace a la noticia original |
| resumen | Primeros 250 caracteres del texto de la noticia |

---

## Mejora futura sugerida

Para mejorar la precisión de títulos, se podría hacer que el scraper entre a cada artículo individual y extraiga el `<h1>` principal de la página. Eso casi siempre es el título real. Sin embargo, esto haría el proceso más lento porque tendría que visitar cada artículo individualmente en lugar de solo la página de sección. Por ahora se deja como mejora pendiente.

---

## Dependencias (librerías de Python necesarias)

- `requests` - para hacer peticiones HTTP a los sitios web
- `beautifulsoup4` + `lxml` - para leer y entender el HTML de las páginas
- `pandas` + `openpyxl` - para manejar los datos y el Excel
- `streamlit` + `plotly` - para el dashboard visual
- `feedparser` - para leer feeds RSS (soporte futuro)

Para instalar todo: `pip install -r requirements.txt`

---

## Archivos de respaldo

Antes de cada modificación, se crean copias versionadas de los archivos principales:
- `config_v1.py` - versión original de la configuración
- `scraper_v1.py` - versión original del scraper
- `dashboard_v1.py` - versión original del dashboard

Esto permite volver a una versión anterior si algo falla.

---

*Documentación creada el 2026-02-12. Sistema construido con la asistencia de Claude para la Subdirección de SDIS.*
