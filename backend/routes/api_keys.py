from fastapi import HTTPException, Depends, APIRouter
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import logging

from models import User, UserLogin, Bot, BotCreate, APIKey, APIKeyCreate, Trade, SystemMode, Alert, ChatMessage, BotRiskMode
from database import users_collection, bots_collection, api_keys_collection, trades_collection, system_modes_collection, alerts_collection, chat_messages_collection
from auth import create_access_token, get_current_user, get_password_hash, verify_password

logger = logging.getLogger(__name__)
router = APIRouter()
from ccxt_service import ccxt_service


@router.get("/api-keys")
async def get_api_keys(user_id: str = Depends(get_current_user)):
    keys = await api_keys_collection.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    for key in keys:
        if 'secret' in key:
            key['secret'] = '***' + key['secret'][-4:] if len(key.get('secret', '')) > 4 else '***'
    return keys


