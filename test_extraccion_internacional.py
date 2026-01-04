"""
═══════════════════════════════════════════════════════════════════════════════
TEST DE EXTRACCIÓN - PyMEs Y EMPRESAS MEDIANAS LATAM
═══════════════════════════════════════════════════════════════════════════════

Público objetivo real de Fortia:
- PyMEs chicas (5-20 empleados)
- Empresas medianas (20-200 empleados)
- Empresas que facturan hasta varios millones USD/año
- NO multinacionales

RUBROS TESTEADOS:
- Agencias de marketing/publicidad
- Estudios contables/legales
- Distribuidores/mayoristas
- Software houses locales
- Consultoras
- Clínicas/salud
- Inmobiliarias
- Constructoras

═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTAR FUNCIONES DEL PROYECTO
# ═══════════════════════════════════════════════════════════════════════════════

IMPORTS_OK = True
IMPORT_ERRORS = []

try:
    from services.web_extractor import extract_web_data
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERRORS.append(f"web_extractor: {e}")

try:
    from services.social_research import research_person_and_company
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERRORS.append(f"social_research: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# DATOS DE TEST - PyMEs Y MEDIANAS REALES DE LATAM
# ═══════════════════════════════════════════════════════════════════════════════

TESTS = [
    # ─────────────────────────────────────────────────────────────────────────
    # ARGENTINA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "pais": "Argentina",
        "bandera": "🇦🇷",
        "tipo": "Agencia Marketing",
        "lead": {
            "nombre": "Martín González",
            "telefono": "+5491145678901",
            "codigo_pais": "+54"
        },
        "empresa": {
            "web": "wearecontent.com",
            "nombre_esperado": "We Are Content",
            "rubro": "Marketing de contenidos",
            "pais_empresa": "Argentina",
            "ciudad_esperada": "Buenos Aires"
        }
    },
    {
        "pais": "Argentina",
        "bandera": "🇦🇷",
        "tipo": "Estudio Contable",
        "lead": {
            "nombre": "Laura Fernández",
            "telefono": "+5491156789012",
            "codigo_pais": "+54"
        },
        "empresa": {
            "web": "baborcontadores.com.ar",
            "nombre_esperado": "Babor Contadores",
            "rubro": "Estudio contable",
            "pais_empresa": "Argentina",
            "ciudad_esperada": "Buenos Aires"
        }
    },
    {
        "pais": "Argentina",
        "bandera": "🇦🇷",
        "tipo": "Software House",
        "lead": {
            "nombre": "Diego Rodríguez",
            "telefono": "+5491167890123",
            "codigo_pais": "+54"
        },
        "empresa": {
            "web": "baufest.com",
            "nombre_esperado": "Baufest",
            "rubro": "Desarrollo de software",
            "pais_empresa": "Argentina",
            "ciudad_esperada": "Buenos Aires"
        }
    },
    # ─────────────────────────────────────────────────────────────────────────
    # MÉXICO
    # ─────────────────────────────────────────────────────────────────────────
    {
        "pais": "México",
        "bandera": "🇲🇽",
        "tipo": "Agencia Digital",
        "lead": {
            "nombre": "Roberto Hernández",
            "telefono": "+5215512345678",
            "codigo_pais": "+52"
        },
        "empresa": {
            "web": "mediasource.mx",
            "nombre_esperado": "Media Source",
            "rubro": "Marketing digital / Inbound",
            "pais_empresa": "México",
            "ciudad_esperada": "Ciudad de México"
        }
    },
    {
        "pais": "México",
        "bandera": "🇲🇽",
        "tipo": "Consultora IT",
        "lead": {
            "nombre": "Ana Martínez",
            "telefono": "+5215523456789",
            "codigo_pais": "+52"
        },
        "empresa": {
            "web": "nativapps.com",
            "nombre_esperado": "Nativapps",
            "rubro": "Desarrollo de apps",
            "pais_empresa": "México",
            "ciudad_esperada": "CDMX"
        }
    },
    # ─────────────────────────────────────────────────────────────────────────
    # COLOMBIA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "pais": "Colombia",
        "bandera": "🇨🇴",
        "tipo": "Agencia Publicidad",
        "lead": {
            "nombre": "Camila López",
            "telefono": "+573101234567",
            "codigo_pais": "+57"
        },
        "empresa": {
            "web": "indexcol.com",
            "nombre_esperado": "Index",
            "rubro": "Agencia de publicidad",
            "pais_empresa": "Colombia",
            "ciudad_esperada": "Bogotá"
        }
    },
    {
        "pais": "Colombia",
        "bandera": "🇨🇴",
        "tipo": "Software/ERP",
        "lead": {
            "nombre": "Andrés Gómez",
            "telefono": "+573112345678",
            "codigo_pais": "+57"
        },
        "empresa": {
            "web": "silogsistemas.com",
            "nombre_esperado": "Silog Sistemas",
            "rubro": "Software ERP/Logística",
            "pais_empresa": "Colombia",
            "ciudad_esperada": "Bogotá"
        }
    },
    # ─────────────────────────────────────────────────────────────────────────
    # CHILE
    # ─────────────────────────────────────────────────────────────────────────
    {
        "pais": "Chile",
        "bandera": "🇨🇱",
        "tipo": "Consultora",
        "lead": {
            "nombre": "Felipe Muñoz",
            "telefono": "+56912345678",
            "codigo_pais": "+56"
        },
        "empresa": {
            "web": "digital.cl",
            "nombre_esperado": "Digital",
            "rubro": "Transformación digital",
            "pais_empresa": "Chile",
            "ciudad_esperada": "Santiago"
        }
    },
    # ─────────────────────────────────────────────────────────────────────────
    # PERÚ
    # ─────────────────────────────────────────────────────────────────────────
    {
        "pais": "Perú",
        "bandera": "🇵🇪",
        "tipo": "Agencia Marketing",
        "lead": {
            "nombre": "Carla Vargas",
            "telefono": "+51987654321",
            "codigo_pais": "+51"
        },
        "empresa": {
            "web": "staffcreativa.pe",
            "nombre_esperado": "Staff Creativa",
            "rubro": "Agencia de marketing",
            "pais_empresa": "Perú",
            "ciudad_esperada": "Lima"
        }
    },
    # ─────────────────────────────────────────────────────────────────────────
    # ESPAÑA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "pais": "España",
        "bandera": "🇪🇸",
        "tipo": "Estudio Diseño",
        "lead": {
            "nombre": "Pablo García",
            "telefono": "+34612345678",
            "codigo_pais": "+34"
        },
        "empresa": {
            "web": "brandcrops.com",
            "nombre_esperado": "Brandcrops",
            "rubro": "Branding y diseño",
            "pais_empresa": "España",
            "ciudad_esperada": "Barcelona"
        }
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE DETECCIÓN
# ═══════════════════════════════════════════════════════════════════════════════

CODIGOS_PAIS = {
    "+54": {
        "pais": "Argentina",
        "timezone": "America/Argentina/Buenos_Aires"
    },
    "+52": {
        "pais": "México",
        "timezone": "America/Mexico_City"
    },
    "+57": {
        "pais": "Colombia",
        "timezone": "America/Bogota"
    },
    "+56": {
        "pais": "Chile",
        "timezone": "America/Santiago"
    },
    "+55": {
        "pais": "Brasil",
        "timezone": "America/Sao_Paulo"
    },
    "+51": {
        "pais": "Perú",
        "timezone": "America/Lima"
    },
    "+34": {
        "pais": "España",
        "timezone": "Europe/Madrid"
    },
}


def detectar_pais_por_telefono(telefono: str) -> Dict:
    """Detecta país y timezone por código de teléfono"""
    for codigo, datos in sorted(CODIGOS_PAIS.items(),
                                key=lambda x: len(x[0]),
                                reverse=True):
        if telefono.startswith(codigo):
            return {
                "codigo": codigo,
                "pais": datos["pais"],
                "timezone": datos["timezone"],
                "detectado": True
            }
    return {
        "codigo": "?",
        "pais": "Desconocido",
        "timezone": "UTC",
        "detectado": False
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL DE TEST
# ═══════════════════════════════════════════════════════════════════════════════


async def run_single_test(test_data: Dict) -> Dict:
    """Ejecuta un test individual"""
    resultado = {
        "pais": test_data["pais"],
        "bandera": test_data["bandera"],
        "tipo": test_data.get("tipo", ""),
        "lead": test_data["lead"],
        "empresa_esperada": test_data["empresa"],
        "extraido": {},
        "scores": {},
        "tiempo": 0,
        "errores": []
    }

    start_time = time.time()

    try:
        # 1. Detectar país del lead por teléfono
        pais_lead = detectar_pais_por_telefono(test_data["lead"]["telefono"])
        resultado["extraido"]["pais_lead"] = pais_lead

        # 2. Extraer datos de la web
        web_data = await extract_web_data(test_data["empresa"]["web"])
        resultado["extraido"]["web"] = web_data

        # 3. Buscar LinkedIn del CEO (si hay nombre)
        linkedin_ceo = None
        try:
            ceo_nombre = web_data.get("ceo_nombre", "")
            cargo = web_data.get("cargo_detectado", "")
            if ceo_nombre and ceo_nombre != "No encontrado":
                research = await research_person_and_company(
                    nombre=ceo_nombre,
                    website=test_data["empresa"]["web"],
                    cargo=cargo)
                linkedin_ceo = research.get("linkedin_personal")
        except Exception as e:
            resultado["errores"].append(f"LinkedIn CEO: {str(e)}")

        resultado["extraido"]["linkedin_ceo"] = linkedin_ceo

    except Exception as e:
        resultado["errores"].append(f"Extracción: {str(e)}")

    resultado["tiempo"] = round(time.time() - start_time, 2)

    # Calcular scores
    resultado["scores"] = calcular_scores(resultado)

    return resultado


def calcular_scores(resultado: Dict) -> Dict:
    """Calcula el score de completitud"""
    web = resultado.get("extraido", {}).get("web", {})

    campos = {
        "Nombre empresa": web.get("business_name", ""),
        "Modelo negocio": web.get("business_model", ""),
        "Email": web.get("email_principal", ""),
        "Teléfono": web.get("phone_empresa", ""),
        "WhatsApp": web.get("whatsapp_empresa", ""),
        "Dirección": web.get("address", ""),
        "Ciudad/Provincia": web.get("province") or web.get("city", ""),
        "Horarios": web.get("horarios", ""),
        "LinkedIn empresa": web.get("linkedin_empresa", ""),
        "Cargo detectado": web.get("cargo_detectado", ""),
        "LinkedIn CEO": resultado.get("extraido", {}).get("linkedin_ceo"),
    }

    encontrados = 0
    detalle = {}

    for campo, valor in campos.items():
        es_valido = bool(valor and valor != "No encontrado"
                         and valor != "No encontrado")
        if es_valido:
            encontrados += 1
        detalle[campo] = {"encontrado": es_valido, "valor": valor}

    return {
        "campos_encontrados": encontrados,
        "campos_totales": len(campos),
        "detalle": detalle,
        "porcentaje": round(encontrados / len(campos) * 100)
    }


def imprimir_resultado(r: Dict):
    """Imprime resultado de un test"""
    scores = r.get("scores", {})
    detalle = scores.get("detalle", {})

    print(f"\n{r['bandera']} {r['pais']} - {r['empresa_esperada']['web']}")
    print(f"   Tipo: {r.get('tipo', 'N/A')}")
    print(f"   Lead: {r['lead']['nombre']} ({r['lead']['telefono']})")
    print(f"   Tiempo: {r['tiempo']}s")
    print()

    for campo, info in detalle.items():
        icono = "✓" if info["encontrado"] else "✗"
        valor = info["valor"] if info["encontrado"] else "NO ENCONTRADO"
        # Truncar valores largos
        if isinstance(valor, str) and len(valor) > 50:
            valor = valor[:47] + "..."
        print(f"   {icono} {campo}: {valor}")

    print(
        f"\n   SCORE: {scores['campos_encontrados']}/{scores['campos_totales']}"
        f" ({scores['porcentaje']}%)")
    print("─" * 75)


async def main():
    """Función principal"""
    print("=" * 75)
    print("TEST DE EXTRACCIÓN - PyMEs Y EMPRESAS MEDIANAS LATAM")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    if not IMPORTS_OK:
        print("\n❌ ERROR: No se pudieron importar los módulos:")
        for err in IMPORT_ERRORS:
            print(f"   - {err}")
        return

    resultados = []
    total_score = 0
    total_tiempo = 0

    for i, test in enumerate(TESTS, 1):
        print(f"\n[{i}/{len(TESTS)}] Testeando {test['empresa']['web']}...")

        resultado = await run_single_test(test)
        resultados.append(resultado)

        imprimir_resultado(resultado)

        total_score += resultado["scores"]["porcentaje"]
        total_tiempo += resultado["tiempo"]

    # Resumen
    print("\n" + "=" * 75)
    print("RESUMEN GLOBAL - PyMEs LATAM")
    print("=" * 75)

    promedio = round(total_score / len(TESTS))
    print(f"\n📊 Promedio de completitud: {promedio}%")
    print(f"⏱️  Tiempo promedio: {round(total_tiempo / len(TESTS), 2)}s")
    print(f"🔢 Empresas testeadas: {len(TESTS)}")

    # Campos con más fallos
    fallos_por_campo = {}
    for r in resultados:
        for campo, info in r["scores"]["detalle"].items():
            if not info["encontrado"]:
                fallos_por_campo[campo] = fallos_por_campo.get(campo, 0) + 1

    print("\n⚠️  Campos con más fallos:")
    for campo, fallos in sorted(fallos_por_campo.items(),
                                key=lambda x: x[1],
                                reverse=True)[:5]:
        print(f"   - {campo}: {fallos} fallos")

    # Guardar resultados
    os.makedirs("test_results", exist_ok=True)

    # Reporte texto
    report_file = f"test_results/pymes_latam_{datetime.now():%Y%m%d_%H%M}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=" * 75 + "\n")
        f.write("TEST DE EXTRACCIÓN - PyMEs Y EMPRESAS MEDIANAS LATAM\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 75 + "\n")

        for r in resultados:
            scores = r["scores"]
            detalle = scores["detalle"]

            f.write(
                f"\n{r['bandera']} {r['pais']} - {r['empresa_esperada']['web']}\n"
            )
            f.write(f"   Tipo: {r.get('tipo', 'N/A')}\n")
            f.write(
                f"   Lead: {r['lead']['nombre']} ({r['lead']['telefono']})\n")
            f.write(f"   Tiempo: {r['tiempo']}s\n\n")

            for campo, info in detalle.items():
                icono = "✓" if info["encontrado"] else "✗"
                valor = info["valor"] if info["encontrado"] else "NO ENCONTRADO"
                if isinstance(valor, str) and len(valor) > 50:
                    valor = valor[:47] + "..."
                f.write(f"   {icono} {campo}: {valor}\n")

            f.write(f"\n   SCORE: {scores['campos_encontrados']}/"
                    f"{scores['campos_totales']} ({scores['porcentaje']}%)\n")
            f.write("─" * 75 + "\n")

        f.write("\n" + "=" * 75 + "\n")
        f.write("RESUMEN GLOBAL\n")
        f.write("=" * 75 + "\n")
        f.write(f"\n📊 Promedio de completitud: {promedio}%\n")
        f.write(
            f"⏱️  Tiempo promedio: {round(total_tiempo / len(TESTS), 2)}s\n")
        f.write(f"🔢 Empresas testeadas: {len(TESTS)}\n")

    # JSON completo
    json_file = f"test_results/pymes_latam_{datetime.now():%Y%m%d_%H%M}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\n📁 Resultados guardados en:")
    print(f"   - {report_file}")
    print(f"   - {json_file}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
