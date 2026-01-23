# Voice AI Architecture

This document explains the architecture of Voice AI systems and how this project implements them.

## The 5 Core Components

Voice AI systems consist of five interconnected components that work together to enable natural phone conversations with AI.

```
┌─────────────────────────────────────────────────────────────────┐
│                     VOICE AI PIPELINE                           │
│                                                                 │
│  ┌──────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐    │
│  │ Telephony│───▶│   STT   │───▶│   LLM   │───▶│   TTS    │    │
│  │ (Twilio) │    │(Deepgram│    │ (GPT-4o)│    │(ElevenLabs│   │
│  │          │◀───│)        │    │         │    │)         │    │
│  └──────────┘    └─────────┘    └─────────┘    └──────────┘    │
│       │                              │                          │
│       │         ┌────────────────────┘                          │
│       │         ▼                                               │
│       │    ┌─────────┐                                          │
│       └───▶│ Vapi.ai │  (Orchestration)                         │
│            └─────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Telephony Layer

**Purpose**: Handles the actual phone call infrastructure.

**What it does**:
- Receives incoming calls
- Makes outbound calls
- Manages call state (ringing, connected, ended)
- Handles call transfers
- Provides phone numbers

**Options**:
| Provider | Strengths | Best For |
|----------|-----------|----------|
| Twilio | Most reliable, extensive docs | Production systems |
| Vonage | Good international coverage | Global deployments |
| Telnyx | Cost-effective | High-volume use cases |

### 2. Speech-to-Text (STT)

**Purpose**: Converts the caller's voice into text that the LLM can process.

**What it does**:
- Real-time audio streaming
- Voice activity detection
- Transcription with punctuation
- Speaker diarization (who's speaking)

**Options**:
| Provider | Latency | Accuracy | Best For |
|----------|---------|----------|----------|
| Deepgram | ~100ms | Good | Real-time conversations |
| OpenAI Whisper | ~500ms | Excellent | Accuracy-critical apps |
| Google Speech | ~200ms | Good | Google Cloud users |
| Azure Speech | ~200ms | Good | Azure ecosystem |

**This project uses**: Deepgram Nova-2 for low-latency real-time transcription.

### 3. Large Language Model (LLM)

**Purpose**: Understands customer intent and generates appropriate responses.

**What it does**:
- Processes transcribed text
- Maintains conversation context
- Generates natural responses
- Decides when to call functions/tools
- Follows system prompt guidelines

**Options**:
| Provider | Speed | Quality | Best For |
|----------|-------|---------|----------|
| OpenAI GPT-4o | Fast | Excellent | General use |
| Anthropic Claude | Medium | Excellent | Safety-critical |
| Google Gemini | Fast | Good | Google ecosystem |
| Open-source | Varies | Good | Cost control |

**This project uses**: OpenAI GPT-4o for balanced speed and quality.

### 4. Text-to-Speech (TTS)

**Purpose**: Converts the LLM's text response into natural-sounding speech.

**What it does**:
- Text normalization (numbers, abbreviations)
- Prosody generation (rhythm, emphasis)
- Voice synthesis
- Streaming audio output

**Options**:
| Provider | Quality | Latency | Best For |
|----------|---------|---------|----------|
| ElevenLabs | Excellent | Low | Natural conversations |
| PlayHT | Good | Low | Budget-conscious |
| Azure Neural | Good | Low | Enterprise |
| OpenAI TTS | Good | Medium | OpenAI users |

**This project uses**: ElevenLabs with the "Adam" voice for professional male tone.

### 5. Orchestration Platform

**Purpose**: Coordinates all components and handles conversation flow.

**What it does**:
- Routes audio between components
- Manages turn-taking (interruptions, pauses)
- Handles timing and latency
- Provides webhooks for events
- Manages function calling

**Options**:
| Platform | Flexibility | Ease of Use | Best For |
|----------|-------------|-------------|----------|
| Vapi.ai | High | Medium | Custom solutions |
| Retell AI | Medium | High | Quick deployment |
| Bland AI | Medium | High | Simple agents |
| Custom | Full | Low | Complete control |

**This project uses**: Vapi.ai for flexibility and learning opportunity.

## Data Flow

Here's how a single exchange flows through the system:

```
1. Customer speaks: "What's the annual fee?"
                    │
                    ▼
2. Telephony (Vapi) receives audio stream
                    │
                    ▼
3. STT (Deepgram) transcribes: "What's the annual fee?"
                    │
                    ▼
4. LLM (GPT-4o) processes with context:
   - System prompt: "You are Andrew..."
   - Conversation history
   - Available tools
   - Generates: "The annual fee is $95, but it's waived for the first year."
                    │
                    ▼
5. TTS (ElevenLabs) synthesizes speech
                    │
                    ▼
6. Telephony streams audio to customer's phone
```

## Function Calling Flow

When Andrew needs to check eligibility:

```
Customer: "Am I eligible for this card?"
                    │
                    ▼
LLM decides to call function: check_credit_card_eligibility
                    │
                    ▼
Vapi sends webhook to your server with function call
                    │
                    ▼
Your server processes eligibility logic
                    │
                    ▼
Your server returns result to Vapi
                    │
                    ▼
LLM receives result and generates natural response
                    │
                    ▼
TTS converts to speech: "Great news! Based on..."
```

## Latency Considerations

Total response latency = STT + LLM + TTS + Network

Typical breakdown:
- STT: 100-300ms
- LLM: 200-500ms (first token)
- TTS: 100-200ms (first audio)
- Network: 50-100ms

**Target**: < 1 second for natural conversation feel

## Vapi.ai Specifics

### Why Vapi?

1. **Abstraction**: Handles STT/TTS/Telephony integration
2. **Dashboard**: Visual call monitoring and testing
3. **Iteration**: Change prompts without code deployment
4. **Phone numbers**: Built-in or bring your own
5. **Free tier**: Generous testing allowance

### Vapi Architecture

```
                    ┌──────────────────────────┐
                    │     Vapi Dashboard       │
                    │  (Configuration & Logs)  │
                    └──────────────────────────┘
                               │
                               ▼
┌─────────────┐    ┌──────────────────────────┐    ┌─────────────┐
│   Phone     │───▶│      Vapi Platform       │───▶│ Your Server │
│  Network    │◀───│  (STT + LLM + TTS +      │◀───│  (Webhooks) │
└─────────────┘    │   Orchestration)         │    └─────────────┘
                    └──────────────────────────┘
```

### Webhook Events

Vapi sends webhooks for:
- `status-update`: Call status changes
- `function-call`: LLM wants to call a function
- `end-of-call-report`: Call summary and transcript
- `transcript`: Real-time transcript updates

## Project Structure Mapping

```
src/
├── config.py           → Environment configuration
├── agent/
│   ├── andrew.py       → Vapi assistant configuration
│   └── prompts.py      → LLM system prompt
├── tools/
│   └── credit_card.py  → Function calling logic
└── webhooks/
    └── server.py       → Webhook handler (FastAPI)
```

## Further Reading

- [Vapi.ai Documentation](https://docs.vapi.ai)
- [Deepgram API Docs](https://developers.deepgram.com)
- [ElevenLabs API Docs](https://docs.elevenlabs.io)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
