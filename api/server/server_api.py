from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from dotenv import load_dotenv
import os
import wave
from services.whisper_service import transcribe_audio_file
from services.ollama_service import ollama_generate_answer, reset_record


app = Flask(__name__)
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Diccionario para almacenar buffers de audio por cliente
clientBuffers = {}

def validate_token(token):
    return token == API_TOKEN

@socketio.on('connect')
def handle_connect():
    isValidToken = validate_token(request.headers.get('Auth'))
    if not isValidToken:
        print("Conexión rechazada: Token inválido")
        disconnect()
    else:
        sesionId = request.sid
        clientBuffers[sesionId] = bytearray()
        print("Cliente conectado")

@socketio.on('disconnect')
def handle_disconnect():
    sesionId = request.sid
    print(f"Cliente {sesionId} desconectado")
    if sesionId in clientBuffers:
        del clientBuffers[sesionId]

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    sesionId = request.sid
    if sesionId in clientBuffers:
        clientBuffers[sesionId].extend(data)


@socketio.on('end_of_audio')
def handle_end_of_audio():

    sesionId = request.sid

    uniqueBuffer = clientBuffers.get(sesionId)
    print("Audio recibido, procesando...")

    if not uniqueBuffer:
        emit('response', {'error': 'No se recibió ningún audio'})
        return
    print(f"Tamaño del buffer de audio: {len(uniqueBuffer)} bytes")

    tempFileName = f"temp_audio_{sesionId}.wav"
    try:
        with wave.open(tempFileName, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(uniqueBuffer)

        trasncribedText = transcribe_audio_file(tempFileName)
        responseText = ollama_generate_answer(trasncribedText)
        emit('response', {'respuesta': responseText})

    except Exception as e:
        emit('response', {'error': f"Error en transcripción: {str(e)}"})

    finally:
        # Se limpia el buffer del cliente y se elimina el archivo temporal
        if sesionId in clientBuffers:
            clientBuffers[sesionId] = bytearray()

        if os.path.exists(tempFileName):
            os.remove(tempFileName)

@socketio.on('reset_record')
def handle_reset_record():
    reset_record()
    print("Historial de conversación reseteado")

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)


# app = Flask(__name__)
# print("Servidor API iniciado.")
# API_TOKEN = os.getenv("API_TOKEN")

# def validate_token(token):
#     return token == API_TOKEN

# # Endpoint 1: Transcripcion de audio via whisper
# # Esta ruta solo se encarga de la web: recibir el archivo y devolver JSON
# @app.route("/process_request", methods=["POST"])
# def process_request():

#     if validate_token(request.headers.get('Auth')) is False:
#         return jsonify({"error": "Token de autenticación invalido"}), 401

#     if 'audio' not in request.files:
#         return jsonify({"error": "No se envió ningún archivo de audio"}), 400

#     audioFile = request.files['audio']
#     tempFileName = "temp_audio.wav"
#     audioFile.save(tempFileName)

#     try:
#         transcribedText = transcribe_audio_file(tempFileName)
#         outputText = ollama_generate_answer(transcribedText)

#         return jsonify({"respuesta": outputText})

#     except Exception as e:
#         # Si el servicio falla, captura el error
#         return jsonify({"error": f"Error en transcripción: {str(e)}"}), 500

# @app.route("/reset_record", methods=["POST"])
# def reset_record_endpoint():
#     """
#     Endpoint para resetear el historial de conversación.
#     """

#     if validate_token(request.headers.get('Auth')) is False:
#         return jsonify({"error": "Token de autenticación inválido"}), 401

#     try:
#         reset_record()
#         return jsonify({"mensaje": "Historial reseteado exitosamente."}), 200
#     except Exception as e:
#         return jsonify({"error": f"Error al resetear el historial: {str(e)}"}), 500

# # Inicia el servidor Flask
# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)