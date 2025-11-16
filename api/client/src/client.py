import requests
import pvporcupine
import pvrecorder
from dotenv import load_dotenv
import os
import wave
import struct


load_dotenv()


IP_SERVIDOR = "localhost"  # IP del servidor donde corre Ollama
PUERTO = "5000" # Puerto donde corre la API
API_URL = f"http://{IP_SERVIDOR}:{PUERTO}/procesar_request"
ACCES_KEY = os.getenv("ACCESS_KEY")
WAKE_WORD = "porcupine"
INDEX_MICROFONO = 5 # Utilizar indice del microfono correspondiente

AUDIO_FILE_PATH = "../data/audio.wav"


def enviar_audio_API(file_path):
    """
    Envía un archivo de audio a la API y devuelve la respuesta.
    Lanza una excepción si falla.
    """
    print(f"Enviando archivo de audio a la API: {file_path}")
    try:
        with open(file_path, 'rb') as audio_file:
            # Es una buena práctica especificar el nombre del archivo y el tipo de contenido.
            files = {'audio': (file_path, audio_file, 'audio/wav')}
            response = requests.post(API_URL, files=files)

            response.raise_for_status()

            print("Archivo enviado, respuesta recibida:")
            respuesta_json = response.json()
            print(respuesta_json)
            return respuesta_json

    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en '{file_path}'")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error en la petición a la API: {e}")
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return None

def detectar_wake_word():
    """
    Escucha el micrófono hasta detectar la wake word."""
    try:
        porcupine = pvporcupine.create(
            access_key=ACCES_KEY,
            keywords=[WAKE_WORD]
        )

        grabador = pvrecorder.PvRecorder(device_index=INDEX_MICROFONO, frame_length=porcupine.frame_length)
        grabador.start()

        print("Escuchando por la wake word...")

        while(True):
            frame = grabador.read()
            resultado = porcupine.process(frame)

            if resultado >= 0:
                print("Wake word detectada!")
                break
    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
    finally:
        if 'grabador' in locals():
            grabador.stop()
            grabador.delete()
        if 'porcupine' in locals():
            porcupine.delete()

def grabar_comando(audioPath, duracion_segundos = 7):
    """
    Graba audio desde el micrófono y lo guarda en audioPath.
    """
    print("Grabando comando de voz...")

    grabador = None
    waveFile = None

    try:
        grabador = pvrecorder.PvRecorder(device_index=INDEX_MICROFONO)
        waveFile = wave.open(audioPath, 'wb')
        waveFile.setnchannels(1)
        waveFile.setsampwidth(2)  # 16 bits
        waveFile.setframerate(grabador.sample_rate)

        grabador.start()
        print("Grabando...")

        for _ in range(int(grabador.sample_rate * duracion_segundos / grabador.frame_length)):
            frame = grabador.read()
            waveFile.writeframes(struct.pack("h" * len(frame), *frame))
        print("Grabación finalizada.")

    except Exception as e:
        print(f"Error durante la grabación: {e}")
    finally:
        if grabador is not None:
            grabador.stop()
            grabador.delete()
        if waveFile is not None:
            waveFile.close()

if __name__ == "__main__":
    while(True):
        detectar_wake_word()
        grabar_comando(AUDIO_FILE_PATH)
        enviar_audio_API(AUDIO_FILE_PATH)
        print("Reiniciando escucha...\n")

