# Configuración del scraper de noticias

# Términos de búsqueda relacionados con JUVENTUD (filtro obligatorio)
TERMINOS_JUVENTUD = [
    "juventud",
    "jóvenes",
    "jovenes",
    "adolescentes",
    "adolescencia",
    "menor de edad",
    "menores de edad",
    "pandillas",
    "idipron",
    "plataformas juveniles",
    "primera infancia",
    "niños",
    "niñas",
    "infancia",
    "juvenil",
    "juveniles",
    "estudiantes",
    "colegios",
    "escolar",
]

# Ciudades de Colombia para clasificación
CIUDADES_COLOMBIA = {
    "bogotá": "Bogotá",
    "bogota": "Bogotá",
    "medellín": "Medellín",
    "medellin": "Medellín",
    "cali": "Cali",
    "barranquilla": "Barranquilla",
    "cartagena": "Cartagena",
    "bucaramanga": "Bucaramanga",
    "pereira": "Pereira",
    "manizales": "Manizales",
    "santa marta": "Santa Marta",
    "ibagué": "Ibagué",
    "ibague": "Ibagué",
    "cúcuta": "Cúcuta",
    "cucuta": "Cúcuta",
    "villavicencio": "Villavicencio",
    "pasto": "Pasto",
    "neiva": "Neiva",
    "armenia": "Armenia",
    "montería": "Montería",
    "monteria": "Montería",
    "valledupar": "Valledupar",
    "popayán": "Popayán",
    "popayan": "Popayán",
    "tunja": "Tunja",
    "sincelejo": "Sincelejo",
    "florencia": "Florencia",
    "quibdó": "Quibdó",
    "quibdo": "Quibdó",
    "riohacha": "Riohacha",
    "yopal": "Yopal",
    "leticia": "Leticia",
    "mocoa": "Mocoa",
    "arauca": "Arauca",
    "mitú": "Mitú",
    "mitu": "Mitú",
    "puerto carreño": "Puerto Carreño",
    "san andrés": "San Andrés",
    "san andres": "San Andrés",
    "inírida": "Inírida",
    "inirida": "Inírida",
    "colombia": "Colombia",
}

# Fuentes de noticias (sin El Tiempo ni El Espectador)
FUENTES = {
    "Blu Radio": {
        "url": "https://www.bluradio.com/",
        "seccion_colombia": "https://www.bluradio.com/nacion",
    },
    "Noticias Caracol": {
        "url": "https://www.noticiascaracol.com/",
        "seccion_colombia": "https://www.noticiascaracol.com/colombia",
    },
    "Alerta Bogotá": {
        "url": "https://www.alertabogota.com/",
        "seccion_colombia": "https://www.alertabogota.com/",
    },
    "Red+": {
        "url": "https://redmas.com.co/",
        "seccion_colombia": "https://redmas.com.co/",
    },
    "Pulzo": {
        "url": "https://www.pulzo.com/",
        "seccion_colombia": "https://www.pulzo.com/nacion",
    },
    "Infobae": {
        "url": "https://www.infobae.com/",
        "seccion_colombia": "https://www.infobae.com/colombia/",
    },
    "Diario ADN": {
        "url": "https://www.diarioadn.co/",
        "seccion_colombia": "https://www.diarioadn.co/",
    },
}

# Ruta del archivo Excel
EXCEL_PATH = "data/noticias.xlsx"

# Headers para las peticiones HTTP
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}
