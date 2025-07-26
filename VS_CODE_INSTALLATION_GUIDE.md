# VS Code Installation Guide - USDT Withdrawal Bot

## Complete Setup Guide for VS Code Development

### Prerequisites
- Windows, macOS, or Linux computer
- Internet connection
- VS Code installed

### Step 1: Install Required Software

#### 1.1 Install Python 3.11+
**Windows:**
- Download Python from https://python.org/downloads/
- Run installer, check "Add Python to PATH"
- Verify: Open Command Prompt, type `python --version`

**macOS:**
- Install Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- Install Python: `brew install python@3.11`
- Verify: `python3 --version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

#### 1.2 Install VS Code Extensions
Open VS Code and install these extensions:
- **Python** (Microsoft)
- **Python Debugger** (Microsoft)
- **Pylance** (Microsoft)
- **GitLens** (optional, for version control)

### Step 2: Set Up the Project

#### 2.1 Create Project Directory
```bash
mkdir usdt-bot
cd usdt-bot
```

#### 2.2 Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2.3 Install Required Packages
```bash
pip install python-telegram-bot==22.3
pip install web3==7.12.1
pip install fastapi==0.116.1
pip install uvicorn==0.32.1
pip install python-dotenv==1.0.0
```

### Step 3: Project Files Setup

#### 3.1 Copy All Bot Files
Copy these files to your project directory:
- `main.py`
- `config.py`
- `blockchain.py`
- `handlers.py`
- `utils.py`
- `auto_mode.py`
- `web_api.py`

#### 3.2 Create Environment File
Create `.env` file in project root:
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
AUTO_GAS_ENABLED=true
AUTO_GAS_PRIVATE_KEY=your_auto_gas_private_key_here
AUTO_GAS_USDT_THRESHOLD=0.5
AUTO_GAS_BNB_THRESHOLD=0.00000720
AUTO_GAS_BNB_AMOUNT=0.00001
AUTO_GAS_CHECK_INTERVAL=60

# Web API Configuration
API_HOST=0.0.0.0
API_PORT=5000
```

### Step 4: Configure VS Code

#### 4.1 Open Project in VS Code
```bash
code .
```

#### 4.2 Select Python Interpreter
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
2. Type "Python: Select Interpreter"
3. Choose the virtual environment interpreter (`./venv/bin/python`)

#### 4.3 Create launch.json for Debugging
Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Bot Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

### Step 5: Required API Keys and Tokens

#### 5.1 Get Telegram Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions to create bot
4. Copy the token to `.env` file

#### 5.2 Set Up Wallet Keys
- `PRIVATE_KEY`: Your main wallet private key (without 0x)
- `SPENDER_ADDRESS`: Your wallet address (with 0x)
- `AUTO_GAS_PRIVATE_KEY`: Private key for auto gas wallet (can be same as main)

### Step 6: Running the Bot

#### 6.1 Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### 6.2 Run the Bot
```bash
python main.py
```

#### 6.3 Debug Mode in VS Code
- Press `F5` to start debugging
- Set breakpoints by clicking left of line numbers
- Use Debug Console to inspect variables

### Step 7: Testing Features

#### 7.1 Test Telegram Bot
1. Start the bot with `/start`
2. Test wallet detection in groups
3. Enable Auto Mode and Auto Gas buttons

#### 7.2 Test Web API
Bot automatically starts web server on port 5000:
- Status endpoint: `http://localhost:5000/api/status`
- Submit wallet: `http://localhost:5000/api/submit-wallet` (POST)

#### 7.3 API Testing Examples
**Check Bot Status:**
```bash
curl http://localhost:5000/api/status
```

**Submit Wallet Address:**
```bash
curl -X POST http://localhost:5000/api/submit-wallet \
  -H "Content-Type: application/json" \
  -d '{"address": "0x738Ce804dF6B2815BC7f743996Ec725a6F037Ccb", "source": "website"}'
```

### Step 8: Common Issues & Solutions

#### 8.1 Module Import Errors
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 8.2 Web3 Connection Issues
- Check BSC_RPC URL is accessible
- Verify internet connection
- Try alternative RPC: `https://bsc-dataseed1.binance.org`

#### 8.3 Bot Token Issues
- Verify token is correct
- Check bot permissions
- Ensure bot is added to test groups

### Step 9: Project Structure
```
usdt-bot/
├── .env                    # Environment variables
├── .vscode/
│   └── launch.json        # VS Code debug configuration
├── main.py                # Bot entry point
├── config.py              # Configuration settings
├── blockchain.py          # Web3 blockchain interactions
├── handlers.py            # Telegram bot handlers
├── utils.py               # Utility functions
├── auto_mode.py           # Auto withdrawal and gas features
├── web_api.py             # FastAPI web server
├── requirements.txt       # Python dependencies
└── venv/                  # Virtual environment
```

### Step 10: Advanced Features

#### 10.1 Auto Gas Configuration
- Automatically sends BNB to wallets with USDT ≥ $0.5 and BNB < 0.00000720
- Works on ALL wallets, not just approved ones
- Configurable thresholds in `.env` file

#### 10.2 Web API Integration
- `/api/submit-wallet`: Submit wallet addresses from your website
- `/api/status`: Get bot status and configuration
- `/api/logs/wallets`: View processed wallet logs

#### 10.3 Debugging Tips
- Use VS Code debugger to step through code
- Check bot logs in integrated terminal
- Monitor blockchain transactions on BSCScan
- Test with small amounts first

### Security Notes
- Never commit `.env` file to version control
- Use separate wallets for testing
- Keep private keys secure
- Monitor auto gas wallet balance
- Set reasonable rate limits

### Support
- Check console logs for error messages
- Verify all environment variables are set
- Test blockchain connection separately
- Use debugger to trace execution flow

## Quick Start Checklist
- [ ] Python 3.11+ installed
- [ ] VS Code with Python extensions
- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Project files copied
- [ ] `.env` file configured with all keys
- [ ] Bot token obtained from @BotFather
- [ ] Wallet private keys added
- [ ] VS Code interpreter selected
- [ ] Bot running successfully
- [ ] Web API accessible on port 5000
- [ ] Auto features tested and working

Your USDT withdrawal bot should now be fully operational in VS Code!