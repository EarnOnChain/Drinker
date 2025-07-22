"""
Utility functions for the USDT Withdrawal Bot
"""

import time
import logging
from typing import Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# Rate limiting storage
user_last_action: Dict[int, float] = {}

def create_main_menu() -> InlineKeyboardMarkup:
    """Create the main menu keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Enter Approved Wallet", callback_data="enter_wallet")],
        [InlineKeyboardButton("💰 Check Wallet Info", callback_data="check_wallet")],
        [InlineKeyboardButton("💸 Withdraw All USDT", callback_data="withdraw_all")],
        [InlineKeyboardButton("✏️ Withdraw Custom Amount", callback_data="withdraw_custom")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh")]
    ])

def create_back_menu() -> InlineKeyboardMarkup:
    """Create a simple back to main menu keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ])

def is_rate_limited(user_id: int, limit_seconds: int = 5) -> bool:
    """Check if user is rate limited"""
    current_time = time.time()
    last_action = user_last_action.get(user_id, 0)
    
    if current_time - last_action < limit_seconds:
        return True
    
    user_last_action[user_id] = current_time
    return False

def validate_usdt_amount(amount_str: str) -> tuple[bool, float, str]:
    """
    Validate USDT amount input
    
    Returns:
        (is_valid, amount, error_message)
    """
    try:
        amount = float(amount_str.strip())
        
        if amount <= 0:
            return False, 0, "Amount must be greater than 0"
        
        if amount > 1000000:  # 1M USDT limit
            return False, 0, "Amount too large (max: 1,000,000 USDT)"
        
        # Check for reasonable decimal places (max 6)
        decimal_places = len(amount_str.split('.')[-1]) if '.' in amount_str else 0
        if decimal_places > 6:
            return False, 0, "Too many decimal places (max: 6)"
        
        return True, amount, ""
        
    except ValueError:
        return False, 0, "Invalid number format"

def format_usdt_amount(amount: float) -> str:
    """Format USDT amount for display"""
    if amount == 0:
        return "0 USDT"
    elif amount < 0.000001:
        return f"{amount:.8f} USDT"
    elif amount < 0.01:
        return f"{amount:.6f} USDT"
    else:
        return f"{amount:,.2f} USDT"

def truncate_address(address: str, chars: int = 8) -> str:
    """Truncate ethereum address for display"""
    if len(address) <= chars * 2:
        return address
    return f"{address[:chars]}...{address[-chars:]}"

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def log_user_action(user_id: int, username: str, action: str, details: str = ""):
    """Log user actions for monitoring"""
    logger.info(f"User {user_id} (@{username or 'N/A'}) performed action: {action} {details}")

def create_wallet_info_text(address: str, balance: float, allowance: float) -> str:
    """Create formatted wallet information text"""
    truncated_addr = truncate_address(address)
    balance_str = format_usdt_amount(balance)
    allowance_str = format_usdt_amount(allowance)
    
    return (
        f"🏦 *Wallet Information*\n\n"
        f"📍 Address: `{truncated_addr}`\n"
        f"💰 Balance: {balance_str}\n"
        f"🔐 Allowance: {allowance_str}\n\n"
        f"Choose an action below:"
    )

def create_error_message(error: str) -> str:
    """Create formatted error message"""
    return f"❌ *Error*\n\n{error}"

def create_success_message(message: str) -> str:
    """Create formatted success message"""
    return f"✅ *Success*\n\n{message}"

def create_info_message(message: str) -> str:
    """Create formatted info message"""
    return f"ℹ️ *Information*\n\n{message}"

def create_warning_message(message: str) -> str:
    """Create formatted warning message"""
    return f"⚠️ *Warning*\n\n{message}"
