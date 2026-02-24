import sys
<<<<<<< Updated upstream
import os

# Ajustamos el path para que encuentre el nuevo SDK
sys.path.append(os.path.join(os.path.dirname(__file__), 'SDKs', 'python'))
from API_consultas import Solicitar_Divisas_Disponibles, Solicitar_Valor_Divisa

def menu():
    while True:
        print("\n======================================================")
        print("                 PRUEBAS DE LA API                    ")
        print("======================================================")
        print("1. Obtener lista de divisas disponibles")
        print("2. Consultar valor de conversión entre dos divisas")
        print("3. Salir")
        print("======================================================")
        
        opcion = input("Elige una opción (1-3): ").strip()
        
        if opcion == '1':
            print("\n[Cliente]: Mesero, dime qué divisas hay disponibles.")
            
            respuesta = Solicitar_Divisas_Disponibles()
            
            if respuesta.get("status") == "success":
                print(f"[Mesero]: Tenemos {respuesta['cantidad']} divisas disponibles el {respuesta['fecha_consulta']}.")
                divisas = respuesta["divisas"]
                for i in range(0, len(divisas), 10):
                    print(", ".join(divisas[i:i+10]))
            else:
                print(f"[Mesero]: Lo siento, hubo un problema: {respuesta.get('mensaje')}")
                
        elif opcion == '2':
            div_1 = input("[Cliente]: Introduce la divisa base (ej: USD): ").strip().upper()
            div_2 = input("[Cliente]: Introduce la divisa objetivo (ej: EUR): ").strip().upper()
            
            if not div_1 or not div_2:
                print("[Mesero]: Necesito ambas divisas para hacer la consulta.")
                continue
                
            print(f"\n[Cliente]: Mesero, ¿cuál es la relación entre {div_1} y {div_2}?")
            
            respuesta = Solicitar_Valor_Divisa(div_1, div_2)
            
            if respuesta.get("status") == "success":
                print(f"[Mesero]: Claro, aquí tienes:")
                print(respuesta)
            else:
                print(f"[Mesero]: Lo siento, hubo un problema: {respuesta.get('mensaje')}")
                
        elif opcion == '3':
            print("Saliendo de la prueba de API...")
            sys.exit(0)
            
        else:
            print("[Mesero]: Opción no válida. Por favor, elige 1, 2 o 3.")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nSaliendo de la prueba de API de forma forzada...")
        sys.exit(0)
=======
from modulos.API_consultas import Solicitar_Divisas_Disponibles, Solicitar_Valor_Divisa

def main():
    while True:
        print("\n--- Menú de Pruebas API de Divisas ---")
        print("1. Ver divisas disponibles")
        print("2. Consultar valor de conversión (Ej: EUR -> CLP)")
        print("3. Salir")
        
        opcion = input("Elige una opción (1/2/3): ").strip()
        
        if opcion == '1':
            print("\nConsultando divisas disponibles...")
            divisas = Solicitar_Divisas_Disponibles()
            if divisas:
                print(f"Total de divisas: {len(divisas)}")
                print(", ".join(divisas))
            else:
                print("No se encontraron divisas o hubo un error.")
                
        elif opcion == '2':
            divisa_1 = input("\nIngresa la divisa de origen (ej. EUR, USD): ").strip().upper()
            divisa_2 = input("Ingresa la divisa de destino (ej. CLP, MXN): ").strip().upper()
            
            if not divisa_1 or not divisa_2:
                print("Debes ingresar ambas divisas.")
                continue
                
            print(f"\nConsultando: 1 {divisa_1} a {divisa_2}...")
            valor = Solicitar_Valor_Divisa(divisa_1, divisa_2)
            
            if valor > 0:
                print(f"\nResultado: 1 {divisa_1} = {valor:.4f} {divisa_2}")
            else:
                print("\nError al obtener el valor o las divisas no existen.")
                
        elif opcion == '3':
            print("\nSaliendo...")
            sys.exit(0)
            
        else:
            print("\nOpción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
>>>>>>> Stashed changes
