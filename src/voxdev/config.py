import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ── Voz ──
VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "pt")
VOICE_SAMPLE_RATE = os.getenv("VOICE_SAMPLE_RATE", "44100")

# ── OpenAI Whisper API ──
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── TTS ──
TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"

# Caminhos baseados na estrutura do VoxDev
# VoxDev/src/voxdev/config.py -> VoxDev/
VOXDEV_ROOT = Path(__file__).parent.parent.parent

PIPER_PATH = os.getenv("PIPER_PATH", str(VOXDEV_ROOT / "bin" / "piper"))
PIPER_MODEL = os.getenv("PIPER_MODEL", str(VOXDEV_ROOT / "models" / "pt_BR-faber-medium.onnx"))

# Configuração do Vault (Opcional, para uso com cli.py)
# Por padrão, assume que o Vault está um nível acima da pasta VoxDev
DEFAULT_VAULT_PATH = VOXDEV_ROOT.parent / "vault" / "00-Inbox"
VAULT_INBOX_PATH = os.getenv("VAULT_INBOX_PATH", str(DEFAULT_VAULT_PATH))

# Pasta de backup de áudio — gravações nunca são perdidas
AUDIO_BACKUP_PATH = os.getenv("AUDIO_BACKUP_PATH", str(VOXDEV_ROOT / "audio-backup"))
