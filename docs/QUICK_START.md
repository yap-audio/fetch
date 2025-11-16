# Quick Start - Dual Agent Negotiation System

## Installation

```bash
cd /Users/osprey/repos/fetch
pip3 install -r negotiator/requirements.txt
```

## Test Everything

```bash
# Run all 28 tests
pytest negotiator/tests/ -v

# Should see: 28 passed ✅
```

## Run Agent-to-Agent Negotiation

### Option 1: Automated Test (Easiest)
```bash
pytest negotiator/tests/test_agent_to_agent.py::test_full_agent_to_agent_negotiation -v -s
```

Watch two agents negotiate in real-time!

### Option 2: Manual Orchestration

**Terminal 1 - Buyer Service:**
```bash
python3 negotiator/main.py --port 9000
```

**Terminal 2 - Seller Service:**
```bash
python3 negotiator/main.py --port 9001
```

**Terminal 3 - Run Negotiation:**
```bash
python3 negotiator/orchestrator.py \
  --intent-id 32ec0fba-931e-49b2-b4c2-02a1d6929a9c \
  --buyer-url http://localhost:9000 \
  --seller-url http://localhost:9001
```

## Test Single Agent

```bash
# Start service
python3 negotiator/main.py --port 8000

# In another terminal, test buyer agent
curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
    "seller_message": "I can sell this for $14,000",
    "agent_type": "buyer"
  }'

# Test seller agent
curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
    "seller_message": "Would you accept $10,000?",
    "agent_type": "seller"
  }'
```

## Environment Variables

Make sure `.env` has:
```
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

## Test Intent

ID: `32ec0fba-931e-49b2-b4c2-02a1d6929a9c`
- Item: 2025 Kawasaki Ninja ZX-6R
- Max Budget: $15,000
- Seller Floor: $9,750 (auto-calculated)

## Expected Results

- ✅ Agents negotiate intelligently
- ✅ Reach deal in 3-6 rounds typically
- ✅ Seller accepts reasonable offers (≥ $9,750)
- ✅ Buyer negotiates even within budget
- ✅ Both use extended thinking

## Success!

When you see:
```
✅ DEAL REACHED!
```

Your system is working perfectly! 🎉

