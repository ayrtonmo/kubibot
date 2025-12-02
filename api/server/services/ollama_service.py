# servicios/servicio_ollama.py
import ollama

ollamaRecord = []

def reset_record():
    """
    Resetea el historial de la conversación.
    """
    global ollamaRecord
    ollamaRecord = []
    #print("Historial de conversación reseteado.")

def ollama_generate_answer(prompt):
    """
    Toma un prompt de texto, lo envia a Ollama y devuelve la respuesta.
    Lanza una excepcion si falla.
    """
    ollamaRecord.append({'role': 'user', 'content': prompt})
    print(f"Enviando prompt a Ollama: {prompt}")
    try:
        respuesta_ollama = ollama.chat(
            model='kubibot:latest',
            messages=ollamaRecord,
            options={
                'num_predict': 70,
                'temperature': 0.5
            }
            )

        generatedAnswer = respuesta_ollama['message']['content']

        ollamaRecord.append({'role': 'assistant', 'content': generatedAnswer})

        #print(f"Ollama respondió: {generatedAnswer}")
        return generatedAnswer

    except Exception as e:
        print(f"Error al contactar Ollama: {e}")
        # Se lanza la excepcion
        raise Exception(f"Error en el servicio Ollama: {str(e)}")