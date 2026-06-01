import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

from .config import (
    VOICE_LANGUAGE,
    VOICE_SAMPLE_RATE,
    TTS_ENABLED,
    PIPER_PATH,
    PIPER_MODEL,
    OPENAI_API_KEY,
)

logger = logging.getLogger(__name__)

class VoiceManager:
    """Manages audio recording, transcription and synthesis."""

    def __init__(self):
        self.language = VOICE_LANGUAGE
        self.sample_rate = VOICE_SAMPLE_RATE
        self.tts_enabled = TTS_ENABLED
        self.piper_path = PIPER_PATH
        self.piper_model = PIPER_MODEL

    def _clean_text_for_tts(self, text: str) -> str:
        """Remove markdown and special characters that sound bad when spoken."""
        import re
        
        # Remove markdown bold/italic/code markers
        text = re.sub(r'[*_`#~]', '', text)
        
        # Remove emojis and other non-BMP characters
        text = re.sub(r'[^\u0000-\u007F\u00C0-\u00FF\u0100-\u017F]+', ' ', text)
        
        # Remove list markers and special symbols
        text = re.sub(r'^[ \t]*[-+•*][ \t]+', '', text, flags=re.MULTILINE)
        text = re.sub(r'[&|=+\\|/]', ' ', text)
        
        # Clean up multiple spaces and empty lines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def speak(self, text: str):
        """Synthesize and play the given text using Piper."""
        if not self.tts_enabled:
            return

        if not os.path.exists(self.piper_path) or not os.path.exists(self.piper_model):
            logger.error("Piper binary or model not found. TTS disabled.")
            return

        # [NOVO] Limpar texto para fala
        clean_text = self._clean_text_for_tts(text)
        if not clean_text:
            return

        logger.info(f"🗣️ Falando: {clean_text[:50]}...")
        
        fd, wav_path = tempfile.mkstemp(suffix=".wav", prefix="santos_tts_")
        os.close(fd)

        try:
            # Piper command: echo "text" | piper --model model.onnx --output_file out.wav
            cmd_piper = [
                self.piper_path,
                "--model", self.piper_model,
                "--output_file", wav_path
            ]
            
            subprocess.run(cmd_piper, input=clean_text.encode("utf-8"), check=True, capture_output=True)
            
            if os.path.exists(wav_path):
                import select
                import termios
                import tty
                import sys
                import platform

                player = "afplay" if platform.system() == "Darwin" else "aplay"
                play_proc = subprocess.Popen([player, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Prepara stdin para leitura "raw" (sem precisar de Enter)
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setcbreak(fd)
                    while play_proc.poll() is None: # Enquanto estiver tocando
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            ch = sys.stdin.read(1)
                            if ch == '\t': # Ctrl+I (Tab)
                                logger.info("🛑 Fala interrompida pelo usuário.")
                                play_proc.terminate()
                                break
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
                play_proc.wait()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro no TTS (Piper/Aplay): {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"Erro inesperado no TTS: {e}")
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)

    def record(self, duration: Optional[int] = None) -> str:
        """
        Record audio from the microphone.
        Interrupted by Ctrl+I (Tab) or Ctrl+C.
        Returns the path to the recorded WAV file.
        """
        import select
        import termios
        import tty
        import sys

        fd_temp, path = tempfile.mkstemp(suffix=".wav", prefix="santos_voice_")
        os.close(fd_temp)
        
        cmd = ["arecord", "-f", "cd", "-r", str(self.sample_rate), path]
        if duration:
            cmd.extend(["-d", str(duration)])
            
        logger.info(f"🎙️ Gravando áudio (Pressione Tab para parar)...")
        
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Prepara stdin para leitura "raw"
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while process.poll() is None:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    ch = sys.stdin.read(1)
                    if ch == '\t': # Ctrl+I (Tab)
                        logger.info("🛑 Gravação encerrada pelo usuário.")
                        break
                    if ch == '\x03': # Ctrl+C fallback
                        break
        except KeyboardInterrupt:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            process.terminate()
            process.wait()
            
        return path

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file via OpenAI Whisper API."""
        import httpx

        if not os.path.exists(audio_path):
            return "Erro: Arquivo de áudio não encontrado."

        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY não configurada.")
            return ""

        logger.info(f"📝 Transcrevendo via OpenAI Whisper API...")

        try:
            with open(audio_path, "rb") as f:
                response = httpx.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    data={"model": "whisper-1", "language": self.language},
                    files={"file": (os.path.basename(audio_path), f, "audio/wav")},
                    timeout=60,
                )
            response.raise_for_status()
            return response.json().get("text", "").strip()
        except Exception as e:
            logger.error(f"Erro na transcrição Whisper API: {e}")
            return ""

    def cleanup(self, path: str):
        """Remove temporary audio file."""
        if os.path.exists(path):
            os.remove(path)
