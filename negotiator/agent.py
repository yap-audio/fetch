"""Negotiation agent using Claude with extended thinking."""

import os
import re
from typing import Dict, Any, AsyncIterator, List, Optional
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Import payment client
try:
    from payments import LocusMCPClient
    PAYMENTS_AVAILABLE = True
except ImportError:
    PAYMENTS_AVAILABLE = False

load_dotenv()


class NegotiationAgent:
    """Agent that negotiates on behalf of a buyer or seller based on their intent."""
    
    def __init__(self, intent_data: Dict[str, Any], agent_type: str = "buyer"):
        """
        Initialize negotiation agent with intent data.
        
        Args:
            intent_data: Dictionary containing max_amount_usd and description
            agent_type: Either "buyer" or "seller" (default: "buyer")
        """
        if agent_type not in ["buyer", "seller"]:
            raise ValueError("agent_type must be 'buyer' or 'seller'")
        
        self.intent_data = intent_data
        self.agent_type = agent_type
        self.max_budget = float(intent_data["max_amount_usd"])
        self.description = intent_data["description"]
        
        # Calculate minimum for seller (65% of buyer's max)
        self.min_amount = self.max_budget * 0.65
        
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")
        self.client = AsyncAnthropic(api_key=api_key)
        
        # Initialize payment client for buyer agents
        if agent_type == "buyer" and PAYMENTS_AVAILABLE:
            buyer_api_key = os.getenv("BUYER_AGENT_WALLET_API_KEY")
            self.mcp_client = LocusMCPClient(buyer_api_key) if buyer_api_key else None
        else:
            self.mcp_client = None
        
        # Build system prompt based on agent type
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build system prompt based on agent type."""
        if self.agent_type == "buyer":
            return self._build_buyer_system_prompt()
        else:
            return self._build_seller_system_prompt()
    
    def _build_buyer_system_prompt(self) -> str:
        """Build system prompt for buyer agent."""
        return f"""You are a skilled negotiation agent representing a buyer. Your goal is to negotiate the best possible deal on their behalf.

BUYER'S INTENT:
- Item wanted: {self.description}
- Maximum budget: ${self.max_budget:.2f} USD

YOUR ROLE:
1. Evaluate seller offers using extended thinking to consider:
   - Whether the price is within budget
   - If there's room for negotiation (even if within budget)
   - Market value and fairness of the offer
   - Negotiation tactics (anchoring, concessions, timing)

2. Respond conversationally but strategically:
   - If the offer is way over budget: politely decline or make a counter-offer
   - If the offer is reasonable but could be better: negotiate for a better price
   - If the offer is at or below budget AND fair: accept the deal

3. When you make a decision, clearly indicate it by ending your response with one of:
   - "DECISION: ACCEPT" - when you want to accept the offer
     IMPORTANT: When accepting, clearly state the exact agreed price: "I accept at $14,200. DECISION: ACCEPT"
   - "DECISION: REJECT" - when you want to decline permanently
   - "DECISION: CONTINUE" - when you want to keep negotiating

NEGOTIATION TACTICS:
- Start with a lower counter-offer to anchor expectations
- Show genuine interest but don't seem desperate
- Use the buyer's constraints as leverage
- Be respectful and professional
- Know when to walk away

Remember: You're protecting the buyer's interests while trying to reach a fair deal. Use your extended thinking to evaluate offers holistically."""
    
    def _build_seller_system_prompt(self) -> str:
        """Build system prompt for seller agent."""
        return f"""You are a skilled negotiation agent representing a seller. Your PRIMARY goal is to SELL the item while getting a fair price.

SELLER'S ITEM:
- Item for sale: {self.description}
- Minimum acceptable price: ${self.min_amount:.2f} USD (this is your floor - don't go below this)
- Target price range: ${self.min_amount:.2f} - ${self.max_budget:.2f} USD

YOUR ROLE:
1. Evaluate buyer offers using extended thinking to consider:
   - Is the offer above your minimum? (${self.min_amount:.2f})
   - How close is it to your target range?
   - Is continuing negotiation worth the risk of losing the sale?
   - You WANT to sell - be flexible and motivated to close

2. Respond conversationally and persuasively:
   - If offer is above minimum: encourage the buyer to accept with your counter-offer
   - If offer is close to minimum: make attractive counter-offer to close the deal
   - If offer is below minimum: counter-offer at or slightly above minimum
   - Emphasize value, condition, and why it's a good deal
   - Remember: The BUYER must accept to complete the purchase and payment

3. When you make a decision, clearly indicate it by ending your response with one of:
   - "DECISION: CONTINUE" - when you want to make a counter-offer or continue negotiating
     IMPORTANT: As the seller, you should almost always use CONTINUE. Only the buyer can finalize the deal.
   - "DECISION: REJECT" - when the offer is unreasonably low and you want to stop
   
NOTE: You should NOT use "DECISION: ACCEPT" as the seller. The buyer must be the one to accept and initiate payment. Your job is to negotiate and present good offers until the buyer accepts.

NEGOTIATION STRATEGY:
- You're MOTIVATED to sell (this is key!)
- Be willing to compromise to close the deal
- If offer is reasonable (>= minimum), lean toward accepting
- Don't let perfect be the enemy of good - a bird in hand is worth two in the bush
- Build rapport and emphasize the item's value
- If buyer seems serious, work with them on price

Remember: Your goal is to SELL while staying above ${self.min_amount:.2f}. Be strategic but willing to close the deal. Use your extended thinking to evaluate if an offer is good enough to accept."""

    async def negotiate(
        self, 
        seller_message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a seller message and stream back the agent's response.
        
        Args:
            seller_message: The seller's offer or message
            conversation_history: Optional list of previous messages
            
        Yields:
            Dictionaries containing response chunks and metadata
        """
        # Build the prompt including conversation history
        prompt = self._build_prompt(seller_message, conversation_history)
        
        # Stream response from Claude with extended thinking
        full_response = ""
        
        async with self.client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            thinking={
                "type": "enabled",
                "budget_tokens": 2000
            }
        ) as stream:
            async for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        text = event.delta.text
                        full_response += text
                        yield {
                            "type": "text",
                            "content": text,
                            "is_final": False
                        }
        
        # Extract decision from final response
        decision = self._extract_decision(full_response)
        
        # Extract transaction amount if buyer is accepting
        transaction_amount = self._extract_transaction_amount(full_response, decision)
        
        # Execute payment if buyer accepts or rejects
        payment_result = None
        if self.agent_type == "buyer" and decision in ["accept", "reject"]:
            payment_result = await self.execute_payment(decision, transaction_amount)
        
        # Send final message with decision and payment
        yield {
            "type": "final",
            "content": full_response,
            "decision": decision,
            "transaction_amount": transaction_amount,
            "payment_result": payment_result,
            "is_final": True
        }
    
    def _build_prompt(
        self, 
        seller_message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build the prompt including conversation history."""
        prompt_parts = []
        
        if conversation_history:
            prompt_parts.append("CONVERSATION SO FAR:")
            for msg in conversation_history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt_parts.append(f"{role.upper()}: {content}")
            prompt_parts.append("")
        
        prompt_parts.append(f"SELLER'S MESSAGE: {seller_message}")
        prompt_parts.append("")
        prompt_parts.append("Please respond to this offer. Remember to end with a clear DECISION.")
        
        return "\n".join(prompt_parts)
    
    def _extract_decision(self, response: str) -> str:
        """
        Extract the decision from the agent's response.
        
        Returns:
            One of: "accept", "reject", "continue"
        """
        response_upper = response.upper()
        
        if "DECISION: ACCEPT" in response_upper:
            return "accept"
        elif "DECISION: REJECT" in response_upper:
            return "reject"
        else:
            return "continue"
    
    def _extract_transaction_amount(self, response: str, decision: str) -> Optional[float]:
        """
        Extract agreed transaction amount from response.
        
        Looks for dollar amounts mentioned in acceptance message.
        
        Returns:
            Agreed amount in USD, or None if not found/applicable
        """
        if decision != "accept":
            return None
        
        # Find all dollar amounts in response
        # Matches: $14,000 or $14000 or 14000 or 14,000.00
        amounts = re.findall(r'\$?\s*([\d,]+(?:\.\d{2})?)', response)
        
        # Convert and filter to reasonable range
        for amount_str in amounts:
            try:
                amount = float(amount_str.replace(',', ''))
                # Must be positive and within budget
                if 0.01 < amount <= self.max_budget:
                    return amount
            except ValueError:
                continue
        
        # Fallback: couldn't parse, use seller minimum
        return self.min_amount if hasattr(self, 'min_amount') else None
    
    async def execute_payment(
        self,
        decision: str,
        transaction_amount: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute USDC payment based on negotiation decision.
        
        Args:
            decision: "accept" or "reject"
            transaction_amount: Agreed amount (for accept)
            
        Returns:
            Payment results with transaction details, or None if no payment
        """
        if not self.mcp_client:
            return None  # No payment capability (seller or no wallet)
        
        seller_address = os.getenv("SELLER_AGENT_WALLET_ADDRESS")
        user_address = os.getenv("USER_WALLET_ADDRESS")
        
        if not seller_address or not user_address:
            return {"error": "Wallet addresses not configured"}
        
        try:
            if decision == "accept" and transaction_amount:
                # Send payment to seller
                seller_payment = await self.mcp_client.send_to_address(
                    address=seller_address,
                    amount=transaction_amount,
                    memo=f"Purchase: {self.description[:80]}"
                )
                
                # Calculate and send refund to user
                remaining = self.max_budget - transaction_amount
                user_refund = None
                
                if remaining > 0.01:  # Skip tiny refunds
                    user_refund = await self.mcp_client.send_to_address(
                        address=user_address,
                        amount=remaining,
                        memo="Refund: Remaining budget"
                    )
                
                return {
                    "seller_payment": seller_payment,
                    "user_refund": user_refund,
                    "amount_paid": transaction_amount,
                    "amount_refunded": remaining
                }
            
            elif decision == "reject":
                # Full refund to user
                refund = await self.mcp_client.send_to_address(
                    address=user_address,
                    amount=self.max_budget,
                    memo="Full refund: Deal rejected"
                )
                
                return {
                    "user_refund": refund,
                    "amount_refunded": self.max_budget
                }
        
        except Exception as e:
            return {"error": str(e)}
        
        return None  # Decision is "continue", no payment yet

