# 📊 Crypto Monitoring & Analysis System

## 🎯 Use Case Overview

Platform AI-powered untuk monitoring dan analisis cryptocurrency yang memungkinkan:

* Real-time price monitoring dengan alert otomatis
* Analisis fundamental berbasis on-chain metrics dan sentiment
* Historical data analysis dengan custom indicators
* Portfolio management dengan risk monitoring
* Daily market summaries dan educational content

---

## 🧠 Business Requirements

1. **Trader Flow**
   * Setup custom price alerts berdasarkan technical indicators
   * Monitor real-time price movements via WebSocket
   * Receive multi-channel notifications (email, SMS, Discord)
   * View alert history dan performance metrics

2. **Investor Flow**
   * Request comprehensive fundamental analysis reports
   * Access on-chain metrics dan whale movements
   * View sentiment analysis dari social media
   * Generate scheduled reports (daily/weekly/monthly)

3. **Analyst Flow**
   * Access historical data dari multiple sources
   * Create custom technical indicators
   * Backtest trading strategies
   * Export analysis results dalam multiple formats

4. **Portfolio Manager Flow**
   * Monitor multiple portfolios dengan risk profiles
   * Receive risk alerts untuk allocation deviations
   * View rebalancing recommendations
   * Track performance attribution

5. **Enthusiast Flow**
   * Receive daily market digests
   * Access educational content dengan personalized learning paths
   * Participate in community discussions
   * Share dan discover crypto insights

---

## 🧰 Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11 + FastAPI |
| AI Framework | LangChain v1 (ReAct agents) |
| Database | PostgreSQL + TimescaleDB |
| Cache | Redis (Pub/Sub + caching) |
| WebSocket | FastAPI WebSocket + connection pooling |
| Task Queue | Celery + Redis broker |
| Analysis | pandas, TA-Lib, pandas-ta |
| NLP | transformers (HuggingFace) |
| Visualization | Plotly, ReportLab (PDF) |
| Frontend | React + TypeScript |

---

## 🧩 Entities

| Entity | Description |
|--------|-------------|
| User | System user dengan preferences |
| Alert | Alert configuration dengan thresholds |
| Portfolio | Collection of crypto positions |
| Position | Individual crypto holdings |
| Report | Generated analysis reports |
| Indicator | Custom technical indicators |
| Analysis | Historical analysis results |
| Notification | Sent alerts via channels |

---

## 🚏 API Endpoints (with Request/Response)

---

### 🔔 Alert Management

#### **POST /api/alerts**

**Request**
```json
{
  "userId": 1,
  "symbol": "BTC-USD",
  "condition": "PRICE_ABOVE",
  "threshold": 50000,
  "channels": ["EMAIL", "DISCORD"],
  "metadata": {
    "indicator": "RSI",
    "value": 70
  }
}
```

**Response**
```json
{
  "id": 101,
  "userId": 1,
  "symbol": "BTC-USD",
  "condition": "PRICE_ABOVE",
  "threshold": 50000,
  "status": "ACTIVE",
  "channels": ["EMAIL", "DISCORD"],
  "createdAt": "2025-11-13T10:30:00Z"
}
```

---

#### **GET /api/alerts/{userId}**

**Query params:** `status`, `symbol`, `from`, `to`

**Response**
```json
{
  "alerts": [
    {
      "id": 101,
      "symbol": "BTC-USD",
      "condition": "PRICE_ABOVE",
      "threshold": 50000,
      "status": "TRIGGERED",
      "triggeredAt": "2025-11-13T12:15:00Z"
    }
  ],
  "total": 15,
  "active": 8
}
```

---

#### **WebSocket /ws/alerts/{userId}**

**Subscription Message**
```json
{
  "action": "subscribe",
  "symbols": ["BTC-USD", "ETH-USD"]
}
```

**Alert Message**
```json
{
  "type": "ALERT_TRIGGERED",
  "alertId": 101,
  "symbol": "BTC-USD",
  "currentPrice": 50250,
  "threshold": 50000,
  "timestamp": "2025-11-13T12:15:30Z"
}
```

---

### 📈 Analysis & Reports

#### **POST /api/analysis/fundamental**

**Request**
```json
{
  "symbol": "BTC-USD",
  "sources": ["COINGECKO", "COINMARKETCAP", "ETHERSCAN"],
  "includeOnChain": true,
  "includeSentiment": true,
  "timeframe": "30d"
}
```

**Response**
```json
{
  "analysisId": "ANLYS-20251113-001",
  "symbol": "BTC-USD",
  "marketCap": 950000000000,
  "volume24h": 45000000000,
  "onChainMetrics": {
    "activeAddresses": 1000000,
    "whaleMovements": 15,
    "tvl": 25000000000
  },
  "sentiment": {
    "score": 0.72,
    "fearGreedIndex": 65,
    "socialVolume": 125000
  },
  "recommendation": "BUY",
  "confidence": 0.85,
  "generatedAt": "2025-11-13T10:45:00Z"
}
```

---

#### **POST /api/analysis/technical**

**Request**
```json
{
  "symbol": "ETH-USD",
  "indicators": ["RSI", "MACD", "BOLLINGER_BANDS"],
  "timeframes": ["1h", "4h", "1d"],
  "period": "90d"
}
```

**Response**
```json
{
  "symbol": "ETH-USD",
  "timeframe": "1d",
  "indicators": {
    "RSI": {
      "value": 58.5,
      "signal": "NEUTRAL"
    },
    "MACD": {
      "value": 125.3,
      "signal": 115.8,
      "histogram": 9.5,
      "trend": "BULLISH"
    },
    "BOLLINGER_BANDS": {
      "upper": 2850,
      "middle": 2750,
      "lower": 2650,
      "position": "NEAR_UPPER"
    }
  },
  "chartUrl": "https://cdn.example.com/charts/ETH-1d.png",
  "timestamp": "2025-11-13T11:00:00Z"
}
```

---

#### **POST /api/reports/generate**

**Request**
```json
{
  "userId": 1,
  "reportType": "COMPREHENSIVE",
  "symbols": ["BTC-USD", "ETH-USD"],
  "includeFundamental": true,
  "includeTechnical": true,
  "includeSentiment": true,
  "format": "PDF",
  "deliveryChannels": ["EMAIL"]
}
```

**Response**
```json
{
  "reportId": "RPT-20251113-001",
  "status": "GENERATING",
  "estimatedTime": 120,
  "downloadUrl": null,
  "notificationSent": false
}
```

---

### 📊 Portfolio Management

#### **POST /api/portfolios**

**Request**
```json
{
  "userId": 1,
  "name": "Conservative Portfolio",
  "riskProfile": "LOW",
  "targetAllocations": {
    "BTC-USD": 0.60,
    "ETH-USD": 0.30,
    "USDT": 0.10
  }
}
```

**Response**
```json
{
  "portfolioId": 501,
  "name": "Conservative Portfolio",
  "riskProfile": "LOW",
  "currentValue": 0,
  "positions": [],
  "createdAt": "2025-11-13T09:00:00Z"
}
```

---

#### **POST /api/portfolios/{portfolioId}/positions**

**Request**
```json
{
  "symbol": "BTC-USD",
  "quantity": 0.5,
  "entryPrice": 48000,
  "entryDate": "2025-11-01T10:00:00Z"
}
```

**Response**
```json
{
  "positionId": 1001,
  "portfolioId": 501,
  "symbol": "BTC-USD",
  "quantity": 0.5,
  "entryPrice": 48000,
  "currentPrice": 50250,
  "currentValue": 25125,
  "pnl": 1125,
  "pnlPercent": 4.69
}
```

---

#### **GET /api/portfolios/{portfolioId}/analysis**

**Response**
```json
{
  "portfolioId": 501,
  "totalValue": 100000,
  "totalPnL": 5000,
  "allocation": {
    "BTC-USD": 0.58,
    "ETH-USD": 0.32,
    "USDT": 0.10
  },
  "allocationDeviation": {
    "BTC-USD": -0.02,
    "ETH-USD": 0.02
  },
  "riskMetrics": {
    "var95": -8500,
    "maxDrawdown": -12.5,
    "sharpeRatio": 1.85,
    "volatility": 0.35
  },
  "rebalancingNeeded": false,
  "alerts": []
}
```

---

### 📚 Historical Data & Backtesting

#### **GET /api/data/historical**

**Query params:** `symbol`, `from`, `to`, `interval`, `source`

**Response**
```json
{
  "symbol": "BTC-USD",
  "interval": "1d",
  "source": "COINGECKO",
  "data": [
    {
      "timestamp": "2025-11-01T00:00:00Z",
      "open": 48000,
      "high": 49500,
      "low": 47800,
      "close": 49200,
      "volume": 28500000000
    }
  ],
  "dataPoints": 30
}
```

---

#### **POST /api/indicators/custom**

**Request**
```json
{
  "userId": 1,
  "name": "Custom RSI Divergence",
  "formula": "RSI(14) - RSI(28)",
  "description": "Dual RSI divergence indicator",
  "parameters": {
    "period1": 14,
    "period2": 28
  }
}
```

**Response**
```json
{
  "indicatorId": 301,
  "name": "Custom RSI Divergence",
  "formula": "RSI(14) - RSI(28)",
  "status": "ACTIVE",
  "createdAt": "2025-11-13T11:30:00Z"
}
```

---

#### **POST /api/backtest/strategy**

**Request**
```json
{
  "strategyName": "RSI Mean Reversion",
  "symbol": "BTC-USD",
  "period": "1y",
  "parameters": {
    "rsiPeriod": 14,
    "buyThreshold": 30,
    "sellThreshold": 70
  },
  "initialCapital": 10000
}
```

**Response**
```json
{
  "backtestId": "BT-20251113-001",
  "strategyName": "RSI Mean Reversion",
  "results": {
    "totalReturn": 0.45,
    "sharpeRatio": 1.92,
    "maxDrawdown": -0.18,
    "winRate": 0.62,
    "totalTrades": 48,
    "profitFactor": 2.15
  },
  "equityCurveUrl": "https://cdn.example.com/backtest/BT-20251113-001.png",
  "completedAt": "2025-11-13T11:45:00Z"
}
```

---

### 📰 Content & Community

#### **GET /api/content/daily-digest/{userId}**

**Response**
```json
{
  "userId": 1,
  "date": "2025-11-13",
  "marketOverview": {
    "summary": "Bitcoin reaches new all-time high above $50k",
    "sentiment": "BULLISH",
    "topMovers": [
      {
        "symbol": "BTC-USD",
        "change24h": 0.08
      }
    ]
  },
  "educationalContent": [
    {
      "id": 501,
      "title": "Understanding On-Chain Metrics",
      "type": "ARTICLE",
      "difficulty": "INTERMEDIATE",
      "url": "https://example.com/article/501"
    }
  ],
  "personalizedNews": [
    {
      "title": "Ethereum 2.0 upgrade progress",
      "source": "CoinDesk",
      "relevanceScore": 0.92,
      "url": "https://coindesk.com/article"
    }
  ]
}
```

---

#### **POST /api/community/posts**

**Request**
```json
{
  "userId": 1,
  "title": "BTC bullish divergence spotted",
  "content": "4h chart showing strong RSI divergence...",
  "tags": ["BTC", "TECHNICAL_ANALYSIS"],
  "attachments": ["https://cdn.example.com/chart.png"]
}
```

**Response**
```json
{
  "postId": 701,
  "userId": 1,
  "title": "BTC bullish divergence spotted",
  "upvotes": 0,
  "comments": 0,
  "visibility": "PUBLIC",
  "createdAt": "2025-11-13T12:00:00Z"
}
```

---

## 📦 Database Schema (simplified)

```sql
TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(100) UNIQUE,
  password_hash TEXT,
  preferences JSONB,
  created_at TIMESTAMP
);

TABLE alerts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  symbol VARCHAR(20),
  condition VARCHAR(50),
  threshold DECIMAL,
  status VARCHAR(20),
  channels TEXT[],
  triggered_at TIMESTAMP,
  created_at TIMESTAMP
);

TABLE portfolios (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  name VARCHAR(100),
  risk_profile VARCHAR(20),
  target_allocations JSONB,
  created_at TIMESTAMP
);

TABLE positions (
  id BIGSERIAL PRIMARY KEY,
  portfolio_id BIGINT REFERENCES portfolios(id),
  symbol VARCHAR(20),
  quantity DECIMAL,
  entry_price DECIMAL,
  entry_date TIMESTAMP
);

TABLE reports (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  report_type VARCHAR(50),
  symbols TEXT[],
  content JSONB,
  file_url TEXT,
  generated_at TIMESTAMP
);

TABLE custom_indicators (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  name VARCHAR(100),
  formula TEXT,
  parameters JSONB,
  created_at TIMESTAMP
);

TABLE price_history (
  symbol VARCHAR(20),
  timestamp TIMESTAMP,
  open DECIMAL,
  high DECIMAL,
  low DECIMAL,
  close DECIMAL,
  volume DECIMAL,
  PRIMARY KEY (symbol, timestamp)
) PARTITION BY RANGE (timestamp);
```

---

## 🧩 Response Pattern

All responses follow this pattern:

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-11-13T12:00:00Z"
}
```

or

```json
{
  "status": "error",
  "code": "INVALID_SYMBOL",
  "message": "Symbol BTC-INVALID not found",
  "timestamp": "2025-11-13T12:01:00Z"
}
```

---

## ✅ Success Metrics

| Metric | Target |
|--------|--------|
| Alert delivery latency | < 500 ms |
| WebSocket concurrent connections | 10,000+ |
| Report generation time | < 30 sec |
| API response time (p95) | < 200 ms |
| Backtest execution (1y data) | < 5 sec |
| System uptime | 99.9% |
| False alert rate | < 5% |

---

## 🔧 LangChain Agent Architecture

### ReAct Agent Tools

```python
# CoinGeckoTool - Market data
# CoinMarketCapTool - Rankings & quotes
# EtherscanTool - On-chain data
# TwitterTool - Social sentiment
# TechnicalAnalysisTool - Indicators
# BacktestTool - Strategy validation
```

### Agent Memory

```python
ConversationBufferWindowMemory(
  memory_key="chat_history",
  k=10  # Last 10 interactions
)
```

---

## 📡 WebSocket Infrastructure

### Connection Architecture
- Redis Pub/Sub for message broadcasting
- Connection pooling with failover
- Health monitoring & auto-reconnection
- Rate limiting per connection

### Message Types
- `PRICE_UPDATE` - Real-time price data
- `ALERT_TRIGGERED` - Alert notifications
- `PORTFOLIO_UPDATE` - Portfolio changes
- `ANALYSIS_COMPLETE` - Report ready

---

## 📁 Folder Structure

```
crypto-monitoring-system/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI application entry
│   │   ├── config.py                    # Environment & settings
│   │   │
│   │   ├── api/                         # API Routes
│   │   │   ├── __init__.py
│   │   │   ├── alerts.py
│   │   │   ├── analysis.py
│   │   │   ├── portfolio.py
│   │   │   ├── backtest.py
│   │   │   ├── content.py
│   │   │   └── community.py
│   │   │
│   │   ├── agents/                      # LangChain Agents
│   │   │   ├── __init__.py
│   │   │   ├── crypto_agent.py          # Base ReAct agent
│   │   │   ├── analysis_agent.py        # Analysis orchestrator
│   │   │   └── memory.py                # Conversation memory
│   │   │
│   │   ├── tools/                       # LangChain Tools
│   │   │   ├── __init__.py
│   │   │   ├── coingecko_tool.py
│   │   │   ├── coinmarketcap_tool.py
│   │   │   ├── etherscan_tool.py
│   │   │   ├── twitter_tool.py
│   │   │   └── technical_tool.py
│   │   │
│   │   ├── analysis/                    # Analysis Modules
│   │   │   ├── __init__.py
│   │   │   ├── fundamental.py           # Fundamental analysis chain
│   │   │   ├── technical.py             # Technical analysis chain
│   │   │   ├── onchain.py               # On-chain analysis
│   │   │   └── sentiment.py             # Sentiment analysis
│   │   │
│   │   ├── alerts/                      # Alert System
│   │   │   ├── __init__.py
│   │   │   ├── engine.py                # Alert evaluation engine
│   │   │   ├── notifier.py              # Multi-channel delivery
│   │   │   └── rules.py                 # Alert rule definitions
│   │   │
│   │   ├── portfolio/                   # Portfolio Management
│   │   │   ├── __init__.py
│   │   │   ├── manager.py               # Portfolio CRUD
│   │   │   ├── risk.py                  # Risk calculation
│   │   │   ├── rebalancing.py           # Rebalancing engine
│   │   │   └── optimizer.py             # Portfolio optimization
│   │   │
│   │   ├── backtesting/                 # Backtesting Engine
│   │   │   ├── __init__.py
│   │   │   ├── engine.py                # Backtest executor
│   │   │   ├── metrics.py               # Performance metrics
│   │   │   └── strategies/
│   │   │       ├── base.py
│   │   │       ├── rsi_strategy.py
│   │   │       └── macd_strategy.py
│   │   │
│   │   ├── indicators/                  # Technical Indicators
│   │   │   ├── __init__.py
│   │   │   ├── builder.py               # Custom indicator builder
│   │   │   ├── library.py               # Built-in indicators
│   │   │   └── calculator.py            # Calculation engine
│   │   │
│   │   ├── data/                        # Data Management
│   │   │   ├── __init__.py
│   │   │   ├── manager.py               # Data aggregation
│   │   │   ├── cache.py                 # Redis caching
│   │   │   └── validators.py            # Data validation
│   │   │
│   │   ├── reports/                     # Report Generation
│   │   │   ├── __init__.py
│   │   │   ├── generator.py             # Report builder
│   │   │   ├── templates/
│   │   │   │   ├── daily.html
│   │   │   │   ├── weekly.html
│   │   │   │   └── comprehensive.html
│   │   │   └── exporters/
│   │   │       ├── pdf_exporter.py
│   │   │       └── excel_exporter.py
│   │   │
│   │   ├── content/                     # Content Management
│   │   │   ├── __init__.py
│   │   │   ├── aggregator.py            # Content collection
│   │   │   ├── digest.py                # Daily digest generator
│   │   │   ├── education.py             # Educational content
│   │   │   └── personalization.py       # ML personalization
│   │   │
│   │   ├── community/                   # Community Features
│   │   │   ├── __init__.py
│   │   │   ├── platform.py              # Forum & discussions
│   │   │   ├── moderation.py            # Content moderation
│   │   │   └── engagement.py            # Tracking & analytics
│   │   │
│   │   ├── websocket/                   # WebSocket Infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── server.py                # WebSocket server
│   │   │   ├── manager.py               # Connection manager
│   │   │   ├── clients/
│   │   │   │   ├── coingecko_ws.py
│   │   │   │   └── exchange_ws.py
│   │   │   └── broadcaster.py           # Redis Pub/Sub
│   │   │
│   │   ├── visualization/               # Charts & Visualization
│   │   │   ├── __init__.py
│   │   │   ├── charts.py                # Plotly charts
│   │   │   └── patterns.py              # Pattern recognition
│   │   │
│   │   ├── models/                      # Database Models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── alert.py
│   │   │   ├── portfolio.py
│   │   │   ├── position.py
│   │   │   ├── report.py
│   │   │   └── indicator.py
│   │   │
│   │   ├── schemas/                     # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── alert_schema.py
│   │   │   ├── portfolio_schema.py
│   │   │   └── report_schema.py
│   │   │
│   │   ├── services/                    # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── alert_service.py
│   │   │   ├── portfolio_service.py
│   │   │   └── analysis_service.py
│   │   │
│   │   ├── integrations/                # External APIs
│   │   │   ├── __init__.py
│   │   │   ├── coingecko.py
│   │   │   ├── coinmarketcap.py
│   │   │   ├── etherscan.py
│   │   │   ├── twitter.py
│   │   │   ├── reddit.py
│   │   │   └── twilio.py
│   │   │
│   │   ├── tasks/                       # Celery Tasks
│   │   │   ├── __init__.py
│   │   │   ├── alert_tasks.py
│   │   │   ├── report_tasks.py
│   │   │   └── digest_tasks.py
│   │   │
│   │   └── utils/                       # Utilities
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       ├── security.py
│   │       ├── qrcode.py
│   │       └── helpers.py
│   │
│   ├── tests/                           # Test Suite
│   │   ├── __init__.py
│   │   ├── test_alerts/
│   │   │   ├── test_engine.py
│   │   │   └── test_notifier.py
│   │   ├── test_analysis/
│   │   ├── test_portfolio/
│   │   ├── test_backtesting/
│   │   └── load_tests/
│   │       └── locustfile.py
│   │
│   ├── migrations/                      # Alembic migrations
│   │   └── versions/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── Alerts/
│   │   │   │   ├── AlertList.tsx
│   │   │   │   ├── AlertForm.tsx
│   │   │   │   ├── AlertMetrics.tsx
│   │   │   │   └── AlertHistory.tsx
│   │   │   │
│   │   │   ├── Portfolio/
│   │   │   │   ├── PortfolioDashboard.tsx
│   │   │   │   ├── PortfolioChart.tsx
│   │   │   │   ├── PositionList.tsx
│   │   │   │   └── RiskMetrics.tsx
│   │   │   │
│   │   │   ├── Analysis/
│   │   │   │   ├── AnalysisPanel.tsx
│   │   │   │   ├── TechnicalChart.tsx
│   │   │   │   ├── FundamentalMetrics.tsx
│   │   │   │   └── SentimentGauge.tsx
│   │   │   │
│   │   │   ├── Research/
│   │   │   │   ├── ResearchInterface.tsx
│   │   │   │   ├── DataExplorer.tsx
│   │   │   │   ├── IndicatorBuilder.tsx
│   │   │   │   └── BacktestPanel.tsx
│   │   │   │
│   │   │   ├── Content/
│   │   │   │   ├── DailyDigest.tsx
│   │   │   │   ├── NewsCard.tsx
│   │   │   │   └── EducationModule.tsx
│   │   │   │
│   │   │   └── Community/
│   │   │       ├── ForumList.tsx
│   │   │       ├── PostCard.tsx
│   │   │       └── CommentSection.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useAlerts.ts
│   │   │   ├── usePortfolio.ts
│   │   │   └── useAnalysis.ts
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── websocket.ts
│   │   │   └── auth.ts
│   │   │
│   │   ├── store/                       # Redux/Zustand
│   │   │   ├── alertStore.ts
│   │   │   ├── portfolioStore.ts
│   │   │   └── userStore.ts
│   │   │
│   │   ├── utils/
│   │   │   ├── formatters.ts
│   │   │   └── validators.ts
│   │   │
│   │   ├── App.tsx
│   │   ├── index.tsx
│   │   └── routes.tsx
│   │
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docs/
│   ├── API.md
│   ├── SETUP.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
│
├── scripts/
│   ├── init_db.sh
│   ├── seed_data.py
│   └── deploy.sh
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
```