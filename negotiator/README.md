# Negotiation Agent Service

A Python service using Claude Agent SDK that negotiates on behalf of buyers by evaluating seller offers against buyer intents stored in Supabase.

## Features

- 🤖 AI-powered negotiation using Claude with extended thinking
- 💬 Real-time streaming responses via Server-Sent Events (SSE)
- 🎯 Decision-making: Accept, Reject, or Continue negotiating
- 📊 Integration with Supabase for buyer intent management
- ✅ Comprehensive test suite with real integration tests

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Seller     │─────▶│   FastAPI    │─────▶│  Supabase    │
│  (Human/AI)  │      │   Service    │      │   Database   │
└──────────────┘      └──────────────┘      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │ Claude Agent │
                      │     SDK      │
                      └──────────────┘
```

## Setup

### Prerequisites

- Python 3.8+
- Anthropic API key
- Supabase account with intents table

### Installation

1. Clone the repository:
```bash
cd /Users/osprey/repos/fetch
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

Required environment variables:
```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

### Database Schema

The service expects an `intents` table in Supabase:

```sql
CREATE TABLE intents (
  uuid UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  taker_id UUID,
  max_amount_usd NUMERIC NOT NULL,
  description TEXT NOT NULL,
  status TEXT
);
```

## Usage

### Starting the Server

```bash
python main.py
```

Server runs on `http://localhost:8000`

### API Endpoints

#### Health Check
```bash
GET /
```

#### Negotiate
```bash
POST /negotiate
```

**Request Body:**
```json
{
  "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
  "seller_message": "I can offer this to you for $500",
  "conversation_history": []
}
```

**Response:** Server-Sent Events (SSE) stream

**Event Format:**
```json
data: {"type": "text", "content": "Thanks for...", "is_final": false}
data: {"type": "final", "content": "...", "decision": "accept", "is_final": true}
```

### Example with cURL

```bash
curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
    "seller_message": "I can sell this for $200"
  }'
```

### Example with Python

```python
import httpx
import json

async def negotiate():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/negotiate",
            json={
                "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
                "seller_message": "I can offer it for $150"
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(data)
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/test_database.py tests/test_agent.py -v

# Integration tests only
pytest tests/test_integration.py -v
```

### Run Interactive Demo

The demo script runs through multiple negotiation scenarios:

```bash
# Start the server first
python main.py

# In another terminal, run the demo
python demo.py
```

The demo will:
1. Show the buyer's intent details
2. Run 3 negotiation scenarios:
   - High offer (above budget)
   - Reasonable offer (60% of budget)
   - Great deal (30% of budget)
3. Display streaming responses and decisions

## Project Structure

```
fetch/
├── main.py                 # FastAPI service
├── agent.py               # NegotiationAgent class
├── database.py            # Supabase client
├── requirements.txt       # Python dependencies
├── demo.py               # Interactive demo script
├── README.md             # This file
├── tests/
│   ├── __init__.py
│   ├── test_database.py  # Database unit tests
│   ├── test_agent.py     # Agent unit tests
│   └── test_integration.py # End-to-end tests
└── .env                  # Environment variables (not in git)
```

## How It Works

### 1. Request Flow

1. Seller sends offer via POST `/negotiate`
2. Service fetches buyer intent from Supabase
3. NegotiationAgent initializes with intent context
4. Claude evaluates offer with extended thinking
5. Response streams back via SSE
6. Final decision: accept, reject, or continue

### 2. Agent Decision Logic

The agent uses Claude's extended thinking to evaluate:
- Is the offer within budget?
- Is there room for negotiation?
- What's the market value?
- What negotiation tactics should be used?

### 3. Decision Types

- **ACCEPT**: Offer is good, buyer should accept
- **REJECT**: Offer is too high, decline permanently
- **CONTINUE**: Keep negotiating with counter-offer

## Negotiation Strategies

The agent employs several tactics:
- **Anchoring**: Starts with lower counter-offers
- **Showing interest**: Maintains engagement without desperation
- **Using constraints**: Leverages budget as negotiation tool
- **Knowing when to walk away**: Rejects unreasonable offers

## Development

### Adding New Features

- **Custom tools**: Modify `ClaudeAgentOptions` in `agent.py`
- **Database changes**: Update `database.py` and schema
- **New endpoints**: Add to `main.py`

### Debugging

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Limitations

- Conversation history stored in request (no persistence)
- Single endpoint for all negotiation states
- Minimal error handling (hackathon focus)
- No authentication/authorization

## Future Enhancements

- [ ] Persistent conversation storage
- [ ] Multi-user support with authentication
- [ ] WebSocket support for bidirectional communication
- [ ] Analytics dashboard for negotiation outcomes
- [ ] A/B testing different negotiation strategies
- [ ] Rate limiting and abuse prevention

## License

MIT

## Contributing

This is a hackathon project. Feel free to fork and improve!

## Support

For issues or questions, please open a GitHub issue.

