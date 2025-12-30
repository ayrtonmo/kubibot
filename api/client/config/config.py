from __future__ import annotations

from dataclasses import dataclass
import os
from dotenv import load_dotenv
from pathlib import Path


@dataclass(frozen=True)
class Config:
    # Variables de entorno
    url_server: str
    api_token: str
    access_key: str
    microphone_index: int

    # General
    audio_temp_file: str = "stream_audio.wav"

    # Rutas base
    base_dir: Path = Path(__file__).resolve().parents[1]  # .../api/client

    # Porcupine
    wake_word_path: Path | None = None
    porcupine_model_path: Path | None = None

    # VAD
    silence_threshold: int = 2500
    silence_limit_seconds: float = 1.0
    max_duration_seconds: float = 15.0

    # Sonidos
    start_sound_file: Path | None = None
    finish_sound_file: Path | None = None
    on_sound_file: Path | None = None
    error_sound_file: Path | None = None

    # Arduino
    port: str = "/dev/ttyACM0"
    fserial: int = 9600
    cooldown_seconds: int = 60
    stop_command: str = "S"
    resume_command: str = "R"
    stop_handshake: str = "K"
    handshake_timeout_seconds: float = 3.0

    # Watchdogs
    connect_retry_base_delay_seconds: int = 1
    connect_retry_max_delay_seconds: int = 30
    response_timeout_seconds: int = 30

    def __post_init__(self):
        config_dir = self.base_dir / "config"
        object.__setattr__(self, "wake_word_path", config_dir / "porcupine" / "wakeword.ppn")
        object.__setattr__(self, "porcupine_model_path", config_dir / "porcupine" / "porcupine_params_es.pv")

        sound_dir = config_dir / "sound"
        object.__setattr__(self, "start_sound_file", sound_dir / "start_sound.wav")
        object.__setattr__(self, "finish_sound_file", sound_dir / "finish_sound.wav")
        object.__setattr__(self, "on_sound_file", sound_dir / "on_sound.wav")
        object.__setattr__(self, "error_sound_file", sound_dir / "error_sound.wav")

    @property
    def server_url(self) -> str:
        raw = self.url_server.strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
        return f"https://{raw}"

    @classmethod
    def from_env(cls) -> 'Config':
        load_dotenv()

        requiredVars = ["URL_SERVER", "API_TOKEN", "ACCESS_KEY", "MICROPHONE_INDEX"]

        missingVars = [var for var in requiredVars if os.getenv(var) is None]
        if missingVars:
            raise EnvironmentError(f"Faltan las siguientes variables de entorno requeridas: {', '.join(missingVars)}")

        try:
            microphone_index = int(os.getenv("MICROPHONE_INDEX"))
        except ValueError:
            raise ValueError("MICROPHONE_INDEX debe ser un entero válido.")

        return cls(
            url_server=os.getenv("URL_SERVER"),
            api_token=os.getenv("API_TOKEN"),
            access_key=os.getenv("ACCESS_KEY"),
            microphone_index=microphone_index,
        )
