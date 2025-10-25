import requests
import time

# --- ⚠️ ¡IMPORTANTE! CONFIGURACIÓN ---
# Asegúrate de poner la IP de tu PC (donde corre el servidor Flask)
IP_SERVIDOR = "192.168.1.102"  # <-- CAMBIA ESTO POR LA IP DE TU PC
PUERTO = "5000"
URL_CHATEAR = f"http://{IP_SERVIDOR}:{PUERTO}/chatear"
# ---------------------------------------

# --- TU PREGUNTA DE PRUEBA ---
# Cambia esto por lo que quieras preguntarle a tu modelo
texto_de_prueba = "Hola, ¿cuál es tu nombre y cuál es tu propósito?"
# ---------------------------------------

print(f"Cliente de prueba iniciado (solo Ollama).")
print(f"Conectando al servidor en: {URL_CHATEAR}")
print(f"Enviando prompt: '{texto_de_prueba}'")

# Preparamos el JSON para enviar, tal como lo haría el script completo
datos_para_ollama = {
    "prompt": texto_de_prueba
}

try:
    # --- PASO 1: Enviar el texto a la API de Ollama ---
    response = requests.post(URL_CHATEAR, json=datos_para_ollama, timeout=30) # 30 seg. timeout
    
    # --- PASO 2: Procesar la respuesta ---
    if response.status_code == 200:
        # La solicitud fue exitosa
        datos_respuesta = response.json()
        
        # Verificamos si la respuesta contiene 'respuesta' o 'error'
        respuesta_robot = datos_respuesta.get('respuesta')
        error_api = datos_respuesta.get('error')
        
        if respuesta_robot:
            print("\n--- Respuesta del Robot ---")
            print(respuesta_robot)
            print("---------------------------")
        else:
            print(f"\n[ERROR EN LA API] El servidor devolvió un error:")
            print(error_api)
            
    else:
        # El servidor devolvió un código de error (ej. 500, 404, 400)
        print(f"\n[ERROR HTTP] La solicitud falló con el código: {response.status_code}")
        print(f"Mensaje del servidor: {response.text}")

except requests.exceptions.ConnectionError:
    print(f"\n[ERROR FATAL] No se pudo conectar al servidor en {URL_CHATEAR}.")
    print("Verifica que:")
    print(f"1. La IP '{IP_SERVIDOR}' sea la correcta.")
    print(f"2. El script 'servidor_api.py' esté corriendo en tu PC.")
    print(f"3. El Firewall de tu PC no esté bloqueando el puerto {PUERTO}.")
except requests.exceptions.ReadTimeout:
    print(f"\n[ERROR] La solicitud tardó demasiado (timeout).")
    print("Ollama podría estar tardando mucho en generar la respuesta.")
except Exception as e:
    print(f"\nOcurrió un error inesperado: {e}")