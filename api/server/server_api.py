from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from dotenv import load_dotenv
import os
import wave
from services.whisper_service import transcribe_audio_file
from services.ollama_service import ollama_generate_answer, reset_record
from services.piper_service import generate_tts_response


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
        audioData = generate_tts_response(responseText)

        if audioData:
            emit('audio_response', audioData)
            print("Respuesta TTS enviada al cliente.")
        else:
            print("No se pudo generar la respuesta TTS.")


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

