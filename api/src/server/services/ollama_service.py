# servicios/servicio_ollama.py
import ollama

def generar_respuesta_ollama(prompt):
    """
    Toma un prompt de texto, lo envía a Ollama y devuelve la respuesta.
    Lanza una excepción si falla.
    """
    print(f"Enviando prompt a Ollama: {prompt}")
    try:
        respuesta_ollama = ollama.chat(
            model='kubibot:latest',  # O el modelo que prefieras
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )

        texto_respuesta = respuesta_ollama['message']['content']
        print(f"Ollama respondió: {texto_respuesta}")
        return texto_respuesta

    except Exception as e:
        print(f"Error al contactar Ollama: {e}")
        # Relanzamos la excepción para que la API la capture
        raise Exception(f"Error en el servicio Ollama: {str(e)}")