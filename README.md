# Kubibot

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-robotics-00979D?logo=arduino&logoColor=white)
![Raspberry%20Pi](https://img.shields.io/badge/Raspberry%20Pi-5-C51A4A?logo=raspberrypi&logoColor=white)
![Flask-SocketIO](https://img.shields.io/badge/Flask--SocketIO-realtime-000000?logo=flask&logoColor=white)

Sistema robótico que integra un robot móvil basado en Arduino con un servidor externo autoalojado, utilizando una Raspberry Pi 5 como intermediario de comunicación.

El objetivo del proyecto es construir un robot de compañía demostrativo, que combine robótica y las posibilidades que trae la inteligencia artificial.

Proyecto realizado para el curso de 'Taller de Integración I'.

---

## Tabla de contenidos

- [Descripción general](#descripción-general)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Modo de uso](#modo-de-uso)
	- [Servidor de IA](#servidor-de-ia)
	- [Cliente de voz (Raspberry Pi 5)](#cliente-de-voz-raspberry-pi-5)
	- [Arduino (control de movimiento)](#arduino-control-de-movimiento)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Autores](#autores)

---

## Descripción general

Kubibot es un robot que puede desplazarse de forma autónoma evitando obstáculos, y puede escuchar y responder al usuario por voz mediante IA.

El repositorio se divide en varios componentes:

- **arduino**: control de motores, sensores y lógica básica de navegación.
- **api**: servidor y clientes para comunicar la Raspberry Pi/PC con el robot.
- **docs**: memoria del proyecto en LaTeX.

---

## Arquitectura

- **Robot físico (Arduino)**
	- Control de 4 motores DC mediante una shield compatible con la librería `AFMotor`.
	- Sensor ultrasónico para detección de obstáculos.
	- Servomotor que mueve el sensor para "escanear" izquierda/derecha.
	- Lógica local de movimiento autónomo (avanza, retrocede y gira evitando obstáculos).

- **Servidor de IA (PC o servidor dedicado)**
	- Ejecuta la API WebSocket con `Flask-SocketIO` ([api/server/server_api.py](api/server/server_api.py)).
	- Recibe audio por streaming desde el cliente (chunks de audio vía evento `audio_chunk`).
	- Reconstruye el audio y lo transcribe a texto usando Whisper ([whisper_service.py](api/server/services/whisper_service.py)).
	- Envía el texto transcrito al modelo de lenguaje local vía Ollama ([ollama_service.py](api/server/services/ollama_service.py)).
	- Mantiene el historial de conversación (contexto) entre turnos de diálogo.
	- Convierte la respuesta de texto a audio mediante TTS con Piper y la devuelve al cliente (`audio_response`).

- **Raspberry Pi 5 (cliente de voz)**
	- Ejecuta el cliente Socket.IO ([api/client/raspberry.py](api/client/raspberry.py)).
	- Usa Porcupine para detectar la *wake word* localmente (sin enviar audio hasta que se active).
	- Una vez detectada la *wake word*, graba unos segundos de audio con `pvrecorder` y lo envía al servidor como stream.
	- Reproduce localmente el audio de respuesta TTS que recibe del servidor.
	- Opcionalmente, puede ejecutarse el cliente genérico [api/client/client.py](api/client/client.py) con una configuración similar.

---

## Requisitos

- Para las configuraciones que se utilizan de manera predeterminada, se recomienda un servidor con una CPU al nivel de una i7 de novena generación, que cuente con un mínimo de 16 GB de memoria RAM o con una tarjeta de video con, por lo menos, 6 GB de VRAM.
- En [api/config/Modelfile](api/config/Modelfile) es posible configurar el modelo para escoger algún otro LLM que se ajuste a las necesidades específicas de cada usuario. Además, se pueden cambiar parámetros del comportamiento del asistente.

### Hardware

- Arduino UNO
	- 4 motores DC con ruedas
	- Shield para motores para Arduino UNO (HW-130)
	- Sensor ultrasónico (HC-SR04)
	- Servomotor
	- Fuente de alimentación adecuada
- Raspberry Pi 5 (o PC con Linux/Windows para pruebas)
	- Interfaz de audio compatible
	- Altavoz y micrófono
- Servidor (PC o servidor dedicado)

### Software

- Arduino IDE para cargar el firmware
- Python 3.8+
- Git

---

## Instalación

1. **Clonar el repositorio**

	 ```bash
	 git clone https://github.com/usuario/kubibot.git
	 cd kubibot
	 ```

2. **Configurar entorno de Python (recomendado)**

	 ```bash
	 python -m venv .venv
	 source .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
	 ```

3. **Configurar variables de entorno**

	 Usa el archivo `envexample.txt` como referencia para crear tu propio archivo de entorno (por ejemplo, `.env`) con claves, rutas y configuraciones necesarias para la API y los servicios de IA.

4. **Instalar dependencias de cada módulo**

	 - Revisa `api/server/services/` para conocer las dependencias de `ollama_service.py` y `whisper_service.py`.
	 - Revisa `emotions/config.yaml` y `emotions/README.md` para el módulo de emociones.

---

## Modo de uso

### Servidor de IA

El servidor se ejecuta en un PC o servidor dedicado y expone una API WebSocket con Flask‑SocketIO.

1. Asegúrate de tener configurado el entorno de Python y las variables de entorno (`API_TOKEN`, etc.).
2. Desde la carpeta raíz del repositorio, lanza:

	```bash
	cd api/server
	python server_api.py
	```

Por defecto se expone en el puerto `5000` sobre `0.0.0.0`.

### Cliente de voz (Raspberry Pi 5)

En la Raspberry Pi se ejecuta el cliente que escucha la *wake word*, graba el audio y lo envía al servidor.

1. Configura en la Raspberry Pi las variables de entorno mínimas:

	- `URL_SERVER`: dominio o IP (y puerto si aplica) donde es accesible el servidor.
	- `API_TOKEN`: debe coincidir con el del servidor.
	- `ACCESS_KEY`: clave de Porcupine.
	- `INDEX_MICROFONO`: índice del dispositivo de audio a utilizar.

2. Desde la carpeta raíz del repositorio en la Raspberry Pi:

	```bash
	cd api/client
	python raspberry.py
	```

El cliente:

- Espera a que se detecte la *wake word* mediante Porcupine.
- Graba unos segundos de audio con `pvrecorder`.
- Envía el audio en *streaming* al servidor vía Socket.IO.
- Reproduce la respuesta de audio TTS que recibe del servidor.

Para pruebas rápidas en otro entorno, puedes usar `client.py` como cliente genérico.

### Arduino (control de movimiento)

1. Abre `arduino/movement/movement.ino` con el Arduino IDE.
2. Selecciona la placa y el puerto serie correctos.
3. Verifica que la librería `AFMotor` esté instalada.
4. Compila y sube el sketch al Arduino.

El firmware implementa lógica básica de navegación con evitación de obstáculos mediante el sensor ultrasónico y el servomotor.

---

## Estructura del proyecto

```text
kubibot/
├── api/
│   ├── client/
│   │   ├── client.py
│   │   └── raspberry.py
│   ├── config/
│   │   ├── Modelfile
│   │   └── ...
│   ├── data/
│   └── server/
│       ├── server_api.py
│       └── services/
│           ├── ollama_service.py
│           └── whisper_service.py
├── arduino/
│   └── movement/
│       └── movement.ino
├── docs/
│   ├── main.tex
│   └── chapters/
│       └── ...
├── envexample.txt
└── README.md
```

---

## Autores

- [Iván Mansilla](https://github.com/ivnmansi)
- [Ayrton Morrison](https://github.com/ayrtonmo)
