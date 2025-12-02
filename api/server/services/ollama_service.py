# servicios/servicio_ollama.py
import ollama

historialConversacion = []

def resetear_historial():
    """
    Resetea el historial de la conversación.
    """
    global historialConversacion
    historialConversacion = [
        {'role': 'system', 'content': ''}
    ]
    print("Historial de conversación reseteado.")

def generar_respuesta_ollama(prompt):
    """
    Toma un prompt de texto, lo envía a Ollama y devuelve la respuesta.
    Lanza una excepcion si falla.
    """
    historialConversacion.append({'role': 'user', 'content': prompt})
    print(f"Enviando prompt a Ollama: {prompt}")
    try:
        respuesta_ollama = ollama.chat(
            model='kubibot:latest',
            messages= historialConversacion
        )

        texto_respuesta = respuesta_ollama['message']['content']

        historialConversacion.append({'role': 'assistant', 'content': texto_respuesta})

        print(f"Ollama respondió: {texto_respuesta}")
        return texto_respuesta

    except Exception as e:
        print(f"Error al contactar Ollama: {e}")
        # Relanzamos la excepción para que la API la capture
        raise Exception(f"Error en el servicio Ollama: {str(e)}")