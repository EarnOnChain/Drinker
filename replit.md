# USDT Withdrawal Bot

## Overview

A Telegram bot for managing USDT withdrawals from approved wallet addresses on the Binance Smart Chain (BSC). The bot provides a secure interface for checking wallet information, setting approved addresses, and executing USDT transfers using allowance-based withdrawals.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Telegram Bot Interface**: Uses python-telegram-bot library for user interactions
- **Inline Keyboard Navigation**: Menu-driven interface with callback query handlers
- **Real-time Updates**: Immediate feedback on transactions and wallet status

### Backend Architecture
- **Modular Python Application**: Organized into separate modules for blockchain, handlers, utilities, and configuration
- **Asynchronous Operations**: Uses asyncio for handling Telegram bot operations
- **Web3 Integration**: Direct interaction with BSC network via Web3.py

### Blockchain Integration
- **BSC Network**: Connects to Binance Smart Chain via RPC endpoint
- **ERC20 Token Support**: Specifically designed for USDT token operations
- **Smart Contract Interaction**: Uses Web3.py to interact with USDT contract functions

## Key Components

### 1. Blockchain Manager (`blockchain.py`)
- **Purpose**: Handles all Web3 connections and smart contract interactions
- **Key Features**:
  - BSC network connection validation
  - USDT contract initialization
  - Address validation utilities
  - Transaction execution capabilities

### 2. Configuration Module (`config.py`)
- **Purpose**: Centralized configuration management
- **Key Settings**:
  - Bot token and blockchain RPC endpoints
  - Contract addresses (USDT and spender)
  - Gas configuration and rate limiting
  - ERC20 ABI definitions

### 3. Handler System (`handlers.py`)
- **Purpose**: Processes Telegram bot commands and user interactions
- **Key Handlers**:
  - Start command handler
  - Inline keyboard button handlers
  - User state management

### 4. Utility Functions (`utils.py`)
- **Purpose**: Common functionality and UI components
- **Key Features**:
  - Rate limiting implementation
  - Input validation for USDT amounts
  - Keyboard markup generation
  - User action logging

### 5. Main Application (`main.py`)
- **Purpose**: Application entry point and bot initialization
- **Responsibilities**:
  - Bot token validation
  - Handler registration
  - Application lifecycle management

## Data Flow

### 1. User Interaction Flow
```
User Command → Telegram API → Bot Handler → Blockchain Operation → Response to User
```

### 2. Wallet Approval Process
```
User Input → Address Validation → Allowance Check → Wallet Registration → Confirmation
```

### 3. Withdrawal Process
```
User Request → Rate Limit Check → Balance Verification → Transaction Execution → Status Update
```

## External Dependencies

### Core Dependencies
- **python-telegram-bot**: Telegram bot API wrapper
- **web3.py**: Ethereum/BSC blockchain interaction
- **logging**: Built-in Python logging for monitoring

### Blockchain Dependencies
- **BSC Network**: Binance Smart Chain RPC endpoint
- **USDT Contract**: ERC20 token contract on BSC
- **Private Key Management**: For transaction signing

### Third-party Services
- **Telegram Bot API**: Message handling and user interface
- **BSC RPC Provider**: Blockchain data and transaction broadcasting

## Security Architecture

### Authentication & Authorization
- **Allowance-based Withdrawals**: Users must pre-approve the bot's spending capability
- **Private Key Security**: Environment variable configuration recommended
- **Rate Limiting**: Built-in protection against spam and abuse

### Transaction Security
- **Address Validation**: All wallet addresses are validated before operations
- **Balance Verification**: Checks available allowance before withdrawal attempts
- **Transaction Confirmation**: Users receive feedback on transaction status

## Deployment Strategy

### Environment Configuration
- **Environment Variables**: Secure configuration via environment variables
- **Logging**: File and console logging for monitoring and debugging
- **Error Handling**: Comprehensive error handling with user-friendly messages

### Scalability Considerations
- **Stateless Design**: Minimal state storage for easy horizontal scaling
- **Rate Limiting**: Per-user rate limiting to manage load
- **Connection Pooling**: Single Web3 connection instance for efficiency

### Monitoring & Maintenance
- **Structured Logging**: Detailed logging for troubleshooting
- **User Action Tracking**: Audit trail for all user interactions
- **Transaction History**: Blockchain transaction tracking via Web3

## Recent Changes

### July 26, 2025 - Project Migration to Replit Completed
✓ Successfully migrated project from Replit Agent to Replit environment
✓ Verified package installations (python-telegram-bot==20.3, web3>=7.12.1)
✓ Confirmed bot startup and Telegram API connectivity
✓ Validated all core components are functional
✓ Applied security best practices with environment variable configuration
✓ Maintained client/server separation architecture

### July 22, 2025 - Complete Bot Functionality Restored
✓ Fixed python-telegram-bot library compatibility issues by using version 20.3
✓ Resolved Web3 transaction signing error ('rawTransaction' → 'raw_transaction')
✓ Optimized rate limiting from 30 seconds to 1 second for instant responses
✓ Fixed "withdraw all" functionality by implementing proper balance/allowance logic
✓ Resolved bot polling conflicts with proper parameter configuration
✓ All withdrawal operations (custom amounts and full withdrawals) now working perfectly

### Current Status
- **Bot Status**: Fully operational and connected to Telegram API
- **Blockchain Status**: Connected to BSC network with successful transaction processing
- **Account Address**: 0x519Ed2DFD2DAadBA796b152f87812Fbd85638e53
- **Withdrawal Functions**: Both custom and "withdraw all" features working correctly
- **Response Time**: Instant (1-second rate limiting only)
- **User Feedback**: Confirmed working perfectly by user

## Development Notes

### Code Organization
- **Separation of Concerns**: Clear module boundaries for different functionalities
- **Error Handling**: Comprehensive exception handling throughout the application
- **Configuration Management**: Centralized configuration with environment variable support

### Future Enhancements
- **Auto Mode**: Mentioned in attached assets for automatic withdrawals
- **Enhanced Security**: Additional validation and security measures
- **Database Integration**: Potential for persistent storage of user preferences and history