"""
Circuit Breaker System
Monitors drawdowns and automatically pauses bots/system
"""

import asyncio
from typing import Dict
from datetime import datetime, timezone, timedelta
import logging

from database import bots_collection, alerts_collection, system_modes_collection, rogue_detections_collection
from config import MAX_DRAWDOWN_PERCENT

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self):
        self.max_bot_drawdown = MAX_DRAWDOWN_PERCENT  # 20% default
        self.max_daily_drawdown_per_bot = 0.10  # 10% per day
        self.max_global_drawdown = 0.15  # 15% total system
        
    async def check_bot_drawdown(self, bot: Dict) -> tuple[bool, str]:
        """Check if bot has exceeded drawdown limits"""
        try:
            initial_capital = bot.get('initial_capital', 1000)
            current_capital = bot.get('current_capital', 1000)
            
            # Calculate total drawdown
            total_drawdown_pct = (initial_capital - current_capital) / initial_capital if initial_capital > 0 else 0
            
            if total_drawdown_pct > self.max_bot_drawdown:
                return True, f"Total drawdown {total_drawdown_pct*100:.1f}% exceeds limit {self.max_bot_drawdown*100:.0f}%"
            
            # Calculate daily drawdown (from start of day)
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get capital at start of day (would need tracking)
            # For now, use a simplified check
            daily_profit = bot.get('total_profit', 0)  # Simplified
            
            return False, "OK"
            
        except Exception as e:
            logger.error(f"Drawdown check error: {e}")
            return False, str(e)
    
    async def check_global_drawdown(self, user_id: str) -> tuple[bool, str]:
        """Check if total system drawdown exceeds limit"""
        try:
            bots = await bots_collection.find(
                {"user_id": user_id},
                {"_id": 0}
            ).to_list(1000)
            
            total_initial = sum(b.get('initial_capital', 0) for b in bots)
            total_current = sum(b.get('current_capital', 0) for b in bots)
            
            if total_initial == 0:
                return False, "OK"
            
            global_drawdown_pct = (total_initial - total_current) / total_initial
            
            if global_drawdown_pct > self.max_global_drawdown:
                return True, f"Global drawdown {global_drawdown_pct*100:.1f}% exceeds {self.max_global_drawdown*100:.0f}%"
            
            return False, "OK"
            
        except Exception as e:
            logger.error(f"Global drawdown check error: {e}")
            return False, str(e)
    
    async def trigger_bot_pause(self, bot_id: str, reason: str):
        """Pause a bot due to circuit breaker"""
        try:
            bot = await bots_collection.find_one({"id": bot_id}, {"_id": 0})
            if not bot:
                return
            
            # Pause bot
            await bots_collection.update_one(
                {"id": bot_id},
                {"$set": {
                    "status": "paused",
                    "paused_reason": f"Circuit breaker: {reason}",
                    "paused_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Log to rogue detections
            await rogue_detections_collection.insert_one({
                "user_id": bot['user_id'],
                "bot_id": bot_id,
                "bot_name": bot['name'],
                "type": "circuit_breaker",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_taken": "paused"
            })
            
            # Create alert
            await alerts_collection.insert_one({
                "user_id": bot['user_id'],
                "type": "circuit_breaker",
                "severity": "critical",
                "message": f"🚨 CIRCUIT BREAKER: {bot['name']} paused - {reason}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dismissed": False
            })
            
            logger.warning(f"🚨 Circuit breaker triggered: {bot['name']} - {reason}")
            
        except Exception as e:
            logger.error(f"Trigger pause error: {e}")
    
    async def trigger_emergency_stop(self, user_id: str, reason: str):
        """Trigger system-wide emergency stop"""
        try:
            # Enable emergency stop
            await system_modes_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "emergencyStop": True,
                    "emergency_reason": reason,
                    "emergency_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
            
            # Create critical alert
            await alerts_collection.insert_one({
                "user_id": user_id,
                "type": "emergency_stop",
                "severity": "critical",
                "message": f"🚨 EMERGENCY STOP ACTIVATED: {reason}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dismissed": False
            })
            
            logger.critical(f"🚨 EMERGENCY STOP: {reason}")
            
        except Exception as e:
            logger.error(f"Emergency stop trigger error: {e}")
    
    async def monitor_all_bots(self, user_id: str):
        """Monitor all bots for circuit breaker conditions"""
        try:
            # Check global drawdown first
            global_breach, global_reason = await self.check_global_drawdown(user_id)
            
            if global_breach:
                await self.trigger_emergency_stop(user_id, global_reason)
                return
            
            # Check individual bots
            bots = await bots_collection.find(
                {"user_id": user_id, "status": "active"},
                {"_id": 0}
            ).to_list(1000)
            
            for bot in bots:
                bot_breach, bot_reason = await self.check_bot_drawdown(bot)
                
                if bot_breach:
                    await self.trigger_bot_pause(bot['id'], bot_reason)
            
        except Exception as e:
            logger.error(f"Monitor bots error: {e}")

# Global instance
circuit_breaker = CircuitBreaker()
