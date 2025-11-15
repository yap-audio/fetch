# Negotiation Agent Service

A production-ready Python service using Claude (Anthropic) that negotiates on behalf of buyers and sellers, supporting HTTP/SSE, A2A Protocol, and seller-initiated negotiations.

## ✨ Features

- 🤖 **Dual Agent Types** - Buyer and seller agents with different strategies
- 💬 **HTTP/SSE API** - Real-time streaming for frontend apps
- 🔄 **A2A Protocol** - Agent-to-agent communication (Google A2A)
- 🎯 **Extended Thinking** - Claude evaluates offers holistically
- 📊 **Supabase Integration** - Intent management
- 🚀 **Seller Initiation** - Sellers can proactively start negotiations
- ✅ **33 Comprehensive Tests** - Full automation

## Architecture

```
Frontend Web App
    ↓ HTTP/SSE
┌─────────────────────────┐         ┌─────────────────────────┐
│   Seller Service        │────────→│   Buyer Service         │
│   main.py (Port 8000)   │  HTTP   │   main.py (Port 8001)   │
│   /negotiate            │         │   /negotiate            │
│   /initiate ⭐          │         │                         │
└─────────────────────────┘         └─────────────────────────┘
    ↓ A2A                               ↓ A2A
┌─────────────────────────┐         ┌─────────────────────────┐
│   Seller A2A            │────────→│   Buyer A2A             │
│   a2a_server.py (8002)  │  A2A    │   a2a_server.py (8003)  │
└─────────────────────────┘         └─────────────────────────┘
            ↓                                   ↓
        ┌───────────────────────────────────────┐
        │         Supabase Database             │
        │         (Buyer Intents)               │
        └───────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
cd /Users/osprey/repos/fetch/negotiator

# Install dependencies with uv
uv sync
```

### Environment Variables

Create `.env` with:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# For seller-initiated negotiations
BUYER_AGENT_URL=http://localhost:8001
SELLER_AGENT_URL=http://localhost:8000
```

### Run Single Service

```bash
# For frontend integration
uv run python main.py --port 8000
```

### Run Both Services (Full System)

```bash
# Terminal 1: Buyer Service
BUYER_AGENT_URL=http://localhost:8001 uv run python main.py --port 8001

# Terminal 2: Seller Service  
BUYER_AGENT_URL=http://localhost:8001 uv run python main.py --port 8000
```

## API Usage

### 1. `/negotiate` - Respond to Offers

**Buyer receives seller offer:**
```bash
curl -X POST http://localhost:8001/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
    "seller_message": "I can sell this for $14,000",
    "agent_type": "buyer"
  }'
```

**Seller receives buyer offer:**
```bash
curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
    "seller_message": "Would you take $12,000?",
    "agent_type": "seller"
  }'
```

### 2. `/initiate` - Seller Starts Negotiation ⭐

```bash
curl -X POST http://localhost:8000/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
    "agent_type": "seller"
  }'
```

**Response:**
```json
{
  "seller_pitch": "Hi! I have a pristine 2025 Kawasaki Ninja ZX-6R...",
  "buyer_response": "Thanks for reaching out! That sounds interesting...",
  "buyer_decision": "continue"
}
```

## Agent Strategies

### Buyer Agent
- **Goal**: Minimize price, protect budget
- **Max Budget**: From intent's `max_amount_usd`
- **Strategy**: Aggressive negotiation, quality focus
- **Decision**: Accept if good value ≤ max

### Seller Agent
- **Goal**: SELL the item (biased to close deals)
- **Min Price**: 65% of buyer's max (auto-calculated)
- **Strategy**: Flexible, motivated to close
- **Decision**: Accept if ≥ minimum, willing to compromise

## Testing

### Run All Tests (33 tests)

```bash
# Start HTTP server first
uv run python main.py --port 8000 &

# Run all tests
uv run pytest tests/ -v

# Expected: 33 passed
```

### Test Categories

- **Unit Tests** (18): Agent logic, database
- **Integration Tests** (12): HTTP API, seller initiation
- **Protocol Tests** (3): A2A agent-to-agent

### Quick Test (Skip A2A)

```bash
uv run pytest tests/ -k "not test_a2a" -v
# Expected: 30 passed in ~2 min
```

## A2A Protocol Support

### Start A2A Services

```bash
# Buyer A2A
uv run python a2a_server.py --port 8002

# Seller A2A
uv run python a2a_server.py --port 8003
```

### Run A2A Orchestrated Negotiation

```bash
uv run python orchestrator.py \
  --intent-id 32ec0fba-931e-49b2-b4c2-02a1d6929a9c \
  --protocol a2a \
  --buyer-url http://localhost:8002 \
  --seller-url http://localhost:8003
```

## Deployment to Render

### Service Configuration

**Build Command**: `cd negotiator && uv sync`

**Start Command**: `cd negotiator && uv run python main.py --port $PORT`

### Environment Variables

Set in Render dashboard:
```
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
BUYER_AGENT_URL=https://negotiator-buyer.onrender.com
SELLER_AGENT_URL=https://negotiator-seller.onrender.com
```

### Deploy Two Services

1. **negotiator-buyer** - Buyer agent service
2. **negotiator-seller** - Seller agent service (set BUYER_AGENT_URL to buyer service URL)

## Database Schema

Supabase `intents` table:
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

## Project Structure

```
negotiator/
├── main.py                 # HTTP API + /initiate endpoint
├── agent.py               # Dual-mode NegotiationAgent
├── database.py            # Supabase integration
├── orchestrator.py        # HTTP & A2A orchestration
├── a2a_server.py         # A2A protocol wrapper
├── demo.py               # Interactive demos
├── pyproject.toml        # uv configuration
├── README.md            # This file
├── RUN_ALL_TESTS.md    # Test guide
└── tests/               # 33 comprehensive tests
    ├── test_agent.py
    ├── test_seller_agent.py
    ├── test_database.py
    ├── test_integration.py
    ├── test_a2a.py
    └── test_initiate.py
```

## Example Flows

### Flow 1: Human App → Seller → Buyer

```
1. Human app calls: POST /initiate on seller service
2. Seller generates pitch
3. Seller contacts buyer service
4. Returns buyer's response to app
```

### Flow 2: Human → Buyer Agent

```
1. Seller (human) sends offer via app
2. App calls: POST /negotiate on buyer service
3. Buyer evaluates and responds
4. Returns streaming response
```

### Flow 3: Agent-to-Agent (A2A)

```
1. Services communicate via A2A protocol
2. Orchestrator coordinates conversation
3. Agents negotiate autonomously
4. Deal reached
```

## Success Metrics

Based on test intent (2025 Kawasaki Ninja ZX-6R, $15k budget):

✅ **Negotiations complete** in 3-6 rounds
✅ **Deals reached** at $13k-$14.5k range
✅ **Both protocols work** (HTTP & A2A)
✅ **Seller can initiate** successfully
✅ **33/33 tests pass** automatically

## Next Steps

- [ ] Add conversation persistence
- [ ] Multi-intent support
- [ ] Analytics dashboard
- [ ] Rate limiting
- [ ] WebSocket support

## License

MIT

## Support

Built for hackathon demo. Questions? Check test files for usage examples!
