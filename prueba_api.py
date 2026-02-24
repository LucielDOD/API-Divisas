import sys
from modulos.API_consultas import Solicitar_Divisas_Disponibles, Solicitar_Valor_Divisa

# Aquí definimos la URL donde la API buscará los datos (en tu nube / GitHub)
URL_API_GITHUB = "https://LucielDOD.github.io/API-Divisas/datos.json"

def menu():
    while True:
        print("\n======================================================")
        print("                 PRUEBAS DE LA API                    ")
        print("======================================================")
        print("1. Obtener lista de divisas disponibles")
        print("2. Consultar valor de conversión entre dos divisas")
        print("3. Cambiar URL de origen de datos (API)")
        print("4. Salir")
        print("======================================================")
        print(f"URL Actual: {URL_API_GITHUB}")
        print("======================================================")
        
        opcion = input("Elige una opción (1-4): ").strip()
        global URL_API_GITHUB
        
        if opcion == '1':
            print(f"\n[Consultando divisas disponibles desde GitHub...]")
            divisas = Solicitar_Divisas_Disponibles(url_origen=URL_API_GITHUB)
            if divisas:
                print(f"[OK] Se obtuvieron {len(divisas)} divisas.")
                print("Lista de divisas (ejemplos):")
                # Mostrar en formato de filas para no saturar la pantalla
                for i in range(0, len(divisas), 10):
                    print(", ".join(divisas[i:i+10]))
            else:
                print("[ERROR] No se pudo obtener la lista. Verifica que el repositorio sea público y la URL sea correcta.")
                
        elif opcion == '2':
            div_1 = input("Introduce la divisa base (ej: USD): ").strip().upper()
            div_2 = input("Introduce la divisa objetivo (ej: EUR): ").strip().upper()
            
            if not div_1 or not div_2:
                print("[ERROR] Debes ingresar ambas divisas.")
                continue
                
            print(f"\n[Calculando conversión de {div_1} a {div_2} desde GitHub...]")
            try:
                # Se pasa la URL configurada al módulo de consultas
                resultado = Solicitar_Valor_Divisa(div_1, div_2, url_origen=URL_API_GITHUB)
                if resultado and resultado > 0:
                    print(f"[OK] 1 {div_1} equivale a {resultado:.4f} {div_2}")
                else:
                    print("[ERROR] No se pudo obtener el valor. Verifica que las divisas existan y la conexión a la URL sea correcta.")
            except Exception as e:
                print(f"[ERROR] Ocurrió un error inesperado al consultar: {e}")
                
        elif opcion == '3':
            nueva_url = input(f"Introduce la nueva URL (Enter para cancelar): ").strip()
            if nueva_url:
                URL_API_GITHUB = nueva_url
                print(f"[OK] URL de la API actualizada a: {URL_API_GITHUB}")
                
        elif opcion == '4':
            print("Saliendo de la prueba de API...")
            sys.exit(0)
            
        else:
            print("[ERROR] Opción no válida. Por favor, elige de 1 a 4.")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nSaliendo de la prueba de API de forma forzada...")
        sys.exit(0)
