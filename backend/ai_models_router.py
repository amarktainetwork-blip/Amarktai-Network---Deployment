"""
Multi-Model AI Router
Routes different tasks to appropriate AI models (GPT-5.1, GPT-4o, GPT-4)
"""
from emergentintegrations.llm.chat import LlmChat, UserMessage
from logger_config import logger
from config import AI_MODELS
import os


class AIModelsRouter:
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self.models = AI_MODELS
    
    async def system_brain_decision(self, prompt: str, context: dict) -> str:
        """
        GPT-5.1 - System Brain
        For: Autopilot decisions, risk management, strategic planning
        """
        try:
            system_message = f"""You are the Amarktai System Brain - the highest-level AI controller.

Your role: Make strategic decisions about autopilot, capital allocation, risk management.

Current system state:
{context}

Think strategically. Consider long-term growth, risk mitigation, and optimal capital deployment."""

            chat = LlmChat(
                api_key=self.api_key,
                session_id="system_brain",
                system_message=system_message
            ).with_model("openai", self.models['system_brain'])
            
            response = await chat.send_message(UserMessage(text=prompt))
            return response.text if hasattr(response, 'text') else str(response)
        
        except Exception as e:
            logger.error(f"System brain error: {e}")
            # Fallback to GPT-4o
            return await self.trade_decision(prompt, context)
    
    async def trade_decision(self, prompt: str, context: dict) -> str:
        """
        GPT-4o - Trade Execution Brain
        For: Individual bot trading decisions, technical analysis
        """
        try:
            system_message = f"""You are the Amarktai Trade Execution Brain.

Your role: Make fast, accurate trading decisions for individual bots.

Context:
{context}

Focus on: Technical patterns, entry/exit timing, position sizing."""

            chat = LlmChat(
                api_key=self.api_key,
                session_id="trade_brain",
                system_message=system_message
            ).with_model("openai", self.models['trade_decision'])
            
            response = await chat.send_message(UserMessage(text=prompt))
            return response.text if hasattr(response, 'text') else str(response)
        
        except Exception as e:
            logger.error(f"Trade decision error: {e}")
            return f"Trade decision unavailable: {str(e)}"
    
    async def generate_report(self, prompt: str, data: dict) -> str:
        """
        GPT-4 - Reporting Brain
        For: Daily summaries, performance reports, email content
        """
        try:
            system_message = f"""You are the Amarktai Reporting Brain.

Your role: Generate clear, concise reports and summaries.

Data to summarize:
{data}

Focus on: Key metrics, insights, actionable recommendations."""

            chat = LlmChat(
                api_key=self.api_key,
                session_id="reporting_brain",
                system_message=system_message
            ).with_model("openai", self.models['reporting'])
            
            response = await chat.send_message(UserMessage(text=prompt))
            return response.text if hasattr(response, 'text') else str(response)
        
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return f"Report generation unavailable: {str(e)}"
    
    async def chatops_response(self, prompt: str, context: dict, user_id: str) -> str:
        """
        GPT-4o - ChatOps Brain
        For: Dashboard chat, real-time commands, user interaction
        """
        try:
            system_message = f"""You are the Amarktai ChatOps Brain - real-time assistant.

Your role: Respond quickly to user queries and execute commands.

System context:
{context}

Be: Fast, accurate, helpful. Execute commands when requested."""

            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"chatops_{user_id}",
                system_message=system_message
            ).with_model("openai", self.models['chatops'])
            
            response = await chat.send_message(UserMessage(text=prompt))
            return response.text if hasattr(response, 'text') else str(response)
        
        except Exception as e:
            logger.error(f"ChatOps error: {e}")
            return f"ChatOps unavailable: {str(e)}"
    
    def route_to_best_model(self, task_type: str) -> str:
        """Determine which model to use for a task"""
        routing_map = {
            "autopilot": "system_brain",
            "risk_assessment": "system_brain",
            "capital_allocation": "system_brain",
            "strategic_planning": "system_brain",
            "trade_execution": "trade_decision",
            "technical_analysis": "trade_decision",
            "bot_decision": "trade_decision",
            "daily_report": "reporting",
            "summary": "reporting",
            "email": "reporting",
            "chat": "chatops",
            "command": "chatops",
            "question": "chatops"
        }
        
        model_type = routing_map.get(task_type, "chatops")
        return self.models[model_type]


ai_models_router = AIModelsRouter()
