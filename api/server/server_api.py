from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from services.whisper_service import transcribe_audio_file
from services.ollama_service import ollama_generate_answer, reset_record


app = Flask(__name__)
print("Servidor API iniciado.")
API_TOKEN = os.getenv("API_TOKEN")

def validate_token(token):
    return token == API_TOKEN

# Endpoint 1: Transcripcion de audio via whisper
# Esta ruta solo se encarga de la web: recibir el archivo y devolver JSON
@app.route("/process_request", methods=["POST"])
def process_request():

    if validate_token(request.headers.get('Auth')) is False:
        return jsonify({"error": "Token de autenticación inválido"}), 401

    if 'audio' not in request.files:
        return jsonify({"error": "No se envió ningún archivo de audio"}), 400

    audioFile = request.files['audio']
    tempFileName = "temp_audio.wav"
    audioFile.save(tempFileName)

    try:
        transcribedText = transcribe_audio_file(tempFileName)
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

    if validate_token(request.headers.get('Auth')) is False:
        return jsonify({"error": "Token de autenticación inválido"}), 401

    try:
        reset_record()
        return jsonify({"mensaje": "Historial reseteado exitosamente."}), 200
    except Exception as e:
        return jsonify({"error": f"Error al resetear el historial: {str(e)}"}), 500

# Inicia el servidor Flask
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)