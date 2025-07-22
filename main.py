#!/usr/bin/env python3
"""
USDT Withdrawal Telegram Bot
Main entry point for the bot application
"""

import logging
import os
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from handlers import start_handler, button_handler, handle_text
from config import BOT_TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot"""
    try:
        # Validate bot token
        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("Bot token not configured. Please set TELEGRAM_BOT_TOKEN environment variable.")
        
        # Create application
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        logger.info("Starting USDT Withdrawal Bot...")
        
        # Run the bot
        app.run_polling(allowed_updates=['message', 'callback_query'])
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
