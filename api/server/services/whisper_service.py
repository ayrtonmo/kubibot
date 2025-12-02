import speech_recognition as sr

# Reconcocedor de voz
r = sr.Recognizer()

def transcribe_audio_file(ruta_archivo):
    """
    Toma la ruta de un archivo de audio, lo procesa con Whisper
    y devuelve el texto.
    Lanza una excepción si no puede entenderlo.
    """
    #print("Procesando audio con Whisper...")
    try:
        # Se utiliza el archivo de audio
        with sr.AudioFile(ruta_archivo) as source:
            audio_data = r.record(source)

        # Se realiza la transcripcion con Whisper
        text = r.recognize_whisper(audio_data, language="spanish", model="base")

        #print(f"Whisper reconoció: {text}")
        return text

    except sr.UnknownValueError:
        #print("Whisper no pudo entender el audio")
        # Relanzamos el error para que la API lo capture
        raise ValueError("Whisper no pudo entender el audio")
    except Exception as e:
        #print(f"Error en el servicio Whisper: {e}")
        raise e # Se relanza la excepcion

