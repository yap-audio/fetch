"""Simple Base transaction lookup via Etherscan API."""

import os
import httpx
from typing import Optional, Dict


class TransactionTracker:
    """Query Base blockchain for latest buyer payment transactions."""
    
    def __init__(self):
        """Initialize tracker with wallet addresses and API key."""
        self.api_key = os.getenv("ETHERSCAN_API_KEY")
        self.buyer_wallet = os.getenv("BUYER_AGENT_WALLET_ADDRESS")
        self.seller_wallet = os.getenv("SELLER_AGENT_WALLET_ADDRESS")
        self.user_wallet = os.getenv("USER_WALLET_ADDRESS")
        self.base_url = "https://api.etherscan.io/v2/api"
        self.chain_id = 8453  # Base mainnet
    
    async def get_latest_tx_to(self, recipient: str, expected_amount_usd: Optional[float] = None) -> Optional[str]:
        """
        Get latest Base transaction to recipient (from any address).
        
        Since Locus MCP uses smart contracts, transactions come from Locus addresses,
        not directly from buyer wallet. We match by recipient and optionally by amount.
        
        Args:
            recipient: Recipient wallet address
            expected_amount_usd: Expected amount in USDC (optional, for matching)
            
        Returns:
            Base transaction hash (0x...) or None
        """
        if not self.api_key or not recipient:
            return None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.base_url,
                params={
                    "chainid": self.chain_id,
                    "module": "account",
                    "action": "txlist",
                    "address": recipient,
                    "startblock": 0,
                    "endblock": 99999999,
                    "sort": "desc",
                    "apikey": self.api_key
                }
            )
            
            data = response.json()
            
            if data.get("status") == "1" and data.get("result"):
                # Get most recent transaction to this address
                # If expected_amount specified, try to match by value
                for tx in data["result"]:
                    if expected_amount_usd:
                        # USDC has 6 decimals, value is in wei
                        # $1 USDC = 1000000 wei (10^6)
                        expected_wei = int(expected_amount_usd * 1_000_000)
                        tx_value = int(tx.get("value", "0"))
                        
                        # Match if within 1% (account for rounding)
                        if abs(tx_value - expected_wei) / expected_wei < 0.01:
                            return tx.get("hash")
                    else:
                        # Just return latest transaction
                        return tx.get("hash")
            
            return None
    
    async def get_latest_payment_txs(self) -> Dict[str, Optional[str]]:
        """
        Get latest buyer payment transactions.
        
        Returns:
            {
              "tx_buyer_to_seller": "0x...",
              "tx_buyer_to_user": "0x..."
            }
        """
        seller_tx = await self.get_latest_tx_to(self.seller_wallet)
        user_tx = await self.get_latest_tx_to(self.user_wallet)
        
        return {
            "tx_buyer_to_seller": seller_tx,
            "tx_buyer_to_user": user_tx
        }

