"""
Tests for Order Pipeline - Fee Coverage and Trade Limiter Guards
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture
def mock_db():
    """Mock database"""
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=AsyncMock())
    return db


@pytest.fixture
def mock_ledger():
    """Mock ledger service"""
    ledger = AsyncMock()
    ledger.get_trade_count = AsyncMock(return_value=0)
    ledger.append_fill = AsyncMock(return_value="fill_123")
    ledger.compute_drawdown = AsyncMock(return_value=(0.05, 0.10))
    ledger.compute_daily_pnl = AsyncMock(return_value=100)
    ledger.compute_equity = AsyncMock(return_value=10000)
    ledger.get_consecutive_losses = AsyncMock(return_value=0)
    ledger.get_error_rate = AsyncMock(return_value=0)
    return ledger


@pytest.fixture
def order_pipeline_config():
    """Default configuration for tests"""
    return {
        "MAX_TRADES_PER_BOT_DAILY": 50,
        "MAX_TRADES_PER_USER_DAILY": 500,
        "BURST_LIMIT_ORDERS_PER_EXCHANGE": 10,
        "BURST_LIMIT_WINDOW_SECONDS": 10,
        "MIN_EDGE_BPS": 10.0,
        "SAFETY_MARGIN_BPS": 5.0,
        "SLIPPAGE_BUFFER_BPS": 10.0
    }


@pytest.mark.asyncio
async def test_fee_coverage_gate_passes_with_sufficient_edge(mock_db, mock_ledger, order_pipeline_config):
    """Test that fee coverage gate passes when edge is sufficient"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    # Test market order on BTC/ZAR with sufficient edge
    result = await pipeline._gate_b_fee_coverage(
        exchange="binance",
        symbol="BTC/USDT",
        side="buy",
        amount=0.01,
        order_type="market",
        price=None
    )
    
    assert result["passed"] is True
    assert "details" in result
    details = result["details"]
    assert details["profit_margin_bps"] >= 0  # Should have positive margin


@pytest.mark.asyncio
async def test_fee_coverage_gate_fails_with_insufficient_edge(mock_db, mock_ledger):
    """Test that fee coverage gate fails when costs exceed edge"""
    from services.order_pipeline import OrderPipeline
    
    # Configure with unrealistic high fees to force failure
    config = {
        "MIN_EDGE_BPS": 5.0,  # Very low edge
        "SAFETY_MARGIN_BPS": 50.0,  # Very high margin
        "SLIPPAGE_BUFFER_BPS": 50.0  # High slippage
    }
    
    pipeline = OrderPipeline(mock_db, mock_ledger, config)
    
    result = await pipeline._gate_b_fee_coverage(
        exchange="luno",  # Luno has higher fees
        symbol="BTC/ZAR",  # Higher spread
        side="buy",
        amount=0.01,
        order_type="market",
        price=None
    )
    
    assert result["passed"] is False
    assert "Insufficient edge" in result["reason"]
    assert "details" in result
    assert result["details"]["profit_margin_bps"] < 0


@pytest.mark.asyncio
async def test_fee_coverage_calculates_costs_correctly(mock_db, mock_ledger, order_pipeline_config):
    """Test that fee coverage correctly calculates all cost components"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    result = await pipeline._gate_b_fee_coverage(
        exchange="binance",
        symbol="BTC/USDT",
        side="buy",
        amount=0.01,
        order_type="market",
        price=50000
    )
    
    assert result["passed"] is True
    details = result["details"]
    
    # Verify all cost components are present
    assert "fee_bps" in details
    assert "spread_bps" in details
    assert "slippage_bps" in details
    assert "safety_margin_bps" in details
    assert "total_cost_bps" in details
    
    # Verify calculations
    expected_total = (
        details["fee_bps"] +
        details["spread_bps"] +
        details["slippage_bps"] +
        details["safety_margin_bps"]
    )
    assert abs(details["total_cost_bps"] - expected_total) < 0.01


@pytest.mark.asyncio
async def test_trade_limiter_respects_bot_daily_limit(mock_db, mock_ledger, order_pipeline_config):
    """Test that trade limiter enforces bot daily limit"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    # Mock ledger to return count at limit
    mock_ledger.get_trade_count = AsyncMock(return_value=50)  # At limit
    
    result = await pipeline._gate_c_trade_limiter(
        user_id="user_123",
        bot_id="bot_456",
        exchange="binance"
    )
    
    assert result["passed"] is False
    assert "Bot daily limit" in result["reason"]
    assert "50/50" in result["reason"]


@pytest.mark.asyncio
async def test_trade_limiter_respects_user_daily_limit(mock_db, mock_ledger, order_pipeline_config):
    """Test that trade limiter enforces user daily limit"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    # Mock ledger to return different counts for bot (under limit) and user (at limit)
    async def mock_get_trade_count(*args, bot_id=None, user_id=None, **kwargs):
        if bot_id:
            return 10  # Bot under limit
        if user_id:
            return 500  # User at limit
        return 0
    
    mock_ledger.get_trade_count = mock_get_trade_count
    
    result = await pipeline._gate_c_trade_limiter(
        user_id="user_123",
        bot_id="bot_456",
        exchange="binance"
    )
    
    assert result["passed"] is False
    assert "User daily limit" in result["reason"]
    assert "500/500" in result["reason"]


@pytest.mark.asyncio
async def test_trade_limiter_respects_burst_limit(mock_db, mock_ledger, order_pipeline_config):
    """Test that trade limiter enforces burst limit"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    # Mock ledger to return low counts for daily limits
    mock_ledger.get_trade_count = AsyncMock(return_value=0)
    
    # Simulate burst by making multiple rapid requests
    user_id = "user_123"
    bot_id = "bot_456"
    exchange = "binance"
    
    # Fill up burst counter
    burst_key = f"{exchange}:{user_id}"
    now = datetime.utcnow()
    pipeline.burst_counters[burst_key] = [now] * 10  # Fill to limit
    
    result = await pipeline._gate_c_trade_limiter(
        user_id=user_id,
        bot_id=bot_id,
        exchange=exchange
    )
    
    assert result["passed"] is False
    assert "Burst limit" in result["reason"]
    assert "10/10" in result["reason"]


@pytest.mark.asyncio
async def test_trade_limiter_cleans_old_burst_timestamps(mock_db, mock_ledger, order_pipeline_config):
    """Test that burst limiter cleans up old timestamps"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    mock_ledger.get_trade_count = AsyncMock(return_value=0)
    
    user_id = "user_123"
    exchange = "binance"
    burst_key = f"{exchange}:{user_id}"
    
    # Add old timestamps (outside window)
    old_time = datetime.utcnow() - timedelta(seconds=20)
    pipeline.burst_counters[burst_key] = [old_time] * 10
    
    # Check limit - should pass because old timestamps are cleaned
    result = await pipeline._gate_c_trade_limiter(
        user_id=user_id,
        bot_id="bot_456",
        exchange=exchange
    )
    
    assert result["passed"] is True
    # Old timestamps should be cleaned
    assert len(pipeline.burst_counters[burst_key]) == 0


@pytest.mark.asyncio
async def test_record_fill_execution_calculates_slippage(mock_db, mock_ledger, order_pipeline_config):
    """Test that recording fill execution calculates actual slippage"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    # Mock pending order
    expected_price = 50000
    filled_price = 50100  # $100 slippage
    
    mock_order = {
        "order_id": "order_123",
        "user_id": "user_123",
        "bot_id": "bot_456",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "side": "buy",
        "price": expected_price,
        "is_paper": True,
        "execution_summary": {
            "fee_bps": 10.0,
            "slippage_bps": 10.0
        }
    }
    
    with patch.object(pipeline.pending_orders, 'find_one', new=AsyncMock(return_value=mock_order)), \
         patch.object(pipeline.pending_orders, 'update_one', new=AsyncMock()):
        
        result = await pipeline.record_fill_execution(
            order_id="order_123",
            filled_price=filled_price,
            filled_qty=0.01,
            actual_fee=0.5,
            fee_currency="USDT"
        )
        
        assert result["success"] is True
        assert "slippage_bps" in result
        
        # Calculate expected slippage in basis points
        expected_slippage_bps = abs((filled_price - expected_price) / expected_price * 10000)
        assert abs(result["slippage_bps"] - expected_slippage_bps) < 0.01


@pytest.mark.asyncio
async def test_record_fill_execution_calculates_actual_fees(mock_db, mock_ledger, order_pipeline_config):
    """Test that recording fill execution calculates actual fee percentage"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    filled_price = 50000
    filled_qty = 0.01
    actual_fee = 5.0  # $5 fee
    
    mock_order = {
        "order_id": "order_123",
        "user_id": "user_123",
        "bot_id": "bot_456",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "side": "buy",
        "price": filled_price,
        "is_paper": True,
        "execution_summary": {"fee_bps": 10.0}
    }
    
    with patch.object(pipeline.pending_orders, 'find_one', new=AsyncMock(return_value=mock_order)), \
         patch.object(pipeline.pending_orders, 'update_one', new=AsyncMock()):
        
        result = await pipeline.record_fill_execution(
            order_id="order_123",
            filled_price=filled_price,
            filled_qty=filled_qty,
            actual_fee=actual_fee,
            fee_currency="USDT"
        )
        
        assert result["success"] is True
        assert "actual_fee_bps" in result
        
        # Calculate expected fee in basis points
        notional_value = filled_price * filled_qty
        expected_fee_bps = (actual_fee / notional_value * 10000)
        assert abs(result["actual_fee_bps"] - expected_fee_bps) < 0.01


@pytest.mark.asyncio
async def test_record_fill_execution_stores_metadata_in_ledger(mock_db, mock_ledger, order_pipeline_config):
    """Test that fill execution stores comprehensive metadata"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    mock_order = {
        "order_id": "order_123",
        "user_id": "user_123",
        "bot_id": "bot_456",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "side": "buy",
        "price": 50000,
        "is_paper": True,
        "order_type": "market",
        "execution_summary": {
            "fee_bps": 10.0,
            "slippage_bps": 10.0
        },
        "gates_passed": ["idempotency", "fee_coverage", "trade_limiter", "circuit_breaker"]
    }
    
    with patch.object(pipeline.pending_orders, 'find_one', new=AsyncMock(return_value=mock_order)), \
         patch.object(pipeline.pending_orders, 'update_one', new=AsyncMock()):
        
        await pipeline.record_fill_execution(
            order_id="order_123",
            filled_price=50100,
            filled_qty=0.01,
            actual_fee=0.5,
            fee_currency="USDT",
            exchange_trade_id="exch_trade_789"
        )
        
        # Verify ledger.append_fill was called with metadata
        mock_ledger.append_fill.assert_called_once()
        call_kwargs = mock_ledger.append_fill.call_args[1]
        
        assert "metadata" in call_kwargs
        metadata = call_kwargs["metadata"]
        
        # Verify all required fields are in metadata
        assert "expected_price" in metadata
        assert "filled_price" in metadata
        assert "expected_fee_bps" in metadata
        assert "actual_fee_bps" in metadata
        assert "expected_slippage_bps" in metadata
        assert "actual_slippage_bps" in metadata
        assert "execution_summary" in metadata
        assert "order_type" in metadata
        assert "gates_passed" in metadata
        
        # Verify gate info is preserved
        assert metadata["gates_passed"] == ["idempotency", "fee_coverage", "trade_limiter", "circuit_breaker"]


@pytest.mark.asyncio
async def test_full_order_pipeline_with_all_gates(mock_db, mock_ledger, order_pipeline_config):
    """Test complete order submission through all gates"""
    from services.order_pipeline import OrderPipeline
    
    pipeline = OrderPipeline(mock_db, mock_ledger, order_pipeline_config)
    
    # Mock all required database operations
    with patch.object(pipeline.pending_orders, 'find_one', new=AsyncMock(return_value=None)), \
         patch.object(pipeline.pending_orders, 'insert_one', new=AsyncMock()), \
         patch.object(pipeline.circuit_breaker_state, 'find_one', new=AsyncMock(return_value=None)):
        
        result = await pipeline.submit_order(
            user_id="user_123",
            bot_id="bot_456",
            exchange="binance",
            symbol="BTC/USDT",
            side="buy",
            amount=0.01,
            order_type="market",
            is_paper=True
        )
        
        # Should pass all gates
        assert result["success"] is True
        assert "order_id" in result
        assert len(result["gates_passed"]) == 4
        assert "idempotency" in result["gates_passed"]
        assert "fee_coverage" in result["gates_passed"]
        assert "trade_limiter" in result["gates_passed"]
        assert "circuit_breaker" in result["gates_passed"]
        assert "execution_summary" in result
