"""
Capital Tracking API Endpoints
Provides accurate profit reporting that separates trading gains from capital injections
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import logging

from auth import get_current_user
from engines.capital_injection_tracker import capital_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/capital", tags=["Capital Tracking"])

@router.get("/bot/{bot_id}/real-profit")
async def get_bot_real_profit(bot_id: str, current_user: Dict = Depends(get_current_user)):
    """Get accurate trading profit for a bot (excludes capital injections)"""
    try:
        result = await capital_tracker.calculate_real_profit(bot_id)
        
        if result.get('error'):
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get bot real profit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/real-profit")
async def get_user_real_profit(current_user: Dict = Depends(get_current_user)):
    """Get accurate total trading profit for user (excludes capital injections)"""
    try:
        result = await capital_tracker.calculate_user_real_profit(current_user['id'])
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
    except Exception as e:
        logger.error(f"Get user real profit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bot/{bot_id}/injections")
async def get_bot_injections(bot_id: str, current_user: Dict = Depends(get_current_user)):
    """Get capital injection history for a bot"""
    try:
        total = await capital_tracker.get_bot_injections(bot_id)
        history = await capital_tracker.get_injection_history(bot_id=bot_id)
        
        return {
            "bot_id": bot_id,
            "total_injections": total,
            "injection_count": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Get bot injections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/injections")
async def get_user_injections(current_user: Dict = Depends(get_current_user)):
    """Get capital injection history for all user's bots"""
    try:
        history = await capital_tracker.get_injection_history(user_id=current_user['id'])
        
        return {
            "user_id": current_user['id'],
            "injection_count": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Get user injections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
async def initialize_capital_tracking(current_user: Dict = Depends(get_current_user)):
    """Initialize capital tracking for existing bots (run once)"""
    try:
        success = await capital_tracker.initialize_existing_bots()
        
        return {
            "success": success,
            "message": "Capital tracking initialized for all existing bots"
        }
    except Exception as e:
        logger.error(f"Initialize capital tracking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
