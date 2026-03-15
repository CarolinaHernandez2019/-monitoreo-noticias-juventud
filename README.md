# Monitor de noticias de juventud

Este sistema revisa automáticamente las principales páginas de noticias de Colombia todos los días y recopila las noticias que mencionan temas de juventud y adolescencia. Los resultados se guardan en un archivo Excel y se pueden consultar en un dashboard visual con filtros por fecha, ciudad, fuente y tipo de medio.

## Usos

- Tener un panorama diario de lo que se publica en medios sobre juventud en Colombia
- No tener que revisar manualmente cada medio todos los días
- Identificar tendencias: qué ciudades aparecen más, qué temas son recurrentes
- Tener un archivo histórico consultable de noticias sobre juventud


## Dashboard

Las noticias son recopiladas en un tablero interactivo:

[Monitor Noticias Juventud en Streamlit](https://monitoreo-noticias-juventud.streamlit.app)

## Fuentes monitoreadas

| Medio | Tipo |
|-------|------|
| El Tiempo | Prensa (pago) |
| El Espectador | Prensa (pago) |
| Blu Radio | Radio |
| Noticias Caracol | TV |
| Red+ Noticias | TV |
| Pulzo | Digital |
| Infobae Colombia | Digital |
| ADN | Digital |
| La Silla Vacía | Digital |
| Las2Orillas | Digital |
| La Nota Económica | Digital |
| Portafolio | Prensa (pago) |
| Alerta Bogotá | Digital |
| Integración Social | Institucional |
| Prosperidad Social | Institucional |

## Actualización automática

El scraper se ejecuta todos los días a las 7:00 AM (hora Colombia) mediante GitHub Actions. Los datos se actualizan automáticamente sin intervención manual.

Hecho en Python. Todas las librerías necesarias están listadas en el archivo `requirements.txt`.
