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

# Optional Web API import
try:
    from web_api import start_web_api, get_connection_info
    WEB_API_AVAILABLE = True
except ImportError:
    WEB_API_AVAILABLE = False
    logger.warning("Web API not available. Install fastapi and uvicorn for web integration features.")

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
        
        # Create application with proper error handling
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Add error handler
        async def error_handler(update, context):
            logger.error(f"Exception while handling an update: {context.error}")
        
        app.add_error_handler(error_handler)
        
        # Add handlers
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        logger.info("Starting USDT Withdrawal Bot...")
        
        # Start web API server if available
        if WEB_API_AVAILABLE:
            if start_web_api():
                connection_info = get_connection_info()
                logger.info(f"Web API server running on {connection_info['base_url']}")
            else:
                logger.warning("Failed to start web API server")
        
        # Run the bot with proper settings
        app.run_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True  # Drop pending updates on startup
        )
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
