import sys
import logging
import subprocess
import os
import time
import struct
from pathlib import Path
from .core import VoiceManager
from .config import VAULT_INBOX_PATH

# Configure minimal logging to stdout for easier parsing
logging.basicConfig(level=logging.WARNING)

def main():
    vm = VoiceManager()
    
    # Configurações de silêncio
    THRESHOLD = 300  # Limiar de amplitude mais sensível
    SILENCE_LIMIT = 5.0  # Segundos de silêncio para parar
    CHUNK_SIZE = 1024 # Tamanho do bloco de leitura
    
    print(f"🎙️ Santos está ouvindo... (Fale e pare por {SILENCE_LIMIT}s para encerrar)")
    
    TIMESTAMP = __import__("datetime").datetime.now().strftime('%Y%m%d_%H%M%S')
    audio_path = f"/tmp/santos_voice_{TIMESTAMP}.wav"
    raw_path = audio_path + ".raw"
    
    # Comando arecord enviando para stdout para análise
    cmd = ["arecord", "-f", "cd", "-r", str(vm.sample_rate), "-t", "raw"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    silence_start = None
    started_talking = False # Nova flag para ignorar silêncio inicial
    
    try:
        with open(raw_path, "wb") as f_raw:
            while True:
                # Lê um bloco de áudio
                data = process.stdout.read(CHUNK_SIZE)
                if not data:
                    break
                
                f_raw.write(data)
                
                # Análise de amplitude
                count = len(data) // 2
                if count > 0:
                    samples = struct.unpack(f"<{count}h", data[:count*2])
                    max_amplitude = max(abs(s) for s in samples)
                    
                    if max_amplitude >= THRESHOLD:
                        started_talking = True
                        silence_start = None
                    elif started_talking: # Só conta silêncio se já tiver começado a falar
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= SILENCE_LIMIT:
                            print(f"\n🔇 Silêncio detectado ({SILENCE_LIMIT}s). Parando...")
                            break
                    
    except KeyboardInterrupt:
        print("\n🛑 Interrompido manualmente.")
    finally:
        process.terminate()
        process.wait()
        
    try:
        if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
            print("❌ Erro: Nenhum dado de áudio capturado.")
            sys.exit(1)
            
        # Converter raw para wav (44100Hz, Stereo, s16le)
        subprocess.run([
            "ffmpeg", "-y", "-f", "s16le", "-ar", str(vm.sample_rate), "-ac", "2", 
            "-i", raw_path, audio_path
        ], check=True, capture_output=True)
        os.remove(raw_path)
        
        if not os.path.exists(audio_path):
            print("❌ Erro: Falha ao gerar arquivo de áudio.")
            sys.exit(1)
            
        print("📝 Transcrevendo...")
        text = vm.transcribe(audio_path)
        
        if text:
            print("\n--- TRANSCRIÇÃO ---")
            print(text)
            print("-------------------\n")
            
            # Salvar no Inbox do Vault
            vault_inbox = Path(VAULT_INBOX_PATH)
            os.makedirs(vault_inbox, exist_ok=True)
            vault_file = vault_inbox / f"transcricao-{TIMESTAMP}.md"
            with open(vault_file, "w", encoding="utf-8") as f_vault:
                f_vault.write(f"# Transcrição — {TIMESTAMP}\n\n{text}\n")
            print(f"✅ Transcrição salva no vault: {vault_file}")
        else:
            print("❌ Não foi possível transcrever nada.")
            
        vm.cleanup(audio_path)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        if os.path.exists(raw_path): os.remove(raw_path)
        sys.exit(1)

if __name__ == "__main__":
    main()
