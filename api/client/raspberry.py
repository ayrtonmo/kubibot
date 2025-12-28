import socketio
import pvporcupine
import pvrecorder
from dotenv import load_dotenv
import os
import struct
import subprocess
import time
import serial
import datetime

load_dotenv()

# Configuracion API
URL_SERVER = os.getenv("URL_SERVER")
API_TOKEN = os.getenv("API_TOKEN")
AUDIO_TEMP_FILE = "stream_audio.wav"

# Configuracion Porcupine
ACCES_KEY = os.getenv("ACCESS_KEY")
INDEX_MICROFONO = int(os.getenv("INDEX_MICROFONO"))

ARCHIVO_WAKE_WORD = "config/porcupine/wakeword.ppn"
MODEL_PATH = "config/porcupine/porcupine_params_es.pv"

# Configuracion Voice Active Detection
SILENCE_THRESHOLD = 2500
SILENCE_LIMIT_SECONDS = 1.0
MAX_DURATION_SECONDS = 15

# Configuraciones generales
START_SOUND_FILE = "config/sound/start_sound.wav"
FINISH_SOUND_FILE = "config/sound/finish_sound.wav"

# Configuracion SocketIO
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1, request_timeout=20)
isBusy = False

# Configuracion comunicacion serial
PORT = '/dev/ttyACM0'
FSERIAL = 9600  # Frecuencia serial arduino
COOLDOWN = 60   # Segundos de cooldown para retornar la senhal de movimiento

arduino = None
isOnUse = False
lastStopTime = None  # datetime del último "Stop" enviado


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


def record_and_stream():

    global isBusy

    isBusy = True
    print("Grabando comando de voz...")

    recorder = None
    try:
        recorder = pvrecorder.PvRecorder(device_index=INDEX_MICROFONO, frame_length = 512)
        recorder.start()

        maxChunks = int(recorder.sample_rate * MAX_DURATION_SECONDS / recorder.frame_length)
        silenceLimit = int(recorder.sample_rate * SILENCE_LIMIT_SECONDS / recorder.frame_length)

        silenceCounter = 0
        chunksRecorded= 0
        voiceDetected = False

        while chunksRecorded < maxChunks:
            frame = recorder.read()
            packedFrame = struct.pack("h" * len(frame), *frame)

            maxAmplitude = max(abs(sample) for sample in frame)
            if maxAmplitude < SILENCE_THRESHOLD:
                silenceCounter += 1 # Hay silencio
            else:
                silenceCounter = 0
                voiceDetected = True # Detectada voz

            sio.emit('audio_chunk', packedFrame)
            chunksRecorded += 1

            if voiceDetected and silenceCounter > silenceLimit:
                print("Silencio detectado, finalizando grabación.")
                break

        subprocess.run(["aplay", FINISH_SOUND_FILE], stderr=subprocess.DEVNULL)
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
    global isOnUse, lastStopTime, arduino

    try:
        if isOnUse and lastStopTime is not None:
            elapsed = (datetime.datetime.now() - lastStopTime).total_seconds()
            if elapsed >= COOLDOWN:
                isOnUse = False
                lastStopTime = None
                if arduino is not None and arduino.is_open:
                    command = "R"
                    arduino.write(command.encode())
                    arduino.flush()

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
                # Se envia senhal de stop al arduino
                if arduino is not None and arduino.is_open:
                    command = "S"
                    arduino.write(command.encode())
                    print("Senhal de STOP enviada al Arduino.")
                    arduino.flush()
                subprocess.run(["aplay", START_SOUND_FILE], stderr=subprocess.DEVNULL)

                isOnUse = True
                lastStopTime = datetime.datetime.now()
                break

    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
    finally:
        if recorder:
            recorder.stop()
            recorder.delete()
        if porcupine:
            porcupine.delete()


def stablish_serial_connection():
    global arduino
    try:
        arduino = serial.Serial(PORT, FSERIAL)
        time.sleep(2)  # Espera a que la conexión serial se establezca
        print("Conexión serial establecida con Arduino.")
    except Exception as e:
        print(f"Error al establecer conexión serial: {e}")


if __name__ == "__main__":
    try:
        stablish_serial_connection()
        fullUrl = f"https://{URL_SERVER}"
        print(f"Conectando a la API... ")

        sio.connect(fullUrl, headers={'Auth': API_TOKEN})
        sio.emit('reset_record')

        while True:
            detect_wake_word()
            record_and_stream()

            # Espera hasta recibir la respuesta antes de continuar
            while isBusy:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
        sio.disconnect()
    except Exception as e:
        print(f"Error inesperado: {e}")
        sio.disconnect()
