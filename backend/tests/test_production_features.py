"""
Comprehensive Tests for Production Features

Tests cover:
1. AI Command Router functionality
2. Ledger-based autopilot reinvestment
3. Ledger-based daily reports
4. Order pipeline gates
5. Circuit breaker functionality
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock


class TestAICommandRouter:
    """Test AI Command Router"""
    
    @pytest.fixture
    async def mock_db(self):
        """Create mock database"""
        db = Mock()
        db["bots"] = AsyncMock()
        db["users"] = AsyncMock()
        db["system_modes"] = AsyncMock()
        db["trades"] = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_parse_start_bot_command(self, mock_db):
        """Test parsing start bot command"""
        from services.ai_command_router import AICommandRouter
        
        router = AICommandRouter(mock_db)
        
        # Mock bot lookup
        mock_bot = {
            "id": "bot_123",
            "name": "Test Bot",
            "status": "paused"
        }
        mock_db["bots"].find_one = AsyncMock(return_value=mock_bot)
        mock_db["bots"].update_one = AsyncMock()
        
        # Test command parsing
        is_command, result = await router.parse_and_execute(
            "user_1",
            "start bot Test Bot",
            confirmed=True
        )
        
        assert is_command is True
        assert result["success"] is True
        assert "started" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_emergency_stop_requires_confirmation(self, mock_db):
        """Test emergency stop requires confirmation"""
        from services.ai_command_router import AICommandRouter
        
        router = AICommandRouter(mock_db)
        
        # Without confirmation
        is_command, result = await router.parse_and_execute(
            "user_1",
            "emergency stop",
            confirmed=False
        )
        
        assert is_command is True
        assert result["success"] is False
        assert result.get("requires_confirmation") is True
    
    @pytest.mark.asyncio
    async def test_portfolio_summary_command(self, mock_db):
        """Test portfolio summary command"""
        from services.ai_command_router import AICommandRouter
        
        router = AICommandRouter(mock_db)
        
        # Mock bots
        mock_db["bots"].find = Mock(return_value=Mock(
            to_list=AsyncMock(return_value=[
                {"id": "bot_1", "current_capital": 1000, "initial_capital": 800},
                {"id": "bot_2", "current_capital": 1500, "initial_capital": 1200}
            ])
        ))
        
        # Mock ledger service
        with patch('services.ai_command_router.get_ledger_service') as mock_ledger:
            mock_ledger_instance = Mock()
            mock_ledger_instance.compute_equity = AsyncMock(return_value=2500)
            mock_ledger_instance.compute_realized_pnl = AsyncMock(return_value=500)
            mock_ledger_instance.compute_fees_paid = AsyncMock(return_value=50)
            mock_ledger_instance.compute_drawdown = AsyncMock(return_value=(0.05, 0.10))
            mock_ledger.return_value = mock_ledger_instance
            
            is_command, result = await router.parse_and_execute(
                "user_1",
                "show portfolio",
                confirmed=False
            )
            
            assert is_command is True
            assert result["success"] is True
            assert "portfolio" in result
            assert result["portfolio"]["equity"] == 2500
    
    @pytest.mark.asyncio
    async def test_admin_only_command_fails_for_non_admin(self, mock_db):
        """Test admin-only commands fail for regular users"""
        from services.ai_command_router import AICommandRouter
        
        router = AICommandRouter(mock_db)
        
        is_command, result = await router.parse_and_execute(
            "user_1",
            "send test report",
            confirmed=True,
            is_admin=False
        )
        
        assert is_command is True
        assert result["success"] is False
        assert "admin" in result["message"].lower()


class TestLedgerIntegration:
    """Test Ledger Integration"""
    
    @pytest.mark.asyncio
    async def test_autopilot_uses_ledger_for_reinvestment(self):
        """Test autopilot uses ledger data for profit calculation"""
        from autopilot_engine import AutopilotEngine
        from unittest.mock import patch
        
        autopilot = AutopilotEngine()
        autopilot.db = Mock()
        
        # Mock users with autopilot enabled
        autopilot.db.users.find = Mock(return_value=Mock(
            to_list=AsyncMock(return_value=[{"id": "user_1", "autopilot_enabled": True}])
        ))
        
        # Mock bots
        autopilot.db.bots.find = Mock(return_value=Mock(
            to_list=AsyncMock(return_value=[
                {"id": "bot_1", "total_profit": 1000, "trades_count": 10, "current_capital": 1000}
            ])
        ))
        
        # Mock ledger service
        with patch('autopilot_engine.get_ledger_service') as mock_ledger_service:
            mock_ledger = Mock()
            mock_ledger.compute_realized_pnl = AsyncMock(return_value=1500)
            mock_ledger.compute_fees_paid = AsyncMock(return_value=50)
            mock_ledger_service.return_value = mock_ledger
            
            # Mock bot creation
            autopilot.create_autonomous_bot = AsyncMock()
            autopilot.db.alerts.insert_one = AsyncMock()
            
            # Run reinvestment
            await autopilot.daily_reinvestment_cycle()
            
            # Verify ledger was called
            mock_ledger.compute_realized_pnl.assert_called_once_with("user_1")
            mock_ledger.compute_fees_paid.assert_called_once_with("user_1")
            
            # Verify bot created with net profit >= 1000
            autopilot.create_autonomous_bot.assert_called_once_with("user_1", 1000)
    
    @pytest.mark.asyncio
    async def test_daily_report_uses_ledger_data(self):
        """Test daily report uses ledger for metrics"""
        from routes.daily_report import DailyReportService
        from unittest.mock import patch
        
        service = DailyReportService()
        
        # Mock database collections
        with patch('routes.daily_report.users_collection') as mock_users, \
             patch('routes.daily_report.bots_collection') as mock_bots, \
             patch('routes.daily_report.alerts_collection') as mock_alerts:
            
            # Mock user
            mock_users.find_one = AsyncMock(return_value={
                "id": "user_1",
                "email": "test@example.com",
                "name": "Test User"
            })
            
            # Mock bots
            mock_bots.find = Mock(return_value=Mock(
                to_list=AsyncMock(return_value=[
                    {"status": "active", "current_capital": 1000},
                    {"status": "paused", "current_capital": 500}
                ])
            ))
            
            # Mock alerts
            mock_alerts.find = Mock(return_value=Mock(
                to_list=AsyncMock(return_value=[])
            ))
            
            # Mock ledger service
            with patch('routes.daily_report.get_ledger_service') as mock_ledger_service, \
                 patch('routes.daily_report.get_database') as mock_get_db:
                
                mock_db = Mock()
                mock_get_db.return_value = asyncio.coroutine(lambda: mock_db)()
                
                mock_ledger = Mock()
                mock_ledger.compute_equity = AsyncMock(return_value=1500)
                mock_ledger.compute_realized_pnl = AsyncMock(return_value=500)
                mock_ledger.compute_fees_paid = AsyncMock(return_value=50)
                mock_ledger.compute_drawdown = AsyncMock(return_value=(0.05, 0.10))
                mock_ledger.get_stats = AsyncMock(return_value={"total_fills": 100})
                mock_ledger.profit_series = AsyncMock(return_value={"values": [100]})
                mock_ledger.get_fills = AsyncMock(return_value=[])
                mock_ledger_service.return_value = mock_ledger
                
                # Generate report
                html = await service.generate_report_html("user_1")
                
                # Verify ledger was called
                assert mock_ledger.compute_equity.called
                assert mock_ledger.compute_realized_pnl.called
                assert mock_ledger.compute_fees_paid.called
                
                # Verify HTML contains key metrics
                assert html is not None
                assert "1500" in html  # Equity
                assert "500" in html   # Realized PnL


class TestOrderPipeline:
    """Test Order Pipeline Gates"""
    
    @pytest.mark.asyncio
    async def test_idempotency_gate_prevents_duplicates(self):
        """Test idempotency gate prevents duplicate orders"""
        from services.order_pipeline import OrderPipeline
        
        mock_db = Mock()
        mock_db["pending_orders"] = AsyncMock()
        mock_ledger = Mock()
        
        pipeline = OrderPipeline(mock_db, mock_ledger)
        
        # Mock existing order with same idempotency key
        mock_db["pending_orders"].find_one = AsyncMock(return_value={
            "idempotency_key": "order_123",
            "state": "pending"
        })
        
        # Try to submit duplicate
        result = await pipeline.submit_order(
            user_id="user_1",
            bot_id="bot_1",
            exchange="luno",
            symbol="BTC/ZAR",
            side="buy",
            amount=0.001,
            price=1000000,
            idempotency_key="order_123"
        )
        
        # Should reject
        assert result["success"] is False
        assert "duplicate" in result.get("reason", "").lower() or "idempotency" in result.get("reason", "").lower()
    
    @pytest.mark.asyncio
    async def test_fee_coverage_gate_rejects_unprofitable(self):
        """Test fee coverage gate rejects orders without sufficient edge"""
        from services.order_pipeline import OrderPipeline
        
        mock_db = Mock()
        mock_db["pending_orders"] = AsyncMock()
        mock_ledger = Mock()
        
        pipeline = OrderPipeline(mock_db, mock_ledger, config={
            "MIN_EDGE_BPS": 50  # Require 50 bps edge
        })
        
        # Mock no existing order
        mock_db["pending_orders"].find_one = AsyncMock(return_value=None)
        
        # Mock order with insufficient edge
        result = await pipeline.submit_order(
            user_id="user_1",
            bot_id="bot_1",
            exchange="luno",
            symbol="BTC/ZAR",
            side="buy",
            amount=0.001,
            price=1000000,
            expected_edge_bps=10  # Only 10 bps edge
        )
        
        # Should reject
        assert result["success"] is False
        assert "fee" in result.get("reason", "").lower() or "edge" in result.get("reason", "").lower()


class TestCircuitBreaker:
    """Test Circuit Breaker Functionality"""
    
    @pytest.mark.asyncio
    async def test_drawdown_trips_breaker(self):
        """Test circuit breaker trips on excessive drawdown"""
        from services.order_pipeline import OrderPipeline
        
        mock_db = Mock()
        mock_db["circuit_breaker_state"] = AsyncMock()
        mock_ledger = Mock()
        
        # Mock high drawdown
        mock_ledger.compute_drawdown = AsyncMock(return_value=(0.25, 0.30))  # 25% current, 30% max
        
        pipeline = OrderPipeline(mock_db, mock_ledger, config={
            "MAX_DRAWDOWN_PERCENT": 0.20  # 20% threshold
        })
        
        # Check circuit breaker
        tripped = await pipeline.check_circuit_breaker("user_1", "bot_1")
        
        # Should trip
        assert tripped is True
    
    @pytest.mark.asyncio
    async def test_consecutive_losses_trip_breaker(self):
        """Test circuit breaker trips on consecutive losses"""
        from services.order_pipeline import OrderPipeline
        
        mock_db = Mock()
        mock_db["circuit_breaker_state"] = AsyncMock()
        mock_db["fills_ledger"] = AsyncMock()
        mock_ledger = Mock()
        
        # Mock consecutive losses
        mock_db["fills_ledger"].find = Mock(return_value=Mock(
            sort=Mock(return_value=Mock(
                limit=Mock(return_value=Mock(
                    to_list=AsyncMock(return_value=[
                        {"side": "sell", "qty": 0.001, "price": 990000},  # Loss
                        {"side": "sell", "qty": 0.001, "price": 980000},  # Loss
                        {"side": "sell", "qty": 0.001, "price": 970000},  # Loss
                        {"side": "sell", "qty": 0.001, "price": 960000},  # Loss
                        {"side": "sell", "qty": 0.001, "price": 950000},  # Loss
                    ])
                ))
            ))
        ))
        
        pipeline = OrderPipeline(mock_db, mock_ledger, config={
            "MAX_CONSECUTIVE_LOSSES": 5
        })
        
        # Check circuit breaker
        tripped = await pipeline.check_circuit_breaker("user_1", "bot_1")
        
        # Should trip
        assert tripped is True


class TestConfigurableLimits:
    """Test Configurable Limits"""
    
    @pytest.mark.asyncio
    async def test_limits_read_from_environment(self):
        """Test limits are read from environment variables"""
        import os
        from services.order_pipeline import OrderPipeline
        
        # Set environment variables
        os.environ["MAX_TRADES_PER_BOT_DAILY"] = "100"
        os.environ["MAX_TRADES_PER_USER_DAILY"] = "1000"
        os.environ["BURST_LIMIT_ORDERS_PER_EXCHANGE"] = "20"
        
        mock_db = Mock()
        mock_ledger = Mock()
        
        # Create pipeline (should read from env)
        pipeline = OrderPipeline(mock_db, mock_ledger)
        
        # Verify limits
        assert pipeline.max_trades_per_bot_daily == 100
        assert pipeline.max_trades_per_user_daily == 1000
        assert pipeline.burst_limit_orders == 20
        
        # Cleanup
        del os.environ["MAX_TRADES_PER_BOT_DAILY"]
        del os.environ["MAX_TRADES_PER_USER_DAILY"]
        del os.environ["BURST_LIMIT_ORDERS_PER_EXCHANGE"]
    
    @pytest.mark.asyncio
    async def test_exchange_specific_overrides(self):
        """Test exchange-specific limit overrides"""
        from services.order_pipeline import OrderPipeline
        
        mock_db = Mock()
        mock_ledger = Mock()
        
        # Create pipeline with exchange overrides
        pipeline = OrderPipeline(mock_db, mock_ledger, config={
            "MAX_TRADES_PER_BOT_DAILY": 50,
            "EXCHANGE_OVERRIDES": {
                "binance": {"MAX_TRADES_PER_BOT_DAILY": 100},
                "luno": {"MAX_TRADES_PER_BOT_DAILY": 30}
            }
        })
        
        # Get limit for binance
        binance_limit = pipeline.config.get("EXCHANGE_OVERRIDES", {}).get("binance", {}).get(
            "MAX_TRADES_PER_BOT_DAILY", pipeline.max_trades_per_bot_daily
        )
        
        # Get limit for luno
        luno_limit = pipeline.config.get("EXCHANGE_OVERRIDES", {}).get("luno", {}).get(
            "MAX_TRADES_PER_BOT_DAILY", pipeline.max_trades_per_bot_daily
        )
        
        assert binance_limit == 100
        assert luno_limit == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
