# ✅ Dual-Agent Negotiation System - COMPLETE!

## Test Results: 28/28 PASSING ✅

### Unit Tests (18 tests)
- ✅ **Buyer Agent** (8 tests) - All passing
- ✅ **Seller Agent** (6 tests) - All passing  
- ✅ **Database** (4 tests) - All passing

### Integration Tests (7 tests)
- ✅ Health check
- ✅ Buyer agent negotiation
- ✅ Seller agent negotiation
- ✅ Invalid intent handling
- ✅ High/reasonable offer scenarios

### Agent-to-Agent Tests (3 tests) 🌟
- ✅ **Full negotiation between two services** - DEAL REACHED in 4 rounds!
- ✅ Buyer rejects unreasonable prices
- ✅ Agents reach agreement

## Live Demonstration

**Test Negotiation Result:**
- **Item**: 2025 Kawasaki Ninja ZX-6R KRT Edition
- **Buyer's Max**: $15,000
- **Seller's Min**: $9,750 (65% of max)
- **Opening Offer**: $18,000
- **Final Deal**: $14,200 
- **Rounds**: 4
- **Outcome**: ✅ ACCEPTED by buyer

## System Architecture

```
┌─────────────┐         ┌─────────────┐
│   Seller    │         │    Buyer    │
│   Agent     │◄────────┤    Agent    │
│ (Port 9001) │         │ (Port 9000) │
└──────┬──────┘         └──────┬──────┘
       │                       │
       │    Orchestrator       │
       └───────────┬───────────┘
                   │
            ┌──────▼──────┐
            │  Supabase   │
            │   Intents   │
            └─────────────┘
```

## Key Features Implemented

### Monorepo Structure ✅
```
negotiator/
├── main.py                    # FastAPI with agent_type support
├── agent.py                   # Dual-mode agent (buyer/seller)
├── database.py                # Supabase integration
├── orchestrator.py            # Agent-to-agent coordinator
├── demo.py                    # Interactive demos
├── requirements.txt
├── README.md
└── tests/
    ├── test_agent.py          # Buyer tests
    ├── test_seller_agent.py   # Seller tests  
    ├── test_database.py       # DB tests
    ├── test_integration.py    # API tests
    └── test_agent_to_agent.py # TWO-SERVICE tests
```

### Agent Types ✅

**Buyer Agent:**
- Goal: Minimize price, protect buyer
- Has: `max_amount_usd` from intent
- Strategy: Aggressive negotiation, quality focus
- Decision: Accept if good value ≤ max

**Seller Agent:**
- Goal: **SELL the item** (motivated!)
- Calculates: `min_amount_usd` = 65% of buyer's max
- Strategy: Flexible, wants to close deal
- Decision: Accept if ≥ minimum, willing to compromise

### HTTP API ✅

```bash
POST /negotiate
{
  "intent_id": "uuid",
  "seller_message": "offer message",
  "agent_type": "buyer" | "seller",
  "conversation_history": []
}
```

### Orchestrator ✅

```bash
python negotiator/orchestrator.py \
  --intent-id 32ec0fba-931e-49b2-b4c2-02a1d6929a9c \
  --buyer-url http://localhost:9000 \
  --seller-url http://localhost:9001 \
  --max-rounds 10
```

## Running the System

### Single Service
```bash
python negotiator/main.py --port 8000
```

### Two Services for Agent-to-Agent
```bash
# Terminal 1: Buyer service
python negotiator/main.py --port 9000

# Terminal 2: Seller service
python negotiator/main.py --port 9001

# Terminal 3: Orchestrator
python negotiator/orchestrator.py \
  --intent-id 32ec0fba-931e-49b2-b4c2-02a1d6929a9c
```

### Run All Tests
```bash
pytest negotiator/tests/ -v
```

## Performance

- **Response Time**: ~15-20 seconds per turn (includes Claude thinking)
- **Negotiation Rounds**: Typically 3-6 rounds to reach deal
- **Test Suite**: 28 tests in ~3.5 minutes
- **Agent-to-Agent**: Successfully negotiates and closes deals

## What Makes This Work

1. **Seller is motivated to sell** - 65% floor gives flexibility
2. **Extended thinking** - Both agents evaluate holistically
3. **Real HTTP communication** - Services truly independent
4. **Conversation history** - Context maintained across turns
5. **Clear decisions** - ACCEPT/REJECT/CONTINUE markers

## Hackathon Ready! 🚀

- ✅ Monorepo structure
- ✅ Dual agent types (buyer/seller)
- ✅ HTTP API for app integration
- ✅ Two-service orchestration
- ✅ Comprehensive tests (28/28)
- ✅ Automated agent-to-agent negotiations
- ✅ Real deals reached!

**Perfect for your app to call and orchestrate negotiations!**

