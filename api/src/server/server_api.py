# servidor_api.py
from flask import Flask, request, jsonify

# ¡AQUÍ ESTÁ LA MAGIA!
# Importamos nuestras funciones de lógica de negocio desde la carpeta 'servicios'
from services.whisper_service import transcribir_archivo_audio
from services.ollama_service import generar_respuesta_ollama

# Inicialización de Flask
app = Flask(__name__)

print("Servidor de IA (Flask + Servicios) listo.")

# --- RUTA 1: WHISPER ---
# Esta ruta solo se encarga de la web: recibir el archivo y devolver JSON
@app.route("/transcribir", methods=["POST"])
def ruta_transcribir():
    if 'audio' not in request.files:
        return jsonify({"error": "No se envió ningún archivo de audio"}), 400

    audio_file = request.files['audio']
    temp_filename = "temp_audio.wav" # Archivo temporal
    audio_file.save(temp_filename)

    try:
        # 1. Llama al servicio de Whisper
        texto = transcribir_archivo_audio(temp_filename)

        # 2. Devuelve la respuesta
        return jsonify({"texto": texto})

    except Exception as e:
        # 3. Si el servicio falla, captura el error
        return jsonify({"error": f"Error en transcripción: {str(e)}"}), 500

# --- RUTA 2: OLLAMA ---
# Esta ruta solo se encarga de recibir y enviar JSON
@app.route("/chatear", methods=["POST"])
def ruta_chatear():
    datos = request.json
    if 'prompt' not in datos:
        return jsonify({"error": "No se envió un 'prompt' de texto"}), 400

    prompt_usuario = datos['prompt']

    try:
        # 1. Llama al servicio de Ollama
        texto_respuesta = generar_respuesta_ollama(prompt_usuario)

        # 2. Devuelve la respuesta
        return jsonify({"respuesta": texto_respuesta})

    except Exception as e:
        # 3. Si el servicio falla, captura el error
        return jsonify({"error": f"Error en el chat: {str(e)}"}), 500

# --- INICIAR SERVIDOR ---
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)