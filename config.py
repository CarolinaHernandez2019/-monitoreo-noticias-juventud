# Configuración del scraper de noticias

# Términos de búsqueda relacionados con JUVENTUD y ADOLESCENCIA (filtro obligatorio)
# La búsqueda es por subcadena: "joven" captura "joven", "jovenes", etc.
# Se incluyen variantes con y sin tilde
TERMINOS_JUVENTUD = [
    "juventud",
    "jóvenes",
    "jovenes",
    "joven",
    "juvenil",
    "adolescente",
    "adolescencia",
    "menor de edad",
    "menores de edad",
    "pandillas",
    "idipron",
    "plataformas juveniles",
    "colj",
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

# Fuentes de noticias
# tipo: "gratuito" = acceso libre, "diario pago" = tiene paywall (se scrapea lo visible)
FUENTES = {
    "Blu Radio": {
        "url": "https://www.bluradio.com/",
        "seccion_colombia": "https://www.bluradio.com/nacion",
        "tipo": "gratuito",
    },
    "Noticias Caracol": {
        "url": "https://www.noticiascaracol.com/",
        "seccion_colombia": "https://www.noticiascaracol.com/colombia",
        "tipo": "gratuito",
    },
    "Alerta Bogotá": {
        "url": "https://www.alertabogota.com/",
        "seccion_colombia": "https://www.alertabogota.com/",
        "tipo": "gratuito",
    },
    "Red+": {
        "url": "https://redmas.com.co/",
        "seccion_colombia": "https://redmas.com.co/",
        "tipo": "gratuito",
    },
    "Pulzo": {
        "url": "https://www.pulzo.com/",
        "seccion_colombia": "https://www.pulzo.com/nacion",
        "tipo": "gratuito",
    },
    "Infobae": {
        "url": "https://www.infobae.com/",
        "seccion_colombia": "https://www.infobae.com/colombia/",
        "tipo": "gratuito",
    },
    "Diario ADN": {
        "url": "https://www.diarioadn.co/",
        "seccion_colombia": "https://www.diarioadn.co/",
        "tipo": "gratuito",
    },
    "El Tiempo": {
        "url": "https://www.eltiempo.com/",
        "seccion_colombia": "https://www.eltiempo.com/colombia",
        "tipo": "diario pago",
    },
    "El Espectador": {
        "url": "https://www.elespectador.com/",
        "seccion_colombia": "https://www.elespectador.com/colombia/",
        "tipo": "diario pago",
    },
    "SDIS - Juventud": {
        "url": "https://www.integracionsocial.gov.co/",
        "seccion_colombia": "https://www.integracionsocial.gov.co/index.php/noticias/94-noticias-juventud",
        "tipo": "institucional",
    },
    "La Silla Vacía": {
        "url": "https://www.lasillavacia.com/",
        "seccion_colombia": "https://www.lasillavacia.com/",
        "tipo": "gratuito",
    },
    "Prosperidad Social": {
        "url": "https://prosperidadsocial.gov.co/",
        "seccion_colombia": "https://prosperidadsocial.gov.co/noticias/",
        "tipo": "institucional",
    },
    "Las2orillas": {
        "url": "https://www.las2orillas.co/",
        "seccion_colombia": "https://www.las2orillas.co/",
        "tipo": "gratuito",
    },
    "La Nota Económica": {
        "url": "https://lanotaeconomica.com.co/",
        "seccion_colombia": "https://lanotaeconomica.com.co/",
        "tipo": "gratuito",
    },
    "Portafolio": {
        "url": "https://www.portafolio.co/",
        "seccion_colombia": "https://www.portafolio.co/economia",
        "tipo": "gratuito",
    },
}

# Categorías temáticas para clasificar cada noticia
# Se asigna la primera categoría cuyas palabras clave aparezcan en el título o resumen
CATEGORIAS = {
    "Violencia": [
        "homicidio", "asesinato", "asesinado", "muerte", "murió", "murio", "muerto",
        "pelea", "arma", "disparos", "ataque", "pandilla", "sicario", "bala",
        "apuñalado", "masacre", "crimen", "criminal", "violencia", "agresión",
        "femicidio", "feminicidio", "riña",
    ],
    "Seguridad": [
        "policía", "policia", "captura", "capturado", "detenido", "detención",
        "judicializado", "robo", "hurto", "extorsión", "banda", "operativo",
        "incautación", "allanamiento", "fuga",
    ],
    "Educación": [
        "colegio", "colegios", "escuela", "escolar", "educación", "educacion",
        "profesor", "profesora", "clase", "icfes", "universidad", "beca",
        "matrícula", "deserción", "académico", "docente", "aula", "enseñanza",
        "saber 11", "puntaje",
    ],
    "Protección": [
        "abuso", "maltrato", "explotación", "reclutamiento", "desaparición",
        "desaparecido", "desaparecida", "trata", "vulneración", "abandono",
        "negligencia", "acoso", "bullying", "matoneo",
    ],
    "Salud": [
        "salud", "hospital", "enfermedad", "droga", "sustancia", "adicción",
        "mental", "suicidio", "embarazo", "nutrición", "desnutrición",
        "vacuna", "discapacidad", "trastorno",
    ],
    "Empleo": [
        "empleo", "trabajo", "desempleo", "laboral", "contratación",
        "primer empleo", "oportunidad laboral", "vacante", "informalidad",
    ],
    "Política pública": [
        "idipron", "icbf", "bienestar", "programa social", "subsidio",
        "política pública", "política publica", "ley", "decreto", "proyecto de ley",
        "concejo", "alcaldía", "gobernación", "plataforma juvenil",
    ],
    "Cultura y deporte": [
        "deporte", "deportivo", "cultura", "cultural", "arte", "música",
        "festival", "torneo", "competencia", "recreación", "olimpiada",
    ],
}


# Palabras que indican que la noticia NO es de Colombia (filtro geográfico)
PAISES_EXCLUIDOS = [
    "londres", "london", "reino unido", "estados unidos", "españa",
    "argentina", "méxico", "mexico", "chile", "santiago",
    "perú", "peru", "lima", "brasil", "venezuela", "caracas", "chavista",
    "ecuador", "quito", "guayaquil", "bolivia", "la paz",
    "paraguay", "asunción", "uruguay", "montevideo",
    "congo", "rusia", "moscú", "china", "beijing", "pekín",
    "francia", "parís", "paris", "alemania", "berlín",
    "italia", "roma", "japón", "tokio", "india",
    "israel", "gaza", "palestina", "ucrania", "irán", "iran",
    "siria", "egipto", "nigeria", "kenia", "sudáfrica",
    "australia", "canadá", "nueva york", "washington",
    "miami", "california", "texas", "florida",
    "valencia cf",
]

# Ruta del archivo Excel
EXCEL_PATH = "data/noticias.xlsx"

# Headers para las peticiones HTTP
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}
