#!/usr/bin/env python3
"""
Script de prueba para verificar detección de ubicación por número
Ejecutar en Replit Shell: python test_ubicacion.py
"""

from config import detect_country

# Números de prueba (formato E.164 sin el +)
NUMEROS_PRUEBA = [
    # México - móviles con "1"
    ("5219843162719", "Playa del Carmen, Quintana Roo, México"),
    ("5215512345678", "Ciudad de México, CDMX, México"),
    ("5218112345678", "Monterrey, Nuevo León, México"),
    ("5213312345678", "Guadalajara, Jalisco, México"),
    
    # USA
    ("15125551234", "Austin, Texas, USA"),
    ("13055551234", "Miami, Florida, USA"),
    ("12125551234", "Manhattan, New York, USA"),
    ("14155551234", "San Francisco, California, USA"),
    ("17025551234", "Las Vegas, Nevada, USA"),
    
    # Brasil
    ("5511912345678", "São Paulo, São Paulo, Brasil"),
    ("5521912345678", "Rio de Janeiro, Rio de Janeiro, Brasil"),
    ("5541912345678", "Curitiba, Paraná, Brasil"),
    
    # Argentina (ya funcionaba)
    ("5493415551234", "Rosario, Santa Fe, Argentina"),
    ("5491112345678", "Buenos Aires, Buenos Aires, Argentina"),
    
    # España (móvil - solo país)
    ("34665989983", "España (móvil, sin ciudad)"),
    ("34911234567", "Madrid, Madrid, España (fijo)"),
]

def main():
    print("=" * 70)
    print("PRUEBA DE DETECCIÓN DE UBICACIÓN POR NÚMERO")
    print("=" * 70)
    print()
    
    exitosos = 0
    fallidos = 0
    
    for numero, esperado in NUMEROS_PRUEBA:
        resultado = detect_country(numero)
        
        # Construir string de ubicación detectada
        if resultado:
            partes = []
            if resultado.get('city'):
                partes.append(resultado['city'])
            if resultado.get('province'):
                partes.append(resultado['province'])
            if resultado.get('country'):
                partes.append(resultado['country'])
            ubicacion = ", ".join(partes)
            emoji = resultado.get('emoji', '')
        else:
            ubicacion = "NO DETECTADO"
            emoji = "❌"
        
        # Mostrar resultado
        print(f"📞 +{numero}")
        print(f"   Esperado: {esperado}")
        print(f"   Detectado: {ubicacion} {emoji}")
        
        # Verificar si es correcto (simplificado)
        if resultado and resultado.get('city'):
            print(f"   ✅ OK")
            exitosos += 1
        elif resultado and not resultado.get('city') and 'móvil' in esperado:
            print(f"   ✅ OK (móvil sin ciudad es correcto)")
            exitosos += 1
        else:
            print(f"   ⚠️  REVISAR")
            fallidos += 1
        print()
    
    print("=" * 70)
    print(f"RESULTADO: {exitosos} exitosos, {fallidos} a revisar")
    print("=" * 70)

if __name__ == "__main__":
    main()
