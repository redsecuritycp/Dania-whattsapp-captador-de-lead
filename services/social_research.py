"""
Servicio de investigación de redes sociales y noticias para DANIA/Fortia
VERSIÓN CORREGIDA:
- LinkedIn empresa: SOLO desde web del cliente (no buscar con Google)
- LinkedIn personal: 2 fases (nombre+empresa, fallback nombre+ubicación)

Flujo:
1. Preparar datos y limpiar inputs
2. Tavily: Verificar nombre completo en sitio web
3. Tavily: Buscar LinkedIn personal (FASE 1: nombre+empresa)
4. Tavily: Buscar LinkedIn personal (FASE 2: nombre+ubicación) - fallback
5. Google: Fallback LinkedIn personal (misma lógica 2 fases)
6. Apify: Crawler de noticias (Google News + Bing News)
7. Google: Noticias fallback
8. Compilar resultados
"""
import logging
import httpx
import re
import asyncio
from typing import Optional, List
from urllib.parse import quote

from config import (TAVILY_API_KEY, GOOGLE_API_KEY, GOOGLE_SEARCH_CX,
                    APIFY_API_TOKEN)

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30.0
APIFY_TIMEOUT = 45.0  # Reducido de 200s a 45s

# ═══════════════════════════════════════════════════════════════════════════════
# DICCIONARIO DE UBICACIONES COMPLETO - VARIANTES Y ABREVIACIONES
# Todos los países hispanohablantes + USA + Brasil + UE principales
# Todos los estados/provincias + ciudades principales
# ═══════════════════════════════════════════════════════════════════════════════
UBICACIONES_VARIANTES = {
    # ═══════════════════════════════════════════════════════════════════════════
    # PAÍSES
    # ═══════════════════════════════════════════════════════════════════════════
    "paises": {
        "argentina":
        ["argentina", "ar", "arg", "argentine", "argentino", "🇦🇷"],
        "mexico":
        ["mexico", "méxico", "mx", "mex", "mexican", "mexicano", "🇲🇽"],
        "espana":
        ["españa", "espana", "spain", "es", "esp", "spanish", "español", "🇪🇸"],
        "colombia": ["colombia", "co", "col", "colombian", "colombiano", "🇨🇴"],
        "chile": ["chile", "cl", "chi", "chilean", "chileno", "🇨🇱"],
        "peru": ["peru", "perú", "pe", "per", "peruvian", "peruano", "🇵🇪"],
        "venezuela":
        ["venezuela", "ve", "ven", "venezuelan", "venezolano", "🇻🇪"],
        "ecuador": ["ecuador", "ec", "ecu", "ecuadorian", "ecuatoriano", "🇪🇨"],
        "bolivia": ["bolivia", "bo", "bol", "bolivian", "boliviano", "🇧🇴"],
        "paraguay": ["paraguay", "py", "par", "paraguayan", "paraguayo", "🇵🇾"],
        "uruguay": ["uruguay", "uy", "uru", "uruguayan", "uruguayo", "🇺🇾"],
        "cuba": ["cuba", "cu", "cub", "cuban", "cubano", "🇨🇺"],
        "dominicana": [
            "dominicana", "república dominicana", "dominican republic", "do",
            "dom", "rd", "🇩🇴"
        ],
        "puerto_rico":
        ["puerto rico", "pr", "puertorriqueño", "boricua", "🇵🇷"],
        "guatemala": ["guatemala", "gt", "gua", "guatemalteco", "🇬🇹"],
        "honduras": ["honduras", "hn", "hon", "hondureño", "🇭🇳"],
        "el_salvador":
        ["el salvador", "salvador", "sv", "sal", "salvadoreño", "🇸🇻"],
        "nicaragua": ["nicaragua", "ni", "nic", "nicaragüense", "🇳🇮"],
        "costa_rica":
        ["costa rica", "cr", "cri", "costarricense", "tico", "🇨🇷"],
        "panama": ["panama", "panamá", "pa", "pan", "panameño", "🇵🇦"],
        "brasil":
        ["brasil", "brazil", "br", "bra", "brazilian", "brasileiro", "🇧🇷"],
        "usa": [
            "usa", "united states", "estados unidos", "us", "ee.uu", "eeuu",
            "america", "american", "estadounidense", "🇺🇸"
        ],
        "canada":
        ["canada", "canadá", "ca", "can", "canadian", "canadiense", "🇨🇦"],
        "alemania": [
            "alemania", "germany", "de", "deu", "ger", "german", "alemán",
            "deutschland", "🇩🇪"
        ],
        "francia":
        ["francia", "france", "fr", "fra", "french", "francés", "🇫🇷"],
        "italia":
        ["italia", "italy", "it", "ita", "italian", "italiano", "🇮🇹"],
        "portugal": ["portugal", "pt", "por", "portuguese", "portugués", "🇵🇹"],
        "reino_unido": [
            "reino unido", "united kingdom", "uk", "gb", "gbr", "britain",
            "british", "británico", "england", "inglaterra", "🇬🇧"
        ],
        "paises_bajos": [
            "países bajos", "holanda", "netherlands", "holland", "nl", "ned",
            "dutch", "holandés", "🇳🇱"
        ],
        "belgica": [
            "bélgica", "belgica", "belgium", "be", "bel", "belgian", "belga",
            "🇧🇪"
        ],
        "suiza": ["suiza", "switzerland", "ch", "sui", "swiss", "suizo", "🇨🇭"],
        "austria": ["austria", "at", "aut", "austrian", "austriaco", "🇦🇹"],
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ARGENTINA - 24 PROVINCIAS + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "argentina": {
        "provincias": {
            "buenos_aires": [
                "buenos aires", "bs as", "bs. as.", "bsas", "ba", "pba",
                "provincia de buenos aires", "pcia bs as"
            ],
            "caba": [
                "caba", "capital federal", "ciudad autónoma",
                "ciudad autonoma", "c.a.b.a", "buenos aires ciudad",
                "cdad de buenos aires", "ciudad de buenos aires"
            ],
            "catamarca":
            ["catamarca", "cat", "san fernando del valle de catamarca"],
            "chaco": ["chaco", "cha", "resistencia"],
            "chubut": ["chubut", "chu", "rawson"],
            "cordoba":
            ["córdoba", "cordoba", "cba", "cba.", "provincia de córdoba"],
            "corrientes": ["corrientes", "corr", "ctes"],
            "entre_rios":
            ["entre ríos", "entre rios", "er", "e. ríos", "e rios"],
            "formosa": ["formosa", "for", "fsa"],
            "jujuy":
            ["jujuy", "juj", "s.s. de jujuy", "san salvador de jujuy"],
            "la_pampa": ["la pampa", "lpampa", "l. pampa", "santa rosa"],
            "la_rioja": ["la rioja", "rioja", "lrioja", "l rioja"],
            "mendoza": ["mendoza", "mza", "mdz", "mend"],
            "misiones": ["misiones", "mis", "posadas"],
            "neuquen": ["neuquén", "neuquen", "nqn", "neuq"],
            "rio_negro":
            ["río negro", "rio negro", "rn", "r. negro", "viedma"],
            "salta": ["salta", "sal", "sla"],
            "san_juan": ["san juan", "sj", "s. juan", "s juan"],
            "san_luis": ["san luis", "sl", "s. luis", "s luis"],
            "santa_cruz":
            ["santa cruz", "sc", "s. cruz", "s cruz", "rio gallegos"],
            "santa_fe": [
                "santa fe", "sf", "sta fe", "sta. fe", "s. fe", "sfe",
                "pcia santa fe", "prov santa fe", "provincia de santa fe"
            ],
            "santiago_estero": [
                "santiago del estero", "sgo estero", "sde", "stgo del estero",
                "santiago estero", "sgo del estero"
            ],
            "tierra_fuego": [
                "tierra del fuego", "tdf", "t. del fuego", "ushuaia",
                "tierra del fuego antártida e islas del atlántico sur"
            ],
            "tucuman": [
                "tucumán", "tucuman", "tuc", "smt", "san miguel de tucumán",
                "san miguel de tucuman"
            ],
        },
        "ciudades": {
            # CABA y GBA
            "caba_ciudad": ["buenos aires", "caba", "capital federal"],
            "la_plata": ["la plata", "laplata"],
            "mar_del_plata": ["mar del plata", "mdp", "mdq", "mardel"],
            "bahia_blanca": ["bahía blanca", "bahia blanca", "bb"],
            "tandil": ["tandil"],
            "olavarria": ["olavarría", "olavarria"],
            "pergamino": ["pergamino"],
            "zarate": ["zárate", "zarate"],
            "campana": ["campana"],
            "pilar": ["pilar"],
            "tigre": ["tigre"],
            "san_isidro": ["san isidro"],
            "vicente_lopez": ["vicente lópez", "vicente lopez"],
            "avellaneda": ["avellaneda"],
            "lanus": ["lanús", "lanus"],
            "lomas_zamora": ["lomas de zamora", "lomas"],
            "quilmes": ["quilmes"],
            "berazategui": ["berazategui"],
            "florencio_varela": ["florencio varela"],
            "almirante_brown": ["almirante brown"],
            "moron": ["morón", "moron"],
            "ituzaingo": ["ituzaingó", "ituzaingo"],
            "hurlingham": ["hurlingham"],
            "san_martin": ["san martín", "san martin", "gral san martín"],
            "san_miguel": ["san miguel"],
            "jose_paz": ["josé c. paz", "jose c paz", "jose c. paz"],
            "malvinas_argentinas": ["malvinas argentinas"],
            "escobar": ["escobar"],
            "san_fernando": ["san fernando"],
            "san_nicolas": ["san nicolás", "san nicolas"],
            "junin": ["junín", "junin"],
            "chivilcoy": ["chivilcoy"],
            "mercedes": ["mercedes"],
            "lujan": ["luján", "lujan"],
            "necochea": ["necochea"],
            "tres_arroyos": ["tres arroyos"],
            "azul": ["azul"],

            # Santa Fe provincia
            "rosario": ["rosario", "ros"],
            "santa_fe_ciudad":
            ["santa fe ciudad", "santa fe capital", "santa fe"],
            "rafaela": ["rafaela"],
            "venado_tuerto": ["venado tuerto"],
            "reconquista": ["reconquista"],
            "san_lorenzo": ["san lorenzo"],
            "casilda": ["casilda"],
            "esperanza": ["esperanza"],
            "san_justo": ["san justo"],
            "villa_constitucion": ["villa constitución", "villa constitucion"],
            "san_jorge": ["san jorge"],
            "galvez": ["gálvez", "galvez"],
            "ceres": ["ceres"],
            "sunchales": ["sunchales"],
            "armstrong": ["armstrong"],
            "firmat": ["firmat"],
            "rufino": ["rufino"],
            "totoras": ["totoras"],
            "carcarana": ["carcarañá", "carcarana"],
            "fray_luis_beltran": ["fray luis beltrán", "fray luis beltran"],
            "granadero_baigorria": ["granadero baigorria"],
            "puerto_san_martin":
            ["puerto general san martín", "puerto san martin"],
            "capitan_bermudez": ["capitán bermúdez", "capitan bermudez"],
            "santo_tome": ["santo tomé", "santo tome"],
            "san_carlos_centro": ["san carlos centro"],
            "carlos_pellegrini": ["carlos pellegrini", "pellegrini"],
            "vera": ["vera"],
            "tostado": ["tostado"],
            "las_parejas": ["las parejas"],
            "las_rosas": ["las rosas"],
            "coronda": ["coronda"],
            "avellaneda_sf": ["avellaneda"],

            # Córdoba provincia
            "cordoba_ciudad": [
                "córdoba ciudad", "córdoba capital", "cordoba capital",
                "córdoba", "cordoba"
            ],
            "villa_maria": ["villa maría", "villa maria"],
            "rio_cuarto": ["río cuarto", "rio cuarto", "río iv", "rio iv"],
            "san_francisco": ["san francisco"],
            "villa_carlos_paz": ["villa carlos paz", "carlos paz"],
            "jesus_maria": ["jesús maría", "jesus maria"],
            "alta_gracia": ["alta gracia"],
            "cosquin": ["cosquín", "cosquin"],
            "la_falda": ["la falda"],
            "bell_ville": ["bell ville"],
            "marcos_juarez": ["marcos juárez", "marcos juarez"],
            "rio_tercero": ["río tercero", "rio tercero"],
            "villa_dolores": ["villa dolores"],
            "dean_funes": ["deán funes", "dean funes"],
            "arroyito": ["arroyito"],

            # Mendoza provincia
            "mendoza_ciudad": ["mendoza ciudad", "mendoza capital", "mendoza"],
            "san_rafael": ["san rafael"],
            "godoy_cruz": ["godoy cruz"],
            "guaymallen": ["guaymallén", "guaymallen"],
            "las_heras_mza": ["las heras"],
            "maipu_mza": ["maipú", "maipu"],
            "lujan_cuyo": ["luján de cuyo", "lujan de cuyo"],
            "tunuyan": ["tunuyán", "tunuyan"],
            "general_alvear": ["general alvear"],
            "malargue": ["malargüe", "malargue"],

            # Tucumán provincia
            "tucuman_ciudad": [
                "san miguel de tucumán", "tucumán capital", "tucuman capital",
                "tucumán", "tucuman"
            ],
            "yerba_buena": ["yerba buena"],
            "tafi_viejo": ["tafí viejo", "tafi viejo"],
            "banda_rio_sali": ["banda del río salí", "banda del rio sali"],
            "concepcion_tuc": ["concepción"],
            "aguilares": ["aguilares"],
            "monteros": ["monteros"],

            # Salta provincia
            "salta_ciudad": ["salta ciudad", "salta capital", "salta"],
            "oran": ["san ramón de la nueva orán", "orán", "oran"],
            "tartagal": ["tartagal"],
            "general_guemes": ["general güemes", "general guemes"],
            "metan": ["metán", "metan"],
            "cafayate": ["cafayate"],

            # Entre Ríos provincia
            "parana": ["paraná", "parana"],
            "concordia": ["concordia"],
            "gualeguaychu": ["gualeguaychú", "gualeguaychu"],
            "concepcion_uruguay": ["concepción del uruguay"],
            "gualeguay": ["gualeguay"],
            "villaguay": ["villaguay"],
            "chajari": ["chajarí", "chajari"],
            "colon": ["colón", "colon"],
            "federacion": ["federación", "federacion"],
            "victoria": ["victoria"],
            "la_paz_er": ["la paz"],
            "crespo": ["crespo"],
            "diamante": ["diamante"],

            # Chaco provincia
            "resistencia": ["resistencia"],
            "saenz_pena":
            ["presidencia roque sáenz peña", "sáenz peña", "saenz pena"],
            "villa_angela": ["villa ángela", "villa angela"],
            "charata": ["charata"],
            "barranqueras": ["barranqueras"],
            "quitilipi": ["quitilipi"],

            # Corrientes provincia
            "corrientes_ciudad":
            ["corrientes ciudad", "corrientes capital", "corrientes"],
            "goya": ["goya"],
            "paso_libres": ["paso de los libres"],
            "curuzu_cuatia": ["curuzú cuatiá", "curuzu cuatia"],
            "mercedes_ctes": ["mercedes"],
            "monte_caseros": ["monte caseros"],
            "bella_vista": ["bella vista"],

            # Misiones provincia
            "posadas": ["posadas"],
            "obera": ["oberá", "obera"],
            "eldorado": ["eldorado"],
            "puerto_iguazu": ["puerto iguazú", "iguazú", "iguazu"],
            "apostoles": ["apóstoles", "apostoles"],

            # Neuquén provincia
            "neuquen_ciudad": [
                "neuquén ciudad", "neuquén capital", "neuquen capital",
                "neuquén", "neuquen"
            ],
            "centenario": ["centenario"],
            "plottier": ["plottier"],
            "cutral_co": ["cutral có", "cutral co"],
            "plaza_huincul": ["plaza huincul"],
            "zapala": ["zapala"],
            "san_martin_andes": ["san martín de los andes"],

            # Río Negro provincia
            "viedma": ["viedma"],
            "bariloche": ["san carlos de bariloche", "bariloche"],
            "general_roca": ["general roca"],
            "cipolletti": ["cipolletti"],
            "allen": ["allen"],
            "el_bolson": ["el bolsón", "el bolson"],

            # Chubut provincia
            "rawson_chu": ["rawson"],
            "comodoro_rivadavia": ["comodoro rivadavia", "comodoro"],
            "trelew": ["trelew"],
            "puerto_madryn": ["puerto madryn", "madryn"],
            "esquel": ["esquel"],

            # Santa Cruz provincia
            "rio_gallegos": ["río gallegos", "rio gallegos"],
            "caleta_olivia": ["caleta olivia"],
            "el_calafate": ["el calafate", "calafate"],
            "puerto_deseado": ["puerto deseado"],

            # San Juan provincia
            "san_juan_ciudad":
            ["san juan ciudad", "san juan capital", "san juan"],
            "rawson_sj": ["rawson"],
            "chimbas": ["chimbas"],
            "pocito": ["pocito"],
            "caucete": ["caucete"],

            # San Luis provincia
            "san_luis_ciudad":
            ["san luis ciudad", "san luis capital", "san luis"],
            "villa_mercedes": ["villa mercedes"],
            "merlo_sl": ["merlo"],
            "la_punta": ["la punta"],

            # Jujuy provincia
            "san_salvador_jujuy": [
                "san salvador de jujuy", "s.s. de jujuy", "jujuy capital",
                "jujuy"
            ],
            "palpala": ["palpalá", "palpala"],
            "san_pedro_juj": ["san pedro"],
            "libertador_san_martin": ["libertador general san martín"],
            "humahuaca": ["humahuaca"],
            "la_quiaca": ["la quiaca"],
            "tilcara": ["tilcara"],

            # La Rioja provincia
            "la_rioja_ciudad":
            ["la rioja ciudad", "la rioja capital", "la rioja"],
            "chilecito": ["chilecito"],
            "aimogasta": ["aimogasta"],

            # Catamarca provincia
            "catamarca_ciudad": [
                "san fernando del valle de catamarca", "catamarca capital",
                "catamarca"
            ],
            "belen": ["belén", "belen"],
            "andalgala": ["andalgalá", "andalgala"],
            "tinogasta": ["tinogasta"],

            # La Pampa provincia
            "santa_rosa_lp": ["santa rosa"],
            "general_pico": ["general pico"],
            "toay": ["toay"],

            # Tierra del Fuego
            "ushuaia": ["ushuaia"],
            "rio_grande_tdf": ["río grande", "rio grande"],
            "tolhuin": ["tolhuin"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # MÉXICO - 32 ESTADOS + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "mexico": {
        "estados": {
            "aguascalientes": ["aguascalientes", "ags"],
            "baja_california":
            ["baja california", "bc", "baja california norte"],
            "baja_california_sur": ["baja california sur", "bcs"],
            "campeche": ["campeche", "camp"],
            "chiapas": ["chiapas", "chis", "chps"],
            "chihuahua": ["chihuahua", "chih"],
            "coahuila": ["coahuila", "coah", "coahuila de zaragoza"],
            "colima": ["colima", "col"],
            "cdmx": [
                "ciudad de méxico", "cdmx", "df", "distrito federal",
                "ciudad de mexico", "méxico df", "mexico df"
            ],
            "durango": ["durango", "dgo"],
            "guanajuato": ["guanajuato", "gto"],
            "guerrero": ["guerrero", "gro"],
            "hidalgo": ["hidalgo", "hgo"],
            "jalisco": ["jalisco", "jal"],
            "estado_mexico": [
                "estado de méxico", "estado de mexico", "edomex", "edo mex",
                "mex"
            ],
            "michoacan": ["michoacán", "michoacan", "mich"],
            "morelos": ["morelos", "mor"],
            "nayarit": ["nayarit", "nay"],
            "nuevo_leon": ["nuevo león", "nuevo leon", "nl"],
            "oaxaca": ["oaxaca", "oax"],
            "puebla": ["puebla", "pue"],
            "queretaro": ["querétaro", "queretaro", "qro"],
            "quintana_roo": ["quintana roo", "qroo", "q roo"],
            "san_luis_potosi": ["san luis potosí", "san luis potosi", "slp"],
            "sinaloa": ["sinaloa", "sin"],
            "sonora": ["sonora", "son"],
            "tabasco": ["tabasco", "tab"],
            "tamaulipas": ["tamaulipas", "tamps"],
            "tlaxcala": ["tlaxcala", "tlax"],
            "veracruz": ["veracruz", "ver"],
            "yucatan": ["yucatán", "yucatan", "yuc"],
            "zacatecas": ["zacatecas", "zac"],
        },
        "ciudades": {
            "ciudad_mexico":
            ["ciudad de méxico", "cdmx", "df", "méxico df", "mexico city"],
            "guadalajara": ["guadalajara", "gdl"],
            "monterrey": ["monterrey", "mty"],
            "puebla_ciudad": ["puebla"],
            "tijuana": ["tijuana", "tj"],
            "leon": ["león", "leon"],
            "juarez": ["ciudad juárez", "juarez", "ciudad juarez"],
            "zapopan": ["zapopan"],
            "ecatepec": ["ecatepec", "ecatepec de morelos"],
            "naucalpan": ["naucalpan"],
            "merida": ["mérida", "merida"],
            "aguascalientes_ciudad": ["aguascalientes"],
            "san_luis_potosi_ciudad": ["san luis potosí", "san luis potosi"],
            "hermosillo": ["hermosillo"],
            "chihuahua_ciudad": ["chihuahua"],
            "saltillo": ["saltillo"],
            "mexicali": ["mexicali"],
            "culiacan": ["culiacán", "culiacan"],
            "queretaro_ciudad": ["querétaro", "queretaro"],
            "morelia": ["morelia"],
            "cancun": ["cancún", "cancun"],
            "acapulco": ["acapulco"],
            "veracruz_ciudad": ["veracruz"],
            "toluca": ["toluca"],
            "durango_ciudad": ["durango"],
            "torreon": ["torreón", "torreon"],
            "reynosa": ["reynosa"],
            "tuxtla_gutierrez": ["tuxtla gutiérrez", "tuxtla"],
            "mazatlan": ["mazatlán", "mazatlan"],
            "oaxaca_ciudad": ["oaxaca"],
            "villahermosa": ["villahermosa"],
            "cuernavaca": ["cuernavaca"],
            "playa_carmen": ["playa del carmen"],
            "tampico": ["tampico"],
            "nuevo_laredo": ["nuevo laredo"],
            "tepic": ["tepic"],
            "la_paz_mx": ["la paz"],
            "campeche_ciudad": ["campeche"],
            "colima_ciudad": ["colima"],
            "pachuca": ["pachuca"],
            "zacatecas_ciudad": ["zacatecas"],
            "xalapa": ["xalapa", "jalapa"],
            "irapuato": ["irapuato"],
            "celaya": ["celaya"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ESPAÑA - 17 COMUNIDADES AUTÓNOMAS + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "espana": {
        "comunidades": {
            "andalucia": ["andalucía", "andalucia", "and"],
            "aragon": ["aragón", "aragon", "ara"],
            "asturias": ["asturias", "principado de asturias", "ast"],
            "baleares": ["islas baleares", "baleares", "illes balears", "ib"],
            "canarias": ["canarias", "islas canarias", "can"],
            "cantabria": ["cantabria", "cant"],
            "castilla_leon": ["castilla y león", "castilla y leon", "cyl"],
            "castilla_mancha":
            ["castilla-la mancha", "castilla la mancha", "clm"],
            "cataluna": ["cataluña", "catalunya", "cataluna", "cat"],
            "ceuta": ["ceuta"],
            "extremadura": ["extremadura", "ext"],
            "galicia": ["galicia", "gal"],
            "la_rioja_esp": ["la rioja", "rioja"],
            "madrid": ["madrid", "comunidad de madrid", "mad"],
            "melilla": ["melilla"],
            "murcia": ["región de murcia", "murcia", "mur"],
            "navarra": ["navarra", "comunidad foral de navarra", "nav"],
            "pais_vasco": ["país vasco", "euskadi", "pais vasco", "pv"],
            "valencia":
            ["comunidad valenciana", "valencia", "país valenciano", "val"],
        },
        "ciudades": {
            "madrid_ciudad": ["madrid"],
            "barcelona": ["barcelona", "bcn"],
            "valencia_ciudad": ["valencia", "valència"],
            "sevilla": ["sevilla"],
            "zaragoza": ["zaragoza"],
            "malaga": ["málaga", "malaga"],
            "murcia_ciudad": ["murcia"],
            "palma": ["palma de mallorca", "palma"],
            "las_palmas": ["las palmas de gran canaria", "las palmas"],
            "bilbao": ["bilbao"],
            "alicante": ["alicante", "alacant"],
            "cordoba_esp": ["córdoba", "cordoba"],
            "valladolid": ["valladolid"],
            "vigo": ["vigo"],
            "gijon": ["gijón", "gijon"],
            "la_coruna": ["a coruña", "la coruña"],
            "granada": ["granada"],
            "vitoria": ["vitoria-gasteiz", "vitoria"],
            "elche": ["elche", "elx"],
            "oviedo": ["oviedo"],
            "santa_cruz_tenerife": ["santa cruz de tenerife"],
            "pamplona": ["pamplona", "iruña"],
            "almeria": ["almería", "almeria"],
            "san_sebastian": ["san sebastián", "donostia", "san sebastian"],
            "santander": ["santander"],
            "burgos": ["burgos"],
            "albacete": ["albacete"],
            "logrono": ["logroño", "logrono"],
            "salamanca": ["salamanca"],
            "badajoz": ["badajoz"],
            "huelva": ["huelva"],
            "lleida": ["lleida", "lérida", "lerida"],
            "tarragona": ["tarragona"],
            "leon_esp": ["león", "leon"],
            "cadiz": ["cádiz", "cadiz"],
            "marbella": ["marbella"],
            "jaen": ["jaén", "jaen"],
            "girona": ["girona", "gerona"],
            "santiago_compostela": ["santiago de compostela"],
            "toledo": ["toledo"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # COLOMBIA - 33 DEPARTAMENTOS + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "colombia": {
        "departamentos": {
            "amazonas_col": ["amazonas"],
            "antioquia": ["antioquia", "ant"],
            "arauca": ["arauca"],
            "atlantico": ["atlántico", "atlantico", "atl"],
            "bolivar_col": ["bolívar", "bolivar", "bol"],
            "boyaca": ["boyacá", "boyaca", "boy"],
            "caldas": ["caldas", "cal"],
            "caqueta": ["caquetá", "caqueta"],
            "casanare": ["casanare"],
            "cauca": ["cauca"],
            "cesar": ["cesar", "ces"],
            "choco": ["chocó", "choco"],
            "cordoba_col": ["córdoba", "cordoba"],
            "cundinamarca": ["cundinamarca", "cund"],
            "guainia": ["guainía", "guainia"],
            "guaviare": ["guaviare"],
            "huila": ["huila"],
            "la_guajira": ["la guajira", "guajira"],
            "magdalena": ["magdalena", "mag"],
            "meta": ["meta"],
            "narino": ["nariño", "narino"],
            "norte_santander": ["norte de santander", "n santander"],
            "putumayo": ["putumayo"],
            "quindio": ["quindío", "quindio"],
            "risaralda": ["risaralda"],
            "san_andres": ["san andrés y providencia", "san andres"],
            "santander": ["santander", "sant"],
            "sucre": ["sucre"],
            "tolima": ["tolima", "tol"],
            "valle_cauca": ["valle del cauca", "valle"],
            "vaupes": ["vaupés", "vaupes"],
            "vichada": ["vichada"],
            "bogota_dc":
            ["bogotá d.c.", "bogota", "bogotá", "distrito capital"],
        },
        "ciudades": {
            "bogota": ["bogotá", "bogota"],
            "medellin": ["medellín", "medellin"],
            "cali": ["cali"],
            "barranquilla": ["barranquilla"],
            "cartagena_col": ["cartagena"],
            "cucuta": ["cúcuta", "cucuta"],
            "bucaramanga": ["bucaramanga"],
            "pereira": ["pereira"],
            "santa_marta": ["santa marta"],
            "ibague": ["ibagué", "ibague"],
            "villavicencio": ["villavicencio"],
            "manizales": ["manizales"],
            "pasto": ["pasto"],
            "neiva": ["neiva"],
            "armenia": ["armenia"],
            "soacha": ["soacha"],
            "valledupar": ["valledupar"],
            "monteria": ["montería", "monteria"],
            "sincelejo": ["sincelejo"],
            "popayan": ["popayán", "popayan"],
            "floridablanca": ["floridablanca"],
            "palmira": ["palmira"],
            "buenaventura": ["buenaventura"],
            "tunja": ["tunja"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CHILE - 16 REGIONES + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "chile": {
        "regiones": {
            "arica_parinacota":
            ["arica y parinacota", "xv región", "xv region"],
            "tarapaca": ["tarapacá", "tarapaca", "i región", "i region"],
            "antofagasta_reg": ["antofagasta", "ii región", "ii region"],
            "atacama": ["atacama", "iii región", "iii region"],
            "coquimbo_reg": ["coquimbo", "iv región", "iv region"],
            "valparaiso_reg":
            ["valparaíso", "valparaiso", "v región", "v region"],
            "metropolitana":
            ["metropolitana", "región metropolitana", "rm", "santiago"],
            "ohiggins": ["o'higgins", "ohiggins", "vi región", "vi region"],
            "maule": ["maule", "vii región", "vii region"],
            "nuble": ["ñuble", "nuble", "xvi región"],
            "biobio": ["biobío", "biobio", "viii región", "viii region"],
            "araucania": ["araucanía", "araucania", "ix región", "ix region"],
            "los_rios": ["los ríos", "los rios", "xiv región"],
            "los_lagos": ["los lagos", "x región", "x region"],
            "aysen": ["aysén", "aysen", "xi región", "xi region"],
            "magallanes": ["magallanes", "xii región", "xii region"],
        },
        "ciudades": {
            "santiago": ["santiago", "santiago de chile", "stgo"],
            "puente_alto": ["puente alto"],
            "maipu_cl": ["maipú", "maipu"],
            "la_florida": ["la florida"],
            "antofagasta_ciudad": ["antofagasta"],
            "vina_mar": ["viña del mar", "vina del mar"],
            "valparaiso_ciudad": ["valparaíso", "valparaiso"],
            "san_bernardo": ["san bernardo"],
            "temuco": ["temuco"],
            "las_condes": ["las condes"],
            "iquique": ["iquique"],
            "concepcion_cl": ["concepción", "concepcion"],
            "rancagua": ["rancagua"],
            "talca": ["talca"],
            "arica": ["arica"],
            "coquimbo_ciudad": ["coquimbo"],
            "la_serena": ["la serena"],
            "puerto_montt": ["puerto montt"],
            "chillan": ["chillán", "chillan"],
            "talcahuano": ["talcahuano"],
            "osorno": ["osorno"],
            "valdivia": ["valdivia"],
            "calama": ["calama"],
            "copiapo": ["copiapó", "copiapo"],
            "los_angeles_cl": ["los ángeles", "los angeles"],
            "punta_arenas": ["punta arenas"],
            "curico": ["curicó", "curico"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PERÚ - 25 DEPARTAMENTOS + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "peru": {
        "departamentos": {
            "amazonas_pe": ["amazonas"],
            "ancash": ["áncash", "ancash"],
            "apurimac": ["apurímac", "apurimac"],
            "arequipa_dep": ["arequipa"],
            "ayacucho": ["ayacucho"],
            "cajamarca": ["cajamarca"],
            "callao": ["callao", "provincia constitucional del callao"],
            "cusco": ["cusco", "cuzco"],
            "huancavelica": ["huancavelica"],
            "huanuco": ["huánuco", "huanuco"],
            "ica": ["ica"],
            "junin": ["junín", "junin"],
            "la_libertad": ["la libertad"],
            "lambayeque": ["lambayeque"],
            "lima_dep": ["lima"],
            "loreto": ["loreto"],
            "madre_dios": ["madre de dios"],
            "moquegua": ["moquegua"],
            "pasco": ["pasco"],
            "piura_dep": ["piura"],
            "puno_dep": ["puno"],
            "san_martin_pe": ["san martín", "san martin"],
            "tacna_dep": ["tacna"],
            "tumbes": ["tumbes"],
            "ucayali": ["ucayali"],
        },
        "ciudades": {
            "lima_ciudad": ["lima"],
            "arequipa_ciudad": ["arequipa"],
            "trujillo": ["trujillo"],
            "chiclayo": ["chiclayo"],
            "piura_ciudad": ["piura"],
            "iquitos": ["iquitos"],
            "cusco_ciudad": ["cusco", "cuzco"],
            "chimbote": ["chimbote"],
            "huancayo": ["huancayo"],
            "tacna_ciudad": ["tacna"],
            "pucallpa": ["pucallpa"],
            "juliaca": ["juliaca"],
            "ica_ciudad": ["ica"],
            "cajamarca_ciudad": ["cajamarca"],
            "sullana": ["sullana"],
            "ayacucho_ciudad": ["ayacucho"],
            "huanuco_ciudad": ["huánuco", "huanuco"],
            "puno_ciudad": ["puno"],
            "tarapoto": ["tarapoto"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # USA - 50 ESTADOS + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "usa": {
        "estados": {
            "alabama": ["alabama", "al"],
            "alaska": ["alaska", "ak"],
            "arizona": ["arizona", "az"],
            "arkansas": ["arkansas", "ar"],
            "california": ["california", "ca", "calif"],
            "colorado": ["colorado", "co"],
            "connecticut": ["connecticut", "ct", "conn"],
            "delaware": ["delaware", "de"],
            "florida": ["florida", "fl", "fla"],
            "georgia_us": ["georgia", "ga"],
            "hawaii": ["hawaii", "hi"],
            "idaho": ["idaho", "id"],
            "illinois": ["illinois", "il"],
            "indiana": ["indiana", "in"],
            "iowa": ["iowa", "ia"],
            "kansas": ["kansas", "ks"],
            "kentucky": ["kentucky", "ky"],
            "louisiana": ["louisiana", "la"],
            "maine": ["maine", "me"],
            "maryland": ["maryland", "md"],
            "massachusetts": ["massachusetts", "ma", "mass"],
            "michigan": ["michigan", "mi", "mich"],
            "minnesota": ["minnesota", "mn", "minn"],
            "mississippi": ["mississippi", "ms", "miss"],
            "missouri": ["missouri", "mo"],
            "montana": ["montana", "mt"],
            "nebraska": ["nebraska", "ne"],
            "nevada": ["nevada", "nv"],
            "new_hampshire": ["new hampshire", "nh"],
            "new_jersey": ["new jersey", "nj"],
            "new_mexico": ["new mexico", "nm"],
            "new_york_state": ["new york", "ny"],
            "north_carolina": ["north carolina", "nc"],
            "north_dakota": ["north dakota", "nd"],
            "ohio": ["ohio", "oh"],
            "oklahoma": ["oklahoma", "ok"],
            "oregon": ["oregon", "or"],
            "pennsylvania": ["pennsylvania", "pa", "penn"],
            "rhode_island": ["rhode island", "ri"],
            "south_carolina": ["south carolina", "sc"],
            "south_dakota": ["south dakota", "sd"],
            "tennessee": ["tennessee", "tn", "tenn"],
            "texas": ["texas", "tx"],
            "utah": ["utah", "ut"],
            "vermont": ["vermont", "vt"],
            "virginia": ["virginia", "va"],
            "washington_state": ["washington", "wa", "wash"],
            "west_virginia": ["west virginia", "wv"],
            "wisconsin": ["wisconsin", "wi", "wis"],
            "wyoming": ["wyoming", "wy"],
            "dc": ["district of columbia", "dc", "d.c.", "washington dc"],
        },
        "ciudades": {
            "new_york": ["new york city", "nyc", "new york", "manhattan"],
            "los_angeles": ["los angeles", "la", "l.a."],
            "chicago": ["chicago", "chi"],
            "houston": ["houston"],
            "phoenix": ["phoenix"],
            "philadelphia": ["philadelphia", "philly"],
            "san_antonio": ["san antonio"],
            "san_diego": ["san diego"],
            "dallas": ["dallas"],
            "san_jose": ["san jose"],
            "austin": ["austin"],
            "jacksonville": ["jacksonville"],
            "fort_worth": ["fort worth"],
            "columbus": ["columbus"],
            "charlotte": ["charlotte"],
            "san_francisco": ["san francisco", "sf"],
            "indianapolis": ["indianapolis"],
            "seattle": ["seattle"],
            "denver": ["denver"],
            "washington_dc": ["washington", "washington dc"],
            "boston": ["boston"],
            "el_paso": ["el paso"],
            "nashville": ["nashville"],
            "detroit": ["detroit"],
            "oklahoma_city": ["oklahoma city"],
            "portland": ["portland"],
            "las_vegas": ["las vegas", "vegas"],
            "memphis": ["memphis"],
            "louisville": ["louisville"],
            "baltimore": ["baltimore"],
            "milwaukee": ["milwaukee"],
            "albuquerque": ["albuquerque"],
            "tucson": ["tucson"],
            "fresno": ["fresno"],
            "sacramento": ["sacramento"],
            "atlanta": ["atlanta", "atl"],
            "miami": ["miami"],
            "oakland": ["oakland"],
            "minneapolis": ["minneapolis"],
            "cleveland": ["cleveland"],
            "tampa": ["tampa"],
            "new_orleans": ["new orleans", "nola"],
            "pittsburgh": ["pittsburgh"],
            "st_louis": ["st. louis", "st louis", "saint louis"],
            "cincinnati": ["cincinnati"],
            "orlando": ["orlando"],
            "salt_lake_city": ["salt lake city", "slc"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # BRASIL - 27 ESTADOS + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "brasil": {
        "estados": {
            "acre": ["acre", "ac"],
            "alagoas": ["alagoas", "al"],
            "amapa": ["amapá", "amapa", "ap"],
            "amazonas_br": ["amazonas", "am"],
            "bahia": ["bahia", "ba"],
            "ceara": ["ceará", "ceara", "ce"],
            "distrito_federal":
            ["distrito federal", "df", "brasília", "brasilia"],
            "espirito_santo": ["espírito santo", "espirito santo", "es"],
            "goias": ["goiás", "goias", "go"],
            "maranhao": ["maranhão", "maranhao", "ma"],
            "mato_grosso": ["mato grosso", "mt"],
            "mato_grosso_sul": ["mato grosso do sul", "ms"],
            "minas_gerais": ["minas gerais", "mg"],
            "para": ["pará", "para", "pa"],
            "paraiba": ["paraíba", "paraiba", "pb"],
            "parana": ["paraná", "parana", "pr"],
            "pernambuco": ["pernambuco", "pe"],
            "piaui": ["piauí", "piaui", "pi"],
            "rio_janeiro": ["rio de janeiro", "rj"],
            "rio_grande_norte": ["rio grande do norte", "rn"],
            "rio_grande_sul": ["rio grande do sul", "rs"],
            "rondonia": ["rondônia", "rondonia", "ro"],
            "roraima": ["roraima", "rr"],
            "santa_catarina": ["santa catarina", "sc"],
            "sao_paulo_estado": ["são paulo", "sao paulo", "sp"],
            "sergipe": ["sergipe", "se"],
            "tocantins": ["tocantins", "to"],
        },
        "ciudades": {
            "sao_paulo_ciudad": ["são paulo", "sao paulo", "sp"],
            "rio_janeiro_ciudad": ["rio de janeiro", "rio"],
            "brasilia": ["brasília", "brasilia"],
            "salvador": ["salvador"],
            "fortaleza": ["fortaleza"],
            "belo_horizonte": ["belo horizonte", "bh"],
            "manaus": ["manaus"],
            "curitiba": ["curitiba"],
            "recife": ["recife"],
            "porto_alegre": ["porto alegre", "poa"],
            "goiania": ["goiânia", "goiania"],
            "belem": ["belém", "belem"],
            "guarulhos": ["guarulhos"],
            "campinas": ["campinas"],
            "sao_luis": ["são luís", "sao luis"],
            "maceio": ["maceió", "maceio"],
            "natal": ["natal"],
            "teresina": ["teresina"],
            "campo_grande": ["campo grande"],
            "joao_pessoa": ["joão pessoa", "joao pessoa"],
            "santo_andre": ["santo andré", "santo andre"],
            "ribeirao_preto": ["ribeirão preto", "ribeirao preto"],
            "uberlandia": ["uberlândia", "uberlandia"],
            "sorocaba": ["sorocaba"],
            "aracaju": ["aracaju"],
            "feira_santana": ["feira de santana"],
            "cuiaba": ["cuiabá", "cuiaba"],
            "joinville": ["joinville"],
            "londrina": ["londrina"],
            "juiz_fora": ["juiz de fora"],
            "florianopolis": ["florianópolis", "florianopolis", "floripa"],
            "santos": ["santos"],
            "vitoria_br": ["vitória", "vitoria"],
            "porto_velho": ["porto velho"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # OTROS PAÍSES LATINOAMERICANOS
    # ═══════════════════════════════════════════════════════════════════════════
    "venezuela": {
        "estados": {
            "amazonas_ve": ["amazonas"],
            "anzoategui": ["anzoátegui", "anzoategui"],
            "apure": ["apure"],
            "aragua": ["aragua"],
            "barinas": ["barinas"],
            "bolivar_ve": ["bolívar", "bolivar"],
            "carabobo": ["carabobo"],
            "cojedes": ["cojedes"],
            "delta_amacuro": ["delta amacuro"],
            "distrito_capital": ["distrito capital", "caracas"],
            "falcon": ["falcón", "falcon"],
            "guarico": ["guárico", "guarico"],
            "lara": ["lara"],
            "merida_ve": ["mérida", "merida"],
            "miranda": ["miranda"],
            "monagas": ["monagas"],
            "nueva_esparta": ["nueva esparta"],
            "portuguesa": ["portuguesa"],
            "sucre_ve": ["sucre"],
            "tachira": ["táchira", "tachira"],
            "trujillo": ["trujillo"],
            "vargas": ["vargas", "la guaira"],
            "yaracuy": ["yaracuy"],
            "zulia": ["zulia"],
        },
        "ciudades": {
            "caracas": ["caracas"],
            "maracaibo": ["maracaibo"],
            "valencia_ve": ["valencia"],
            "barquisimeto": ["barquisimeto"],
            "maracay": ["maracay"],
            "ciudad_guayana": ["ciudad guayana"],
            "san_cristobal": ["san cristóbal", "san cristobal"],
            "maturin": ["maturín", "maturin"],
            "barcelona_ve": ["barcelona"],
            "cumana": ["cumaná", "cumana"],
            "puerto_la_cruz": ["puerto la cruz"],
            "merida_ciudad": ["mérida", "merida"],
            "cabimas": ["cabimas"],
            "barinas_ciudad": ["barinas"],
            "punto_fijo": ["punto fijo"],
            "los_teques": ["los teques"],
            "ciudad_bolivar": ["ciudad bolívar", "ciudad bolivar"],
            "guarenas": ["guarenas"],
            "turmero": ["turmero"],
            "acarigua": ["acarigua"],
            "valera": ["valera"],
            "coro": ["coro"],
        }
    },
    "ecuador": {
        "provincias": {
            "azuay": ["azuay"],
            "bolivar_ec": ["bolívar", "bolivar"],
            "canar": ["cañar", "canar"],
            "carchi": ["carchi"],
            "chimborazo": ["chimborazo"],
            "cotopaxi": ["cotopaxi"],
            "el_oro": ["el oro"],
            "esmeraldas": ["esmeraldas"],
            "galapagos": ["galápagos", "galapagos"],
            "guayas": ["guayas"],
            "imbabura": ["imbabura"],
            "loja": ["loja"],
            "los_rios_ec": ["los ríos", "los rios"],
            "manabi": ["manabí", "manabi"],
            "morona_santiago": ["morona santiago"],
            "napo": ["napo"],
            "orellana": ["orellana"],
            "pastaza": ["pastaza"],
            "pichincha": ["pichincha"],
            "santa_elena": ["santa elena"],
            "santo_domingo": ["santo domingo de los tsáchilas"],
            "sucumbios": ["sucumbíos", "sucumbios"],
            "tungurahua": ["tungurahua"],
            "zamora_chinchipe": ["zamora chinchipe"],
        },
        "ciudades": {
            "quito": ["quito"],
            "guayaquil": ["guayaquil"],
            "cuenca": ["cuenca"],
            "santo_domingo_ciudad": ["santo domingo"],
            "ambato": ["ambato"],
            "portoviejo": ["portoviejo"],
            "machala": ["machala"],
            "duran": ["durán", "duran"],
            "manta": ["manta"],
            "loja_ciudad": ["loja"],
            "riobamba": ["riobamba"],
            "esmeraldas_ciudad": ["esmeraldas"],
            "quevedo": ["quevedo"],
            "ibarra": ["ibarra"],
            "latacunga": ["latacunga"],
            "milagro": ["milagro"],
            "tulcan": ["tulcán", "tulcan"],
            "babahoyo": ["babahoyo"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # BOLIVIA - 9 DEPARTAMENTOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "bolivia": {
        "departamentos": {
            "chuquisaca": ["chuquisaca"],
            "cochabamba": ["cochabamba", "cbba"],
            "beni": ["beni"],
            "la_paz_bo": ["la paz"],
            "oruro": ["oruro"],
            "pando": ["pando"],
            "potosi": ["potosí", "potosi"],
            "santa_cruz_bo": ["santa cruz"],
            "tarija": ["tarija"],
        },
        "ciudades": {
            "la_paz_ciudad": ["la paz"],
            "santa_cruz_ciudad": ["santa cruz de la sierra", "santa cruz"],
            "cochabamba_ciudad": ["cochabamba"],
            "sucre": ["sucre"],
            "oruro_ciudad": ["oruro"],
            "tarija_ciudad": ["tarija"],
            "potosi_ciudad": ["potosí", "potosi"],
            "sacaba": ["sacaba"],
            "quillacollo": ["quillacollo"],
            "montero": ["montero"],
            "trinidad": ["trinidad"],
            "warnes": ["warnes"],
            "yacuiba": ["yacuiba"],
            "riberalta": ["riberalta"],
            "el_alto": ["el alto"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PARAGUAY - 17 DEPARTAMENTOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "paraguay": {
        "departamentos": {
            "alto_paraguay": ["alto paraguay"],
            "alto_parana": ["alto paraná", "alto parana"],
            "amambay": ["amambay"],
            "boqueron": ["boquerón", "boqueron"],
            "caaguazu": ["caaguazú", "caaguazu"],
            "caazapa": ["caazapá", "caazapa"],
            "canindeyu": ["canindeyú", "canindeyu"],
            "central_py": ["central"],
            "concepcion_py": ["concepción", "concepcion"],
            "cordillera": ["cordillera"],
            "guaira": ["guairá", "guaira"],
            "itapua": ["itapúa", "itapua"],
            "misiones_py": ["misiones"],
            "neembucu": ["ñeembucú", "neembucu"],
            "paraguari": ["paraguarí", "paraguari"],
            "presidente_hayes": ["presidente hayes"],
            "san_pedro_py": ["san pedro"],
            "asuncion_dep": ["asunción", "asuncion", "distrito capital"],
        },
        "ciudades": {
            "asuncion": ["asunción", "asuncion"],
            "ciudad_este": ["ciudad del este"],
            "san_lorenzo": ["san lorenzo"],
            "luque": ["luque"],
            "capiata": ["capiatá", "capiata"],
            "lambare": ["lambaré", "lambare"],
            "fernando_mora": ["fernando de la mora"],
            "limpio": ["limpio"],
            "nemby": ["ñemby", "nemby"],
            "encarnacion": ["encarnación", "encarnacion"],
            "mariano_alonso": ["mariano roque alonso"],
            "pedro_caballero": ["pedro juan caballero"],
            "villa_elisa": ["villa elisa"],
            "caaguazu_ciudad": ["caaguazú", "caaguazu"],
            "coronel_oviedo": ["coronel oviedo"],
            "presidente_franco": ["presidente franco"],
            "itaugua": ["itauguá", "itaugua"],
            "villeta": ["villeta"],
            "caacupe": ["caacupé", "caacupe"],
            "concepcion_ciudad_py": ["concepción", "concepcion"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # URUGUAY - 19 DEPARTAMENTOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "uruguay": {
        "departamentos": {
            "artigas": ["artigas"],
            "canelones": ["canelones"],
            "cerro_largo": ["cerro largo"],
            "colonia": ["colonia"],
            "durazno": ["durazno"],
            "flores": ["flores"],
            "florida_uy": ["florida"],
            "lavalleja": ["lavalleja"],
            "maldonado": ["maldonado"],
            "montevideo": ["montevideo", "mdeo"],
            "paysandu": ["paysandú", "paysandu"],
            "rio_negro_uy": ["río negro", "rio negro"],
            "rivera": ["rivera"],
            "rocha": ["rocha"],
            "salto_uy": ["salto"],
            "san_jose_uy": ["san josé", "san jose"],
            "soriano": ["soriano"],
            "tacuarembo": ["tacuarembó", "tacuarembo"],
            "treinta_tres": ["treinta y tres"],
        },
        "ciudades": {
            "montevideo_ciudad": ["montevideo"],
            "salto_ciudad": ["salto"],
            "ciudad_costa": ["ciudad de la costa"],
            "paysandu_ciudad": ["paysandú", "paysandu"],
            "las_piedras": ["las piedras"],
            "rivera_ciudad": ["rivera"],
            "maldonado_ciudad": ["maldonado"],
            "tacuarembo_ciudad": ["tacuarembó", "tacuarembo"],
            "melo": ["melo"],
            "mercedes_uy": ["mercedes"],
            "artigas_ciudad": ["artigas"],
            "minas": ["minas"],
            "san_jose_ciudad": ["san josé de mayo", "san jose de mayo"],
            "durazno_ciudad": ["durazno"],
            "florida_ciudad": ["florida"],
            "treinta_tres_ciudad": ["treinta y tres"],
            "rocha_ciudad": ["rocha"],
            "colonia_sacramento": ["colonia del sacramento", "colonia"],
            "punta_este": ["punta del este"],
            "fray_bentos": ["fray bentos"],
            "carmelo": ["carmelo"],
            "dolores_uy": ["dolores"],
            "young": ["young"],
            "nueva_helvecia": ["nueva helvecia"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # GUATEMALA - 22 DEPARTAMENTOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "guatemala": {
        "departamentos": {
            "alta_verapaz": ["alta verapaz"],
            "baja_verapaz": ["baja verapaz"],
            "chimaltenango": ["chimaltenango"],
            "chiquimula": ["chiquimula"],
            "el_progreso": ["el progreso"],
            "escuintla": ["escuintla"],
            "guatemala_dep": ["guatemala"],
            "huehuetenango": ["huehuetenango"],
            "izabal": ["izabal"],
            "jalapa": ["jalapa"],
            "jutiapa": ["jutiapa"],
            "peten": ["petén", "peten"],
            "quetzaltenango": ["quetzaltenango", "xela"],
            "quiche": ["quiché", "quiche"],
            "retalhuleu": ["retalhuleu"],
            "sacatepequez": ["sacatepéquez", "sacatepequez"],
            "san_marcos_gt": ["san marcos"],
            "santa_rosa_gt": ["santa rosa"],
            "solola": ["sololá", "solola"],
            "suchitepequez": ["suchitepéquez", "suchitepequez"],
            "totonicapan": ["totonicapán", "totonicapan"],
            "zacapa": ["zacapa"],
        },
        "ciudades": {
            "guatemala_ciudad":
            ["ciudad de guatemala", "guatemala city", "guatemala"],
            "mixco": ["mixco"],
            "villa_nueva_gt": ["villa nueva"],
            "quetzaltenango_ciudad": ["quetzaltenango", "xela"],
            "san_juan_sacatepequez": ["san juan sacatepéquez"],
            "petapa": ["petapa"],
            "escuintla_ciudad": ["escuintla"],
            "chinautla": ["chinautla"],
            "chimaltenango_ciudad": ["chimaltenango"],
            "huehuetenango_ciudad": ["huehuetenango"],
            "amatitlan": ["amatitlán", "amatitlan"],
            "coban": ["cobán", "coban"],
            "jalapa_ciudad": ["jalapa"],
            "puerto_barrios": ["puerto barrios"],
            "santa_lucia_cotzumalguapa": ["santa lucía cotzumalguapa"],
            "antigua_guatemala": ["antigua guatemala", "antigua"],
            "chiquimula_ciudad": ["chiquimula"],
            "zacapa_ciudad": ["zacapa"],
            "mazatenango": ["mazatenango"],
            "retalhuleu_ciudad": ["retalhuleu"],
            "solola_ciudad": ["sololá", "solola"],
            "flores_peten": ["flores"],
            "tikal": ["tikal"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # HONDURAS - 18 DEPARTAMENTOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "honduras": {
        "departamentos": {
            "atlantida": ["atlántida", "atlantida"],
            "choluteca": ["choluteca"],
            "colon_hn": ["colón", "colon"],
            "comayagua": ["comayagua"],
            "copan": ["copán", "copan"],
            "cortes": ["cortés", "cortes"],
            "el_paraiso": ["el paraíso", "el paraiso"],
            "francisco_morazan": ["francisco morazán", "francisco morazan"],
            "gracias_dios": ["gracias a dios"],
            "intibuca": ["intibucá", "intibuca"],
            "islas_bahia": ["islas de la bahía", "islas de la bahia"],
            "la_paz_hn": ["la paz"],
            "lempira": ["lempira"],
            "ocotepeque": ["ocotepeque"],
            "olancho": ["olancho"],
            "santa_barbara_hn": ["santa bárbara", "santa barbara"],
            "valle_hn": ["valle"],
            "yoro": ["yoro"],
        },
        "ciudades": {
            "tegucigalpa": ["tegucigalpa", "tegus"],
            "san_pedro_sula": ["san pedro sula", "sps"],
            "choloma": ["choloma"],
            "la_ceiba": ["la ceiba"],
            "el_progreso_hn": ["el progreso"],
            "choluteca_ciudad": ["choluteca"],
            "comayagua_ciudad": ["comayagua"],
            "puerto_cortes": ["puerto cortés", "puerto cortes"],
            "la_lima": ["la lima"],
            "danli": ["danlí", "danli"],
            "siguatepeque": ["siguatepeque"],
            "juticalpa": ["juticalpa"],
            "villanueva_hn": ["villanueva"],
            "tocoa": ["tocoa"],
            "tela": ["tela"],
            "santa_rosa_copan": ["santa rosa de copán", "santa rosa de copan"],
            "roatan": ["roatán", "roatan"],
            "copan_ruinas": ["copán ruinas", "copan ruinas"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # EL SALVADOR - 14 DEPARTAMENTOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "el_salvador": {
        "departamentos": {
            "ahuachapan": ["ahuachapán", "ahuachapan"],
            "cabanas": ["cabañas", "cabanas"],
            "chalatenango": ["chalatenango"],
            "cuscatlan": ["cuscatlán", "cuscatlan"],
            "la_libertad_sv": ["la libertad"],
            "la_paz_sv": ["la paz"],
            "la_union": ["la unión", "la union"],
            "morazan": ["morazán", "morazan"],
            "san_miguel_sv": ["san miguel"],
            "san_salvador": ["san salvador"],
            "san_vicente": ["san vicente"],
            "santa_ana_sv": ["santa ana"],
            "sonsonate": ["sonsonate"],
            "usulutan": ["usulután", "usulutan"],
        },
        "ciudades": {
            "san_salvador_ciudad": ["san salvador"],
            "santa_ana_ciudad": ["santa ana"],
            "san_miguel_ciudad": ["san miguel"],
            "mejicanos": ["mejicanos"],
            "santa_tecla": ["santa tecla", "nueva san salvador"],
            "apopa": ["apopa"],
            "soyapango": ["soyapango"],
            "delgado": ["delgado", "ciudad delgado"],
            "ilopango": ["ilopango"],
            "sonsonate_ciudad": ["sonsonate"],
            "usulutan_ciudad": ["usulután", "usulutan"],
            "ahuachapan_ciudad": ["ahuachapán", "ahuachapan"],
            "cojutepeque": ["cojutepeque"],
            "zacatecoluca": ["zacatecoluca"],
            "chalatenango_ciudad": ["chalatenango"],
            "la_libertad_ciudad": ["la libertad"],
            "san_vicente_ciudad": ["san vicente"],
            "sensuntepeque": ["sensuntepeque"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # NICARAGUA - 15 DEPARTAMENTOS + 2 REGIONES AUTÓNOMAS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "nicaragua": {
        "departamentos": {
            "boaco": ["boaco"],
            "carazo": ["carazo"],
            "chinandega": ["chinandega"],
            "chontales": ["chontales"],
            "esteli": ["estelí", "esteli"],
            "granada_ni": ["granada"],
            "jinotega": ["jinotega"],
            "leon_ni": ["león", "leon"],
            "madriz": ["madriz"],
            "managua_dep": ["managua"],
            "masaya_dep": ["masaya"],
            "matagalpa": ["matagalpa"],
            "nueva_segovia": ["nueva segovia"],
            "rivas": ["rivas"],
            "rio_san_juan": ["río san juan", "rio san juan"],
            "raccn": [
                "raccn", "región autónoma costa caribe norte", "raan",
                "atlántico norte"
            ],
            "raccs": [
                "raccs", "región autónoma costa caribe sur", "raas",
                "atlántico sur"
            ],
        },
        "ciudades": {
            "managua": ["managua"],
            "leon_ciudad": ["león", "leon"],
            "masaya": ["masaya"],
            "tipitapa": ["tipitapa"],
            "chinandega_ciudad": ["chinandega"],
            "matagalpa_ciudad": ["matagalpa"],
            "esteli_ciudad": ["estelí", "esteli"],
            "granada_ciudad": ["granada"],
            "ciudad_sandino": ["ciudad sandino"],
            "jinotega_ciudad": ["jinotega"],
            "juigalpa": ["juigalpa"],
            "el_viejo": ["el viejo"],
            "bluefields": ["bluefields"],
            "puerto_cabezas": ["puerto cabezas", "bilwi"],
            "rivas_ciudad": ["rivas"],
            "ocotal": ["ocotal"],
            "somoto": ["somoto"],
            "boaco_ciudad": ["boaco"],
            "diriamba": ["diriamba"],
            "jinotepe": ["jinotepe"],
            "san_juan_sur": ["san juan del sur"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # COSTA RICA - 7 PROVINCIAS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "costa_rica": {
        "provincias": {
            "alajuela": ["alajuela"],
            "cartago_cr": ["cartago"],
            "guanacaste": ["guanacaste"],
            "heredia": ["heredia"],
            "limon": ["limón", "limon"],
            "puntarenas": ["puntarenas"],
            "san_jose_cr": ["san josé", "san jose"],
        },
        "ciudades": {
            "san_jose_ciudad": ["san josé", "san jose"],
            "limon_ciudad": ["limón", "limon"],
            "alajuela_ciudad": ["alajuela"],
            "heredia_ciudad": ["heredia"],
            "puntarenas_ciudad": ["puntarenas"],
            "cartago_ciudad": ["cartago"],
            "liberia_cr": ["liberia"],
            "paraiso": ["paraíso", "paraiso"],
            "san_isidro_general":
            ["san isidro de el general", "pérez zeledón"],
            "curridabat": ["curridabat"],
            "san_francisco_heredia": ["san francisco"],
            "desamparados": ["desamparados"],
            "nicoya": ["nicoya"],
            "santa_cruz_cr": ["santa cruz"],
            "san_carlos_cr": ["san carlos", "ciudad quesada"],
            "turrialba": ["turrialba"],
            "grecia": ["grecia"],
            "san_ramon_cr": ["san ramón", "san ramon"],
            "puerto_limon": ["puerto limón", "puerto limon"],
            "tamarindo": ["tamarindo"],
            "jaco": ["jacó", "jaco"],
            "manuel_antonio": ["manuel antonio"],
            "monteverde": ["monteverde"],
            "la_fortuna": ["la fortuna"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PANAMÁ - 10 PROVINCIAS + 3 COMARCAS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "panama": {
        "provincias": {
            "bocas_toro": ["bocas del toro"],
            "chiriqui": ["chiriquí", "chiriqui"],
            "cocle": ["coclé", "cocle"],
            "colon_pa": ["colón", "colon"],
            "darien": ["darién", "darien"],
            "herrera": ["herrera"],
            "los_santos": ["los santos"],
            "panama_dep": ["panamá", "panama"],
            "panama_oeste": ["panamá oeste", "panama oeste"],
            "veraguas": ["veraguas"],
            "guna_yala": ["guna yala", "kuna yala", "san blas"],
            "embera_wounaan": ["emberá-wounaan", "embera wounaan"],
            "ngabe_bugle": ["ngäbe-buglé", "ngabe bugle"],
        },
        "ciudades": {
            "panama_ciudad": [
                "ciudad de panamá", "panamá city", "panama city", "panamá",
                "panama"
            ],
            "san_miguelito": ["san miguelito"],
            "juan_diaz": ["juan díaz", "juan diaz"],
            "david": ["david"],
            "arraijan": ["arraiján", "arraijan"],
            "colon_ciudad": ["colón", "colon"],
            "la_chorrera": ["la chorrera"],
            "tocumen": ["tocumen"],
            "santiago_veraguas": ["santiago"],
            "chitre": ["chitré", "chitre"],
            "las_tablas": ["las tablas"],
            "penonome": ["penonomé", "penonome"],
            "aguadulce": ["aguadulce"],
            "bocas_town": ["bocas town", "bocas del toro"],
            "boquete": ["boquete"],
            "volcan": ["volcán", "volcan"],
            "portobelo": ["portobelo"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CUBA - 15 PROVINCIAS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "cuba": {
        "provincias": {
            "pinar_rio": ["pinar del río", "pinar del rio"],
            "artemisa": ["artemisa"],
            "la_habana": ["la habana", "habana"],
            "mayabeque": ["mayabeque"],
            "matanzas": ["matanzas"],
            "cienfuegos": ["cienfuegos"],
            "villa_clara": ["villa clara"],
            "sancti_spiritus": ["sancti spíritus", "sancti spiritus"],
            "ciego_avila": ["ciego de ávila", "ciego de avila"],
            "camaguey": ["camagüey", "camaguey"],
            "las_tunas": ["las tunas"],
            "holguin": ["holguín", "holguin"],
            "granma": ["granma"],
            "santiago_cuba": ["santiago de cuba"],
            "guantanamo": ["guantánamo", "guantanamo"],
            "isla_juventud": ["isla de la juventud"],
        },
        "ciudades": {
            "habana_ciudad": ["la habana", "habana"],
            "santiago_cuba_ciudad": ["santiago de cuba"],
            "camaguey_ciudad": ["camagüey", "camaguey"],
            "holguin_ciudad": ["holguín", "holguin"],
            "guantanamo_ciudad": ["guantánamo", "guantanamo"],
            "santa_clara": ["santa clara"],
            "bayamo": ["bayamo"],
            "las_tunas_ciudad": ["las tunas"],
            "cienfuegos_ciudad": ["cienfuegos"],
            "pinar_rio_ciudad": ["pinar del río", "pinar del rio"],
            "matanzas_ciudad": ["matanzas"],
            "ciego_avila_ciudad": ["ciego de ávila", "ciego de avila"],
            "sancti_spiritus_ciudad": ["sancti spíritus", "sancti spiritus"],
            "manzanillo": ["manzanillo"],
            "cardenas": ["cárdenas", "cardenas"],
            "moron": ["morón", "moron"],
            "nuevitas": ["nuevitas"],
            "trinidad_cu": ["trinidad"],
            "varadero": ["varadero"],
            "vinales": ["viñales", "vinales"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # REPÚBLICA DOMINICANA - 31 PROVINCIAS + DN + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "dominicana": {
        "provincias": {
            "azua": ["azua"],
            "bahoruco": ["bahoruco"],
            "barahona": ["barahona"],
            "dajabon": ["dajabón", "dajabon"],
            "distrito_nacional": ["distrito nacional", "dn", "santo domingo"],
            "duarte": ["duarte"],
            "el_seibo": ["el seibo"],
            "elias_pina": ["elías piña", "elias pina"],
            "espaillat": ["espaillat"],
            "hato_mayor": ["hato mayor"],
            "hermanas_mirabal": ["hermanas mirabal", "salcedo"],
            "independencia": ["independencia"],
            "la_altagracia": ["la altagracia"],
            "la_romana": ["la romana"],
            "la_vega": ["la vega"],
            "maria_trinidad_sanchez":
            ["maría trinidad sánchez", "maria trinidad sanchez"],
            "monsenor_nouel": ["monseñor nouel", "monsenor nouel"],
            "monte_cristi": ["monte cristi", "montecristi"],
            "monte_plata": ["monte plata"],
            "pedernales": ["pedernales"],
            "peravia": ["peravia"],
            "puerto_plata": ["puerto plata"],
            "samana": ["samaná", "samana"],
            "san_cristobal_rd": ["san cristóbal", "san cristobal"],
            "san_jose_ocoa": ["san josé de ocoa", "san jose de ocoa"],
            "san_juan_rd": ["san juan"],
            "san_pedro_macoris":
            ["san pedro de macorís", "san pedro de macoris"],
            "sanchez_ramirez": ["sánchez ramírez", "sanchez ramirez"],
            "santiago_rd": ["santiago"],
            "santiago_rodriguez": ["santiago rodríguez", "santiago rodriguez"],
            "santo_domingo_prov": ["santo domingo"],
            "valverde": ["valverde", "mao"],
        },
        "ciudades": {
            "santo_domingo": ["santo domingo"],
            "santiago_rd_ciudad": ["santiago de los caballeros", "santiago"],
            "santo_domingo_este": ["santo domingo este"],
            "santo_domingo_norte": ["santo domingo norte"],
            "santo_domingo_oeste": ["santo domingo oeste"],
            "san_pedro_macoris_ciudad":
            ["san pedro de macorís", "san pedro de macoris"],
            "la_romana_ciudad": ["la romana"],
            "san_cristobal_ciudad": ["san cristóbal", "san cristobal"],
            "puerto_plata_ciudad": ["puerto plata"],
            "san_francisco_macoris":
            ["san francisco de macorís", "san francisco de macoris"],
            "la_vega_ciudad": ["la vega"],
            "higuey": ["higüey", "higuey"],
            "moca": ["moca"],
            "bani": ["baní", "bani"],
            "bonao": ["bonao"],
            "azua_ciudad": ["azua"],
            "barahona_ciudad": ["barahona"],
            "nagua": ["nagua"],
            "cotui": ["cotuí", "cotui"],
            "punta_cana": ["punta cana"],
            "bavaro": ["bávaro", "bavaro"],
            "samana_ciudad": ["samaná", "samana"],
            "sosua": ["sosúa", "sosua"],
            "cabarete": ["cabarete"],
            "jarabacoa": ["jarabacoa"],
            "constanza": ["constanza"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PUERTO RICO - REGIONES + MUNICIPIOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "puerto_rico": {
        "regiones": {
            "area_metro":
            ["área metropolitana", "area metropolitana", "metro"],
            "norte": ["norte", "north"],
            "sur": ["sur", "south"],
            "este": ["este", "east"],
            "oeste": ["oeste", "west"],
            "centro": ["centro", "central"],
        },
        "ciudades": {
            "san_juan_pr": ["san juan"],
            "bayamon": ["bayamón", "bayamon"],
            "carolina": ["carolina"],
            "ponce": ["ponce"],
            "caguas": ["caguas"],
            "guaynabo": ["guaynabo"],
            "mayaguez": ["mayagüez", "mayaguez"],
            "toa_baja": ["toa baja"],
            "arecibo": ["arecibo"],
            "trujillo_alto": ["trujillo alto"],
            "fajardo": ["fajardo"],
            "humacao": ["humacao"],
            "aguadilla": ["aguadilla"],
            "vega_baja": ["vega baja"],
            "catano": ["cataño", "catano"],
            "isabela": ["isabela"],
            "rio_piedras": ["río piedras", "rio piedras"],
            "santurce": ["santurce"],
            "condado": ["condado"],
            "viejo_san_juan": ["viejo san juan"],
            "rincon": ["rincón", "rincon"],
            "cabo_rojo": ["cabo rojo"],
            "dorado": ["dorado"],
            "vieques": ["vieques"],
            "culebra": ["culebra"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PORTUGAL - 18 DISTRITOS + REGIONES AUTÓNOMAS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "portugal": {
        "distritos": {
            "aveiro": ["aveiro"],
            "beja": ["beja"],
            "braga": ["braga"],
            "braganca": ["bragança", "braganca"],
            "castelo_branco": ["castelo branco"],
            "coimbra": ["coimbra"],
            "evora": ["évora", "evora"],
            "faro": ["faro", "algarve"],
            "guarda": ["guarda"],
            "leiria": ["leiria"],
            "lisboa": ["lisboa", "lisbon"],
            "portalegre": ["portalegre"],
            "porto": ["porto", "oporto"],
            "santarem": ["santarém", "santarem"],
            "setubal": ["setúbal", "setubal"],
            "viana_castelo": ["viana do castelo"],
            "vila_real": ["vila real"],
            "viseu": ["viseu"],
            "acores": ["açores", "azores", "acores"],
            "madeira": ["madeira"],
        },
        "ciudades": {
            "lisboa_ciudad": ["lisboa", "lisbon"],
            "porto_ciudad": ["porto", "oporto"],
            "braga_ciudad": ["braga"],
            "amadora": ["amadora"],
            "almada": ["almada"],
            "coimbra_ciudad": ["coimbra"],
            "funchal": ["funchal"],
            "setubal_ciudad": ["setúbal", "setubal"],
            "agualva_cacem": ["agualva-cacém"],
            "queluz": ["queluz"],
            "vila_nova_gaia": ["vila nova de gaia", "gaia"],
            "loures": ["loures"],
            "guimaraes": ["guimarães", "guimaraes"],
            "rio_tinto": ["rio tinto"],
            "leiria_ciudad": ["leiria"],
            "matosinhos": ["matosinhos"],
            "aveiro_ciudad": ["aveiro"],
            "evora_ciudad": ["évora", "evora"],
            "faro_ciudad": ["faro"],
            "viseu_ciudad": ["viseu"],
            "viana_castelo_ciudad": ["viana do castelo"],
            "ponta_delgada": ["ponta delgada"],
            "sintra": ["sintra"],
            "cascais": ["cascais"],
            "lagos": ["lagos"],
            "albufeira": ["albufeira"],
            "portimao": ["portimão", "portimao"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ITALIA - 20 REGIONES + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "italia": {
        "regiones": {
            "abruzzo": ["abruzzo", "abruzos"],
            "basilicata": ["basilicata"],
            "calabria": ["calabria"],
            "campania": ["campania"],
            "emilia_romagna":
            ["emilia-romaña", "emilia romagna", "emilia-romagna"],
            "friuli": ["friuli-venezia giulia", "friuli"],
            "lazio": ["lazio", "lacio"],
            "liguria": ["liguria"],
            "lombardia": ["lombardía", "lombardia", "lombardy"],
            "marche": ["marche", "marcas"],
            "molise": ["molise"],
            "piemonte": ["piemonte", "piamonte", "piedmont"],
            "puglia": ["puglia", "apulia"],
            "sardegna": ["sardegna", "cerdeña", "sardinia"],
            "sicilia": ["sicilia", "sicily"],
            "toscana": ["toscana", "tuscany"],
            "trentino": ["trentino-alto adige", "trentino"],
            "umbria": ["umbria", "umbría"],
            "valle_aosta": ["valle d'aosta", "valle de aosta"],
            "veneto": ["veneto", "véneto"],
        },
        "ciudades": {
            "roma": ["roma", "rome"],
            "milano": ["milano", "milán", "milan"],
            "napoli": ["napoli", "nápoles", "naples"],
            "torino": ["torino", "turín", "turin"],
            "palermo": ["palermo"],
            "genova": ["genova", "génova", "genoa"],
            "bologna": ["bologna", "bolonia"],
            "firenze": ["firenze", "florencia", "florence"],
            "bari": ["bari"],
            "catania": ["catania"],
            "venezia": ["venezia", "venecia", "venice"],
            "verona": ["verona"],
            "messina": ["messina"],
            "padova": ["padova", "padua"],
            "trieste": ["trieste"],
            "brescia": ["brescia"],
            "parma": ["parma"],
            "taranto": ["taranto"],
            "prato": ["prato"],
            "modena": ["modena"],
            "reggio_calabria": ["reggio calabria"],
            "reggio_emilia": ["reggio emilia"],
            "perugia": ["perugia"],
            "ravenna": ["ravenna", "rávena"],
            "livorno": ["livorno"],
            "cagliari": ["cagliari"],
            "rimini": ["rimini", "rímini"],
            "siena": ["siena"],
            "pisa": ["pisa"],
            "como": ["como"],
            "bergamo": ["bergamo", "bérgamo"],
            "trento": ["trento"],
            "amalfi": ["amalfi"],
            "positano": ["positano"],
            "capri": ["capri"],
            "sorrento": ["sorrento"],
            "cinque_terre": ["cinque terre"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # FRANCIA - 18 REGIONES + CIUDADES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    "francia": {
        "regiones": {
            "auvergne_rhone_alpes":
            ["auvergne-rhône-alpes", "auvergne rhone alpes"],
            "bourgogne_franche_comte":
            ["bourgogne-franche-comté", "bourgogne franche comte", "borgoña"],
            "bretagne": ["bretagne", "bretaña", "brittany"],
            "centre_val_loire": ["centre-val de loire", "centre val de loire"],
            "corse": ["corse", "córcega", "corsica"],
            "grand_est": ["grand est"],
            "hauts_de_france": ["hauts-de-france", "hauts de france"],
            "ile_de_france":
            ["île-de-france", "ile de france", "paris region"],
            "normandie": ["normandie", "normandía", "normandy"],
            "nouvelle_aquitaine": ["nouvelle-aquitaine", "nouvelle aquitaine"],
            "occitanie": ["occitanie", "occitania"],
            "pays_de_la_loire": ["pays de la loire"],
            "provence_alpes":
            ["provence-alpes-côte d'azur", "provence", "paca"],
            "guadeloupe": ["guadeloupe", "guadalupe"],
            "martinique": ["martinique", "martinica"],
            "guyane": ["guyane", "guayana francesa", "french guiana"],
            "reunion": ["réunion", "reunion"],
            "mayotte": ["mayotte"],
        },
        "ciudades": {
            "paris": ["paris", "parís"],
            "marseille": ["marseille", "marsella"],
            "lyon": ["lyon", "lión"],
            "toulouse": ["toulouse", "tolosa"],
            "nice": ["nice", "niza"],
            "nantes": ["nantes"],
            "montpellier": ["montpellier"],
            "strasbourg": ["strasbourg", "estrasburgo"],
            "bordeaux": ["bordeaux", "burdeos"],
            "lille": ["lille"],
            "rennes": ["rennes"],
            "reims": ["reims"],
            "saint_etienne": ["saint-étienne", "saint etienne"],
            "le_havre": ["le havre"],
            "toulon": ["toulon", "tolón"],
            "grenoble": ["grenoble"],
            "dijon": ["dijon"],
            "angers": ["angers"],
            "nimes": ["nîmes", "nimes"],
            "aix_en_provence": ["aix-en-provence", "aix en provence"],
            "clermont_ferrand": ["clermont-ferrand", "clermont ferrand"],
            "le_mans": ["le mans"],
            "brest": ["brest"],
            "tours": ["tours"],
            "amiens": ["amiens"],
            "limoges": ["limoges"],
            "perpignan": ["perpignan", "perpiñán"],
            "metz": ["metz"],
            "besancon": ["besançon", "besancon"],
            "orleans": ["orléans", "orleans"],
            "rouen": ["rouen", "ruan"],
            "mulhouse": ["mulhouse"],
            "caen": ["caen"],
            "nancy": ["nancy"],
            "avignon": ["avignon", "aviñón"],
            "cannes": ["cannes"],
            "saint_tropez": ["saint-tropez", "saint tropez"],
            "monaco": ["monaco", "mónaco"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ALEMANIA - 16 ESTADOS FEDERADOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "alemania": {
        "estados": {
            "baden_wurttemberg":
            ["baden-württemberg", "baden wurttemberg", "bw"],
            "bayern": ["bayern", "baviera", "bavaria", "by"],
            "berlin": ["berlin", "berlín", "be"],
            "brandenburg": ["brandenburg", "brandeburgo", "bb"],
            "bremen": ["bremen", "hb"],
            "hamburg": ["hamburg", "hamburgo", "hh"],
            "hessen": ["hessen", "hesse", "he"],
            "mecklenburg_vorpommern":
            ["mecklenburg-vorpommern", "mecklenburg vorpommern", "mv"],
            "niedersachsen":
            ["niedersachsen", "baja sajonia", "lower saxony", "ni"],
            "nordrhein_westfalen":
            ["nordrhein-westfalen", "nrw", "renania del norte-westfalia"],
            "rheinland_pfalz": ["rheinland-pfalz", "renania-palatinado", "rp"],
            "saarland": ["saarland", "sarre", "sl"],
            "sachsen": ["sachsen", "sajonia", "saxony", "sn"],
            "sachsen_anhalt": ["sachsen-anhalt", "sajonia-anhalt", "st"],
            "schleswig_holstein": ["schleswig-holstein", "sh"],
            "thuringen": ["thüringen", "thuringen", "turingia", "th"],
        },
        "ciudades": {
            "berlin_ciudad": ["berlin", "berlín"],
            "hamburg_ciudad": ["hamburg", "hamburgo"],
            "munchen": ["münchen", "munchen", "múnich", "munich"],
            "koln": ["köln", "koln", "colonia", "cologne"],
            "frankfurt": ["frankfurt", "fráncfort", "frankfurt am main"],
            "stuttgart": ["stuttgart"],
            "dusseldorf": ["düsseldorf", "dusseldorf"],
            "dortmund": ["dortmund"],
            "essen": ["essen"],
            "leipzig": ["leipzig"],
            "bremen_ciudad": ["bremen"],
            "dresden": ["dresden", "dresde"],
            "hannover": ["hannover", "hanóver"],
            "nurnberg": ["nürnberg", "nurnberg", "núremberg", "nuremberg"],
            "duisburg": ["duisburg"],
            "bochum": ["bochum"],
            "wuppertal": ["wuppertal"],
            "bielefeld": ["bielefeld"],
            "bonn": ["bonn"],
            "munster": ["münster", "munster"],
            "karlsruhe": ["karlsruhe"],
            "mannheim": ["mannheim"],
            "augsburg": ["augsburg", "augsburgo"],
            "wiesbaden": ["wiesbaden"],
            "mainz": ["mainz", "maguncia"],
            "heidelberg": ["heidelberg"],
            "freiburg": ["freiburg", "friburgo"],
            "potsdam": ["potsdam"],
            "lubeck": ["lübeck", "lubeck"],
            "erfurt": ["erfurt"],
            "rostock": ["rostock"],
            "kiel": ["kiel"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # REINO UNIDO - 4 NACIONES + REGIONES + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "reino_unido": {
        "naciones": {
            "england": ["england", "inglaterra"],
            "scotland": ["scotland", "escocia"],
            "wales": ["wales", "gales"],
            "northern_ireland": ["northern ireland", "irlanda del norte"],
        },
        "regiones": {
            "greater_london": ["greater london", "london", "londres"],
            "south_east": ["south east", "sureste"],
            "south_west": ["south west", "suroeste"],
            "east_of_england": ["east of england", "este de inglaterra"],
            "west_midlands": ["west midlands", "midlands occidentales"],
            "east_midlands": ["east midlands", "midlands orientales"],
            "yorkshire": ["yorkshire and the humber", "yorkshire"],
            "north_west": ["north west", "noroeste"],
            "north_east": ["north east", "noreste"],
        },
        "ciudades": {
            "london": ["london", "londres"],
            "birmingham": ["birmingham"],
            "manchester": ["manchester", "mánchester"],
            "leeds": ["leeds"],
            "glasgow": ["glasgow"],
            "liverpool": ["liverpool"],
            "newcastle": ["newcastle", "newcastle upon tyne"],
            "sheffield": ["sheffield"],
            "bristol": ["bristol"],
            "edinburgh": ["edinburgh", "edimburgo"],
            "leicester": ["leicester"],
            "cardiff": ["cardiff"],
            "belfast": ["belfast"],
            "nottingham": ["nottingham"],
            "southampton": ["southampton"],
            "brighton": ["brighton"],
            "portsmouth": ["portsmouth"],
            "reading": ["reading"],
            "aberdeen": ["aberdeen"],
            "cambridge": ["cambridge"],
            "oxford": ["oxford"],
            "coventry": ["coventry"],
            "hull": ["hull", "kingston upon hull"],
            "stoke_on_trent": ["stoke-on-trent", "stoke on trent"],
            "wolverhampton": ["wolverhampton"],
            "plymouth": ["plymouth"],
            "derby": ["derby"],
            "swansea": ["swansea"],
            "dundee": ["dundee"],
            "inverness": ["inverness"],
            "york": ["york"],
            "bath": ["bath"],
            "canterbury": ["canterbury"],
            "stratford": ["stratford-upon-avon", "stratford upon avon"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PAÍSES BAJOS - 12 PROVINCIAS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "paises_bajos": {
        "provincias": {
            "drenthe": ["drenthe"],
            "flevoland": ["flevoland"],
            "friesland": ["friesland", "frisia"],
            "gelderland": ["gelderland", "güeldres"],
            "groningen": ["groningen"],
            "limburg_nl": ["limburg", "limburgo"],
            "noord_brabant":
            ["noord-brabant", "noord brabant", "brabante septentrional"],
            "noord_holland":
            ["noord-holland", "noord holland", "holanda septentrional"],
            "overijssel": ["overijssel"],
            "utrecht_prov": ["utrecht"],
            "zeeland": ["zeeland", "zelanda"],
            "zuid_holland":
            ["zuid-holland", "zuid holland", "holanda meridional"],
        },
        "ciudades": {
            "amsterdam": ["amsterdam", "ámsterdam"],
            "rotterdam": ["rotterdam", "róterdam"],
            "den_haag": ["den haag", "the hague", "la haya", "'s-gravenhage"],
            "utrecht": ["utrecht"],
            "eindhoven": ["eindhoven"],
            "tilburg": ["tilburg"],
            "groningen_ciudad": ["groningen"],
            "almere": ["almere"],
            "breda": ["breda"],
            "nijmegen": ["nijmegen", "nimega"],
            "arnhem": ["arnhem"],
            "haarlem": ["haarlem"],
            "enschede": ["enschede"],
            "zaanstad": ["zaanstad", "zaandam"],
            "amersfoort": ["amersfoort"],
            "apeldoorn": ["apeldoorn"],
            "maastricht": ["maastricht"],
            "leiden": ["leiden", "leyden"],
            "dordrecht": ["dordrecht"],
            "zoetermeer": ["zoetermeer"],
            "zwolle": ["zwolle"],
            "deventer": ["deventer"],
            "delft": ["delft"],
            "alkmaar": ["alkmaar"],
            "heerlen": ["heerlen"],
            "venlo": ["venlo"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # BÉLGICA - 10 PROVINCIAS + 3 REGIONES + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "belgica": {
        "regiones": {
            "flandes": ["flandes", "vlaanderen", "flanders"],
            "valonia": ["valonia", "wallonie", "wallonia"],
            "bruselas_region":
            ["bruselas capital", "bruxelles capitale", "brussels capital"],
        },
        "provincias": {
            "amberes": ["amberes", "antwerpen", "antwerp"],
            "brabante_flamenco": ["brabante flamenco", "vlaams-brabant"],
            "brabante_valon": ["brabante valón", "brabant wallon"],
            "flandes_occidental": ["flandes occidental", "west-vlaanderen"],
            "flandes_oriental": ["flandes oriental", "oost-vlaanderen"],
            "hainaut": ["henao", "hainaut"],
            "lieja": ["lieja", "liège", "liege"],
            "limburgo_be": ["limburgo", "limburg"],
            "luxemburgo_be": ["luxemburgo", "luxembourg"],
            "namur": ["namur"],
        },
        "ciudades": {
            "bruselas": ["bruselas", "bruxelles", "brussels", "brussel"],
            "amberes_ciudad": ["amberes", "antwerpen", "antwerp"],
            "gante": ["gante", "gent", "ghent"],
            "charleroi": ["charleroi"],
            "lieja_ciudad": ["lieja", "liège", "liege"],
            "brujas": ["brujas", "brugge", "bruges"],
            "namur_ciudad": ["namur"],
            "lovaina": ["lovaina", "leuven", "louvain"],
            "mons": ["mons"],
            "aalst": ["aalst"],
            "mechelen": ["mechelen", "malinas"],
            "la_louviere": ["la louvière", "la louviere"],
            "kortrijk": ["kortrijk", "courtrai"],
            "hasselt": ["hasselt"],
            "ostende": ["ostende", "oostende", "ostend"],
            "genk": ["genk"],
            "sint_niklaas": ["sint-niklaas", "sint niklaas"],
            "tournai": ["tournai", "doornik"],
            "spa": ["spa"],
            "dinant": ["dinant"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # SUIZA - 26 CANTONES + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "suiza": {
        "cantones": {
            "aargau": ["aargau", "argovia"],
            "appenzell_ar": ["appenzell ausserrhoden", "appenzell exterior"],
            "appenzell_ir": ["appenzell innerrhoden", "appenzell interior"],
            "basel_landschaft": ["basel-landschaft", "basilea-campiña"],
            "basel_stadt": ["basel-stadt", "basilea-ciudad"],
            "bern": ["bern", "berna"],
            "fribourg": ["fribourg", "freiburg", "friburgo"],
            "geneve": ["genève", "geneve", "genf", "ginebra", "geneva"],
            "glarus": ["glarus", "glaris"],
            "graubunden": ["graubünden", "graubunden", "grisones", "grisons"],
            "jura": ["jura"],
            "luzern": ["luzern", "lucerna", "lucerne"],
            "neuchatel": ["neuchâtel", "neuchatel", "neuenburg"],
            "nidwalden": ["nidwalden", "nidwald"],
            "obwalden": ["obwalden", "obwald"],
            "schaffhausen": ["schaffhausen", "schaffhouse", "escafusa"],
            "schwyz": ["schwyz"],
            "solothurn": ["solothurn", "soleure", "soleura"],
            "st_gallen": ["st. gallen", "st gallen", "san galo"],
            "thurgau": ["thurgau", "turgovia", "thurgovie"],
            "ticino": ["ticino", "tesino", "tessin"],
            "uri": ["uri"],
            "valais": ["valais", "wallis", "valés"],
            "vaud": ["vaud", "waadt"],
            "zug": ["zug"],
            "zurich": ["zürich", "zurich"],
        },
        "ciudades": {
            "zurich_ciudad": ["zürich", "zurich"],
            "ginebra_ciudad": ["ginebra", "genève", "geneva", "genf"],
            "basilea": ["basilea", "basel", "bâle"],
            "lausana": ["lausana", "lausanne"],
            "berna_ciudad": ["berna", "bern", "berne"],
            "winterthur": ["winterthur"],
            "lucerna_ciudad": ["lucerna", "luzern", "lucerne"],
            "st_gallen_ciudad": ["san galo", "st. gallen", "st gallen"],
            "lugano": ["lugano"],
            "biel": ["biel", "bienne"],
            "thun": ["thun"],
            "koniz": ["köniz", "koniz"],
            "la_chaux_de_fonds": ["la chaux-de-fonds"],
            "fribourg_ciudad": ["friburgo", "fribourg", "freiburg"],
            "schaffhausen_ciudad": ["schaffhausen", "escafusa"],
            "chur": ["chur", "coira"],
            "neuchatel_ciudad": ["neuchâtel", "neuchatel"],
            "sion": ["sion", "sitten"],
            "montreux": ["montreux"],
            "interlaken": ["interlaken"],
            "zermatt": ["zermatt"],
            "davos": ["davos"],
            "st_moritz": ["st. moritz", "st moritz", "san moritz"],
            "locarno": ["locarno"],
            "bellinzona": ["bellinzona"],
            "ascona": ["ascona"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # AUSTRIA - 9 ESTADOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "austria": {
        "estados": {
            "burgenland": ["burgenland"],
            "carintia": ["carintia", "kärnten", "carinthia"],
            "baja_austria":
            ["baja austria", "niederösterreich", "lower austria"],
            "alta_austria":
            ["alta austria", "oberösterreich", "upper austria"],
            "salzburgo": ["salzburgo", "salzburg"],
            "estiria": ["estiria", "steiermark", "styria"],
            "tirol": ["tirol", "tyrol"],
            "vorarlberg": ["vorarlberg"],
            "viena": ["viena", "wien", "vienna"],
        },
        "ciudades": {
            "viena_ciudad": ["viena", "wien", "vienna"],
            "graz": ["graz"],
            "linz": ["linz"],
            "salzburgo_ciudad": ["salzburgo", "salzburg"],
            "innsbruck": ["innsbruck"],
            "klagenfurt": ["klagenfurt"],
            "villach": ["villach"],
            "wels": ["wels"],
            "sankt_polten": ["sankt pölten", "st. pölten", "st polten"],
            "dornbirn": ["dornbirn"],
            "wiener_neustadt": ["wiener neustadt"],
            "steyr": ["steyr"],
            "feldkirch": ["feldkirch"],
            "bregenz": ["bregenz"],
            "klosterneuburg": ["klosterneuburg"],
            "baden": ["baden bei wien", "baden"],
            "leoben": ["leoben"],
            "krems": ["krems an der donau", "krems"],
            "traun": ["traun"],
            "amstetten": ["amstetten"],
            "wolfsberg": ["wolfsberg"],
            "hallstatt": ["hallstatt"],
            "zell_am_see": ["zell am see"],
            "bad_ischl": ["bad ischl"],
            "kitzbuhel": ["kitzbühel", "kitzbuhel"],
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CANADÁ - 13 PROVINCIAS/TERRITORIOS + CIUDADES
    # ═══════════════════════════════════════════════════════════════════════════
    "canada": {
        "provincias": {
            "alberta": ["alberta", "ab"],
            "british_columbia":
            ["british columbia", "columbia británica", "bc"],
            "manitoba": ["manitoba", "mb"],
            "new_brunswick": ["new brunswick", "nuevo brunswick", "nb"],
            "newfoundland": ["newfoundland and labrador", "terranova", "nl"],
            "northwest_territories":
            ["northwest territories", "territorios del noroeste", "nt"],
            "nova_scotia": ["nova scotia", "nueva escocia", "ns"],
            "nunavut": ["nunavut", "nu"],
            "ontario": ["ontario", "on"],
            "prince_edward_island":
            ["prince edward island", "isla del príncipe eduardo", "pei", "pe"],
            "quebec": ["quebec", "québec", "qc"],
            "saskatchewan": ["saskatchewan", "sk"],
            "yukon": ["yukon", "yt"],
        },
        "ciudades": {
            "toronto": ["toronto"],
            "montreal": ["montreal", "montréal"],
            "vancouver": ["vancouver"],
            "calgary": ["calgary"],
            "edmonton": ["edmonton"],
            "ottawa": ["ottawa"],
            "winnipeg": ["winnipeg"],
            "quebec_ciudad": ["quebec city", "ville de québec", "quebec"],
            "hamilton": ["hamilton"],
            "kitchener": ["kitchener"],
            "london_ca": ["london"],
            "victoria": ["victoria"],
            "halifax": ["halifax"],
            "oshawa": ["oshawa"],
            "windsor": ["windsor"],
            "saskatoon": ["saskatoon"],
            "regina": ["regina"],
            "st_johns": ["st. john's", "st johns"],
            "barrie": ["barrie"],
            "kelowna": ["kelowna"],
            "abbotsford": ["abbotsford"],
            "sudbury": ["sudbury"],
            "kingston": ["kingston"],
            "sherbrooke": ["sherbrooke"],
            "trois_rivieres": ["trois-rivières", "trois rivieres"],
            "guelph": ["guelph"],
            "moncton": ["moncton"],
            "brantford": ["brantford"],
            "thunder_bay": ["thunder bay"],
            "saint_john": ["saint john"],
            "whistler": ["whistler"],
            "banff": ["banff"],
            "niagara_falls": ["niagara falls"],
        }
    },
}


def obtener_variantes_ubicacion(ubicacion: str) -> list:
    """
    Dado un nombre de ubicación, retorna todas sus variantes.
    Busca en países, provincias/estados y ciudades.
    """
    if not ubicacion:
        return []

    ubicacion_lower = ubicacion.lower().strip()
    variantes = [ubicacion_lower]

    # Buscar en países
    for pais, lista in UBICACIONES_VARIANTES.get("paises", {}).items():
        if ubicacion_lower in [v.lower() for v in lista]:
            variantes.extend([v.lower() for v in lista])
            return list(set(variantes))

    # Buscar en cada país (provincias/estados y ciudades)
    for pais in [
            "argentina", "mexico", "espana", "colombia", "chile", "peru",
            "usa", "brasil", "venezuela", "ecuador"
    ]:
        pais_data = UBICACIONES_VARIANTES.get(pais, {})

        # Buscar en provincias/estados
        for key in [
                "provincias", "estados", "comunidades", "departamentos",
                "regiones"
        ]:
            subdiv = pais_data.get(key, {})
            for nombre, lista in subdiv.items():
                if ubicacion_lower in [v.lower() for v in lista]:
                    variantes.extend([v.lower() for v in lista])
                    return list(set(variantes))

        # Buscar en ciudades
        ciudades = pais_data.get("ciudades", {})
        for nombre, lista in ciudades.items():
            if ubicacion_lower in [v.lower() for v in lista]:
                variantes.extend([v.lower() for v in lista])
                return list(set(variantes))

    return variantes


def ubicacion_en_texto(ubicacion: str, texto: str) -> bool:
    """
    Verifica si alguna variante de la ubicación está en el texto.
    """
    if not ubicacion or not texto:
        return False

    texto_lower = texto.lower()
    variantes = obtener_variantes_ubicacion(ubicacion)

    for v in variantes:
        if v in texto_lower:
            return True

    return False


def es_url_valida_noticia(url: str, texto: str, empresa: str) -> bool:
    """Valida si una URL es una noticia real y relevante."""
    url_lower = url.lower()
    texto_lower = texto.lower()
    empresa_lower = empresa.lower()

    if url_lower.endswith('.pdf'):
        return False

    dominios_basura = [
        # Académicos/documentos
        'pdfcoffee',
        'scribd',
        'academia.edu',
        'slideshare',
        'coursehero',
        'repositorio',
        'bitstream',
        'handle/',
        'thesis',
        'tesis',
        # Gobierno/legal
        'icj-cij.org',
        'cancilleria.gob',
        'boletinoficial',
        'sidof.segob.gob',
        'segob.gob.mx',
        # Ecommerce/spam
        'cityfilespress',
        'amazon.com',
        'mercadolibre',
        'aliexpress',
        'ebay.com',
        'alibaba.com',
        'wish.com',
        'shopee',
        'olx.com',
        'craiglist',
        'segundamano',
        'vibbo',
        # Redes sociales (NO son noticias)
        'linkedin.com',
        'facebook.com',
        'instagram.com',
        'twitter.com',
        'x.com',
        'youtube.com',
        'tiktok.com',
    ]
    if any(d in url_lower for d in dominios_basura):
        return False

    palabras_empresa = [p for p in empresa_lower.split() if len(p) > 2]
    matches = sum(1 for p in palabras_empresa if p in texto_lower)
    if matches < 1:
        return False

    return True


def es_red_social(url: str) -> bool:
    """Verifica si la URL es de una red social."""
    redes = [
        'linkedin.com', 'facebook.com', 'instagram.com', 'twitter.com',
        'youtube.com', 'tiktok.com', 'x.com'
    ]
    return any(red in url.lower() for red in redes)


def es_buscador(url: str) -> bool:
    """Verifica si la URL es de un buscador o página de resultados."""
    url_lower = url.lower()

    # Patrones de buscadores y páginas de resultados
    patrones_buscador = [
        'google.com/search',
        'bing.com/search',
        'bing.com/news/search',
        'yahoo.com/search',
        'duckduckgo.com',
        'news.google.com/search',
        'search?q=',
        '/search?',
    ]

    # Detectar URLs que son páginas de búsqueda
    if any(p in url_lower for p in patrones_buscador):
        return True

    # Detectar news.google.com (cualquier path)
    if 'news.google.com' in url_lower and '/articles/' not in url_lower:
        return True

    return False


def es_registro_legal(url: str, texto: str) -> bool:
    """Verifica si es un registro legal o boletín oficial."""
    url_lower = url.lower()
    texto_lower = texto.lower()

    if 'boletinoficial' in url_lower or 'boletin-oficial' in url_lower:
        return True
    if '/contratos' in url_lower or 'contratos.pdf' in url_lower:
        return True

    keywords_legales = [
        'modificación de contrato', 'modificacion de contrato',
        'cesión de cuotas', 'cesion de cuotas', 'constitución de sociedad',
        'constitucion de sociedad', 'designación de gerentes',
        'designacion de gerentes', 'contrato social', 'expte.', 'expediente',
        'autos caratulados', 'inscripción matrícula', 'inscripcion matricula'
    ]

    if any(kw in texto_lower for kw in keywords_legales):
        return True

    return False


def calcular_peso_linkedin(url: str,
                           texto: str,
                           primer_nombre: str,
                           apellido: str,
                           empresa: str = "",
                           provincia: str = "",
                           ciudad: str = "",
                           pais: str = "") -> int:
    """
    Calcula el peso de un perfil de LinkedIn.

    PESO MÁXIMO 100:
    - Nombre (obligatorio): 40 puntos
    - Apellido (obligatorio): 40 puntos
    - Empresa: 10 puntos
    - Ubicación (provincia/ciudad/país): 10 puntos

    Si no tiene nombre Y apellido EXACTOS, retorna 0 (descartar).
    Usa variantes de ubicación para mejor matching.
    """
    url_lower = url.lower()
    texto_lower = texto.lower()

    # Extraer slug de la URL
    slug = ""
    if "/in/" in url_lower:
        slug = url_lower.split("/in/")[1].split("/")[0].split("?")[0]
    slug_clean = slug.replace("-", " ").replace("_", " ")

    # Combinar texto y slug para búsqueda
    contenido = f"{texto_lower} {slug_clean}"

    primer_lower = primer_nombre.lower().strip()
    apellido_lower = apellido.lower().strip()
    empresa_lower = empresa.lower().strip() if empresa else ""

    peso = 0
    tiene_nombre = False
    tiene_apellido = False

    # ═══════════════════════════════════════════════════════════════════
    # VERIFICACIÓN ESTRICTA DE NOMBRE (40 puntos)
    # El nombre DEBE estar en el contenido
    # ═══════════════════════════════════════════════════════════════════
    if primer_lower and len(primer_lower) > 1:
        if primer_lower in contenido:
            peso += 40
            tiene_nombre = True

    # ═══════════════════════════════════════════════════════════════════
    # VERIFICACIÓN ESTRICTA DE APELLIDO (40 puntos)
    # El apellido DEBE estar en el contenido
    # ═══════════════════════════════════════════════════════════════════
    if apellido_lower and len(apellido_lower) > 1:
        if apellido_lower in contenido:
            peso += 40
            tiene_apellido = True

    # ═══════════════════════════════════════════════════════════════════
    # CRÍTICO: Si no tiene AMBOS (nombre Y apellido), DESCARTAR
    # Esto evita falsos positivos como Samuel Rodriguez
    # ═══════════════════════════════════════════════════════════════════
    if not (tiene_nombre and tiene_apellido):
        return 0

    # Verificar empresa (10 puntos)
    if empresa_lower and len(empresa_lower) > 2:
        palabras_empresa = [p for p in empresa_lower.split() if len(p) > 2]
        if empresa_lower in contenido:
            peso += 10
        elif any(p in contenido for p in palabras_empresa):
            peso += 5

    # ═══════════════════════════════════════════════════════════════════
    # VERIFICACIÓN DE UBICACIÓN CON VARIANTES (10 puntos máximo)
    # Usa el diccionario UBICACIONES_VARIANTES para mejor matching
    # ═══════════════════════════════════════════════════════════════════
    puntos_ubicacion = 0

    # Provincia/Estado (5 puntos)
    if provincia and ubicacion_en_texto(provincia, contenido):
        puntos_ubicacion += 5

    # Ciudad (5 puntos)
    if ciudad and ubicacion_en_texto(ciudad, contenido):
        puntos_ubicacion += 5

    # País (3 puntos, solo si no sumó por provincia/ciudad)
    if pais and puntos_ubicacion == 0:
        if ubicacion_en_texto(pais, contenido):
            puntos_ubicacion += 3

    peso += min(puntos_ubicacion, 10)

    return min(peso, 100)


async def research_person_and_company(nombre_persona: str,
                                      empresa: str,
                                      website: str = "",
                                      linkedin_empresa_input: str = "",
                                      facebook_empresa_input: str = "",
                                      instagram_empresa_input: str = "",
                                      city: str = "",
                                      province: str = "",
                                      country: str = "",
                                      email_contacto: str = "") -> dict:
    """
    Función principal que replica el workflow completo de n8n.
    LinkedIn empresa: SOLO desde web del cliente.
    LinkedIn personal: 2 fases de búsqueda.
    """
    logger.info(f"[RESEARCH] ========== Iniciando investigación ==========")
    logger.info(f"[RESEARCH] Persona: {nombre_persona}, "
                f"Empresa: {empresa}, Web: {website}")

    # ═══════════════════════════════════════════════════════════════════
    # PASO 1: PREPARAR DATOS
    # ═══════════════════════════════════════════════════════════════════

    nombre = nombre_persona.strip()
    nombre_partes = nombre.split()
    primer_nombre = nombre_partes[0] if nombre_partes else ""
    apellido = nombre_partes[-1] if len(nombre_partes) > 1 else ""

    website_limpio = (website.replace("https://",
                                      "").replace("http://",
                                                  "").replace("www.",
                                                              "").rstrip("/"))
    tiene_website = bool(website_limpio)

    empresa_busqueda = empresa if empresa else website_limpio

    # Ubicación completa para búsquedas
    ubicacion_query = city or province or country or ""
    ubicacion_completa = ""
    if city and province:
        ubicacion_completa = f"{city}, {province}"
    elif city:
        ubicacion_completa = city
    elif province:
        ubicacion_completa = province
    if country and ubicacion_completa:
        ubicacion_completa += f", {country}"
    elif country:
        ubicacion_completa = country

    # Inicializar resultados
    # NOTA: LinkedIn empresa SOLO viene de web, no se busca
    results = {
        "nombre_original":
        nombre,
        "nombre":
        nombre,
        "primer_nombre":
        primer_nombre,
        "apellido":
        apellido,
        "empresa":
        empresa,
        "website":
        website,
        "website_limpio":
        website_limpio,
        "empresa_busqueda":
        empresa_busqueda,

        # LinkedIn personal
        "linkedin_personal":
        "No encontrado",
        "linkedin_personal_confianza":
        0,
        "linkedin_personal_source":
        "ninguno",

        # LinkedIn empresa - SOLO de la web del cliente
        "linkedin_empresa":
        linkedin_empresa_input or "No encontrado",
        "linkedin_empresa_source":
        ("web_cliente" if linkedin_empresa_input else "ninguno"),

        # Otras redes (SOLO de la web del cliente, NO se buscan)
        "facebook_empresa":
        facebook_empresa_input or "No encontrado",
        "instagram_empresa":
        instagram_empresa_input or "No encontrado",

        # Noticias
        "noticias_lista": [],
        "noticias_empresa":
        "No se encontraron noticias",
        "noticias_count":
        0,
        "noticias_source":
        "ninguno"
    }

    try:
        # ═══════════════════════════════════════════════════════════════
        # PASO 2: TAVILY - VERIFICAR NOMBRE EN SITIO WEB
        # ═══════════════════════════════════════════════════════════════
        if tiene_website and TAVILY_API_KEY:
            logger.info(f"[TAVILY] Verificando nombre en sitio web...")
            nombre_verificado = await tavily_verificar_nombre(
                website_limpio, primer_nombre, apellido)
            if nombre_verificado:
                results["nombre"] = nombre_verificado
                results["nombre_verificado"] = True
                partes = nombre_verificado.split()
                results[
                    "primer_nombre"] = partes[0] if partes else primer_nombre
                results["apellido"] = partes[-1] if len(
                    partes) > 1 else apellido
                logger.info(
                    f"[TAVILY] ✓ Nombre verificado: {nombre_verificado}")

        # ═══════════════════════════════════════════════════════════════
        # PASO 3: LINKEDIN PERSONAL - BÚSQUEDA CON PESO
        # ═══════════════════════════════════════════════════════════════
        # Buscar en TODAS las fuentes, calcular peso, mostrar los mejores
        # ═══════════════════════════════════════════════════════════════

        candidatos_linkedin = []  # Lista de {url, peso, source}

        primer_nombre_busqueda = results["primer_nombre"]
        apellido_busqueda = results["apellido"]

        # ───────────────────────────────────────────────────────────────
        # 3A: BUSCAR EN WEB DEL CLIENTE
        # ───────────────────────────────────────────────────────────────
        if tiene_website:
            logger.info(f"[LINKEDIN] PASO 3A: Buscando en web...")
            try:
                paginas = [
                    f"https://{website_limpio}",
                    f"https://{website_limpio}/nosotros",
                    f"https://{website_limpio}/about",
                    f"https://{website_limpio}/equipo",
                    f"https://{website_limpio}/team",
                    f"https://{website_limpio}/contacto",
                ]

                contenido_web = ""
                async with httpx.AsyncClient(timeout=15.0) as client:
                    for pagina in paginas[:4]:
                        try:
                            resp = await client.get(
                                pagina,
                                headers={"User-Agent": "Mozilla/5.0"},
                                follow_redirects=True)
                            if resp.status_code == 200:
                                contenido_web += resp.text + "\n"
                        except:
                            continue

                if contenido_web:
                    # Buscar URLs de LinkedIn en el contenido
                    pattern = r'https?://(?:www\.)?(?:ar\.)?linkedin\.com/in/([a-zA-Z0-9_~-]+)'
                    matches = re.findall(pattern, contenido_web, re.IGNORECASE)

                    for slug in matches:
                        if slug.lower() in ['company', 'jobs', 'pulse']:
                            continue

                        url = f"https://linkedin.com/in/{slug}"
                        peso = calcular_peso_linkedin(
                            url=url,
                            texto=contenido_web,
                            primer_nombre=primer_nombre_busqueda,
                            apellido=apellido_busqueda,
                            empresa=empresa_busqueda,
                            provincia=province,
                            ciudad=city)

                        if peso >= 60:
                            ya_existe = any(c["url"] == url
                                            for c in candidatos_linkedin)
                            if not ya_existe:
                                candidatos_linkedin.append({
                                    "url":
                                    url,
                                    "peso":
                                    peso,
                                    "source":
                                    "web_cliente"
                                })
                                logger.info(
                                    f"[LINKEDIN-WEB] ✓ {url} (peso: {peso})")
                        else:
                            logger.info(f"[LINKEDIN-WEB] ✗ {url} descartado "
                                        f"(peso: {peso} < 60)")
            except Exception as e:
                logger.warning(f"[LINKEDIN-WEB] Error: {e}")

        # ───────────────────────────────────────────────────────────────
        # 3B: BUSCAR POR EMAIL
        # ───────────────────────────────────────────────────────────────
        if email_contacto and email_contacto != "No encontrado":
            logger.info(f"[LINKEDIN] PASO 3B: Buscando por email...")
            linkedin_email = await buscar_linkedin_por_email(email_contacto)
            if linkedin_email:
                peso = calcular_peso_linkedin(
                    url=linkedin_email,
                    texto=email_contacto,
                    primer_nombre=primer_nombre_busqueda,
                    apellido=apellido_busqueda,
                    empresa=empresa_busqueda,
                    provincia=province,
                    ciudad=city)
                # Email tiene peso mínimo 70 si encontró algo
                peso = max(peso, 70)
                ya_existe = any(c["url"] == linkedin_email
                                for c in candidatos_linkedin)
                if not ya_existe:
                    candidatos_linkedin.append({
                        "url": linkedin_email,
                        "peso": peso,
                        "source": "email"
                    })
                    logger.info(
                        f"[LINKEDIN-EMAIL] ✓ {linkedin_email} (peso: {peso})")

        # ───────────────────────────────────────────────────────────────
        # 3C: BUSCAR POR NOMBRE+EMPRESA (Tavily)
        # ───────────────────────────────────────────────────────────────
        if TAVILY_API_KEY:
            logger.info(f"[LINKEDIN] PASO 3C: Buscando en Tavily...")
            linkedin_result = await tavily_buscar_linkedin_personal(
                results["nombre"], empresa_busqueda, primer_nombre_busqueda,
                apellido_busqueda, ubicacion_completa, city, province, country)
            if linkedin_result:
                urls_tavily = linkedin_result.get("url", "")
                confianza = linkedin_result.get("confianza", 0)

                # Puede venir una URL o varias separadas por |
                for url in urls_tavily.split(" | "):
                    url = url.strip()
                    if not url or url == "No encontrado":
                        continue

                    ya_existe = any(c["url"] == url
                                    for c in candidatos_linkedin)
                    if not ya_existe:
                        candidatos_linkedin.append({
                            "url": url,
                            "peso": confianza,
                            "source": "tavily"
                        })
                        logger.info(
                            f"[LINKEDIN-TAVILY] ✓ {url} (peso: {confianza})")

        # ───────────────────────────────────────────────────────────────
        # 3D: BUSCAR CON GOOGLE (fallback)
        # ───────────────────────────────────────────────────────────────
        if GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
            logger.info(f"[LINKEDIN] PASO 3D: Buscando en Google...")
            google_result = await google_buscar_linkedin_personal(
                results["nombre"],
                empresa_busqueda,
                primer_nombre_busqueda,
                apellido_busqueda,
                0,  # confianza_actual
                ubicacion_completa,
                city,
                province,
                country)
            if google_result:
                urls_google = google_result.get("url", "")
                confianza = google_result.get("confianza", 0)

                for url in urls_google.split(" | "):
                    url = url.strip()
                    if not url or url == "No encontrado":
                        continue

                    ya_existe = any(c["url"] == url
                                    for c in candidatos_linkedin)
                    if not ya_existe:
                        candidatos_linkedin.append({
                            "url": url,
                            "peso": confianza,
                            "source": "google"
                        })
                        logger.info(
                            f"[LINKEDIN-GOOGLE] ✓ {url} (peso: {confianza})")

        # ───────────────────────────────────────────────────────────────
        # 3E: BUSCAR POR CARGO (CEO/fundador)
        # ───────────────────────────────────────────────────────────────
        if len(candidatos_linkedin) < 2:
            logger.info(f"[LINKEDIN] PASO 3E: Buscando por cargo...")
            por_cargo = await buscar_linkedin_por_cargo(
                empresa=empresa_busqueda, ubicacion=ubicacion_completa)
            for url in por_cargo:
                peso = calcular_peso_linkedin(
                    url=url,
                    texto=f"{empresa_busqueda} {ubicacion_completa}",
                    primer_nombre=primer_nombre_busqueda,
                    apellido=apellido_busqueda,
                    empresa=empresa_busqueda,
                    provincia=province,
                    ciudad=city)
                if peso >= 60:
                    ya_existe = any(c["url"] == url
                                    for c in candidatos_linkedin)
                    if not ya_existe:
                        candidatos_linkedin.append({
                            "url": url,
                            "peso": peso,
                            "source": "cargo"
                        })
                        logger.info(f"[LINKEDIN-CARGO] ✓ {url} (peso: {peso})")

        # ───────────────────────────────────────────────────────────────
        # CONSOLIDAR RESULTADOS
        # ───────────────────────────────────────────────────────────────
        if candidatos_linkedin:
            # Ordenar por peso (mayor a menor)
            candidatos_linkedin.sort(key=lambda x: x["peso"], reverse=True)

            # Filtrar solo los que tienen peso >= 60
            validos = [c for c in candidatos_linkedin if c["peso"] >= 60]

            if validos:
                # Formato: uno por línea
                urls_finales = [c["url"] for c in validos[:5]]
                results["linkedin_personal"] = "\n".join(urls_finales)
                results["linkedin_personal_confianza"] = validos[0]["peso"]
                results["linkedin_personal_source"] = validos[0]["source"]

                logger.info(
                    f"[LINKEDIN] ✓ {len(urls_finales)} perfiles encontrados")
                for c in validos[:5]:
                    logger.info(f"  - {c['url']} (peso: {c['peso']}, "
                                f"source: {c['source']})")
            else:
                logger.info("[LINKEDIN] ✗ Ningún candidato con peso >= 60")
        else:
            logger.info("[LINKEDIN] ✗ No se encontraron candidatos")

        # ═══════════════════════════════════════════════════════════════
        # PASO 5: NOTICIAS - GOOGLE PRIMERO (RÁPIDO) + APIFY PARALELO
        # ═══════════════════════════════════════════════════════════════
        noticias = []

        # Primero Google (rápido, ~2 seg)
        if GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
            logger.info(f"[GOOGLE] Buscando noticias...")
            noticias = await google_buscar_noticias(empresa, empresa_busqueda,
                                                    ubicacion_query)
            if noticias:
                results["noticias_source"] = "google"

        # Si Google no encontró, intentar APIFY con timeout corto
        if not noticias and APIFY_API_TOKEN:
            logger.info(f"[APIFY] Intentando crawler (timeout 30s)...")
            try:
                noticias = await asyncio.wait_for(apify_buscar_noticias(
                    empresa_busqueda, ubicacion_query),
                                                  timeout=30.0)
                if noticias:
                    results["noticias_source"] = "apify"
            except asyncio.TimeoutError:
                logger.warning("[APIFY] Timeout - continuando sin noticias")

        if noticias:
            results["noticias_lista"] = noticias
            results["noticias_count"] = len(noticias)

            noticias_texto = []
            for n in noticias[:10]:
                titulo = n.get("titulo", "Sin título")
                url = n.get("url", "")

                # Extraer nombre del dominio como label
                try:
                    dominio = url.split('/')[2].replace('www.', '')
                    source_label = dominio.split('.')[0].upper()
                except:
                    source_label = 'WEB'

                linea = f"• {titulo} [{source_label}]"
                if url:
                    linea += f"\n  {url}"
                noticias_texto.append(linea)

            if noticias_texto:
                results["noticias_empresa"] = "\n\n".join(noticias_texto)

    except Exception as e:
        logger.error(f"[RESEARCH] Error en investigación: {e}", exc_info=True)

    logger.info(f"[RESEARCH] ========== Investigación completada ==========")
    logger.info(
        f"[RESEARCH] LinkedIn personal: {results['linkedin_personal']} "
        f"(conf: {results['linkedin_personal_confianza']})")
    logger.info(f"[RESEARCH] LinkedIn empresa: {results['linkedin_empresa']}")
    logger.info(f"[RESEARCH] Noticias: {results['noticias_count']} "
                f"({results['noticias_source']})")

    return results


async def tavily_verificar_nombre(website: str, primer_nombre: str,
                                  apellido: str) -> Optional[str]:
    """
    Busca en el sitio web para verificar/encontrar el nombre completo.
    """
    if not TAVILY_API_KEY:
        return None

    try:
        query = (f'site:{website} "{primer_nombre}" OR "{apellido}" '
                 f'equipo nosotros about contacto')

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post("https://api.tavily.com/search",
                                         json={
                                             "api_key": TAVILY_API_KEY,
                                             "query": query,
                                             "search_depth": "advanced",
                                             "include_raw_content": True,
                                             "max_results": 5
                                         })

            if response.status_code != 200:
                return None

            data = response.json()
            results = data.get("results", [])

            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()

            patrones = [
                re.compile(
                    rf'{primer_lower}\s+[a-záéíóúñ]+\s+{apellido_lower}',
                    re.IGNORECASE),
                re.compile(
                    rf'(?:ing\.?|dr\.?|lic\.?|arq\.?|sr\.?|sra\.?|cpa\.?|mba\.?)'
                    rf'\s*{primer_lower}\s+(?:[a-záéíóúñ]+\s+)?{apellido_lower}',
                    re.IGNORECASE),
                re.compile(rf'{primer_lower}\s+{apellido_lower}',
                           re.IGNORECASE),
                re.compile(rf'{apellido_lower},?\s+{primer_lower}',
                           re.IGNORECASE),
                re.compile(
                    rf'{primer_lower}\s+(?:de\s+|del\s+)?'
                    rf'[a-záéíóúñ]+\s+{apellido_lower}', re.IGNORECASE)
            ]

            mejor_match = None
            mejor_longitud = 0

            for result in results:
                contenido = ((result.get("content") or "") + " " +
                             (result.get("raw_content") or "")).lower()

                for patron in patrones:
                    matches = patron.findall(contenido)
                    for match in matches:
                        nombre_limpio = re.sub(
                            r'^(ing\.?|dr\.?|lic\.?|arq\.?|'
                            r'sr\.?|sra\.?|cpa\.?|mba\.?)\s*',
                            '',
                            match,
                            flags=re.IGNORECASE)
                        nombre_limpio = nombre_limpio.strip()
                        nombre_limpio = " ".join(
                            p.capitalize() for p in nombre_limpio.split())

                        if (len(nombre_limpio) > mejor_longitud
                                and len(nombre_limpio.split()) >= 2):
                            mejor_match = nombre_limpio
                            mejor_longitud = len(nombre_limpio)

            return mejor_match

    except Exception as e:
        logger.error(f"[TAVILY] Error verificando nombre: {e}")
        return None


async def buscar_linkedin_por_cargo(empresa: str,
                                    ubicacion: str = "",
                                    cargos: list = None) -> list:
    """
    Busca LinkedIn de fundadores/CEO/directores de una empresa.
    Retorna lista de URLs encontradas.
    """
    if not TAVILY_API_KEY:
        return []

    if cargos is None:
        cargos = [
            'fundador', 'founder', 'CEO', 'director', 'dueño', 'owner',
            'gerente general'
        ]

    resultados = []

    for cargo in cargos[:3]:  # Limitar a 3 cargos
        query = f'{cargo} "{empresa}" site:linkedin.com/in'
        if ubicacion:
            query = f'{cargo} "{empresa}" {ubicacion} site:linkedin.com/in'

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post("https://api.tavily.com/search",
                                             json={
                                                 "api_key":
                                                 TAVILY_API_KEY,
                                                 "query":
                                                 query,
                                                 "search_depth":
                                                 "basic",
                                                 "include_domains":
                                                 ["linkedin.com"],
                                                 "max_results":
                                                 5
                                             })

                if response.status_code == 200:
                    data = response.json()
                    for r in data.get("results", []):
                        url = r.get("url", "")
                        if "linkedin.com/in/" in url and \
                           "/company/" not in url:
                            url_clean = url.split("?")[0]
                            if url_clean not in resultados:
                                resultados.append(url_clean)
                                logger.info(f"[CARGO] LinkedIn por {cargo}: "
                                            f"{url_clean}")
        except Exception as e:
            logger.error(f"[CARGO] Error buscando {cargo}: {e}")

    return resultados[:5]  # Máximo 5 resultados


async def buscar_linkedin_en_web(contenido_web: str,
                                 nombre: str = "",
                                 apellido: str = "") -> list:
    """
    Busca URLs de LinkedIn personal en el contenido de la web.
    Busca en secciones Equipo, Nosotros, About, etc.
    """
    resultados = []

    # Patrón para LinkedIn personal
    pattern = r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)'
    matches = re.findall(pattern, contenido_web, re.IGNORECASE)

    for slug in matches:
        # Filtrar slugs genéricos
        if slug.lower() in ['company', 'jobs', 'pulse', 'learning']:
            continue

        url = f"https://linkedin.com/in/{slug}"

        # Si tenemos nombre/apellido, priorizar matches
        if nombre or apellido:
            slug_lower = slug.lower().replace("-", " ")
            nombre_lower = nombre.lower() if nombre else ""
            apellido_lower = apellido.lower() if apellido else ""

            if nombre_lower in slug_lower or apellido_lower in slug_lower:
                # Match con nombre, agregar al principio
                if url not in resultados:
                    resultados.insert(0, url)
                    logger.info(f"[WEB] LinkedIn en web (match nombre): {url}")
            else:
                if url not in resultados:
                    resultados.append(url)
                    logger.info(f"[WEB] LinkedIn en web: {url}")
        else:
            if url not in resultados:
                resultados.append(url)

    return resultados[:5]


async def buscar_linkedin_por_email(email: str) -> Optional[str]:
    """
    Busca LinkedIn usando el email como query.
    """
    if not TAVILY_API_KEY or not email or email == "No encontrado":
        return None

    # Extraer nombre del email (antes del @)
    nombre_email = email.split("@")[0]
    # Limpiar (quitar números, puntos, guiones)
    nombre_limpio = re.sub(r'[0-9._-]', ' ', nombre_email).strip()

    if len(nombre_limpio) < 3:
        return None

    query = f'"{email}" site:linkedin.com/in'

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://api.tavily.com/search",
                                         json={
                                             "api_key": TAVILY_API_KEY,
                                             "query": query,
                                             "search_depth": "basic",
                                             "include_domains":
                                             ["linkedin.com"],
                                             "max_results": 3
                                         })

            if response.status_code == 200:
                data = response.json()
                for r in data.get("results", []):
                    url = r.get("url", "")
                    if "linkedin.com/in/" in url:
                        url_clean = url.split("?")[0]
                        logger.info(f"[EMAIL] LinkedIn por email: {url_clean}")
                        return url_clean
    except Exception as e:
        logger.error(f"[EMAIL] Error: {e}")

    return None


async def tavily_buscar_linkedin_personal(nombre: str,
                                          empresa_busqueda: str,
                                          primer_nombre: str,
                                          apellido: str,
                                          ubicacion: str = "",
                                          city: str = "",
                                          province: str = "",
                                          country: str = "") -> Optional[dict]:
    """
    Busca LinkedIn personal usando Tavily con 2 FASES:
    - FASE 1: nombre + empresa + ubicación (alta confianza)
    - FASE 2: nombre + ubicación sin empresa (fallback)
    """
    if not TAVILY_API_KEY:
        return None

    # ═══════════════════════════════════════════════════════════════════
    # FASE 1: Búsqueda con nombre + empresa
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"[TAVILY] FASE 1: nombre + empresa + ubicación")
    resultado = await _tavily_buscar_linkedin_interno(
        nombre=nombre,
        empresa_busqueda=empresa_busqueda,
        primer_nombre=primer_nombre,
        apellido=apellido,
        ubicacion=ubicacion,
        city=city,
        province=province,
        country=country,
        incluir_empresa=True,
        umbral_score=50,
        confianza_base=70)

    if resultado and resultado.get("confianza", 0) >= 70:
        return resultado

    # ═══════════════════════════════════════════════════════════════════
    # FASE 2: Fallback solo nombre + ubicación (sin empresa)
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"[TAVILY] FASE 2: nombre + ubicación (sin empresa)")
    resultado_fallback = await _tavily_buscar_linkedin_interno(
        nombre=nombre,
        empresa_busqueda="",  # Sin empresa
        primer_nombre=primer_nombre,
        apellido=apellido,
        ubicacion=ubicacion,
        city=city,
        province=province,
        country=country,
        incluir_empresa=False,
        umbral_score=40,
        confianza_base=50  # Menor confianza porque no validó empresa
    )

    # Retornar el mejor resultado
    if resultado and resultado_fallback:
        if resultado["confianza"] >= resultado_fallback["confianza"]:
            return resultado
        return resultado_fallback

    return resultado or resultado_fallback


async def _tavily_buscar_linkedin_interno(
        nombre: str, empresa_busqueda: str, primer_nombre: str, apellido: str,
        ubicacion: str, city: str, province: str, country: str,
        incluir_empresa: bool, umbral_score: int,
        confianza_base: int) -> Optional[dict]:
    """
    Función interna de búsqueda LinkedIn con Tavily.
    """
    try:
        # Construir ubicación simplificada (solo provincia + país)
        ubicacion_simple = ""
        if province and province != "No encontrado":
            ubicacion_simple = province
            if country and country != "No encontrado":
                ubicacion_simple += f", {country}"
        elif country and country != "No encontrado":
            ubicacion_simple = country

        # Construir query - usar ubicación simplificada, no completa
        if incluir_empresa and empresa_busqueda:
            if ubicacion_simple:
                query = (f'"{nombre}" "{empresa_busqueda}" '
                         f'{ubicacion_simple} site:linkedin.com/in')
            else:
                query = (f'"{nombre}" "{empresa_busqueda}" '
                         f'site:linkedin.com/in')
        else:
            # Sin empresa, usar ubicación
            if ubicacion_simple:
                query = (f'"{nombre}" {ubicacion_simple} '
                         f'site:linkedin.com/in')
            else:
                query = f'"{nombre}" site:linkedin.com/in'

        logger.info(f"[TAVILY] Query: {query}")

        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post("https://api.tavily.com/search",
                                         json={
                                             "api_key": TAVILY_API_KEY,
                                             "query": query,
                                             "search_depth": "advanced",
                                             "include_domains":
                                             ["linkedin.com"],
                                             "max_results": 15,
                                             "include_raw_content": False
                                         })

            if response.status_code != 200:
                return None

            data = response.json()
            results = data.get("results", [])

            nombre_lower = nombre.lower()
            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()
            empresa_lower = empresa_busqueda.lower(
            ) if empresa_busqueda else ""
            city_lower = city.lower() if city else ""
            province_lower = province.lower() if province else ""
            country_lower = country.lower() if country else ""

            rubros_incompatibles = [
                'pinturas', 'pintura', 'inmobiliaria', 'real estate',
                'abogado', 'lawyer', 'médico', 'doctor', 'dentist'
            ]

            candidatos = []

            for result in results:
                url = result.get("url", "")
                titulo = (result.get("title", "") or "").lower()
                snippet = (result.get("content", "") or "").lower()
                texto = f"{titulo} {snippet}"

                if "linkedin.com/in/" not in url:
                    continue
                if "/company/" in url:
                    continue

                score = 0

                # Scoring por nombre en texto
                if nombre_lower in texto:
                    score += 50
                elif primer_lower in texto and apellido_lower in texto:
                    score += 45

                # Scoring por URL slug
                url_slug = ""
                if "/in/" in url:
                    url_slug = (
                        url.split("/in/")[1].split("/")[0].split("?")[0])
                url_slug_clean = url_slug.lower().replace("-", " ")

                if primer_lower in url_slug_clean and apellido_lower in url_slug_clean:
                    score += 40
                elif apellido_lower in url_slug_clean:
                    score += 25

                # ═══════════════════════════════════════════════════════
                # VALIDACIÓN ESTRICTA: debe tener nombre Y apellido
                # en texto O en URL
                # ═══════════════════════════════════════════════════════
                tiene_primer_nombre = (primer_lower in texto
                                       or primer_lower in url_slug_clean)
                tiene_apellido = (apellido_lower in texto
                                  or apellido_lower in url_slug_clean)
                tiene_match_nombre = tiene_primer_nombre and tiene_apellido

                # Scoring por empresa (solo si ya tiene match de nombre)
                tiene_match_empresa = False
                if empresa_lower and empresa_lower in texto:
                    tiene_match_empresa = True
                    score += 30

                # ═══════════════════════════════════════════════════════
                # SCORING POR UBICACIÓN (NUEVO)
                # ═══════════════════════════════════════════════════════
                if city_lower and city_lower in texto:
                    score += 15
                    logger.debug(f"[TAVILY] +15 por ciudad: {city}")
                if province_lower and province_lower in texto:
                    score += 10
                    logger.debug(f"[TAVILY] +10 por provincia: {province}")
                if country_lower and country_lower in texto:
                    score += 5
                    logger.debug(f"[TAVILY] +5 por país: {country}")

                # Detectar rubros incompatibles
                tiene_rubro_incompatible = False
                for rubro in rubros_incompatibles:
                    if rubro in texto and not tiene_match_empresa:
                        tiene_rubro_incompatible = True
                        break

                if tiene_rubro_incompatible:
                    logger.info(
                        f"[TAVILY] Descartado (rubro incompatible): {url}")
                    continue

                # Aceptar si tiene match de nombre y supera umbral
                if tiene_match_nombre and score >= umbral_score:
                    # ═══════════════════════════════════════════════════════
                    # VALIDACIÓN ADICIONAL CON calcular_peso_linkedin
                    # Esto descarta perfiles donde nombre/apellido aparecen
                    # en el snippet pero NO corresponden a ESE perfil
                    # Ejemplo: descarta "Samuel Rodriguez" cuando buscamos
                    # "Rafael Driuzzi"
                    # ═══════════════════════════════════════════════════════
                    peso_verificacion = calcular_peso_linkedin(
                        url=url,
                        texto=texto,
                        primer_nombre=primer_lower,
                        apellido=apellido_lower,
                        empresa=empresa_lower,
                        provincia=province,
                        ciudad=city,
                        pais=country)

                    # Si peso < 60, significa que NO tiene nombre+apellido
                    # en la URL/texto de ESE perfil específico
                    if peso_verificacion < 60:
                        logger.info(f"[TAVILY] Descartado por peso: {url} "
                                    f"(peso: {peso_verificacion} < 60)")
                        continue

                    logger.info(f"[TAVILY] ✓ Candidato: {url} "
                                f"(score: {score}, peso: {peso_verificacion})")
                    candidatos.append({
                        "url": url.split("?")[0],
                        "confianza": min(score, 100),
                        "score": score,
                        "tiene_empresa": tiene_match_empresa
                    })

            candidatos.sort(key=lambda x: x["confianza"], reverse=True)

            if candidatos:
                # Devolver hasta 3 candidatos separados por " | "
                resultados = []
                for c in candidatos[:3]:
                    conf = min(95,
                               confianza_base + (c["score"] - umbral_score))
                    resultados.append({"url": c["url"], "confianza": conf})

                mejor_conf = resultados[0]["confianza"]

                if len(resultados) == 1:
                    logger.info(f"[TAVILY] ✓ LinkedIn: {resultados[0]['url']}")
                    return resultados[0]
                else:
                    urls = [r["url"] for r in resultados]
                    logger.info(f"[TAVILY] ✓ LinkedIn múltiples: {len(urls)}")
                    return {"url": " | ".join(urls), "confianza": mejor_conf}

            return None

    except Exception as e:
        logger.error(f"[TAVILY] Error buscando LinkedIn personal: {e}")
        return None


async def google_buscar_linkedin_personal(nombre: str,
                                          empresa_busqueda: str,
                                          primer_nombre: str,
                                          apellido: str,
                                          confianza_actual: int,
                                          ubicacion: str = "",
                                          city: str = "",
                                          province: str = "",
                                          country: str = "") -> Optional[dict]:
    """
    Busca LinkedIn personal con Google Custom Search (2 FASES).
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        return None

    # ═══════════════════════════════════════════════════════════════════
    # FASE 1: Búsqueda con nombre + empresa
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"[GOOGLE] FASE 1: nombre + empresa + ubicación")
    resultado = await _google_buscar_linkedin_interno(
        nombre=nombre,
        empresa_busqueda=empresa_busqueda,
        primer_nombre=primer_nombre,
        apellido=apellido,
        ubicacion=ubicacion,
        city=city,
        province=province,
        country=country,
        confianza_actual=confianza_actual,
        incluir_empresa=True,
        umbral_score=50,
        confianza_base=70)

    if resultado and resultado.get("confianza", 0) >= 70:
        return resultado

    # ═══════════════════════════════════════════════════════════════════
    # FASE 2: Fallback solo nombre + ubicación (sin empresa)
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"[GOOGLE] FASE 2: nombre + ubicación (sin empresa)")
    resultado_fallback = await _google_buscar_linkedin_interno(
        nombre=nombre,
        empresa_busqueda="",
        primer_nombre=primer_nombre,
        apellido=apellido,
        ubicacion=ubicacion,
        city=city,
        province=province,
        country=country,
        confianza_actual=confianza_actual,
        incluir_empresa=False,
        umbral_score=40,
        confianza_base=50)

    if resultado and resultado_fallback:
        if resultado["confianza"] >= resultado_fallback["confianza"]:
            return resultado
        return resultado_fallback

    return resultado or resultado_fallback


async def _google_buscar_linkedin_interno(
        nombre: str, empresa_busqueda: str, primer_nombre: str, apellido: str,
        ubicacion: str, city: str, province: str, country: str,
        confianza_actual: int, incluir_empresa: bool, umbral_score: int,
        confianza_base: int) -> Optional[dict]:
    """
    Función interna de búsqueda LinkedIn con Google.
    """
    try:
        # Construir ubicación simplificada (solo provincia + país)
        ubicacion_simple = ""
        if province and province != "No encontrado":
            ubicacion_simple = province
            if country and country != "No encontrado":
                ubicacion_simple += f" {country}"
        elif country and country != "No encontrado":
            ubicacion_simple = country

        # Construir query con ubicación simplificada
        if incluir_empresa and empresa_busqueda:
            if ubicacion_simple:
                query = (f"site:linkedin.com/in {nombre} "
                         f"{empresa_busqueda} {ubicacion_simple}")
            else:
                query = f"site:linkedin.com/in {nombre} {empresa_busqueda}"
        else:
            if ubicacion_simple:
                query = f"site:linkedin.com/in {nombre} {ubicacion_simple}"
            else:
                query = f"site:linkedin.com/in {nombre}"

        url = (f"https://www.googleapis.com/customsearch/v1"
               f"?cx={GOOGLE_SEARCH_CX}"
               f"&q={quote(query)}&num=10&key={GOOGLE_API_KEY}")

        logger.info(f"[GOOGLE] Query: {query}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)

            if response.status_code != 200:
                logger.warning(f"[GOOGLE] Error {response.status_code} "
                               f"buscando LinkedIn personal")
                return None

            data = response.json()
            items = data.get("items", [])

            nombre_lower = nombre.lower()
            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()
            empresa_lower = empresa_busqueda.lower(
            ) if empresa_busqueda else ""
            city_lower = city.lower() if city else ""
            province_lower = province.lower() if province else ""
            country_lower = country.lower() if country else ""

            rubros_incompatibles = [
                'pinturas', 'pintura', 'inmobiliaria', 'real estate',
                'abogado', 'lawyer', 'médico', 'doctor', 'dentist'
            ]

            candidatos = []

            for item in items:
                link = item.get("link", "")
                titulo = (item.get("title", "") or "").lower()
                snippet = (item.get("snippet", "") or "").lower()
                texto = f"{titulo} {snippet}"

                if "linkedin.com/in/" not in link:
                    continue

                score = 0

                # Scoring por nombre en texto
                if nombre_lower in texto:
                    score += 40
                elif primer_lower in texto and apellido_lower in texto:
                    score += 35

                # Scoring por URL slug
                url_slug = ""
                if "/in/" in link:
                    url_slug = (
                        link.split("/in/")[1].split("/")[0].split("?")[0])
                url_slug_lower = url_slug.lower().replace("-", "")
                url_slug_clean = url_slug.lower().replace("-", " ")

                if (primer_lower in url_slug_lower
                        and apellido_lower in url_slug_lower):
                    score += 30
                elif apellido_lower in url_slug_lower:
                    score += 15

                # ═══════════════════════════════════════════════════════
                # VALIDACIÓN ESTRICTA: debe tener nombre Y apellido
                # en texto O en URL
                # ═══════════════════════════════════════════════════════
                tiene_primer_nombre = (primer_lower in texto
                                       or primer_lower in url_slug_clean)
                tiene_apellido = (apellido_lower in texto
                                  or apellido_lower in url_slug_clean)
                tiene_match_nombre = tiene_primer_nombre and tiene_apellido

                # Scoring por empresa (solo si ya tiene match de nombre)
                tiene_match_empresa = False
                if empresa_lower and empresa_lower in texto:
                    tiene_match_empresa = True
                    score += 30

                # ═══════════════════════════════════════════════════════
                # SCORING POR UBICACIÓN (NUEVO)
                # ═══════════════════════════════════════════════════════
                if city_lower and city_lower in texto:
                    score += 15
                if province_lower and province_lower in texto:
                    score += 10
                if country_lower and country_lower in texto:
                    score += 5

                # Detectar rubros incompatibles
                tiene_rubro_incompatible = False
                for rubro in rubros_incompatibles:
                    if rubro in texto and not tiene_match_empresa:
                        tiene_rubro_incompatible = True
                        break

                if tiene_rubro_incompatible:
                    logger.info(
                        f"[GOOGLE] Descartado (rubro incompatible): {link}")
                    continue

                if tiene_match_nombre and score >= umbral_score:
                    # ═══════════════════════════════════════════════════════
                    # VALIDACIÓN ADICIONAL CON calcular_peso_linkedin
                    # ═══════════════════════════════════════════════════════
                    peso_verificacion = calcular_peso_linkedin(
                        url=link,
                        texto=texto,
                        primer_nombre=primer_lower,
                        apellido=apellido_lower,
                        empresa=empresa_lower,
                        provincia=province,
                        ciudad=city,
                        pais=country)

                    if peso_verificacion < 60:
                        logger.info(f"[GOOGLE] Descartado por peso: {link} "
                                    f"(peso: {peso_verificacion} < 60)")
                        continue

                    logger.info(f"[GOOGLE] ✓ Candidato: {link} "
                                f"(score: {score}, peso: {peso_verificacion})")
                    candidatos.append({
                        "url": link,
                        "score": score,
                        "tiene_empresa": tiene_match_empresa
                    })

            candidatos.sort(key=lambda x: x["score"], reverse=True)

            if candidatos:
                # Devolver hasta 3 candidatos separados por " | "
                resultados = []
                for c in candidatos[:3]:
                    conf = min(95,
                               confianza_base + (c["score"] - umbral_score))
                    resultados.append({"url": c["url"], "confianza": conf})

                mejor = resultados[0]
                if mejor["confianza"] > confianza_actual:
                    if len(resultados) == 1:
                        logger.info(f"[GOOGLE] ✓ LinkedIn: {mejor['url']}")
                        return mejor
                    else:
                        urls = [r["url"] for r in resultados]
                        logger.info(
                            f"[GOOGLE] ✓ LinkedIn múltiples: {len(urls)}")
                        return {
                            "url": " | ".join(urls),
                            "confianza": mejor["confianza"]
                        }

            return None

    except Exception as e:
        logger.error(f"[GOOGLE] Error buscando LinkedIn personal: {e}")
        return None


async def apify_buscar_noticias(empresa_busqueda: str,
                                ubicacion_query: str = "") -> List[dict]:
    """
    Busca noticias usando Apify website-content-crawler.
    """
    if not APIFY_API_TOKEN:
        return []

    try:
        # Query para Google News - usar nombre completo
        # Si empresa_busqueda es solo siglas (DPM), agregar contexto
        query_parts = []

        # Usar nombre completo entre comillas para exactitud
        if empresa_busqueda:
            # Si parece sigla (menos de 5 chars), buscar con
            # más contexto
            if len(empresa_busqueda.replace(" ", "")) <= 5:
                query_parts.append(f'"{empresa_busqueda}"')
            else:
                query_parts.append(f'"{empresa_busqueda}"')

        # Agregar rubro si está disponible (viene del context)
        # Por ahora solo ubicación
        if ubicacion_query:
            query_parts.append(ubicacion_query)

        query = " ".join(query_parts)

        # URLs de noticias
        news_urls = [
            f"https://news.google.com/search?q={quote(query)}&hl=es-419",
            f"https://www.bing.com/news/search?q={quote(query)}"
        ]

        start_urls = [{"url": u} for u in news_urls]

        async with httpx.AsyncClient(timeout=APIFY_TIMEOUT) as client:
            # Iniciar el crawler
            response = await client.post(
                f"https://api.apify.com/v2/acts/apify~website-content-crawler"
                f"/runs?token={APIFY_API_TOKEN}&waitForFinish=30",
                json={
                    "startUrls": start_urls,
                    "maxCrawlPages": 20,
                    "maxCrawlDepth": 1,
                    "proxyConfiguration": {
                        "useApifyProxy": True
                    }
                })

            if response.status_code != 201:
                logger.warning(
                    f"[APIFY] Error iniciando crawler: {response.status_code}")
                return []

            run_data = response.json()
            dataset_id = run_data.get("data", {}).get("defaultDatasetId")

            if not dataset_id:
                return []

            # Obtener resultados
            results_response = await client.get(
                f"https://api.apify.com/v2/datasets/{dataset_id}/items"
                f"?token={APIFY_API_TOKEN}")

            if results_response.status_code != 200:
                return []

            items = results_response.json()

            empresa_lower = empresa_busqueda.lower()
            noticias = []

            for item in items:
                url = item.get("url", "")
                titulo = item.get("title", "") or ""
                texto = item.get("text", "") or ""
                texto_lower = texto.lower()

                # Las redes sociales ya se filtran en es_url_valida_noticia
                # No las procesamos como noticias

                # Saltar buscadores y registros legales
                if es_buscador(url):
                    continue
                if es_registro_legal(url, f"{titulo} {texto}"):
                    continue

                if not es_url_valida_noticia(url, f"{titulo} {texto}",
                                             empresa_busqueda):
                    logger.debug(f"[NOTICIAS] Descartado: {url[:50]}...")
                    continue

                # Verificar relevancia
                palabras_empresa = [
                    p for p in empresa_lower.split() if len(p) > 3
                ]
                if (empresa_lower in texto_lower
                        or any(p in texto_lower for p in palabras_empresa)):
                    noticia = {
                        "titulo": titulo[:200] if titulo else "Sin título",
                        "url": url,
                        "resumen": texto[:300] if texto else "",
                        "source": "apify"
                    }

                    noticias.append(noticia)

            noticias_finales = noticias

            logger.info(
                f"[APIFY] ✓ {len(noticias_finales)} noticias procesadas")
            return noticias_finales[:10]

    except asyncio.TimeoutError:
        logger.warning("[APIFY] Timeout esperando crawler")
        return []
    except Exception as e:
        logger.error(f"[APIFY] Error: {e}")
        return []


async def google_buscar_noticias(empresa: str, empresa_busqueda: str,
                                 ubicacion_query: str) -> List[dict]:
    """
    Busca noticias relevantes de la empresa con Google.
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        return []

    try:
        query_parts = []

        # Usar nombre completo de empresa
        if empresa:
            query_parts.append(f'"{empresa}"')

        # Si empresa_busqueda es diferente (tiene dominio),
        # agregarlo
        if empresa_busqueda and empresa_busqueda != empresa:
            # Extraer dominio limpio si es URL
            dominio = empresa_busqueda.replace("https://", "").replace(
                "http://", "").replace("www.", "").split("/")[0]
            if "." in dominio:
                query_parts.append(f'OR "{dominio}"')

        query_parts.append("noticias OR prensa OR nota")

        query = " ".join(query_parts)
        url = (f"https://www.googleapis.com/customsearch/v1"
               f"?cx={GOOGLE_SEARCH_CX}&q={quote(query)}"
               f"&num=10&key={GOOGLE_API_KEY}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)

            if response.status_code != 200:
                logger.warning(
                    f"[GOOGLE] Error {response.status_code} buscando noticias")
                return []

            data = response.json()
            items = data.get("items", [])

            empresa_lower = empresa.lower()
            palabras_clave = [p for p in empresa_lower.split() if len(p) > 2]

            noticias = []

            for item in items:
                url = item.get("link", "")
                titulo = item.get("title", "") or ""
                snippet = item.get("snippet", "") or ""
                texto = f"{titulo} {snippet}"
                texto_lower = texto.lower()

                # Las redes sociales ya se filtran en es_url_valida_noticia
                # No las procesamos como noticias

                if es_buscador(url):
                    continue
                if es_registro_legal(url, texto):
                    continue

                if not es_url_valida_noticia(url, texto, empresa_busqueda):
                    continue

                # Verificar relevancia
                matches = sum(1 for p in palabras_clave if p in texto_lower)
                if matches >= 1 or empresa_lower in texto_lower:
                    noticia = {
                        "titulo": titulo[:200] if titulo else "Sin título",
                        "url": url,
                        "resumen": snippet[:300] if snippet else "",
                        "source": "google"
                    }

                    noticias.append(noticia)

            noticias_finales = noticias

            logger.info(
                f"[GOOGLE] ✓ {len(noticias_finales)} noticias encontradas")
            return noticias_finales[:10]

    except Exception as e:
        logger.error(f"[GOOGLE] Error buscando noticias: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES WRAPPER PARA BACKWARD COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════════


async def search_news(business_name: str,
                      person_name: str = "",
                      location: str = "") -> List[dict]:
    """Wrapper para búsqueda de noticias."""
    if APIFY_API_TOKEN:
        noticias = await apify_buscar_noticias(business_name, location)
        if noticias:
            return noticias
    return await google_buscar_noticias(business_name, business_name, location)
