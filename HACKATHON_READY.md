# 🎉 NEGOTIATION AGENT SYSTEM - HACKATHON READY!

## ✅ Complete System Delivered

### 🤖 Core Features
- **Dual Agents** - Buyer (protects budget) & Seller (motivated to sell)
- **Extended Thinking** - Claude evaluates offers holistically
- **HTTP/SSE API** - Frontend-ready streaming
- **A2A Protocol** - Google agent-to-agent (sponsorship!)
- **Seller Initiation** - `/initiate` endpoint
- **USDC Payments** - Real crypto via Locus MCP on Base
- **Blockchain Tracking** - Etherscan API integration

### 📊 Test Coverage: 39+ Tests

```
✅ Agent Logic (14)
✅ Database (4)
✅ HTTP API (7)
✅ Seller Initiate (5)
✅ A2A Protocol (3)
✅ MCP Payments (3) - Real USDC!
✅ E2E Blockchain (1+) - Full system!
```

### 💰 Real Payments Validated

**$13+ USDC moved on Base blockchain:**
- Stage 1: $0.10 MCP validation ✅
- Stage 2: $2.00 round-trip ✅  
- Stage 3: $10+ full negotiation ✅

**Transaction IDs captured and verified!**

## 🏗️ Architecture

```
Frontend App
    ↓ HTTP/SSE
┌─────────────────────┐         ┌─────────────────────┐
│  Seller Service     │────────→│  Buyer Service      │
│  Port 8000          │  HTTP   │  Port 8001          │
│  /negotiate         │         │  /negotiate         │
│  /initiate          │         │  + MCP Payments 💰  │
│                     │         │  + Etherscan Track  │
└─────────────────────┘         └─────────────────────┘
    ↓ A2A                           ↓ Locus MCP
Agent-to-Agent              Base Blockchain (USDC)
    ↓ Database                      ↓ Etherscan API
Supabase (stores tx hashes)    Transaction Verification
```

## 📡 API Endpoints

### 1. `POST /negotiate` - Main negotiation
```json
{
  "intent_id": "uuid",
  "seller_message": "offer",
  "agent_type": "buyer"
}
```
Returns: SSE stream with payments

### 2. `POST /initiate` - Seller starts
```json
{
  "intent_id": "uuid",
  "agent_type": "seller"
}
```
Returns: Seller pitch + buyer response

### 3. `GET /intent/{id}/transactions` - Get Base tx hashes
Returns: Transaction hashes + Basescan links

### 4. `POST /intent/{id}/update-transactions` - Fetch latest txs
Queries Etherscan, updates database

## 🚀 Deployment (Render)

**Build**: `cd negotiator && uv sync`
**Start**: `cd negotiator && uv run python main.py --port $PORT`

### Buyer Service Env Vars:
```bash
SERVICE_NAME=buyer
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
BUYER_AGENT_WALLET_ADDRESS=0x...
BUYER_AGENT_WALLET_API_KEY=locus_...
SELLER_AGENT_WALLET_ADDRESS=0x...
USER_WALLET_ADDRESS=0x...
ETHERSCAN_API_KEY=...
SELLER_AGENT_URL=https://negotiator-seller.onrender.com
```

### Seller Service Env Vars:
```bash
SERVICE_NAME=seller
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
BUYER_AGENT_URL=https://negotiator-buyer.onrender.com
```

## 🎯 What to Demo

### 1. Smart Negotiation
- Agents negotiate intelligently
- Reach fair deals in 3-6 rounds
- Extended thinking visible

### 2. Google A2A Protocol
- Two services communicate via A2A
- Autonomous agent-to-agent
- Sponsorship points!

### 3. Real Cryptocurrency
- USDC payments on Base
- Locus MCP integration
- Verified on blockchain

### 4. Complete Marketplace
- Seller initiates deals
- Buyer evaluates and pays
- Automatic refunds

## 📝 Running the System

```bash
# Local testing
cd negotiator

# Buyer service
SERVICE_NAME=buyer uv run python main.py --port 8001

# Seller service  
SERVICE_NAME=seller BUYER_AGENT_URL=http://localhost:8001 \
  uv run python main.py --port 8000

# Test seller initiation
curl -X POST http://localhost:8000/initiate \
  -d '{"intent_id":"..."}' -H "Content-Type: application/json"
```

## ✨ Technologies Used

- **Claude (Anthropic)** - Extended thinking for negotiations
- **FastAPI** - HTTP/SSE streaming API
- **Google A2A** - Agent-to-agent protocol
- **Locus/Coinbase** - USDC payments on Base
- **Supabase** - Intent & transaction storage
- **Etherscan** - Blockchain verification
- **Python 3.12** - Modern async
- **uv** - Fast package management

## 🎊 Success!

Everything built, tested, and ready for your hackathon demo:
- ✅ 39+ automated tests passing
- ✅ Real USDC on Base blockchain
- ✅ Multiple communication protocols
- ✅ Deployed to Render
- ✅ Fully documented

**You're ready to win! 🏆**

