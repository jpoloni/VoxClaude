import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

from .config import (
    VOICE_LANGUAGE,
    WHISPER_MODEL,
    WHISPER_DEVICE,
    VOICE_SAMPLE_RATE,
    TTS_ENABLED,
    PIPER_PATH,
    PIPER_MODEL,
)

logger = logging.getLogger(__name__)

class VoiceManager:
    """Manages audio recording, transcription and synthesis."""

    def __init__(self):
        self.language = VOICE_LANGUAGE
        self.model = WHISPER_MODEL
        self.device = WHISPER_DEVICE
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
            
            # [NOVO] Reprodução interrompível
            if os.path.exists(wav_path):
                import select
                import termios
                import tty
                import sys

                play_proc = subprocess.Popen(["aplay", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
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
        """
        Transcribe the given audio file using Whisper.
        Returns the transcribed text.
        """
        if not os.path.exists(audio_path):
            return "Erro: Arquivo de áudio não encontrado."

        logger.info(f"📝 Transcrevendo {audio_path}...")
        
        # Try primary device (e.g. cuda)
        text = self._run_whisper(audio_path, self.device)
        
        # Fallback to CPU if primary failed or returned empty (common with CUDA OOM)
        if not text and self.device != "cpu":
            logger.warning("⚠️ Transcrição falhou ou retornou vazia. Tentando fallback para CPU...")
            text = self._run_whisper(audio_path, "cpu")
            
        return text.strip()

    def _run_whisper(self, audio_path: str, device: str) -> str:
        """Internal helper to run the whisper command."""
        cmd = [
            "whisper",
            audio_path,
            "--language", self.language,
            "--model", self.model,
            "--device", device,
            "--output_format", "txt",
            "--verbose", "False"
        ]
        
        try:
            # whisper command creates a .txt file in the same directory as the audio
            # we need to capture that or read it.
            # Actually, whisper prints the result if verbose is True, 
            # but we'll use the generated txt file for reliability.
            
            output_dir = os.path.dirname(audio_path)
            subprocess.run(cmd, cwd=output_dir, check=True, capture_output=True)
            
            txt_path = audio_path.replace(".wav", ".txt")
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                os.remove(txt_path)
                return content
            return ""
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar Whisper ({device}): {e.stderr.decode()}")
            return ""
        except Exception as e:
            logger.error(f"Erro inesperado na transcrição: {e}")
            return ""

    def cleanup(self, path: str):
        """Remove temporary audio file."""
        if os.path.exists(path):
            os.remove(path)
