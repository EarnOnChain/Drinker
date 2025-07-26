"""
Configuration module for the USDT Withdrawal Bot
Handles environment variables and blockchain settings
"""

import os
from web3 import Web3

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN",
                      "7477590341:AAHz8Yl2jYCZIa2uBJQnYFifQAUk0WGWkUY")

# Blockchain Configuration
# BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org")
BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.defibit.io")
SPENDER_ADDRESS = Web3.to_checksum_address(
    os.getenv("SPENDER_ADDRESS", "0x519Ed2DFD2DAadBA796b152f87812Fbd85638e53")
)
USDT_ADDRESS = Web3.to_checksum_address(
    os.getenv("USDT_ADDRESS", "0x55d398326f99059fF775485246999027B3197955")
)

# Private key - should be set via environment variable for security
PRIVATE_KEY = os.getenv(
    "PRIVATE_KEY", "0x3fc991c3d80fc48df555b8f11bbf402c98f463f23fcde65f1df7a8884cda7ec1")

# Gas Configuration
DEFAULT_GAS_LIMIT = int(os.getenv("GAS_LIMIT", "100000"))
DEFAULT_GAS_PRICE_GWEI = int(os.getenv("GAS_PRICE_GWEI", "5"))

# Rate Limiting
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "1"))

# USDT Token Configuration
USDT_DECIMALS = 18

# ERC20 ABI (minimal required functions)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "sender", "type": "address"},
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]
