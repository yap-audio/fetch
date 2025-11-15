"""Unit tests for negotiation agent."""

import pytest
from agent import NegotiationAgent


def test_agent_initialization():
    """Test that agent can be initialized with intent data."""
    intent_data = {
        "max_amount_usd": 100.00,
        "description": "Vintage camera"
    }
    
    agent = NegotiationAgent(intent_data, agent_type="buyer")
    
    assert agent.max_budget == 100.00
    assert agent.description == "Vintage camera"
    assert agent.agent_type == "buyer"
    assert agent.client is not None
    assert agent.system_prompt is not None


def test_system_prompt_includes_intent():
    """Test that system prompt includes intent information."""
    intent_data = {
        "max_amount_usd": 250.50,
        "description": "Gaming laptop"
    }
    
    agent = NegotiationAgent(intent_data, agent_type="buyer")
    system_prompt = agent._build_buyer_system_prompt()
    
    assert "Gaming laptop" in system_prompt
    assert "250.50" in system_prompt
    assert "BUYER'S INTENT" in system_prompt
    assert "DECISION" in system_prompt


def test_decision_extraction_accept():
    """Test extracting accept decision from response."""
    intent_data = {
        "max_amount_usd": 100.00,
        "description": "Test item"
    }
    agent = NegotiationAgent(intent_data, agent_type="buyer")
    
    response = "That sounds great! DECISION: ACCEPT"
    decision = agent._extract_decision(response)
    
    assert decision == "accept"


def test_decision_extraction_reject():
    """Test extracting reject decision from response."""
    intent_data = {
        "max_amount_usd": 100.00,
        "description": "Test item"
    }
    agent = NegotiationAgent(intent_data, agent_type="buyer")
    
    response = "I'm sorry, that's too much. DECISION: REJECT"
    decision = agent._extract_decision(response)
    
    assert decision == "reject"


def test_decision_extraction_continue():
    """Test extracting continue decision from response."""
    intent_data = {
        "max_amount_usd": 100.00,
        "description": "Test item"
    }
    agent = NegotiationAgent(intent_data, agent_type="buyer")
    
    response = "How about we try $80 instead?"
    decision = agent._extract_decision(response)
    
    assert decision == "continue"


def test_prompt_building_with_history():
    """Test building prompt with conversation history."""
    intent_data = {
        "max_amount_usd": 100.00,
        "description": "Test item"
    }
    agent = NegotiationAgent(intent_data, agent_type="buyer")
    
    history = [
        {"role": "seller", "content": "I can offer it for $150"},
        {"role": "buyer", "content": "That's too high, how about $80?"}
    ]
    
    prompt = agent._build_prompt("I can do $120", history)
    
    assert "CONVERSATION SO FAR" in prompt
    assert "$150" in prompt
    assert "$80" in prompt
    assert "$120" in prompt


def test_prompt_building_without_history():
    """Test building prompt without conversation history."""
    intent_data = {
        "max_amount_usd": 100.00,
        "description": "Test item"
    }
    agent = NegotiationAgent(intent_data, agent_type="buyer")
    
    prompt = agent._build_prompt("I can offer it for $150")
    
    assert "SELLER'S MESSAGE" in prompt
    assert "$150" in prompt
    assert "CONVERSATION SO FAR" not in prompt


def test_invalid_agent_type():
    """Test that invalid agent type raises error."""
    intent_data = {
        "max_amount_usd": 100.00,
        "description": "Test item"
    }
    
    with pytest.raises(ValueError, match="agent_type must be"):
        NegotiationAgent(intent_data, agent_type="invalid")

