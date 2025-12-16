"""
Email Scheduler - Send automated daily reports
Runs twice daily: 8 AM and 6 PM
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from email_service import email_service

logger = logging.getLogger(__name__)

class EmailScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db = None
        
    async def init_db(self):
        """Initialize database connection"""
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.getenv('DB_NAME', 'amarktai_trading')
        client = AsyncIOMotorClient(mongo_url)
        self.db = client[db_name]
        
    async def start(self):
        """Start email scheduler"""
        await self.init_db()
        
        # Schedule morning report at 8 AM
        self.scheduler.add_job(
            self.send_morning_reports,
            trigger='cron',
            hour=8,
            minute=0,
            timezone='Africa/Johannesburg',
            id='morning_report'
        )
        
        # Schedule evening report at 6 PM
        self.scheduler.add_job(
            self.send_evening_reports,
            trigger='cron',
            hour=18,
            minute=0,
            timezone='Africa/Johannesburg',
            id='evening_report'
        )
        
        self.scheduler.start()
        logger.info("📧 Email Scheduler started - Reports at 8 AM and 6 PM")
        
    async def send_morning_reports(self):
        """Send morning reports to all active users"""
        try:
            logger.info("📧 Sending morning reports...")
            users = await self.db.users.find({'blocked': {'$ne': True}}, {'_id': 0}).to_list(1000)
            
            for user in users:
                try:
                    stats = await self.calculate_daily_stats(user['id'])
                    await self.send_daily_report_email(
                        user['email'],
                        user.get('first_name', 'Trader'),
                        stats,
                        'morning'
                    )
                except Exception as e:
                    logger.error(f"Failed to send morning report to {user['email']}: {e}")
                    
            logger.info(f"✅ Morning reports sent to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Morning report batch error: {e}")
            
    async def send_evening_reports(self):
        """Send evening reports to all active users"""
        try:
            logger.info("📧 Sending evening reports...")
            users = await self.db.users.find({'blocked': {'$ne': True}}, {'_id': 0}).to_list(1000)
            
            for user in users:
                try:
                    stats = await self.calculate_daily_stats(user['id'])
                    await self.send_daily_report_email(
                        user['email'],
                        user.get('first_name', 'Trader'),
                        stats,
                        'evening'
                    )
                except Exception as e:
                    logger.error(f"Failed to send evening report to {user['email']}: {e}")
                    
            logger.info(f"✅ Evening reports sent to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Evening report batch error: {e}")
            
    async def calculate_daily_stats(self, user_id: str) -> dict:
        """Calculate today's trading statistics"""
        try:
            # Get today's start time
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
            
            # Get today's trades
            trades = await self.db.trades.find({
                'user_id': user_id,
                'timestamp': {'$gte': today_start}
            }).to_list(10000)
            
            # Get all user bots
            bots = await self.db.bots.find({'user_id': user_id}, {'_id': 0}).to_list(1000)
            
            # Calculate stats
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.get('profit_loss', 0) > 0)
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_profit = sum(t.get('profit_loss', 0) for t in trades)
            total_volume = sum(t.get('amount', 0) * t.get('price', 0) for t in trades)
            
            active_bots = sum(1 for b in bots if b.get('status') == 'active')
            total_bots = len(bots)
            
            # Best performing bot
            bot_profits = {}
            for trade in trades:
                bot_id = trade.get('bot_id')
                if bot_id:
                    bot_profits[bot_id] = bot_profits.get(bot_id, 0) + trade.get('profit_loss', 0)
            
            best_bot = None
            best_profit = 0
            if bot_profits:
                best_bot_id = max(bot_profits, key=bot_profits.get)
                best_profit = bot_profits[best_bot_id]
                bot_doc = await self.db.bots.find_one({'id': best_bot_id}, {'_id': 0})
                if bot_doc:
                    best_bot = bot_doc.get('name', 'Unknown')
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'total_volume': total_volume,
                'active_bots': active_bots,
                'total_bots': total_bots,
                'best_bot': best_bot,
                'best_bot_profit': best_profit
            }
            
        except Exception as e:
            logger.error(f"Error calculating stats for {user_id}: {e}")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'total_volume': 0,
                'active_bots': 0,
                'total_bots': 0,
                'best_bot': None,
                'best_bot_profit': 0
            }
            
    async def send_daily_report_email(self, to_email: str, first_name: str, stats: dict, period: str):
        """Send comprehensive daily report email"""
        
        # Determine subject and greeting based on time of day
        if period == 'morning':
            subject = f"☀️ Good Morning {first_name} - Your Trading Summary"
            greeting = "Good Morning"
            time_context = "Here's your overnight trading summary"
        else:
            subject = f"🌙 Good Evening {first_name} - Today's Results"
            greeting = "Good Evening"
            time_context = "Here's your full day trading summary"
        
        profit = stats['total_profit']
        profit_color = '#10b981' if profit >= 0 else '#ef4444'
        profit_symbol = '+' if profit >= 0 else ''
        profit_text = 'Profit' if profit >= 0 else 'Loss'
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }}
                .container {{ max-width: 650px; margin: 0 auto; background: #ffffff; }}
                .header {{ background: linear-gradient(135deg, #002b57 0%, #10b981 100%); padding: 40px 30px; text-align: center; color: #ffffff; }}
                .header h1 {{ margin: 0 0 10px 0; font-size: 28px; }}
                .content {{ padding: 30px; background: #ffffff; }}
                .profit-banner {{ background: linear-gradient(135deg, {profit_color}15 0%, {profit_color}05 100%); border: 2px solid {profit_color}; border-radius: 12px; padding: 30px; text-align: center; margin: 20px 0; }}
                .profit-amount {{ font-size: 48px; font-weight: 700; color: {profit_color}; margin: 10px 0; }}
                .profit-label {{ color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
                .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 25px 0; }}
                .stat-card {{ background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; text-align: center; }}
                .stat-label {{ color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }}
                .stat-value {{ font-size: 24px; font-weight: 700; color: #002b57; }}
                .highlight {{ background: linear-gradient(135deg, #10b98120 0%, #10b98110 100%); border-left: 4px solid #10b981; padding: 15px 20px; border-radius: 4px; margin: 20px 0; }}
                .bot-performance {{ background: #002b5710; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                .footer {{ background: #f8f9fa; padding: 30px; text-align: center; color: #666; font-size: 12px; border-top: 1px solid #e0e0e0; }}
                .btn {{ display: inline-block; background: #10b981; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
                .win-rate {{ display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; background: #10b98120; color: #10b981; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Amarktai Network</h1>
                    <p style="margin: 0; opacity: 0.9;">{greeting}, {first_name}!</p>
                </div>
                
                <div class="content">
                    <p style="font-size: 16px; color: #333;">{time_context}</p>
                    
                    <div class="profit-banner">
                        <div class="profit-label">Today's {profit_text}</div>
                        <div class="profit-amount">{profit_symbol}R{abs(profit):.2f}</div>
                        <div class="win-rate">Win Rate: {stats['win_rate']:.1f}%</div>
                    </div>
                    
                    <h3 style="color: #002b57; margin-top: 30px;">📊 Trading Statistics</h3>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Total Trades</div>
                            <div class="stat-value">{stats['total_trades']}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Win Rate</div>
                            <div class="stat-value">{stats['win_rate']:.1f}%</div>
                        </div>
                        <div class="stat-card" style="border-left: 3px solid #10b981;">
                            <div class="stat-label">Winning Trades</div>
                            <div class="stat-value" style="color: #10b981;">{stats['winning_trades']}</div>
                        </div>
                        <div class="stat-card" style="border-left: 3px solid #ef4444;">
                            <div class="stat-label">Losing Trades</div>
                            <div class="stat-value" style="color: #ef4444;">{stats['losing_trades']}</div>
                        </div>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Total Volume</div>
                            <div class="stat-value">R{stats['total_volume']:.0f}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Active Bots</div>
                            <div class="stat-value">{stats['active_bots']}/{stats['total_bots']}</div>
                        </div>
                    </div>
                    
                    {f'''
                    <div class="bot-performance">
                        <h4 style="margin: 0 0 10px 0; color: #002b57;">🏆 Best Performing Bot</h4>
                        <p style="margin: 5px 0;"><strong>{stats['best_bot']}</strong></p>
                        <p style="margin: 5px 0; color: {profit_color}; font-size: 20px; font-weight: 700;">
                            {profit_symbol}R{abs(stats['best_bot_profit']):.2f}
                        </p>
                    </div>
                    ''' if stats['best_bot'] else ''}
                    
                    <div class="highlight">
                        <strong>🤖 AI System Status:</strong> Your autonomous trading system is actively monitoring markets and optimizing strategies 24/7.
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://amarktai.online/dashboard" class="btn">View Full Dashboard</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p style="margin: 0 0 10px 0;"><strong>Amarktai Network</strong></p>
                    <p style="margin: 0;">Autonomous AI-Powered Crypto Trading</p>
                    <p style="margin: 15px 0 0 0;">Growing Your Wealth 24/7</p>
                    <p style="margin: 10px 0 0 0;">📧 amarktainetwork@gmail.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            success = await email_service.send_email(
                to_email=to_email,
                subject=subject,
                body=html_body,
                html=True
            )
            if success:
                logger.info(f"✅ Daily report sent to {to_email}")
            return success
        except Exception as e:
            logger.error(f"Failed to send daily report to {to_email}: {e}")
            return False
            
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Email Scheduler stopped")

# Global instance
email_scheduler = EmailScheduler()
