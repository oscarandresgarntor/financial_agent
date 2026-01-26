# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Andrew is a Voice AI agent for Bull Bank built with Vapi.ai. He helps customers learn about and apply for the Bank-travel credit card. The agent is bilingual (English/Spanish) and uses GPT-4o for conversation with ElevenLabs for text-to-speech.

## Commands

### Deploy/Update Assistant
```bash
python scripts/create_assistant.py    # Create new assistant on Vapi
python scripts/update_assistant.py    # Update existing assistant with local changes
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
- `src/agent/andrew.py` - Vapi assistant configuration: voice settings (`VOICE_CONFIG`), LLM settings (`LLM_CONFIG`), transcriber settings, and call analysis plan (`ANALYSIS_PLAN`).

### Updating Andrew

After editing `prompts.py` or `andrew.py`, run:
```bash
python scripts/update_assistant.py
```

This sends a PATCH request to Vapi's API with the new `ANDREW_CONFIG`.

### Webhook Flow

When `WEBHOOK_URL` is set in `.env`, Vapi sends events to your server:
1. `function-call` → handled in `src/webhooks/server.py:handle_function_call()`
2. `end-of-call-report` → triggers transcript analysis via `src/services/transcript_analyzer.py`
3. Analysis results are pushed back to Vapi via `src/services/vapi_client.py`

### Data Models

`src/models/call_analysis.py` defines structured output for call analysis:
- `CallMetrics` - duration, cost, timestamps
- `TranscriptAnalysis` - conversion status, satisfaction, objections
- `EligibilityOutcome` - eligibility check results
- `CallAnalysisResult` - combines all analysis data

## Environment Variables

Required in `.env`:
- `VAPI_API_KEY` - Vapi private API key
- `OPENAI_API_KEY` - For transcript analysis (also add to Vapi dashboard for LLM)
- `WEBHOOK_URL` - Optional, your server URL for function calls (e.g., ngrok URL)

## Assistant ID

Current deployed assistant: `8a376a7b-b66f-490c-b43a-3af3bb15cd60`

This ID is hardcoded in `scripts/update_assistant.py`. Update it if you create a new assistant.
