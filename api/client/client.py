import socketio
#import requests
import pvporcupine
import pvrecorder
from dotenv import load_dotenv
import os
#import wave
import struct
import subprocess
import time

load_dotenv()

# Configuracion API
URL_SERVER = os.getenv("URL_SERVER")
API_TOKEN = os.getenv("API_TOKEN")
#API_URL = f"https://{URL_SERVER}/process_request"
#RESET_URL = f"https://{URL_SERVER}/reset_record"

# Configuracion Porcupine
ACCES_KEY = os.getenv("ACCESS_KEY")
WAKE_WORD = "porcupine"
INDEX_MICROFONO = int(os.getenv("INDEX_MICROFONO"))

# Configuracion Voice Active Detection
SILENCE_THRESHOLD = 500
SILENCE_LIMIT_SECONDS = 1.5
MAX_DURATION_SECONDS = 20

# Configuracion TTS (Piper)
PIPER_BINARY = "piper"
VOICE_MODEL = os.path.expanduser("~/piper-voices/es_AR-daniela-high.onnx")
TTS_OUTPUT_FILE = "respuesta_tts.wav"

# Configuracion SocketIO
sio = socketio.Client()
isBusy = False

# Directorios
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
# AUDIO_FILE_PATH = os.path.join(DATA_DIR, "audio.wav")


#os.makedirs(DATA_DIR, exist_ok=True)



@sio.event
def connect():
    print("Conectado al servidor de la API")

@sio.event
def disconnect():
    print("Desconectado del servidor de la API")

@sio.event
def response(data):

    global isBusy

    if 'error' in data:
        print(f"Error del servidor: {data['error']}")

    text = data.get('respuesta')

    if text:
        print(f"Respuesta del servidor: {text}")
        text_to_voice(text)

    isBusy = False
    print("Esperando Wake Word...\n")

def text_to_voice(text):
    """
    Toma un texto, genera audio con Piper y lo reproduce con aplay.
    """
    if not text:
        return

    print(f"Piper hablando: {text}")

    # Se limpia el texto
    safeText = text.replace('"', '').replace("'", "")

    # Estructura: echo "text" | piper --model ruta_modelo --output_file archivo.wav
    cmdCommand = f'echo "{safeText}" | {PIPER_BINARY} --model "{VOICE_MODEL}" --output_file "{TTS_OUTPUT_FILE}"'

    try:
        # Se genera y reproduce el audio
        subprocess.run(cmdCommand, shell=True, check=True, stderr=subprocess.DEVNULL)
        subprocess.run(["aplay", TTS_OUTPUT_FILE], stderr=subprocess.DEVNULL)

    except subprocess.CalledProcessError as e:
        print(f"Error en TTS (Piper/Aplay): {e}")
    except Exception as e:
        print(f"Error inesperado en TTS: {e}")
    finally:
        # Opcional: Borrar archivo temporal
        if os.path.exists(TTS_OUTPUT_FILE):
            os.remove(TTS_OUTPUT_FILE)

def record_and_stream(lengthSeconds = 7):

    global isBusy
    isBusy = True

    print("Grabando comando de voz...")

    recorder = None
    try:
        recorder = pvrecorder.PvRecorder(device_index=INDEX_MICROFONO, frame_length = 512)
        recorder.start()

        audioChunks = int(recorder.sample_rate * lengthSeconds / recorder.frame_length)

        for _ in range(audioChunks):
            frame = recorder.read()
            packedFrame = struct.pack("h" * len(frame), *frame)
            sio.emit('audio_chunk', packedFrame)

        print("Grabación finalizada.")
        sio.emit('end_of_audio')

    except Exception as e:
        print(f"Error durante la grabación: {e}")
        isBusy = False
    finally:
        if recorder:
            recorder.stop()
            recorder.delete()

# def send_audio_API(file_path):
#     """
#     Envía un archivo de audio a la API y devuelve la respuesta.
#     Lanza una excepción si falla.
#     """
#     print(f"Enviando archivo de audio a la API: {file_path}")
#     try:
#         with open(file_path, 'rb') as audio_file:
#             files = {'audio': (file_path, audio_file, 'audio/wav')}

#             headers = {'Auth': API_TOKEN}
#             response = requests.post(API_URL, files=files, headers=headers)

#             response.raise_for_status()

#             print("Archivo enviado, respuesta recibida:")
#             jsonOutput = response.json()
#             print(jsonOutput)



#             # Intenta obtener el text de claves comunes, o usa el JSON entero como string si falla
#             textToSpeech = jsonOutput.get('response') or \
#                             jsonOutput.get('respuesta') or \
#                             jsonOutput.get('text') or \
#                             jsonOutput.get('mensaje')

#             if textToSpeech:
#                 text_to_voice(textToSpeech)
#             else:
#                 # Si no encuentra clave conocida, imprime aviso (o puedes hacer que lea el json crudo)
#                 print("No se encontró una clave de text estandar en el JSON para leer.")

#             return jsonOutput

#     except FileNotFoundError:
#         print(f"Error: Archivo no encontrado en '{file_path}'")
#         return None
#     except requests.exceptions.RequestException as e:
#         print(f"Error en la petición a la API: {e}")
#         return None
#     except Exception as e:
#         print(f"Ocurrió un error inesperado: {e}")
#         return None

def detect_wake_word():
    """
    Escucha el micrófono hasta detectar la wake word.
    """
    try:
        porcupine = pvporcupine.create(
            access_key=ACCES_KEY,
            keywords=[WAKE_WORD]
        )

        recorder = pvrecorder.PvRecorder(device_index=INDEX_MICROFONO, frame_length=porcupine.frame_length)
        recorder.start()

        print("Escuchando por la wake word...")

        while(True):
            frame = recorder.read()
            output = porcupine.process(frame)

            if output >= 0:
                print("Wake word detectada!")
                break
    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
    finally:
        if 'recorder' in locals():
            recorder.stop()
            recorder.delete()
        if 'porcupine' in locals():
            porcupine.delete()

# def record_command(audioPath, duracion_segundos = 7):
#     """
#     Graba audio desde el micrófono y lo guarda en audioPath.
#     """
#     print("Grabando comando de voz...")

#     recorder = None
#     waveFile = None

#     try:
#         recorder = pvrecorder.PvRecorder(device_index=INDEX_MICROFONO, frame_length = 512)
#         waveFile = wave.open(audioPath, 'wb')
#         waveFile.setnchannels(1)
#         waveFile.setsampwidth(2)  # 16 bits
#         waveFile.setframerate(recorder.sample_rate)

#         recorder.start()
#         print("Grabando...")

#         for _ in range(int(recorder.sample_rate * duracion_segundos / recorder.frame_length)):
#             frame = recorder.read()
#             waveFile.writeframes(struct.pack("h" * len(frame), *frame))
#         print("Grabación finalizada.")

#     except Exception as e:
#         print(f"Error durante la grabación: {e}")
#     finally:
#         if recorder is not None:
#             recorder.stop()
#             recorder.delete()
#         if waveFile is not None:
#             waveFile.close()

# def reset_conversation():
#     """
#     Envía una solicitud al servidor para reiniciar el historial de conversacion.
#     """
#     try:
#         headers = {'Auth': API_TOKEN}
#         response = requests.post(RESET_URL, headers=headers)
#         response.raise_for_status()
#         print("Historial de conversacion reiniciado en el servidor.")
#     except requests.exceptions.RequestException as e:
#         print(f"Error al reiniciar el historial en el servidor: {e}")

# if __name__ == "__main__":
#     reset_conversation()
#     while(True):
#         detect_wake_word()
#         record_command(AUDIO_FILE_PATH)
#         send_audio_API(AUDIO_FILE_PATH)
#         print("Reiniciando escucha...\n")

if __name__ == "__main__":
    try:
        fullUrl = f"https://{URL_SERVER}"
        print(f"Conectando a la API... ")

        sio.connect(fullUrl, headers={'Auth': API_TOKEN})
        sio.emit('reset_record')

        while True:
            detect_wake_word()
            record_and_stream(lengthSeconds=7)

            # Espera hasta recibir la respuesta antes de continuar
            while isBusy:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
        sio.disconnect()
    except Exception as e:
        print(f"Error inesperado: {e}")
        sio.disconnect()