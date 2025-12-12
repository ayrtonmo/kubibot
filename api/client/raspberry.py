import socketio
import pvporcupine
import pvrecorder
from dotenv import load_dotenv
import os
import struct
import subprocess
import time

load_dotenv()

# Configuracion API
URL_SERVER = os.getenv("URL_SERVER")
API_TOKEN = os.getenv("API_TOKEN")
AUDIO_TEMP_FILE = "stream_audio.wav"

# Configuracion Porcupine
ACCES_KEY = os.getenv("ACCESS_KEY")
INDEX_MICROFONO = int(os.getenv("INDEX_MICROFONO"))

ARCHIVO_WAKE_WORD = "config/wakeword.ppn"
MODEL_PATH = "config/porcupine_params_es.pv"

# Configuracion Voice Active Detection
SILENCE_THRESHOLD = 500
SILENCE_LIMIT_SECONDS = 1.5
MAX_DURATION_SECONDS = 20


# Configuracion SocketIO
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1, request_timeout=20)
isBusy = False

# Arh


@sio.event

def connect():
    print("Conectado al servidor de la API")

@sio.event
def disconnect():
    print("Desconectado del servidor de la API")

@sio.event
def response(data):
    if 'respuesta_texto' in data:
        texto = data['respuesta_texto']
        print(f"Respuesta de texto recibida: {texto}")
    if 'error'  in data:
        print(f"Error recibido del servidor: {data['error']}")

@sio.event
def audio_response(data):

    global isBusy

    print("Respuesta de audio recibida del servidor.")

    try:
        with open(AUDIO_TEMP_FILE, 'wb') as f:
            f.write(data)
        
        subprocess.run(["aplay", AUDIO_TEMP_FILE], stderr=subprocess.DEVNULL)

    except Exception as e:
        print(f"Error al reproducir audio: {e}")
    finally:
        if os.path.exists(AUDIO_TEMP_FILE):
            os.remove(AUDIO_TEMP_FILE)
    isBusy = False


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


def detect_wake_word():
    """
    Escucha el micrófono hasta detectar la wake word.
    """
    try:
        porcupine = pvporcupine.create(
            access_key=ACCES_KEY,
            keyword_paths=[ARCHIVO_WAKE_WORD],
            model_path=MODEL_PATH
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
