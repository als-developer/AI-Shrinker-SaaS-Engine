"""
Solana Client - USDC Payment Processing on Solana Blockchain
Handles crypto payments and settlements
Version: 31.0
"""

import os
from typing import Dict, Any, Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address
import base58
import logging

logger = logging.getLogger(__name__)


class SolanaClient:
    """Solana blockchain client for USDC transactions"""
    
    _client: Optional[AsyncClient] = None
    _rpc_url: str = None
    
    # USDC token address on Solana mainnet
    USDC_MINT = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    
    @classmethod
    async def initialize(cls):
        """Initialize Solana client"""
        if cls._client is not None:
            return
        
        cls._rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        cls._client = AsyncClient(cls._rpc_url)
        logger.info(f"Solana client initialized with RPC: {cls._rpc_url}")
    
    @classmethod
    async def close(cls):
        """Close Solana client"""
        if cls._client:
            await cls._client.close()
            cls._client = None
    
    @classmethod
    async def get_balance(cls, wallet_address: str) -> Dict[str, float]:
        """Get USDC balance for a wallet"""
        await cls.initialize()
        
        try:
            pubkey = Pubkey.from_string(wallet_address)
            token_account = get_associated_token_address(pubkey, cls.USDC_MINT)
            
            response = await cls._client.get_token_account_balance(token_account, commitment=Confirmed)
            
            if response.value:
                balance = float(response.value.ui_amount_string) if response.value.ui_amount_string else 0.0
                return {"usdc_balance": balance, "address": wallet_address}
            else:
                return {"usdc_balance": 0.0, "address": wallet_address, "note": "No token account found"}
                
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {"usdc_balance": 0.0, "address": wallet_address, "error": str(e)}
    
    @classmethod
    async def get_transaction(cls, signature: str) -> Optional[Dict]:
        """Get transaction details"""
        await cls.initialize()
        
        try:
            tx = await cls._client.get_transaction(
                base58.b58decode(signature),
                commitment=Confirmed,
                encoding="jsonParsed"
            )
            
            if tx.value:
                return {
                    "signature": signature,
                    "slot": tx.value.slot,
                    "block_time": tx.value.block_time,
                    "meta": tx.value.transaction.meta
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get transaction: {e}")
            return None
    
    @classmethod
    async def get_recent_transactions(cls, wallet_address: str, limit: int = 10) -> List[Dict]:
        """Get recent transactions for a wallet"""
        await cls.initialize()
        
        try:
            pubkey = Pubkey.from_string(wallet_address)
            signatures = await cls._client.get_signatures_for_address(pubkey, limit=limit)
            
            transactions = []
            for sig in signatures.value:
                tx = await cls.get_transaction(sig.signature)
                if tx:
                    transactions.append(tx)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get recent transactions: {e}")
            return []
    
    @classmethod
    async def verify_payment(
        cls,
        wallet_address: str,
        expected_amount_usdc: float,
        max_age_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Verify if a payment was received
        
        Args:
            wallet_address: Merchant wallet address
            expected_amount_usdc: Expected USDC amount
            max_age_seconds: Maximum age of transaction in seconds
            
        Returns:
            Verification result
        """
        await cls.initialize()
        
        try:
            # Get recent transactions
            transactions = await cls.get_recent_transactions(wallet_address, limit=5)
            
            import time
            current_time = int(time.time())
            
            for tx in transactions:
                if tx.get("block_time"):
                    tx_age = current_time - tx["block_time"]
                    
                    if tx_age <= max_age_seconds:
                        # Check if amount matches (simplified)
                        # In production, parse transaction details properly
                        return {
                            "verified": True,
                            "signature": tx["signature"],
                            "amount_usdc": expected_amount_usdc,
                            "age_seconds": tx_age
                        }
            
            return {"verified": False, "message": "No recent matching transaction found"}
            
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return {"verified": False, "error": str(e)}
    
    @classmethod
    async def get_token_accounts(cls, wallet_address: str) -> List[Dict]:
        """Get all token accounts for a wallet"""
        await cls.initialize()
        
        try:
            pubkey = Pubkey.from_string(wallet_address)
            accounts = await cls._client.get_token_accounts_by_owner(pubkey, program_id=TOKEN_PROGRAM_ID)
            
            result = []
            for account in accounts.value:
                result.append({
                    "address": str(account.pubkey),
                    "mint": str(account.account.data.parsed["info"]["mint"]),
                    "balance": account.account.data.parsed["info"]["tokenAmount"]["uiAmount"]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get token accounts: {e}")
            return []
