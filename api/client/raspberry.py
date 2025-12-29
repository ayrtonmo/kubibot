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
INDEX_MICROFONO = os.getenv("INDEX_MICROFONO")

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
STOP_COMMAND = 'S'
RESUME_COMMAND = 'R'
STOP_HANDSHAKE = 'K'
HANDSHAKE_TIMEOUT = 1.5

arduino = None
isOnUse = False
lastStopTime = None
elapsedTime = 0

# Configuracion Watchdogs
CONNECT_RETRY_BASE_DELAY = 1 # Segundos entre reintentos de conexion
CONNECT_RETRY_MAX_DELAY = 30 # Maximo delay entre reintentos de conexion
RESPONSE_TIMEOUT_SECONDS = 30 # Segundos maximos de espera por respuesta de la API


@sio.event
def connect():
    print("Conectado al servidor de la API")

@sio.event
def disconnect():
    print("Desconectado del servidor de la API")


@sio.event
def response(data):
    global isBusy
    if 'respuesta_texto' in data:
        texto = data['respuesta_texto']
        print(f"Respuesta de texto recibida: {texto}")
    if 'error'  in data:
        isBusy = False
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
        isBusy = False
        print(f"Error al reproducir audio: {e}")
    finally:
        if os.path.exists(AUDIO_TEMP_FILE):
            os.remove(AUDIO_TEMP_FILE)
    isBusy = False

def check_env_variables():
    global INDEX_MICROFONO

    required_vars = ["URL_SERVER", "API_TOKEN", "ACCESS_KEY", "INDEX_MICROFONO"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")
    try:
        INDEX_MICROFONO = int(os.getenv("INDEX_MICROFONO"))
    except ValueError:
        raise ValueError("INDEX_MICROFONO debe ser un entero válido.")

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
            cooldown_tick()
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
    global isOnUse, lastStopTime, arduino, elapsedTime

    recorder = None
    porcupine = None

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

            cooldown_tick()

            frame = recorder.read()
            output = porcupine.process(frame)

            if output >= 0:
                print("Wake word detectada!")
                # Se envia senhal de stop al arduino

                stopped = process_arduino_handshake()
                if stopped:
                    print("Senhal de STOP confirmada por el Arduino.")
                else:
                    print("No se recibio confirmacion de STOP del Arduino.")

                subprocess.run(["aplay", START_SOUND_FILE], stderr=subprocess.DEVNULL)

                isOnUse = True
                lastStopTime = datetime.datetime.now()
                break

    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
    finally:
        if recorder is not None:
            recorder.stop()
            recorder.delete()
        if porcupine is not None:
            porcupine.delete()

def process_arduino_handshake():
    global arduino

    if arduino is None or not arduino.is_open:
        return False

    try:
        arduino.reset_input_buffer()
        arduino.write(STOP_COMMAND.encode())
        arduino.flush()

        startTime = time.time()
        deadLine = startTime + HANDSHAKE_TIMEOUT
        while time.time() < deadLine:
            cooldown_tick()

            b = arduino.read(1)
            if not b:
                continue
            charRecieved = b.decode(errors='ignore')
            if charRecieved == STOP_HANDSHAKE:
                print("Handshake con Arduino exitoso.")
                return True
        print("Timeout esperando handshake del Arduino.")
        return False

    except Exception as e:
        print(f"Error durante el handshake con Arduino: {e}")
        return False

def stablish_serial_connection():
    global arduino
    try:
        arduino = serial.Serial(PORT, FSERIAL, timeout=0.1, write_timeout=0.5)
        time.sleep(2)  # Espera a que la conexión serial se establezca
        arduino.write(RESUME_COMMAND.encode())
        arduino.flush()
        print("Conexión serial establecida con Arduino.")
    except Exception as e:
        print(f"Error al establecer conexión serial: {e}")

def establish_server_conecction():
    delay = CONNECT_RETRY_BASE_DELAY
    while not sio.connected:
        try:
            print("Intentando conectar al servidor...")
            fullUrl = f"https://{URL_SERVER}"
            sio.connect(fullUrl, headers={'Auth': API_TOKEN})
            sio.emit('reset_record')
            print("Conexion Establecida.")
        except Exception as e:
            print(f"Error de reconexion: {e}")
            time.sleep(delay)
            delay = min(delay * 2, CONNECT_RETRY_MAX_DELAY)

def cooldown_tick():
    global isOnUse, lastStopTime, elapsedTime, arduino

    if not isOnUse or lastStopTime is None:
        return

    elapsedTime = (datetime.datetime.now() - lastStopTime).total_seconds()
    #print(f"Tiempo desde ultimo STOP: {int(elapsedTime)} segundos")

    if elapsedTime < COOLDOWN:
        return # Si todavia no ha pasado el cooldown, no hacer nada

    isOnUse = False
    lastStopTime = None
    if arduino is not None and arduino.is_open:
        print("Enviando senhal de reanudacion al Arduino.")
        arduino.write(RESUME_COMMAND.encode())
        arduino.flush()

if __name__ == "__main__":
    try:
        check_env_variables()
        print("Iniciando cliente Raspberry Pi...")
        stablish_serial_connection()
        establish_server_conecction()

        while True:

            if not sio.connected:
                establish_server_conecction()

            detect_wake_word()
            record_and_stream()

            # Espera hasta recibir la respuesta antes de continuar
            waitStart = time.time()
            while isBusy:
                cooldown_tick()

                if not sio.connected:
                    print("Desconectado del servidor, intentando reconectar...")
                    establish_server_conecction()
                    isBusy = False
                    break
                if time.time() - waitStart > RESPONSE_TIMEOUT_SECONDS:
                    print("Tiempo de espera de respuesta excedido.")
                    isBusy = False
                    break

                time.sleep(0.1)

    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
        sio.disconnect()
    except Exception as e:
        print(f"Error inesperado: {e}")
        sio.disconnect()
