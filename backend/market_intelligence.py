"""
Market Intelligence Service
- Fetches real-time market data from CoinGecko
- Analyzes market trends and sentiment
- Provides trading signals to AI
- Monitors global crypto market conditions
"""

import aiohttp
import asyncio
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class MarketIntelligence:
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    async def get_market_overview(self):
        """Get global crypto market overview"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.coingecko_base}/global") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        global_data = data.get('data', {})
                        
                        return {
                            'total_market_cap_usd': global_data.get('total_market_cap', {}).get('usd', 0),
                            'total_volume_24h': global_data.get('total_volume', {}).get('usd', 0),
                            'btc_dominance': global_data.get('market_cap_percentage', {}).get('btc', 0),
                            'eth_dominance': global_data.get('market_cap_percentage', {}).get('eth', 0),
                            'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                            'market_cap_change_24h': global_data.get('market_cap_change_percentage_24h_usd', 0)
                        }
        except Exception as e:
            logger.error(f"Market overview error: {e}")
            return None
            
    async def get_top_coins_data(self, limit=10):
        """Get top cryptocurrencies by market cap"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': limit,
                    'page': 1,
                    'sparkline': False,
                    'price_change_percentage': '24h,7d'
                }
                
                async with session.get(f"{self.coingecko_base}/coins/markets", params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.error(f"Top coins error: {e}")
            return []
            
    async def get_coin_price(self, coin_id='bitcoin'):
        """Get current price for a specific coin"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {'ids': coin_id, 'vs_currencies': 'usd', 'include_24hr_change': 'true'}
                async with session.get(f"{self.coingecko_base}/simple/price", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get(coin_id, {})
        except Exception as e:
            logger.error(f"Coin price error: {e}")
            return None
            
    async def analyze_market_sentiment(self):
        """Analyze overall market sentiment"""
        try:
            overview = await self.get_market_overview()
            if not overview:
                return "neutral"
                
            # Calculate sentiment based on market cap change
            change = overview.get('market_cap_change_24h', 0)
            
            if change > 5:
                return "very_bullish"
            elif change > 2:
                return "bullish"
            elif change < -5:
                return "very_bearish"
            elif change < -2:
                return "bearish"
            else:
                return "neutral"
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return "neutral"
            
    async def get_trading_signal(self, symbol='BTC'):
        """Generate trading signal based on market data"""
        try:
            # Get coin data
            coin_map = {'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin'}
            coin_id = coin_map.get(symbol, 'bitcoin')
            
            price_data = await self.get_coin_price(coin_id)
            if not price_data:
                return {'signal': 'hold', 'confidence': 0}
                
            # Get market sentiment
            sentiment = await self.analyze_market_sentiment()
            
            # Simple signal logic
            change_24h = price_data.get('usd_24h_change', 0)
            
            if sentiment in ['very_bullish', 'bullish'] and change_24h > 3:
                return {'signal': 'buy', 'confidence': 0.7, 'reason': 'Bullish market with positive momentum'}
            elif sentiment in ['very_bearish', 'bearish'] and change_24h < -3:
                return {'signal': 'sell', 'confidence': 0.7, 'reason': 'Bearish market with negative momentum'}
            else:
                return {'signal': 'hold', 'confidence': 0.5, 'reason': 'Market conditions unclear'}
                
        except Exception as e:
            logger.error(f"Trading signal error: {e}")
            return {'signal': 'hold', 'confidence': 0}
            
    async def get_volatility_index(self):
        """Calculate market volatility index"""
        try:
            top_coins = await self.get_top_coins_data(20)
            if not top_coins:
                return 50  # Default medium volatility
                
            # Calculate average price change
            changes = [abs(coin.get('price_change_percentage_24h', 0)) for coin in top_coins]
            avg_change = sum(changes) / len(changes)
            
            # Normalize to 0-100 scale
            volatility = min(avg_change * 10, 100)
            return round(volatility, 2)
            
        except Exception as e:
            logger.error(f"Volatility calculation error: {e}")
            return 50
            
    async def get_fear_greed_index(self):
        """Get crypto fear & greed index"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.alternative.me/fng/") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('data'):
                            index_data = data['data'][0]
                            return {
                                'value': int(index_data.get('value', 50)),
                                'classification': index_data.get('value_classification', 'Neutral'),
                                'timestamp': index_data.get('timestamp', '')
                            }
        except Exception as e:
            logger.error(f"Fear & Greed index error: {e}")
            return {'value': 50, 'classification': 'Neutral'}
            
    async def should_trade_now(self):
        """Determine if it's a good time to trade"""
        try:
            sentiment = await self.analyze_market_sentiment()
            volatility = await self.get_volatility_index()
            fear_greed = await self.get_fear_greed_index()
            
            # Trading conditions
            conditions = {
                'market_sentiment': sentiment,
                'volatility': volatility,
                'fear_greed': fear_greed['value'],
                'recommendation': 'hold'
            }
            
            # Logic for trading recommendation
            if volatility < 30 and sentiment in ['bullish', 'very_bullish']:
                conditions['recommendation'] = 'favorable'
            elif volatility > 70:
                conditions['recommendation'] = 'risky'
            elif sentiment in ['very_bearish']:
                conditions['recommendation'] = 'caution'
            else:
                conditions['recommendation'] = 'normal'
                
            return conditions
            
        except Exception as e:
            logger.error(f"Trade timing analysis error: {e}")
            return {'recommendation': 'hold'}
            
    async def get_market_intelligence_summary(self):
        """Get comprehensive market intelligence summary"""
        try:
            overview = await self.get_market_overview()
            sentiment = await self.analyze_market_sentiment()
            volatility = await self.get_volatility_index()
            fear_greed = await self.get_fear_greed_index()
            trade_conditions = await self.should_trade_now()
            
            return {
                'overview': overview,
                'sentiment': sentiment,
                'volatility': volatility,
                'fear_greed': fear_greed,
                'trade_conditions': trade_conditions,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Market intelligence summary error: {e}")
            return None

# Global instance
market_intelligence = MarketIntelligence()
