# Amarktai Network - Production Trading Platform

**Production-grade, plug-and-play deployment** for Ubuntu 24.04 with systemd + nginx. After `git pull`, `.env` setup, and restart, everything works in real-time.

## 🎯 Phase 1: Ledger-First Accounting (NEW!)

**Immutable ledger** for fills and events provides single source of truth for all accounting:
- ✅ **Fills Ledger**: Immutable trade execution records
- ✅ **Ledger Events**: Funding, transfers, allocations
- ✅ **Derived Metrics**: Equity, realized PnL, fees, drawdown
- ✅ **Endpoints**: `/api/portfolio/summary`, `/api/profits`, `/api/countdown/status`
- ✅ **Phase 1 Status**: Read-only + parallel write (opt-in)

See [Ledger Documentation](#ledger-first-accounting) below for details.

## ⚡ Quick Start (Ubuntu 24.04)

### One-Command Setup

```bash
# Run as root or with sudo
sudo ./deployment/vps-setup.sh
```

This idempotent script will:
- ✅ Install Python 3.12 (Ubuntu 24.04 default), Node.js 20.x, MongoDB
- ✅ Setup Python virtual environment with all dependencies
- ✅ Configure systemd service for auto-restart
- ✅ Setup nginx reverse proxy with CORS
- ✅ Create necessary directories and permissions

### Manual Configuration

After running the setup script:

1. **Edit `.env` file** with your configuration:
   ```bash
   sudo nano /var/amarktai/backend/.env
   ```
   
   **Required**:
   - `JWT_SECRET` - Generate with: `openssl rand -hex 32`
   - `MONGO_URL` - MongoDB connection string
   - `OPENAI_API_KEY` - For AI trading decisions
   
   **Optional (for SMTP reports)**:
   - `SMTP_USER` - Gmail address or SMTP username
   - `SMTP_PASSWORD` - App-specific password (not your Gmail password)
   - `DAILY_REPORT_TIME` - Time to send reports (e.g., "08:00" for 8 AM UTC)

2. **Restart services**:
   ```bash
   sudo systemctl restart amarktai-api
   sudo systemctl reload nginx
   ```

3. **Verify deployment**:
   ```bash
   cd /var/amarktai
   ./deployment/smoke_test.sh
   ```

### Access Your Platform

- **Web UI**: `http://YOUR_SERVER_IP`
- **API**: `http://YOUR_SERVER_IP/api`
- **Health Check**: `curl http://YOUR_SERVER_IP/api/health/ping`

### Optional: SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## 🏗️ Architecture
# Amarktai Network (Production-Ready)

Autonomous AI cryptocurrency trading system designed for **plug-and-play deployment** to Ubuntu 24.04 VPS.

- **Frontend**: Served by Nginx at `/`
- **Backend API**: Reverse-proxied under `/api`
- **WebSocket**: Real-time updates at `/api/ws`
- **SSE**: Server-sent events at `/api/realtime/events`
- **Static Assets**: Served from `frontend/public/assets/` as `/assets/...`

```
Client → Nginx (80/443) → FastAPI Backend (8000)
                       ↓
                   MongoDB (27017)
```

## 🚀 Features

### Trading
- **Paper Trading**: 95% realistic simulation with real market data
- **Live Trading**: Real exchange orders with full risk management
- **Multi-Exchange**: Support for LUNO, Binance, KuCoin, Kraken, VALR
- **Smart Budget Allocation**: Fair distribution across bots (floor(budget/N))
- **Rate Limiting**: Exchange-aware limits to prevent bans

### Bot Management
- **Pause/Resume**: Fine-grained control over individual or all bots
- **Cooldown Periods**: Custom trade intervals (5-120 minutes)
- **Lifecycle Management**: Automatic promotion from paper to live
- **Performance Tracking**: Real-time profit, win rate, trade count

### Autonomous Systems
- **Trading Scheduler**: Continuous staggered execution (24/7)
- **Autopilot Engine**: Auto-manages capital and bot spawning
- **AI Bodyguard**: Detects and pauses rogue bots
- **Self-Healing**: Automatic error recovery
- **AI Learning**: Learns from trade performance

### Real-Time Updates
- **WebSocket**: Instant notifications for trades, profits, bot status
- **Server-Sent Events**: Live price feeds, system metrics
- **Dashboard Sync**: Multi-device real-time synchronization

## 📚 Key Files

| File/Directory | Purpose |
|----------------|---------|
| `backend/server.py` | FastAPI application with lifespan management |
| `backend/engines/trade_budget_manager.py` | Fair budget allocation per exchange |
| `backend/routes/bot_lifecycle.py` | Bot pause/resume/cooldown endpoints |
| `deployment/quick_setup.sh` | Automated setup script |
| `deployment/amarktai-api.service` | Systemd service configuration |
| `deployment/nginx-amarktai.conf` | Nginx reverse proxy config |
| `deployment/smoke_test.sh` | Health check validation |
| `DEPLOYMENT.md` | Comprehensive deployment guide |
| `.env.example` | Environment configuration template |

## 🔌 API Endpoints

### Core
- `GET /api/health/ping` - Simple health check
- `GET /api/health/indicators` - Comprehensive health
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Bots
- `GET /api/bots` - List all bots
- `POST /api/bots` - Create bot
- `POST /api/bots/{id}/start` - Start bot trading
- `POST /api/bots/{id}/pause` - Pause bot
- `POST /api/bots/{id}/resume` - Resume bot
- `POST /api/bots/{id}/stop` - Stop bot permanently
- `POST /api/bots/{id}/cooldown` - Set cooldown (5-120 min)
- `GET /api/bots/{id}/status` - Detailed status with performance
- `POST /api/bots/pause-all` - Pause all user bots
- `POST /api/bots/resume-all` - Resume all user bots

### Dashboard & Analytics
- `GET /api/overview` - Dashboard overview
- `GET /api/profits?period=daily|weekly|monthly` - Profit breakdown
- `GET /api/countdown/status` - Countdown to R1M with projections
- `GET /api/portfolio/summary` - Complete portfolio metrics
- `GET /api/analytics/pnl_timeseries` - PnL timeseries (5m-1d intervals)
- `GET /api/analytics/capital_breakdown` - Funded vs realized vs unrealized
- `GET /api/analytics/performance_summary` - Win rate, profit factor

### Trading
- `GET /api/trades/recent` - Recent trades
- `GET /api/analytics/profit-history` - Profit history
- `GET /api/prices/live` - Live crypto prices

### API Keys (Encrypted Storage)
- `POST /api/keys/test` - Test API key before saving
- `POST /api/keys/save` - Save encrypted API key
- `GET /api/keys/list` - List saved keys (masked)
- `DELETE /api/keys/{provider}` - Delete API key

### Reports
- `POST /api/reports/daily/send-test` - Send test daily report
- `POST /api/reports/daily/send-all` - Send reports to all users (admin)
- `GET /api/reports/daily/config` - Get SMTP configuration

### System
- `GET /api/system/mode` - Get trading modes
- `PUT /api/system/mode` - Update trading modes
- `WS /api/ws` - WebSocket connection
- `GET /api/realtime/events` - SSE stream

Full API reference in [DEPLOYMENT.md](DEPLOYMENT.md).

## 🔒 Security

- ✅ JWT token authentication
- ✅ Encrypted API keys in MongoDB
- ✅ Per-user isolated data
- ✅ Rate limiting per exchange
- ✅ CORS protection
- ✅ CodeQL security scanning (0 vulnerabilities)

## 📊 Monitoring

```bash
# Check service status
sudo systemctl status amarktai-api

# View logs
sudo journalctl -u amarktai-api -f

# Run smoke tests
./deployment/smoke_test.sh
```

## 🛠️ Development

```bash
# Backend (Python)
cd backend
source venv/bin/activate
python -m uvicorn server:app --reload

# Frontend (if applicable)
cd frontend
npm install
npm run dev
```

## 📊 Ledger-First Accounting

### Phase 1: Read-Only + Parallel Write (Current)

**Status**: ✅ Implemented and deployed

#### Collections

1. **`fills_ledger`** - Immutable fill records
   - `fill_id`, `user_id`, `bot_id`
   - `exchange`, `symbol`, `side`, `qty`, `price`
   - `fee`, `fee_currency`
   - `timestamp`, `order_id`, `client_order_id`, `exchange_trade_id`
   - `is_paper` flag

2. **`ledger_events`** - Funding and allocation events
   - `event_id`, `user_id`, `bot_id`
   - `event_type` (funding, transfer, allocation, circuit_breaker)
   - `amount`, `currency`, `timestamp`
   - `description`, `metadata`

#### Endpoints

**Read-Only** (Phase 1):
```bash
# Portfolio summary (from ledger)
GET /api/portfolio/summary
# Returns: equity, realized_pnl, unrealized_pnl, fees_total, drawdown

# Profit time series
GET /api/profits?period=daily&limit=30
# Returns: Time series of profits by period

# Countdown to target
GET /api/countdown/status?target=1000000
# Returns: Equity-based projection to R1M goal

# Query fills
GET /api/ledger/fills?bot_id=xxx&since=2025-01-01T00:00:00Z&limit=100

# Audit trail
GET /api/ledger/audit-trail?bot_id=xxx&limit=100
```

**Append-Only** (Safe for Phase 1):
```bash
# Record funding event
POST /api/ledger/funding
{
  "amount": 10000,
  "currency": "USDT",
  "description": "Initial capital"
}
```

#### Service API

```python
from services.ledger_service import get_ledger_service

ledger = get_ledger_service(db)

# Append fill (immutable)
fill_id = await ledger.append_fill(
    user_id="user_1",
    bot_id="bot_1",
    exchange="binance",
    symbol="BTC/USDT",
    side="buy",
    qty=0.01,
    price=50000,
    fee=0.5,
    fee_currency="USDT",
    timestamp=datetime.utcnow(),
    order_id="order_123"
)

# Compute metrics
equity = await ledger.compute_equity(user_id)
realized_pnl = await ledger.compute_realized_pnl(user_id)
fees_paid = await ledger.compute_fees_paid(user_id)
current_dd, max_dd = await ledger.compute_drawdown(user_id)
```

#### Testing

```bash
# Run ledger tests
cd backend
source venv/bin/activate
python -m pytest tests/test_ledger_phase1.py -v

# Tests cover:
# - Immutable fill appending
# - FIFO PnL calculation
# - Fee aggregation
# - Drawdown calculation
# - Profit series generation
# - API contract validation
```

#### Phase 1 Principles

1. **Immutable**: Fills never updated, only appended
2. **Parallel**: Works alongside existing `trades` collection
3. **Opt-in**: New code uses ledger, old code unaffected
4. **Read-only**: Endpoints are safe to deploy
5. **Deterministic**: Math is reproducible and testable

#### Next: Phase 2 (Execution Guardrails)

Phase 2 will add:
- Order pipeline with 4 gates
- Idempotency protection
- Fee coverage checks
- Trade limiters
- Circuit breaker

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📝 License

[Your License Here]

## 🆘 Support

- **Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: GitHub Issues
- **Logs**: `sudo journalctl -u amarktai-api -n 100`

---

**Version**: 3.1.0 - Phase 1 (Ledger-First Accounting)  
**Last Updated**: December 2025
## 🚀 Quick Start (VPS Deployment)

This repository is production-ready with automated setup:

```bash
# 1. Clone repository
git clone YOUR_REPO_URL /var/amarktai/app
cd /var/amarktai/app

# 2. Run automated setup script
sudo bash deployment/vps-setup.sh

# 3. Configure environment variables
sudo nano /var/amarktai/app/backend/.env
# Set: OPENAI_API_KEY, JWT_SECRET, ADMIN_PASSWORD

# 4. Restart service
sudo systemctl restart amarktai-api

# 5. Access dashboard
# Open http://YOUR_SERVER_IP in browser
```

## 📋 Requirements

- **OS**: Ubuntu 24.04 LTS
- **RAM**: 2GB minimum (4GB recommended)
- **CPU**: 2 cores minimum
- **Disk**: 20GB minimum
- **Network**: Public IP address
- **Ports**: 80 (HTTP), 443 (HTTPS), 22 (SSH)

## 🏗️ Architecture

```
/var/amarktai/app/
├── backend/           # FastAPI backend (port 8000)
├── frontend/build/    # React frontend (served by nginx)
└── deployment/        # Config files
    ├── nginx/         # Nginx reverse proxy config
    └── systemd/       # Systemd service unit
```

### Path Layout

- **Backend**: `/var/amarktai/app/backend` (Python 3.11, FastAPI, MongoDB)
- **Frontend**: `/var/amarktai/app/frontend/build` (React, served by nginx)
- **MongoDB**: Docker container on `127.0.0.1:27017`
- **API**: Proxied by nginx at `/api/*`
- **WebSocket**: `/api/ws`
- **SSE (Real-time)**: `/api/realtime/*`

## 🔧 Configuration

### Environment Variables (.env)

Copy `.env.example` to `/var/amarktai/app/backend/.env` and configure:

```bash
# Database
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB_NAME=amarktai

# Security (CHANGE THESE!)
JWT_SECRET=<generate with: openssl rand -hex 32>
ADMIN_PASSWORD=<generate with: openssl rand -base64 24>

# AI Features
OPENAI_API_KEY=<your OpenAI API key>

# Email (Optional)
SMTP_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=

# Trading Limits
MAX_BOTS=10
MAX_DAILY_LOSS_PERCENT=5

# Features
ENABLE_REALTIME=true
```

### Nginx Configuration

Nginx serves the frontend and proxies API requests:

- **Frontend**: Served from `/var/amarktai/app/frontend/build`
- **API**: Proxied to `http://127.0.0.1:8000/api/`
- **WebSocket**: Upgraded connections on `/api/ws`
- **SSE**: Long-polling disabled for `/api/realtime/`

Config location: `/etc/nginx/sites-available/amarktai`

### Systemd Service

Backend runs as a systemd service:

```bash
# Status
sudo systemctl status amarktai-api

# Logs
sudo journalctl -u amarktai-api -f

# Restart
sudo systemctl restart amarktai-api
```

## ✅ Verification

After setup, verify installation:

```bash
# 1. Check service is running
systemctl status amarktai-api

# 2. Check backend is listening
ss -lntp | grep :8000

# 3. Test health endpoint
curl -i http://127.0.0.1:8000/api/health/ping

# 4. Check API routes
curl http://127.0.0.1:8000/openapi.json | jq '.paths | keys[]'

# 5. Test SSE streaming
curl -N http://127.0.0.1:8000/api/realtime/events

# 6. Run smoke tests
cd /var/amarktai/app/deployment
bash smoke_test.sh
```

## 🔐 Security

### Production Checklist

- [ ] Change `JWT_SECRET` (use `openssl rand -hex 32`)
- [ ] Change `ADMIN_PASSWORD` (use `openssl rand -base64 24`)
- [ ] Set up SSL/TLS with certbot
- [ ] Configure firewall (UFW)
- [ ] Restrict MongoDB to localhost only
- [ ] Review CORS settings in backend
- [ ] Enable rate limiting (optional)
- [ ] Set up automated backups

### SSL Setup (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## 🎯 Features

### Trading Modes

- **Paper Trading**: Safe simulation with virtual funds
- **Live Trading**: Real trading with exchange APIs (requires 7-day paper training)
- **Autopilot**: Automated bot management and capital allocation

### AI Features

- **ChatOps**: Natural language dashboard control
- **Risk Management**: Automated stop-loss, take-profit, trailing stops
- **Self-Learning**: Performance analysis and strategy optimization
- **Market Intelligence**: Real-time market analysis and sentiment

### Supported Exchanges

- Luno (ZAR pairs)
- Binance
- KuCoin
- Kraken
- VALR

## 🛠️ Maintenance

### Updating

```bash
cd /var/amarktai/app
git pull
sudo systemctl restart amarktai-api
```

### Backup Database

```bash
docker exec amarktai-mongo mongodump --out /data/backup
docker cp amarktai-mongo:/data/backup ./mongo-backup-$(date +%Y%m%d)
```

### Logs

```bash
# Backend logs
sudo journalctl -u amarktai-api -n 100

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# MongoDB logs
docker logs amarktai-mongo
```

## 📚 API Documentation

Once running, access interactive API docs:

- **Swagger UI**: `http://YOUR_SERVER_IP/docs`
- **ReDoc**: `http://YOUR_SERVER_IP/redoc`
- **OpenAPI JSON**: `http://YOUR_SERVER_IP/openapi.json`

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u amarktai-api -n 50

# Check MongoDB
docker ps | grep amarktai-mongo

# Check .env file
cat /var/amarktai/app/backend/.env
```

### Frontend Not Loading

```bash
# Check nginx
sudo nginx -t
sudo systemctl status nginx

# Check build exists
ls -la /var/amarktai/app/frontend/build
```

### Database Connection Error

```bash
# Check MongoDB is running
docker ps | grep amarktai-mongo

# Test connection
docker exec amarktai-mongo mongosh --eval "db.adminCommand('ping')"
```

## 📞 Support

For issues and questions:

1. Check logs: `journalctl -u amarktai-api -f`
2. Review configuration: `.env` and nginx config
3. Run smoke tests: `bash deployment/smoke_test.sh`

## 📄 License

All rights reserved.
