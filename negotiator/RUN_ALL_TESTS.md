# Complete Test Validation Guide

## Quick Test (Without A2A - 2 min)
```bash
cd /Users/osprey/repos/fetch/negotiator

# Start HTTP server
uv run python main.py --port 8000 &
sleep 3

# Run non-A2A tests (30 tests)
uv run pytest tests/ -k "not test_a2a" -v

# Kill server
pkill -f "main.py"
```

**Expected: 30/30 passing**

## Full Test Suite (With A2A - 5 min)
```bash
cd /Users/osprey/repos/fetch/negotiator

# Start HTTP server
uv run python main.py --port 8000 &
sleep 3

# Run ALL tests
uv run pytest tests/ -v

# Kill server
pkill -f "main.py"
```

**Expected: 33/33 passing**

## Test Categories

### Unit Tests (18) - No server needed
- `test_agent.py` (8 tests)
- `test_seller_agent.py` (6 tests)
- `test_database.py` (4 tests)

### Integration Tests (12) - Require server(s)
- `test_integration.py` (7 tests) - HTTP API
- `test_initiate.py` (5 tests) - Seller initiation

### Protocol Tests (3) - Spawn own services
- `test_a2a.py` (3 tests) - A2A protocol

## Individual Test Suites

```bash
# Unit tests only
uv run pytest tests/test_agent.py tests/test_seller_agent.py tests/test_database.py -v

# HTTP integration
uv run python main.py --port 8000 &
uv run pytest tests/test_integration.py -v
pkill -f "main.py"

# Seller initiation
uv run pytest tests/test_initiate.py -v

# A2A protocol
uv run pytest tests/test_a2a.py -v
```

## Success Criteria

✅ All 33 tests pass
✅ No critical errors
✅ Services start without issues
✅ Agents negotiate and reach deals

## Test Output

You should see:
```
======================== 33 passed, XX warnings ========================
```

Warnings about deprecations are expected and don't affect functionality.

