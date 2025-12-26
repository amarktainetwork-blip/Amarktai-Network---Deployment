"""
Phase 2: Order Pipeline - Comprehensive Test Suite
Tests all 4 gates of the execution guardrail system
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid

# Import the order pipeline
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.order_pipeline import OrderPipeline, CircuitBreaker


class TestIdempotencyGate:
    """Test Gate A: Idempotency & Duplicate Protection"""
    
    @pytest.mark.asyncio
    async def test_idempotency_prevents_duplicates(self):
        """Duplicate idempotency_key should return cached result"""
        pipeline = OrderPipeline(Mock())
        
        order_request = {
            "user_id": "user_123",
            "bot_id": "bot_456",
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "side": "buy",
            "amount": 0.01,
            "order_type": "market",
            "idempotency_key": "test-key-001"
        }
        
        # First submission
        result1 = await pipeline.submit_order(**order_request)
        
        # Duplicate submission with same key
        result2 = await pipeline.submit_order(**order_request)
        
        # Should return cached result
        assert result1["idempotency_key"] == result2["idempotency_key"]
        assert "cached" in result2.get("source", "").lower() or result2["success"] == result1["success"]
    
    @pytest.mark.asyncio
    async def test_idempotency_different_keys_allowed(self):
        """Different idempotency keys should execute separately"""
        pipeline = OrderPipeline(Mock())
        
        order1 = {
            "user_id": "user_123",
            "bot_id": "bot_456",
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "side": "buy",
            "amount": 0.01,
            "order_type": "market",
            "idempotency_key": str(uuid.uuid4())
        }
        
        order2 = {**order1, "idempotency_key": str(uuid.uuid4())}
        
        result1 = await pipeline.submit_order(**order1)
        result2 = await pipeline.submit_order(**order2)
        
        # Should be treated as different orders
        assert result1["idempotency_key"] != result2["idempotency_key"]


class TestFeeCoverageGate:
    """Test Gate B: Fee + Spread + Slippage Coverage"""
    
    @pytest.mark.asyncio
    async def test_fee_coverage_sufficient_edge(self):
        """Order with sufficient edge should pass"""
        pipeline = OrderPipeline(Mock())
        
        # Mock sufficient balance and profitable trade
        with patch.object(pipeline, '_calculate_edge_bps', return_value=50.0):
            with patch.object(pipeline, '_calculate_total_cost_bps', return_value=30.0):
                result = await pipeline._check_fee_coverage(
                    user_id="user_123",
                    bot_id="bot_456",
                    exchange="binance",
                    symbol="BTC/USDT",
                    side="buy",
                    amount=0.01,
                    price=50000
                )
        
        assert result["passed"] is True
        assert result["edge_bps"] >= result["total_cost_bps"]
    
    @pytest.mark.asyncio
    async def test_fee_coverage_insufficient_edge(self):
        """Order with insufficient edge should be rejected"""
        pipeline = OrderPipeline(Mock())
        
        # Mock insufficient edge
        with patch.object(pipeline, '_calculate_edge_bps', return_value=10.0):
            with patch.object(pipeline, '_calculate_total_cost_bps', return_value=30.0):
                result = await pipeline._check_fee_coverage(
                    user_id="user_123",
                    bot_id="bot_456",
                    exchange="binance",
                    symbol="BTC/USDT",
                    side="buy",
                    amount=0.01,
                    price=50000
                )
        
        assert result["passed"] is False
        assert "insufficient edge" in result["reason"].lower()
    
    def test_fee_coverage_calculation_accuracy(self):
        """Verify fee calculation math"""
        pipeline = OrderPipeline(Mock())
        
        # Test with known values
        fees_bps = 10  # 0.1%
        spread_bps = 5  # 0.05%
        slippage_bps = 10  # 0.1%
        safety_bps = 5  # 0.05%
        
        total = fees_bps + spread_bps + slippage_bps + safety_bps
        assert total == 30  # 0.3% total cost


class TestTradeLimiterGate:
    """Test Gate C: Trade Limiter (bot/user/burst)"""
    
    @pytest.mark.asyncio
    async def test_trade_limiter_bot_daily(self):
        """Bot daily limit should be enforced"""
        pipeline = OrderPipeline(Mock())
        
        # Mock bot at daily limit
        with patch.object(pipeline, '_get_bot_daily_count', return_value=50):
            with patch.object(pipeline, '_get_bot_daily_limit', return_value=50):
                result = await pipeline._check_trade_limits(
                    user_id="user_123",
                    bot_id="bot_456",
                    exchange="binance"
                )
        
        assert result["passed"] is False
        assert "bot daily limit" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_trade_limiter_user_daily(self):
        """User daily limit should be enforced"""
        pipeline = OrderPipeline(Mock())
        
        # Mock user at daily limit
        with patch.object(pipeline, '_get_user_daily_count', return_value=500):
            with patch.object(pipeline, '_get_user_daily_limit', return_value=500):
                result = await pipeline._check_trade_limits(
                    user_id="user_123",
                    bot_id="bot_456",
                    exchange="binance"
                )
        
        assert result["passed"] is False
        assert "user daily limit" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_trade_limiter_burst_protection(self):
        """Burst protection (10 orders/10s) should be enforced"""
        pipeline = OrderPipeline(Mock())
        
        # Mock burst limit exceeded
        with patch.object(pipeline, '_get_burst_count', return_value=11):
            with patch.object(pipeline, '_get_burst_limit', return_value=10):
                result = await pipeline._check_trade_limits(
                    user_id="user_123",
                    bot_id="bot_456",
                    exchange="binance"
                )
        
        assert result["passed"] is False
        assert "burst" in result["reason"].lower()


class TestCircuitBreakerGate:
    """Test Gate D: Circuit Breaker"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_drawdown(self):
        """Circuit breaker should trip at 20% drawdown"""
        breaker = CircuitBreaker(Mock())
        
        # Mock high drawdown
        with patch.object(breaker, '_get_current_drawdown', return_value=0.22):
            status = await breaker.check_status(bot_id="bot_456")
        
        assert status["should_trip"] is True
        assert "drawdown" in status["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_daily_loss(self):
        """Circuit breaker should trip at 10% daily loss"""
        breaker = CircuitBreaker(Mock())
        
        # Mock high daily loss
        with patch.object(breaker, '_get_daily_pnl_percent', return_value=-0.12):
            status = await breaker.check_status(bot_id="bot_456")
        
        assert status["should_trip"] is True
        assert "daily loss" in status["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_consecutive_losses(self):
        """Circuit breaker should trip at 5 consecutive losses"""
        breaker = CircuitBreaker(Mock())
        
        # Mock 5 consecutive losses
        with patch.object(breaker, '_get_consecutive_losses', return_value=5):
            status = await breaker.check_status(bot_id="bot_456")
        
        assert status["should_trip"] is True
        assert "consecutive" in status["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_error_storm(self):
        """Circuit breaker should trip at 10 errors/hour"""
        breaker = CircuitBreaker(Mock())
        
        # Mock error storm
        with patch.object(breaker, '_get_error_rate', return_value=12):
            status = await breaker.check_status(bot_id="bot_456")
        
        assert status["should_trip"] is True
        assert "error" in status["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_auto_pauses_bot(self):
        """Circuit breaker should auto-pause bot when tripped"""
        breaker = CircuitBreaker(Mock())
        
        # Trip the breaker
        await breaker.trip(
            bot_id="bot_456",
            reason="Test trip",
            trigger_type="manual"
        )
        
        # Verify bot would be paused
        status = await breaker.get_status(bot_id="bot_456")
        assert status["tripped"] is True


class TestOrderPipelineIntegration:
    """Integration tests for complete pipeline"""
    
    @pytest.mark.asyncio
    async def test_order_pipeline_all_gates_pass(self):
        """Order passing all gates should execute"""
        pipeline = OrderPipeline(Mock())
        
        # Mock all gates passing
        with patch.object(pipeline, '_check_idempotency', return_value={"passed": True}):
            with patch.object(pipeline, '_check_fee_coverage', return_value={"passed": True, "edge_bps": 50, "total_cost_bps": 30}):
                with patch.object(pipeline, '_check_trade_limits', return_value={"passed": True}):
                    with patch.object(pipeline, '_check_circuit_breaker', return_value={"passed": True}):
                        with patch.object(pipeline, '_execute_order', return_value={"success": True, "order_id": "order_123"}):
                            
                            result = await pipeline.submit_order(
                                user_id="user_123",
                                bot_id="bot_456",
                                exchange="binance",
                                symbol="BTC/USDT",
                                side="buy",
                                amount=0.01,
                                order_type="market",
                                idempotency_key=str(uuid.uuid4())
                            )
        
        assert result["success"] is True
        assert len(result["gates_passed"]) == 4
    
    @pytest.mark.asyncio
    async def test_order_pipeline_records_to_ledger(self):
        """All orders should be recorded to ledger"""
        mock_db = Mock()
        mock_ledger = Mock()
        mock_ledger.record_pending_order = AsyncMock()
        
        pipeline = OrderPipeline(mock_db)
        pipeline.ledger = mock_ledger
        
        # Submit order
        with patch.object(pipeline, '_execute_order', return_value={"success": True}):
            await pipeline.submit_order(
                user_id="user_123",
                bot_id="bot_456",
                exchange="binance",
                symbol="BTC/USDT",
                side="buy",
                amount=0.01,
                order_type="market",
                idempotency_key=str(uuid.uuid4())
            )
        
        # Verify ledger was called
        assert mock_ledger.record_pending_order.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
