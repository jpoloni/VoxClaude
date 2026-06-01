from .core import VoiceManager
import sys

def main():
    vm = VoiceManager()
    text = "Olá! Eu sou o VoxDev. Agora eu também consigo falar com você. O que achou da minha voz?"
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        
    print(f"🎙️ Testando TTS: {text}")
    vm.speak(text)

if __name__ == "__main__":
    main()
