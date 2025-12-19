import os
import subprocess
import uuid


# Configuracion TTS (Piper)
# Se puede sobreescribir con variables de entorno.
PIPER_BINARY = os.getenv("PIPER_BINARY", "piper")
VOICE_MODEL = os.path.expanduser(
    os.getenv("PIPER_VOICE_MODEL", "~/piper-voices/es_AR-daniela-high.onnx")
)


def generate_tts_response(text: str):
    """
    Genera audio TTS con Piper a partir de texto.

    Devuelve bytes WAV si fue exitoso, o None si no se pudo generar.
    """

    if not text:
        return None

    temp_wav = f"tts_response_{uuid.uuid4().hex}.wav"
    processed_text = text.replace('"', "").replace("'", "")

    try:
        # Piper acepta texto por stdin; evitamos shell=True.
        subprocess.run(
            [PIPER_BINARY, "--model", VOICE_MODEL, "--output_file", temp_wav],
            input=processed_text,
            text=True,
            check=True,
            stderr=subprocess.DEVNULL,
        )

        if os.path.exists(temp_wav):
            with open(temp_wav, "rb") as f:
                return f.read()

        return None

    except Exception as e:
        print(f"Error generando TTS: {e}")
        return None

    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
