from flask import Flask, request, jsonify

from services.whisper_service import transcribir_archivo_audio
from services.ollama_service import generar_respuesta_ollama, resetear_historial


app = Flask(__name__)
print("Servidor API iniciado.")

# Endpoint 1: Transcripcion de audio via whisper
# Esta ruta solo se encarga de la web: recibir el archivo y devolver JSON
@app.route("/procesar_request", methods=["POST"])
def procesar_request():

    if 'audio' not in request.files:
        return jsonify({"error": "No se envió ningún archivo de audio"}), 400

    audio_file = request.files['audio']
    temp_filename = "temp_audio.wav"
    audio_file.save(temp_filename)

    try:
        textoTranscrito = transcribir_archivo_audio(temp_filename)
        textoRespuesta = generar_respuesta_ollama(textoTranscrito)

        return jsonify({"respuesta": textoRespuesta})

    except Exception as e:
        # 3. Si el servicio falla, captura el error
        return jsonify({"error": f"Error en transcripción: {str(e)}"}), 500

@app.route("/resetear_historial", methods=["POST"])
def resetear_historial_endpoint():
    """
    Endpoint para resetear el historial de conversación.
    """
    try:
        resetear_historial()
        return jsonify({"mensaje": "Historial reseteado exitosamente."}), 200
    except Exception as e:
        return jsonify({"error": f"Error al resetear el historial: {str(e)}"}), 500

# Inicia el servidor Flask
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)