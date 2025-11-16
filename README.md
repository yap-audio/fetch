# Fetch: Have everything.

An autonomous agent-to-agent negotiation system that uses AI to negotiate purchases on your behalf, with real cryptocurrency payments on Base blockchain.

## Overview

Fetch is a complete marketplace where AI agents negotiate with each other to reach fair deals. Buyers express intent, sellers initiate offers, and agents autonomously negotiate prices—all backed by real USDC payments on the Base network.

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Next.js App    │         │  Landing Page   │
│  (Dashboard)    │         │  (Marketing)    │
└────────┬────────┘         └─────────────────┘
         │
         ↓ HTTP/SSE
┌─────────────────┐         ┌─────────────────┐
│ Seller Service  │────────→│ Buyer Service   │
│ Port 8000       │  HTTP   │ Port 8001       │
│ /negotiate      │  A2A    │ /negotiate      │
│ /initiate       │         │ + Payments 💰   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │                           ↓ Locus MCP
         │                    ┌─────────────────┐
         │                    │ Base Blockchain │
         │                    │ (USDC Payments) │
         │                    └─────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│            Supabase Database                 │
│         (Intents & Transactions)             │
└──────────────────────────────────────────────┘
```

## Key Features

### 🤖 Dual-Agent Negotiation
- **Buyer Agent**: Minimizes price, protects budget, evaluates quality
- **Seller Agent**: Motivated to sell (65% floor), flexible pricing
- Both use Claude's extended thinking for strategic decision-making

### 💰 Real Cryptocurrency Payments
- USDC payments on Base blockchain via Locus MCP
- Automatic payment execution on deal acceptance
- Automatic refunds for unused budget
- Full transaction tracking with Etherscan integration

### 🔄 Multiple Communication Protocols
- **HTTP/SSE**: Streaming responses for web frontends
- **A2A Protocol**: Google's agent-to-agent standard
- **Seller Initiation**: Proactive deal-making

### ✅ Production-Ready
- 39+ automated tests (all passing)
- Real blockchain transactions validated
- Deployed on Render
- Comprehensive error handling

## Quick Start

### Prerequisites

```bash
# Required environment variables
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
BUYER_AGENT_WALLET_ADDRESS=0x...
BUYER_AGENT_WALLET_API_KEY=locus_...
SELLER_AGENT_WALLET_ADDRESS=0x...
USER_WALLET_ADDRESS=0x...
ETHERSCAN_API_KEY=...
```

### Run Negotiator Backend

```bash
cd negotiator
uv sync
uv run python main.py --port 8000
```

### Run Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Run Full System (Both Agents)

```bash
# Terminal 1: Buyer service
cd negotiator
SERVICE_NAME=buyer uv run python main.py --port 8001

# Terminal 2: Seller service
SERVICE_NAME=seller BUYER_AGENT_URL=http://localhost:8001 \
  uv run python main.py --port 8000

# Terminal 3: Test seller initiation
curl -X POST http://localhost:8000/initiate \
  -H "Content-Type: application/json" \
  -d '{"intent_id": "YOUR_INTENT_UUID", "agent_type": "seller"}'
```

## Technology Stack

### Backend
- **Python 3.12** with FastAPI for HTTP/SSE streaming
- **Claude (Anthropic)** with extended thinking for negotiation intelligence
- **Locus MCP** for USDC payments on Base blockchain
- **Supabase** for intent and transaction storage
- **Google A2A SDK** for agent-to-agent protocol
- **uv** for fast dependency management

### Frontend
- **Next.js 15** with App Router and TypeScript
- **shadcn/ui** for beautiful, accessible components
- **Tailwind CSS** for styling
- **Server-Side Rendering** for real-time intent updates

### Blockchain
- **Base** (Ethereum L2) for low-cost transactions
- **USDC** stablecoin for payments
- **Etherscan API** for transaction verification

## API Endpoints

### POST `/negotiate`
Respond to an offer from the other party.

```json
{
  "intent_id": "uuid",
  "seller_message": "I can sell this for $14,000",
  "agent_type": "buyer",
  "conversation_history": []
}
```

Returns: Server-Sent Events (SSE) stream

### POST `/initiate`
Seller proactively starts a negotiation.

```json
{
  "intent_id": "uuid",
  "agent_type": "seller"
}
```

Returns: Seller pitch + buyer response

### GET `/intent/{id}/transactions`
Get blockchain transaction hashes for an intent.

### POST `/intent/{id}/update-transactions`
Fetch latest transactions from Etherscan.

## Testing

```bash
cd negotiator

# Run all tests (39 tests)
uv run pytest tests/ -v

# Run quick tests (skip A2A)
uv run pytest tests/ -k "not test_a2a" -v

# Run specific test suites
uv run pytest tests/test_agent.py -v              # Agent logic
uv run pytest tests/test_mcp_stage1.py -v         # Payment validation
uv run pytest tests/test_ultimate_e2e.py -v       # Full system
```

**Expected: All tests passing ✅**

## Project Structure

```
fetch/
├── landing/                    # Marketing landing page
│   └── index.html
├── frontend/                   # Next.js dashboard
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── intent/[id]/       # Intent detail pages
│   │   └── page.tsx           # Main dashboard
│   └── components/            # React components
├── negotiator/                # Python backend
│   ├── main.py               # FastAPI server
│   ├── agent.py              # Negotiation agent (dual-mode)
│   ├── payments.py           # Locus MCP client
│   ├── database.py           # Supabase integration
│   ├── orchestrator.py       # Agent-to-agent coordinator
│   ├── a2a_server.py        # A2A protocol wrapper
│   └── tests/               # 39 comprehensive tests
└── docs/                     # Documentation
    ├── HACKATHON_READY.md
    ├── QUICK_START.md
    └── ...
```

## Deployment

Services are deployed on Render:
- **Buyer Service**: `negotiator-buyer.onrender.com`
- **Seller Service**: `negotiator-seller.onrender.com`

See [`docs/DEPLOY_TO_RENDER.md`](docs/DEPLOY_TO_RENDER.md) for detailed deployment instructions.

## Example Negotiation

```
Intent: 2025 Kawasaki Ninja ZX-6R
Budget: $15,000

Round 1:
Seller: "I can sell this pristine bike for $18,000"
Buyer: "That's above my budget. Would you consider $12,000?"

Round 2:
Seller: "I could go down to $16,500 for a serious buyer"
Buyer: "Still too high. How about $13,000?"

Round 3:
Seller: "Let's meet in the middle at $14,200"
Buyer: "ACCEPT - That's fair value"

✅ Deal reached at $14,200
💰 Buyer pays seller $14,200 USDC
💰 Buyer refunds user $800 USDC
🔗 Transactions verified on Base blockchain
```

## Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running quickly
- **[Hackathon Ready](docs/HACKATHON_READY.md)** - Demo preparation guide
- **[System Overview](docs/COMPLETE_SYSTEM.md)** - Complete technical details
- **[Deployment Guide](docs/DEPLOY_TO_RENDER.md)** - Production deployment

## Success Metrics

- ✅ **39+ automated tests** - All passing
- ✅ **$13+ USDC** moved on Base blockchain during testing
- ✅ **3-6 rounds** typical negotiation length
- ✅ **Fair deals** reached consistently
- ✅ **Multiple protocols** - HTTP, SSE, A2A
- ✅ **Real payments** - Verified on blockchain

## License

MIT

## Built With

Made with Claude (Anthropic), deployed on Render, powered by Base blockchain.

YCombinator November 2025

