# Financial Agent - Andrew

A Voice AI agent for Bull Bank, built with Vapi.ai. Andrew is a friendly and professional representative who helps customers learn about and apply for the Bank-travel credit card.

## Features

- **Natural Voice Conversations**: Powered by ElevenLabs TTS and Deepgram STT
- **Intelligent Responses**: Uses GPT-4o for context-aware conversation
- **Eligibility Checking**: Function calling to check credit card eligibility
- **Professional Personality**: Helpful without being pushy

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Vapi.ai account ([Sign up](https://vapi.ai))
- OpenAI API key

### 2. Installation

```bash
# Clone and navigate to the project
cd financial_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
# VAPI_API_KEY=your_vapi_api_key
# OPENAI_API_KEY=your_openai_api_key
```

### 4. Create the Assistant

```bash
python scripts/create_assistant.py
```

This creates Andrew on Vapi and outputs the assistant ID.

### 5. Test the Assistant

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai/assistants)
2. Find "Andrew - Bull Bank Representative"
3. Click "Test Call" to try it in your browser

## Project Structure

```
financial_agent/
├── src/
│   ├── config.py              # Environment configuration
│   ├── agent/
│   │   ├── andrew.py          # Assistant configuration
│   │   └── prompts.py         # System prompt and personality
│   ├── tools/
│   │   └── credit_card.py     # Eligibility check tool
│   └── webhooks/
│       └── server.py          # FastAPI webhook server
├── scripts/
│   ├── create_assistant.py    # Deploy Andrew to Vapi
│   ├── test_call.py           # Trigger outbound test calls
│   └── list_calls.py          # View call history
└── docs/
    └── ARCHITECTURE.md        # Voice AI architecture guide
```

## Usage

### Testing via Dashboard

The easiest way to test Andrew is through the Vapi dashboard:
1. Navigate to your assistant
2. Click "Test Call"
3. Speak with Andrew in your browser

### Running the Webhook Server

For function calling (eligibility checks), run the webhook server:

```bash
# Start the server
uvicorn src.webhooks.server:app --reload --port 8000

# For production, use a tunnel like ngrok
ngrok http 8000
```

Then update your assistant's webhook URL in the Vapi dashboard.

### Making Test Calls

To trigger an outbound call:

```bash
python scripts/test_call.py --assistant-id asst_xxx --phone +1234567890
```

### Viewing Call History

```bash
# List recent calls
python scripts/list_calls.py

# View specific call details
python scripts/list_calls.py --call-id call_xxx
```

## Andrew's Capabilities

### Conversation Topics

- Bank-travel credit card benefits
- Annual fees and terms
- Eligibility requirements
- Application process

### Product Knowledge

| Feature | Details |
|---------|---------|
| Rewards | 1 mile per dollar spent |
| Perks | Airport lounge access worldwide |
| Fees | $95/year (waived first year) |
| International | No foreign transaction fees |

### Eligibility Check

Andrew can check if a customer qualifies:

- **Income ≥ $25,000**: Eligible
- **Income < $25,000 + credit history**: Review required
- **Income < $25,000 + no credit**: Not eligible (suggests starter card)

## Customization

### Changing the Personality

Edit `src/agent/prompts.py` to modify Andrew's:
- Tone and communication style
- Product knowledge
- Conversation flow
- Guidelines and boundaries

### Adding New Tools

1. Define the tool in `src/tools/`
2. Add it to `ANDREW_CONFIG` in `src/agent/andrew.py`
3. Handle the function call in `src/webhooks/server.py`
4. Redeploy with `python scripts/create_assistant.py`

### Changing the Voice

Edit `VOICE_CONFIG` in `src/agent/andrew.py`:

```python
VOICE_CONFIG = {
    "provider": "11labs",
    "voiceId": "new_voice_id_here",
    "stability": 0.5,
    "similarityBoost": 0.75,
}
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a detailed explanation of:
- The 5-component Voice AI pipeline
- How Vapi.ai orchestrates everything
- Function calling flow
- Latency considerations

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Quality

```bash
# Format code
pip install black isort
black src/ scripts/
isort src/ scripts/

# Type checking
pip install mypy
mypy src/
```

## Deployment

### Webhook Server

For production webhook handling:

1. Deploy the FastAPI server to a cloud provider (Railway, Render, AWS, etc.)
2. Update `WEBHOOK_URL` in Vapi dashboard
3. Consider adding authentication for webhook security

### Phone Numbers

1. Get a phone number from Vapi dashboard
2. Assign it to Andrew
3. Customers can now call directly

## Troubleshooting

### Assistant not responding

- Check Vapi API key is correct
- Verify OpenAI API key is added to Vapi dashboard
- Review call logs in Vapi dashboard

### Function calls not working

- Ensure webhook server is running and accessible
- Check webhook URL is configured in Vapi
- Review server logs for errors

### Voice sounds unnatural

- Adjust `stability` and `similarityBoost` in voice config
- Try different voice IDs from ElevenLabs
- Simplify prompts for more natural responses

## Resources

- [Vapi.ai Documentation](https://docs.vapi.ai)
- [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)
- [OpenAI API Reference](https://platform.openai.com/docs)

## License

MIT
