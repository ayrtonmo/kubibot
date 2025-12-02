from flask import Flask, request, jsonify

from services.whisper_service import transcribe_audioFile
from services.ollama_service import ollama_generate_answer, reset_record


app = Flask(__name__)
print("Servidor API iniciado.")

# Endpoint 1: Transcripcion de audio via whisper
# Esta ruta solo se encarga de la web: recibir el archivo y devolver JSON
@app.route("/procesar_request", methods=["POST"])
def procesar_request():

    if 'audio' not in request.files:
        return jsonify({"error": "No se envió ningún archivo de audio"}), 400

    audioFile = request.files['audio']
    tempFileName = "temp_audio.wav"
    audioFile.save(tempFileName)

    try:
        transcribedText = transcribe_audioFile(tempFileName)
        outputText = ollama_generate_answer(transcribedText)

        return jsonify({"respuesta": outputText})

    except Exception as e:
        # 3. Si el servicio falla, captura el error
        return jsonify({"error": f"Error en transcripción: {str(e)}"}), 500

@app.route("/reset_record", methods=["POST"])
def reset_record_endpoint():
    """
    Endpoint para resetear el historial de conversación.
    """
    try:
        reset_record()
        return jsonify({"mensaje": "Historial reseteado exitosamente."}), 200
    except Exception as e:
        return jsonify({"error": f"Error al resetear el historial: {str(e)}"}), 500

# Inicia el servidor Flask
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)