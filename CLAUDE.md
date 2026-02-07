# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Andrew is a Voice AI agent for Bull Bank built with Vapi.ai. He helps customers learn about and apply for the Bank-travel credit card. The agent is bilingual (English/Spanish) and uses GPT-4o for conversation with ElevenLabs for text-to-speech.

## Commands

### Setup
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in API keys
```

### Deploy/Update Assistant
```bash
python scripts/create_assistant.py           # Create new assistant on Vapi
python scripts/update_assistant.py           # Update existing assistant with local changes
python scripts/create_structured_output.py   # Create/link structured output schema on Vapi
```

### Run Webhook Server (for function calling)
```bash
uvicorn src.webhooks.server:app --reload --port 8000
```

### View Call History
```bash
python scripts/list_calls.py
python scripts/list_calls.py --call-id <call_id>
```

### Test Outbound Call
```bash
python scripts/test_call.py --assistant-id <id> --phone <number>
```

## Architecture

```
Vapi.ai (orchestration)
    ├── Deepgram Nova-2 (STT, multi-language)
    ├── GPT-4o (LLM)
    └── ElevenLabs multilingual_v2 (TTS)
           │
           ▼
    Your Webhook Server (optional, for function calls)
```

### Key Configuration Files

- `src/agent/prompts.py` - System prompt and first message. Edit this to change Andrew's personality, language, or conversation flow.
- `src/agent/andrew.py` - Vapi assistant configuration: voice settings (`VOICE_CONFIG`), LLM settings (`LLM_CONFIG`), transcriber settings, and call analysis plan (`ANALYSIS_PLAN`). The full assistant config is assembled in `ANDREW_CONFIG`.
- `src/config.py` - Singleton `Config` class loading from `.env`. Import as `from src.config import config`.

### Updating Andrew

After editing `prompts.py` or `andrew.py`, run:
```bash
python scripts/update_assistant.py
```

This sends a PATCH request to Vapi's API with the new `ANDREW_CONFIG`.

### Webhook Flow

When `WEBHOOK_URL` is set in `.env`, Vapi sends events to your server at `POST /webhook`:

1. `function-call` → `handle_function_call()` in `server.py` → dispatches to tools in `src/tools/`
2. `end-of-call-report` → `handle_call_end()` → extracts metrics, runs LLM transcript analysis via `transcript_analyzer.py`, pushes results to Vapi via `vapi_client.py`
3. `transcript-update` → `handle_transcript()` (logging only)
4. `status-update` → `handle_status_update()` (logging only)

### Adding New Tools (Function Calling)

To add a new tool the agent can call during conversations:
1. Define the tool function and its Vapi JSON schema in a new file under `src/tools/` (follow the pattern in `credit_card.py` with `ELIGIBILITY_CHECK_TOOL`)
2. Add the tool schema to `LLM_CONFIG["tools"]` in `src/agent/andrew.py`
3. Add a handler case in `handle_function_call()` in `src/webhooks/server.py`
4. Update the system prompt in `src/agent/prompts.py` if the agent needs instructions on when to use the tool

### Data Models

`src/models/call_analysis.py` defines Pydantic models for structured call analysis:
- `CallMetrics` - duration, cost, timestamps
- `TranscriptAnalysis` - conversion status, satisfaction, objections
- `EligibilityOutcome` - eligibility check results
- `CallAnalysisResult` - top-level model combining all analysis data

## Environment Variables

Required in `.env`:
- `VAPI_API_KEY` - Vapi private API key
- `OPENAI_API_KEY` - For transcript analysis (also add to Vapi dashboard for LLM)
- `WEBHOOK_URL` - Optional, your server URL for function calls (e.g., ngrok URL)

## Assistant ID

Current deployed assistant: `8a376a7b-b66f-490c-b43a-3af3bb15cd60`

This ID is hardcoded in `scripts/update_assistant.py`. Update it if you create a new assistant.
