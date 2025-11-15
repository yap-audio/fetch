"""Unit tests for seller negotiation agent."""

import pytest
from agent import NegotiationAgent


def test_seller_agent_initialization():
    """Test that seller agent can be initialized."""
    intent_data = {
        "max_amount_usd": 15000.00,
        "description": "2025 Kawasaki Ninja ZX-6R"
    }
    
    agent = NegotiationAgent(intent_data, agent_type="seller")
    
    assert agent.max_budget == 15000.00
    assert agent.agent_type == "seller"
    assert agent.min_amount == 9750.00  # 65% of max
    assert agent.client is not None


def test_seller_minimum_calculation():
    """Test that seller minimum is calculated correctly."""
    intent_data = {
        "max_amount_usd": 10000.00,
        "description": "Test item"
    }
    
    agent = NegotiationAgent(intent_data, agent_type="seller")
    
    # Should be 65% of max
    assert agent.min_amount == 6500.00


def test_seller_system_prompt():
    """Test that seller system prompt has correct elements."""
    intent_data = {
        "max_amount_usd": 15000.00,
        "description": "Motorcycle"
    }
    
    agent = NegotiationAgent(intent_data, agent_type="seller")
    system_prompt = agent._build_seller_system_prompt()
    
    assert "Motorcycle" in system_prompt
    assert "SELL" in system_prompt or "sell" in system_prompt
    assert "9750.00" in system_prompt  # minimum amount
    assert "DECISION" in system_prompt
    assert "MOTIVATED" in system_prompt or "motivated" in system_prompt


def test_seller_prompt_emphasizes_selling():
    """Test that seller prompt emphasizes motivation to sell."""
    intent_data = {
        "max_amount_usd": 10000.00,
        "description": "Test"
    }
    
    agent = NegotiationAgent(intent_data, agent_type="seller")
    prompt = agent._build_seller_system_prompt()
    
    # Should emphasize selling
    assert "PRIMARY goal" in prompt or "goal is to SELL" in prompt.upper()
    assert "willing to compromise" in prompt or "flexible" in prompt


def test_seller_has_minimum_floor():
    """Test that seller has minimum price floor."""
    intent_data = {
        "max_amount_usd": 20000.00,
        "description": "Test"
    }
    
    agent = NegotiationAgent(intent_data, agent_type="seller")
    prompt = agent._build_seller_system_prompt()
    
    # Should mention minimum
    assert "13000.00" in prompt  # 65% of 20000
    assert "Minimum" in prompt or "minimum" in prompt


def test_buyer_vs_seller_prompts_different():
    """Test that buyer and seller prompts are meaningfully different."""
    intent_data = {
        "max_amount_usd": 10000.00,
        "description": "Test item"
    }
    
    buyer_agent = NegotiationAgent(intent_data, agent_type="buyer")
    seller_agent = NegotiationAgent(intent_data, agent_type="seller")
    
    buyer_prompt = buyer_agent._build_buyer_system_prompt()
    seller_prompt = seller_agent._build_seller_system_prompt()
    
    # Should have different goals
    assert "buyer" in buyer_prompt.lower()
    assert "seller" in seller_prompt.lower()
    
    # Buyer should mention maximum, seller should mention minimum
    assert "Maximum budget" in buyer_prompt
    assert "Minimum acceptable" in seller_prompt
    
    # Prompts should be different enough
    assert buyer_prompt != seller_prompt

