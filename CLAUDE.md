# CLAUDE.md — VoxClaude

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Contexto da Empresa (Vault)

@/Users/jpoloni/Library/Mobile Documents/iCloud~md~obsidian/Documents/mac-vault/Vixxia.md

---

## Este Projeto (Vault)

@/Users/jpoloni/Library/Mobile Documents/iCloud~md~obsidian/Documents/mac-vault/02-projetos/VoxDev.md

---

## Estado Operacional
> Atualizado a cada sessão. Reflete o agora.

- **Status:** ✅ Funcionando no Mac — ffmpeg + OpenAI Whisper API
- **Output:** `resposta-voz-{TIMESTAMP}.md` → inbox do MindCloud
- **Foco atual:** Estável — usado como upstream do MindCloud e interface chkvox

---

## Protocolo chkvox

**chkvox** é o comando de comunicação voz → instrução direta entre João e Claude.

**Fluxo:**
```
João fala → VoxClaude grava + transcreve via Whisper API
                    ↓
         00-Inbox/resposta-voz-*.md
                    ↓
João escreve "chkvox" no Claude Code
                    ↓
Claude lê a última transcrição e executa como instrução pura
```

**Como usar:**
1. Gravar: `PYTHONPATH=src python3 -m voxdev.cli` (na pasta VoxClaude)
2. Escrever `chkvox` no Claude Code
3. Claude lê e executa

Sem redigitar, sem copiar — voz vira instrução direta.

---

## Arquitetura

```
src/voxdev/
├── cli.py      — entry point: grava áudio, chama transcribe, salva no inbox
├── core.py     — VoiceManager: record(), transcribe() via Whisper API, speak()
└── config.py   — variáveis de ambiente
```

**Gravação:** `ffmpeg -f avfoundation` (Mac) / `arecord` (Linux)
**Transcrição:** OpenAI Whisper API (`whisper-1`)
**TTS:** `afplay` (Mac) / `aplay` (Linux) via Piper — desabilitado por padrão
**Silêncio:** para automaticamente após 5s de silêncio

## Comandos

```bash
# Gravar e transcrever
PYTHONPATH=src python3 -m voxdev.cli

# Instalar dependências
pip3 install -r requirements.txt
```

## Configuração (.env)

```bash
OPENAI_API_KEY=sk-...
VOICE_LANGUAGE=pt
VOICE_SAMPLE_RATE=44100
TTS_ENABLED=false
VAULT_INBOX_PATH=/Users/jpoloni/dev/vMindCloud/vMindCloud/vixxia-vault/vixxia-vault/00-Inbox
```

## Convenções

- Arquivos salvos como `resposta-voz-{TIMESTAMP}.md` — padrão esperado pelo MindCloud
- Header obrigatório: `# Resposta — {TIMESTAMP}` (linha 1), linha em branco, conteúdo
- Nunca alterar o formato de saída sem atualizar `inbox.py` do MindCloud simultaneamente

## Restrições — não fazer sem confirmar

- Alterar formato do arquivo de saída — quebra o pipeline MindCloud
- Habilitar TTS sem instalar Piper — vai falhar silenciosamente

## Ritual de Sessão

**Abertura:** *"Claude, abre sessão do VoxClaude — qual o contexto?"*
**Durante:** *"Anota isso no CLAUDE.md"*
**Encerramento:** *"Claude, fecha sessão — o que vale registrar?"*
