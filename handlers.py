"""
Telegram bot handlers for USDT withdrawal functionality
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from blockchain import blockchain_manager
from utils import (
    create_main_menu, create_back_menu, is_rate_limited, validate_usdt_amount,
    log_user_action, create_wallet_info_text, create_error_message,
    create_success_message, create_info_message, create_warning_message,
    truncate_address, format_usdt_amount
)
from config import RATE_LIMIT_SECONDS

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    log_user_action(user.id, user.username, "start")
    
    welcome_text = (
        f"🤖 *Welcome to USDT Withdrawal Bot*\n\n"
        f"Hello {user.first_name}! This bot helps you manage USDT withdrawals "
        f"from approved wallets on Binance Smart Chain.\n\n"
        f"🔐 *Security Features:*\n"
        f"• Only approved wallet addresses\n"
        f"• Allowance-based withdrawals\n"
        f"• Transaction verification\n"
        f"• Rate limiting protection\n\n"
        f"Choose an option from the menu below:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=create_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    # Rate limiting check (reduced from 30 to 5 seconds)
    if is_rate_limited(user.id, RATE_LIMIT_SECONDS):
        await query.edit_message_text(
            create_warning_message(
                f"Please wait {RATE_LIMIT_SECONDS} seconds between actions."
            ),
            reply_markup=create_back_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    log_user_action(user.id, user.username, f"button_press:{data}")
    
    try:
        if data == "enter_wallet":
            await handle_enter_wallet(query, context)
        elif data == "check_wallet":
            await handle_check_wallet(query, context)
        elif data == "withdraw_all":
            await handle_withdraw_all(query, context)
        elif data == "withdraw_custom":
            await handle_withdraw_custom(query, context)
        elif data == "refresh":
            await handle_refresh(query, context)
        elif data == "main_menu":
            await handle_main_menu(query, context)
        else:
            await query.edit_message_text(
                create_error_message("Unknown action"),
                reply_markup=create_main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.edit_message_text(
            create_error_message("An unexpected error occurred. Please try again."),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # Rate limiting check
    if is_rate_limited(user.id, RATE_LIMIT_SECONDS):
        await update.message.reply_text(
            create_warning_message(
                f"Please wait {RATE_LIMIT_SECONDS} seconds between actions."
            ),
            reply_markup=create_back_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        if context.user_data.get("awaiting_wallet"):
            await handle_wallet_input(update, context, text)
        elif context.user_data.get("awaiting_amount"):
            await handle_amount_input(update, context, text)
        else:
            # Unknown text input
            await update.message.reply_text(
                create_info_message(
                    "Please use the menu buttons to interact with the bot."
                ),
                reply_markup=create_main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Error in text handler: {e}")
        await update.message.reply_text(
            create_error_message("An unexpected error occurred. Please try again."),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_enter_wallet(query, context):
    """Handle wallet address entry"""
    await query.edit_message_text(
        create_info_message(
            "Please send the approved wallet address:\n\n"
            "📋 *Format:* 0x followed by 40 hexadecimal characters\n"
            "🔍 *Example:* 0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8"
        ),
        reply_markup=create_back_menu(),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data["awaiting_wallet"] = True

async def handle_check_wallet(query, context):
    """Handle wallet information check"""
    wallet = context.user_data.get("wallet")
    if not wallet:
        await query.edit_message_text(
            create_warning_message(
                "No wallet address set. Please enter an approved wallet first."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await query.edit_message_text(
        create_info_message("Checking wallet information..."),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Get wallet information
    balance = blockchain_manager.get_usdt_balance(wallet)
    allowance = blockchain_manager.get_allowance(wallet)
    
    if balance is None or allowance is None:
        await query.edit_message_text(
            create_error_message(
                "Failed to retrieve wallet information. Please check your connection and try again."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    wallet_info = create_wallet_info_text(wallet, balance, allowance)
    await query.edit_message_text(
        wallet_info,
        reply_markup=create_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_withdraw_all(query, context):
    """Handle full withdrawal"""
    wallet = context.user_data.get("wallet")
    if not wallet:
        await query.edit_message_text(
            create_warning_message(
                "No wallet address set. Please enter an approved wallet first."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await query.edit_message_text(
        create_info_message("Processing full withdrawal..."),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Get allowance amount
    allowance = blockchain_manager.get_allowance(wallet)
    if allowance is None:
        await query.edit_message_text(
            create_error_message("Failed to check allowance. Please try again."),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if allowance <= 0:
        await query.edit_message_text(
            create_warning_message(
                f"No allowance available for withdrawal.\n\n"
                f"Current allowance: {format_usdt_amount(allowance)}"
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Perform withdrawal
    success, message = blockchain_manager.withdraw_usdt(wallet, allowance)
    
    if success:
        log_user_action(query.from_user.id, query.from_user.username, 
                       f"withdraw_all:{allowance}", wallet)
        await query.edit_message_text(
            create_success_message(message),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            create_error_message(message),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_withdraw_custom(query, context):
    """Handle custom amount withdrawal"""
    wallet = context.user_data.get("wallet")
    if not wallet:
        await query.edit_message_text(
            create_warning_message(
                "No wallet address set. Please enter an approved wallet first."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await query.edit_message_text(
        create_info_message(
            "Please send the amount of USDT to withdraw:\n\n"
            "💰 *Format:* Decimal number (e.g., 100.50)\n"
            "📊 *Range:* 0.000001 - 1,000,000 USDT\n"
            "🎯 *Precision:* Up to 6 decimal places"
        ),
        reply_markup=create_back_menu(),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data["awaiting_amount"] = True

async def handle_refresh(query, context):
    """Handle refresh action"""
    wallet = context.user_data.get("wallet")
    if not wallet:
        await query.edit_message_text(
            create_info_message(
                "🤖 *USDT Withdrawal Bot*\n\n"
                "No wallet configured. Please enter an approved wallet to continue."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await handle_check_wallet(query, context)

async def handle_main_menu(query, context):
    """Handle return to main menu"""
    # Clear any awaiting states
    context.user_data.pop("awaiting_wallet", None)
    context.user_data.pop("awaiting_amount", None)
    
    wallet = context.user_data.get("wallet")
    if wallet:
        wallet_display = truncate_address(wallet)
        menu_text = (
            f"🤖 *USDT Withdrawal Bot*\n\n"
            f"🏦 Current wallet: `{wallet_display}`\n\n"
            f"Choose an action from the menu below:"
        )
    else:
        menu_text = (
            f"🤖 *USDT Withdrawal Bot*\n\n"
            f"Please select an option from the menu below:"
        )
    
    await query.edit_message_text(
        menu_text,
        reply_markup=create_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_wallet_input(update, context, wallet_address):
    """Handle wallet address input validation"""
    context.user_data["awaiting_wallet"] = False
    
    if not blockchain_manager.validate_address(wallet_address):
        await update.message.reply_text(
            create_error_message(
                "Invalid wallet address format.\n\n"
                "Please provide a valid Ethereum address starting with '0x' "
                "followed by 40 hexadecimal characters."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Store wallet address
    wallet = blockchain_manager.w3.to_checksum_address(wallet_address)
    context.user_data["wallet"] = wallet
    
    log_user_action(update.effective_user.id, update.effective_user.username,
                   "wallet_set", wallet)
    
    # Get and display wallet information
    balance = blockchain_manager.get_usdt_balance(wallet)
    allowance = blockchain_manager.get_allowance(wallet)
    
    if balance is None or allowance is None:
        await update.message.reply_text(
            create_warning_message(
                f"Wallet address saved: `{truncate_address(wallet)}`\n\n"
                f"⚠️ Could not retrieve wallet information. "
                f"Please check your connection and try again."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    success_text = (
        f"✅ *Wallet Successfully Added*\n\n"
        f"📍 Address: `{truncate_address(wallet)}`\n"
        f"💰 Balance: {format_usdt_amount(balance)}\n"
        f"🔐 Allowance: {format_usdt_amount(allowance)}\n\n"
        f"You can now perform withdrawals using the menu below:"
    )
    
    await update.message.reply_text(
        success_text,
        reply_markup=create_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_amount_input(update, context, amount_text):
    """Handle withdrawal amount input validation"""
    context.user_data["awaiting_amount"] = False
    
    # Validate amount
    is_valid, amount, error_msg = validate_usdt_amount(amount_text)
    if not is_valid:
        await update.message.reply_text(
            create_error_message(error_msg),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    wallet = context.user_data.get("wallet")
    if not wallet:
        await update.message.reply_text(
            create_error_message(
                "No wallet address set. Please enter an approved wallet first."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await update.message.reply_text(
        create_info_message(f"Processing withdrawal of {format_usdt_amount(amount)}..."),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Perform withdrawal
    success, message = blockchain_manager.withdraw_usdt(wallet, amount)
    
    if success:
        log_user_action(update.effective_user.id, update.effective_user.username,
                       f"withdraw_custom:{amount}", wallet)
        await update.message.reply_text(
            create_success_message(message),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            create_error_message(message),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
