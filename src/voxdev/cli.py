import sys
import logging
import subprocess
import os
import shutil
import platform
from pathlib import Path
from .core import VoiceManager
from .config import VAULT_INBOX_PATH, AUDIO_BACKUP_PATH

# Configure minimal logging to stdout for easier parsing
logging.basicConfig(level=logging.WARNING)

def main():
    vm = VoiceManager()

    CHUNK_SIZE = 1024

    print(f"🎙️ Santos está ouvindo... (Ctrl+C para parar)")

    from datetime import datetime
    TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_path = f"/tmp/santos_voice_{TIMESTAMP}.wav.raw"
    tmp_wav  = f"/tmp/santos_voice_{TIMESTAMP}.wav"

    # Pasta de backup persistente — criada antes de qualquer gravação
    backup_dir = Path(AUDIO_BACKUP_PATH)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_wav = backup_dir / f"resposta-voz-{TIMESTAMP}.wav"

    if platform.system() == "Darwin":
        cmd = [
            "ffmpeg", "-f", "avfoundation", "-i", ":0",
            "-ar", str(vm.sample_rate), "-ac", "2", "-f", "s16le", "pipe:1",
            "-loglevel", "quiet"
        ]
    else:
        cmd = ["arecord", "-f", "cd", "-r", str(vm.sample_rate), "-t", "raw"]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        with open(raw_path, "wb") as f_raw:
            while True:
                data = process.stdout.read(CHUNK_SIZE)
                if not data:
                    break
                f_raw.write(data)
    except KeyboardInterrupt:
        print("\n🛑 Interrompido.")
    finally:
        process.terminate()
        process.wait()

    try:
        if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
            print("❌ Erro: Nenhum dado de áudio capturado.")
            sys.exit(1)

        # Converter raw → wav temporário
        subprocess.run([
            "ffmpeg", "-y", "-f", "s16le", "-ar", str(vm.sample_rate), "-ac", "2",
            "-i", raw_path, tmp_wav
        ], check=True, capture_output=True)
        os.remove(raw_path)

        # Salvar cópia persistente imediatamente — antes de qualquer chamada de API
        shutil.copy2(tmp_wav, backup_wav)
        print(f"💾 Áudio salvo em: {backup_wav}")

        print("📝 Transcrevendo...")
        text = vm.transcribe(tmp_wav)

        if text:
            print("\n--- TRANSCRIÇÃO ---")
            print(text)
            print("-------------------\n")

            vault_inbox = Path(VAULT_INBOX_PATH)
            vault_inbox.mkdir(parents=True, exist_ok=True)
            vault_file = vault_inbox / f"resposta-voz-{TIMESTAMP}.md"
            vault_file.write_text(f"# Resposta — {TIMESTAMP}\n\n{text}\n", encoding="utf-8")
            print(f"✅ Transcrição salva: {vault_file}")

            # Só remove o backup após confirmação de sucesso no vault
            os.remove(tmp_wav)
            os.remove(backup_wav)
        else:
            print(f"❌ Transcrição falhou. Áudio preservado em: {backup_wav}")
            os.remove(tmp_wav)
            sys.exit(1)

    except Exception as e:
        print(f"❌ Erro: {e}")
        if os.path.exists(raw_path):
            os.remove(raw_path)
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        if backup_wav.exists():
            print(f"💾 Áudio preservado em: {backup_wav}")
        sys.exit(1)

if __name__ == "__main__":
    main()
