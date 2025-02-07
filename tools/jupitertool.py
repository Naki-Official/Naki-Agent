import json
import httpx
import base64
import base58
from typing import Optional
try:
    from jupiter_python_sdk.jupiter import Jupiter
except ImportError:
    raise ImportError("`JupiterSDK` not installed. Please install using `pip install jupiter-python-sdk`.")
from solders import message
from solana.rpc.commitment import Processed
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from spl.token.instructions import get_associated_token_address

class JupiterTools():
    """
    Toolkit for interacting with Solana blockchain using Jupiter.
    """
    DEFAULT_ENDPOINTS = {
        "QUOTE": "https://quote-api.jup.ag/v6/quote?",
        "SWAP": "https://quote-api.jup.ag/v6/swap",
        "OPEN_ORDER": "https://api.jup.ag/limit/v2/createOrder",
        "CANCEL_ORDERS": "https://api.jup.ag/limit/v2/cancelOrders",
        "QUERY_OPEN_ORDERS": "https://api.jup.ag/limit/v2/openOrders?wallet=",
        "QUERY_ORDER_HISTORY": "https://api.jup.ag/limit/v2/orderHistory",
        "QUERY_TRADE_HISTORY": "https://api.jup.ag/limit/v2/tradeHistory"
    }
    def __init__(
        self,
        private_key: str = None,
        rpc_url: Optional[str] = "https://api.mainnet-beta.solana.com",
        custom_endpoints: Optional[dict] = None,
    ):
        """
        Initialize the SolanaTools with JupiterSDK.
        """
        self.ENDPOINT_APIS_URL = self.DEFAULT_ENDPOINTS.copy()
        if custom_endpoints:
            self.ENDPOINT_APIS_URL.update(custom_endpoints)
        self.wallet = Keypair.from_bytes(base58.b58decode(private_key))
        self.client = AsyncClient(rpc_url)
        # Initialize the Jupiter SDK
        self.jupiter = Jupiter(
            self.client,
            self.wallet,
            quote_api_url=self.ENDPOINT_APIS_URL["QUOTE"],
            swap_api_url=self.ENDPOINT_APIS_URL["SWAP"],
            open_order_api_url=self.ENDPOINT_APIS_URL["OPEN_ORDER"],
            cancel_orders_api_url=self.ENDPOINT_APIS_URL["CANCEL_ORDERS"],
            query_open_orders_api_url=self.ENDPOINT_APIS_URL["QUERY_OPEN_ORDERS"],
            query_order_history_api_url=self.ENDPOINT_APIS_URL["QUERY_ORDER_HISTORY"],
            query_trade_history_api_url=self.ENDPOINT_APIS_URL["QUERY_TRADE_HISTORY"],
        )

    async def check_balance(self, token_mint: Optional[str] = None) -> dict:
        """
        Retrieves the balance of the wallet for a given token mint.
        Args:
            token_mint (str, optional): The mint address of the token to retrieve the balance for.
        Returns:
            dict: A dictionary containing the token mint address and its balance.
        """
        wallet_address = self.wallet.pubkey()
        if token_mint is None:
            balance_response = await self.client.get_balance(wallet_address)
            balance = balance_response.value / (10**9)
            return {"token": "SOL", "balance": balance}
        ata_address = get_associated_token_address(wallet_address, Pubkey.from_string(token_mint))
        response = await self.client.get_token_account_balance(ata_address)
        accounts = response.value
        if not accounts:
            return {"token": token_mint, "balance": 0}
        token_amount = response.value.ui_amount
        return {"token": token_mint, "balance": token_amount}
    
    async def get_quote(self, input_mint: str, output_mint: str, amount: float, slippage_bps: int = 1) -> dict:
        """
        Retrieves a quote for a given token swap.
        Args:
            input_mint (str): The mint address of the input token.
            output_mint (str): The mint address of the output token.
            amount (float): The amount of input token to send.
            slippage_bps (int, optional): The slippage % in BPS. Defaults to 1.
        Returns:
            dict: The quote for the given token swap.
        """
        swap_result = await self.jupiter.swap(
            user=self.wallet,
            input_mint=Pubkey.from_string(input_mint),
            output_mint=Pubkey.from_string(output_mint),
            amount=int(amount * (10**9)),  # Convert to lamports
            slippage_bps=slippage_bps
        )
        return swap_result
    
    async def swap_token(self, input_mint: str, output_mint: str, amount: float, slippage_bps: int = 1) -> str:
        """
        Swaps the given amount of input token to output token using Jupiter's router.
        Args:
            input_mint (str): The mint address of the input token.
            output_mint (str): The mint address of the output token.
            amount (float): The amount of input token to swap in SOL.
            slippage_bps (int, optional): The maximum slippage in basis points (bps). Defaults to 1.
        Returns:
            str: The transaction data of the swap transaction.
        """
        amount_in_lamports = int(amount * (10**9))
        
        transaction_data = await self.jupiter.swap(
            input_mint=input_mint,
            output_mint=output_mint,
            amount=amount_in_lamports,
            slippage_bps=slippage_bps,
        )
        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
        signature = self.wallet.sign_message(message.to_bytes_versioned(raw_transaction.message))
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
        # Send the transaction
        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        result = await self.client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
        
        return json.loads(result.to_json())['result']
    
    async def get_open_orders(self, wallet_address: Optional[str] = None, input_mint: Optional[str] = None, output_mint: Optional[str] = None) -> list:
        """
        Retrieves a list of open orders on Jupiter.
        Args:
            wallet_address (Optional[str], optional): The wallet address to retrieve open orders for. Defaults to None.
            input_mint (Optional[str], optional): The mint address of the input token. Defaults to None.
            output_mint (Optional[str], optional): The mint address of the output token. Defaults to None.
        Returns:
            list: A list of open orders.
        """
        wallet_address = wallet_address if wallet_address else str(self.wallet.pubkey())
        list_open_orders = await self.jupiter.query_open_orders(
            wallet_address=wallet_address,
            input_mint=input_mint,
            output_mint=output_mint
        )
        return list_open_orders
    
    async def open_limit_order(
        self,
        input_mint: str,
        output_mint: str,
        in_amount: float,
        out_amount: float,
        expired_at: Optional[int] = None
    ) -> str:
        """
        Places a limit order on Jupiter.
        Args:
            input_mint (str): The mint address of the input token.
            output_mint (str): The mint address of the output token.
            in_amount (float): The amount of input token to send.
            out_amount (float): The amount of output token to receive.
            expired_at (Optional[int], optional): The timestamp of when the order should expire. Defaults to None.
        Returns:
            str: The transaction ID of the limit order.
        """
        keypair = self.wallet 
        
        # Request transaction data from Jupiter
        transaction_parameters = {
            "inputMint": str(Pubkey.from_string(input_mint)),
            "outputMint": str(Pubkey.from_string(output_mint)),
            "maker": keypair.pubkey().__str__(),
            "payer": keypair.pubkey().__str__(),
            "params": {
                "makingAmount": str(in_amount),  # Amount of input token
                "takingAmount": str(out_amount)  # Expected amount of output token
            },
            "computeUnitPrice": "auto"
        }
        if expired_at:
            transaction_parameters["params"]["expiredAt"] = expired_at
            
        response = httpx.post(
            url=self.ENDPOINT_APIS_URL['OPEN_ORDER'],
            json=transaction_parameters,
            headers={"Content-Type": "application/json"}
        )
        print(response.text)
        transaction_data = response.json()["tx"]
                
        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
        signature = self.wallet.sign_message(message.to_bytes_versioned(raw_transaction.message))
        
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
        # Send the transaction
        opts = TxOpts(skip_preflight=True, max_retries=2)
        result = await self.client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
        return result.value
    
    async def cancel_order(self, orders: list) -> str:
        """
        Cancel open orders on Jupiter.
        
        Args:
            orders (list): A list of order public keys to cancel.
        
        Returns:
            str: The transaction data of the cancel orders transaction.
        """
        keypair = self.wallet
        transaction_parameters = {
            "maker": keypair.pubkey().__str__(),
            "computeUnitPrice": "auto",
            "orders": orders
        }
        
        response = httpx.post(
            url=self.ENDPOINT_APIS_URL['CANCEL_ORDERS'],
            json=transaction_parameters,
            headers={"Content-Type": "application/json"}
        )
        return response.json()['tx']