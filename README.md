# VoxDev | Modular Voice Interface for AI Agents

VoxDev é um módulo de interface de voz local-first, standalone e portátil, que fornece capacidades de alta qualidade de Speech-to-Text (STT) e Text-to-Speech (TTS).

## 🚀 Key Features

- **Local STT**: Alimentado por OpenAI Whisper (executando em GPU/CUDA ou CPU como fallback).
- **Local TTS**: Alimentado por Piper (extremamente rápido, vozes neurais de alta fidelidade).
- **Lógica Interrompível**: Interrompa gravações ou a fala instantaneamente usando a tecla **Tab** (ou Ctrl+I).
- **Áudio Limpo**: Filtragem automática de símbolos Markdown e emojis para uma narração natural.
- **Portabilidade Total**: Pasta autocontida; pode ser copiada para qualquer projeto.

## 📂 Estrutura

- `bin/`: Binário pré-compilado do `piper` e suas dependências (`.so`).
- `models/`: Modelos de voz ONNX (ex: português faber-medium).
- `src/voxdev/`:
    - `core.py`: O coração do sistema (`VoiceManager`).
    - `config.py`: Gestão de caminhos dinâmicos e variáveis de ambiente.
    - `cli.py`: Script para testar gravação e transcrição com detecção de silêncio.
    - `test_tts.py`: Script rápido para testar a síntese de voz.
- `requirements.txt`: Dependências Python necessárias.

## 🛠️ Requisitos de Sistema

Para que o VoxDev funcione, o sistema Linux hospedeiro deve possuir:

1.  **ALSA Utilities**: `arecord` e `aplay` (pacote `alsa-utils`).
2.  **FFmpeg**: Para conversão de formatos de áudio.
3.  **OpenAI Whisper**: O comando `whisper` deve estar disponível no PATH.
4.  **Python 3.12+**

### Dependências Python
Instale as dependências necessárias via pip:
```bash
pip install python-dotenv
```

## 💡 Guia de Integração

O VoxDev foi desenhado para ser "copy-paste ready":

1.  Copie a pasta `VoxDev/` para a raiz do seu novo projeto.
2.  Importe o `VoiceManager` (ajuste o path conforme sua estrutura):
    ```python
    # Se a pasta VoxDev estiver na raiz:
    from VoxDev.src.voxdev import VoiceManager
    
    vm = VoiceManager()
    ```
3.  **Gravar áudio**:
    ```python
    audio_path = vm.record() # Pressione Tab para parar
    text = vm.transcribe(audio_path)
    ```
4.  **Sintetizar fala**:
    ```python
    vm.speak("Olá! Como posso ajudar?") # Pressione Tab para interromper
    ```

## ⚙️ Configuração

O VoxDev suporta variáveis de ambiente via arquivo `.env` na raiz do seu projeto:

- `VOICE_LANGUAGE`: Idioma para o Whisper (Default: `Portuguese`).
- `WHISPER_MODEL`: Modelo do Whisper (`tiny`, `base`, `small`, etc).
- `WHISPER_DEVICE`: Dispositivo de execução (`cuda` ou `cpu`).
- `TTS_ENABLED`: Habilita/Desabilita o som (`true`/`false`).
- `VAULT_INBOX_PATH`: Caminho onde o `cli.py` salvará as transcrições (Default: `../vault/00-Inbox`).

## 🧪 Testes Rápidos

Dentro da pasta `VoxDev`, você pode testar os componentes individualmente:

**Testar Voz (TTS):**
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 -m voxdev.test_tts "Este é um teste de voz local."
```

**Testar Escuta (STT):**
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 -m voxdev.cli
```

---
Atualizado por Antigravity AI | 2026
