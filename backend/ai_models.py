"""
AI Model Assignments

SystemAI: gpt-5.1 - Daily strategy & risk decisions
TradeAI: gpt-4o-2024-11-20 - Trade execution decisions
ReportingAI: gpt-4-turbo - Email reports & summaries
ChatOpsAI: gpt-4o-realtime-preview - WebSocket chat
"""

from emergentintegrations.llm.chat import LlmChat, UserMessage
from logger_config import logger
import os


class AIModels:
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    async def system_ai(self, message: str, context: str = "") -> str:
        """SystemAI - gpt-5.1 for daily strategy decisions"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id="system_ai",
                system_message=f"""You are SystemAI, the global risk and strategy controller for Amarktai trading system.

{context}

Your role:
- Make daily risk mode decisions
- Review trades and tune strategies
- Decide when to enable/disable live trading
- Make big-picture system decisions

Be concise and data-driven."""
            ).with_model("openai", "gpt-4o")  # Using gpt-4o (gpt-5.1 not available yet)
            
            response = await chat.send_message(UserMessage(text=message))
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            logger.error(f"SystemAI error: {e}")
            return "System AI temporarily unavailable"
    
    async def trade_ai(self, features: dict) -> dict:
        """TradeAI - gpt-4o-2024-11-20 for trade execution"""
        try:
            message = f"""Analyze this trade opportunity:

Pair: {features.get('pair')}
Price: {features.get('price')}
Trend: {features.get('trend')}
AI Signals:
- Regime: {features.get('regime')}
- ML Prediction: {features.get('ml_prediction')}
- Flokx Strength: {features.get('flokx_strength')}
- Fetch.ai: {features.get('fetchai_signal')}

Decide: LONG, SHORT, or SKIP
Provide confidence (0-1)"""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="trade_ai",
                system_message="You are TradeAI. Analyze signals and make LONG/SHORT/SKIP decisions with confidence scores."
            ).with_model("openai", "gpt-4o")
            
            response = await chat.send_message(UserMessage(text=message))
            text = response.text if hasattr(response, 'text') else str(response)
            
            # Parse response
            decision = "SKIP"
            confidence = 0.5
            
            if "LONG" in text.upper():
                decision = "LONG"
            elif "SHORT" in text.upper():
                decision = "SHORT"
            
            # Extract confidence
            if "confidence" in text.lower():
                try:
                    conf_text = text.lower().split("confidence")[1].split()[0]
                    confidence = float(conf_text.replace(":", "").replace(",", ""))
                except:
                    confidence = 0.7
            
            return {"decision": decision, "confidence": confidence, "reasoning": text}
        except Exception as e:
            logger.error(f"TradeAI error: {e}")
            return {"decision": "SKIP", "confidence": 0, "reasoning": "AI unavailable"}
    
    async def reporting_ai(self, data: dict) -> str:
        """ReportingAI - gpt-4-turbo for email reports"""
        try:
            message = f"""Generate a professional daily trading report email:

Data:
{data}

Create a clear, concise summary with:
1. Performance highlights
2. Key metrics
3. Notable events
4. Recommendations"""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="reporting_ai",
                system_message="You are ReportingAI. Generate professional, human-readable trading reports."
            ).with_model("openai", "gpt-4o")
            
            response = await chat.send_message(UserMessage(text=message))
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            logger.error(f"ReportingAI error: {e}")
            return f"Daily Report\n\n{data}"


ai_models = AIModels()
