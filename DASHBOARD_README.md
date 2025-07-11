# MacroIntel Dashboard

Real-time Streamlit web application for comprehensive financial market analysis and monitoring.

## 🎯 Features

### 📊 Live Market Overview
- **Watchlist Tracking**: Real-time performance metrics for customizable asset list
- **Performance Charts**: Interactive visualizations with multiple timeframes
- **Sentiment Analysis**: Bullish/Bearish/Neutral indicators based on market data
- **Volatility Metrics**: Low/Moderate/High classification with daily calculations

### 📅 Economic Calendar
- **FMP API Integration**: Live economic events from Financial Modeling Prep
- **Event Filtering**: High/Medium/Low impact classification
- **Timeline View**: Next 7 days of scheduled releases
- **Impact Analysis**: Visual distribution of event importance

### 📈 Interactive Charts
- **Performance Comparison**: Normalized returns across assets
- **Volatility Analysis**: Daily volatility rankings and trends
- **Correlation Matrix**: Asset correlation heatmaps
- **Volume Analysis**: Trading volume patterns and anomalies

### 🎯 Regime Analysis
- **Market Regime Score**: Current market environment classification
- **Strategy Recommendations**: Tier-based investment strategies
- **Component Breakdown**: Fear & Greed, VIX, and macro factors
- **Historical Context**: Regime strength and directional indicators

### 📰 News Integration
- **Real-time Headlines**: Latest market-moving news
- **Sentiment Classification**: AI-powered sentiment analysis
- **Source Attribution**: Multi-source news aggregation
- **Geopolitical Tracking**: Trade war and policy impact monitoring

### 🔄 Automation Features
- **Auto-refresh**: Configurable 10-minute data updates
- **Desktop Notifications**: Optional alerts for significant market moves
- **Background Polling**: Continuous data monitoring
- **Caching System**: Optimized performance with intelligent data caching

## 🚀 Quick Start

### Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_dashboard.txt
   ```

2. **Configure Environment**:
   - Add `FMP_API_KEY` to `config/.env` for economic calendar
   - Ensure MacroIntel core modules are available

3. **Launch Dashboard**:
   ```bash
   python launch_dashboard.py
   ```
   
   Or directly with Streamlit:
   ```bash
   streamlit run dashboard_app.py
   ```

### Alternative Launch Options

```bash
# Custom port
python launch_dashboard.py --port 8502

# No auto-browser opening
python launch_dashboard.py --no-browser

# Show detailed help
python launch_dashboard.py --help
```

## 📋 Requirements

### Core Dependencies
- `streamlit>=1.28.0` - Web application framework
- `plotly>=5.17.0` - Interactive charting
- `pandas>=2.1.0` - Data manipulation
- `yfinance>=0.2.0` - Financial data API
- `requests>=2.31.0` - HTTP requests

### Optional Dependencies
- `plyer>=2.1.0` - Desktop notifications
- `python-dotenv>=1.0.0` - Environment configuration

### MacroIntel Integration
- `calendar_tracker.py` - Economic calendar functionality
- `core.email_report` - Ticker data and regime analysis
- `core.enhanced_visualizations` - Chart generation
- `agents.summarizer_agent` - News analysis (optional)

## 🎛️ Dashboard Layout

### Sidebar Controls
- **Auto Refresh Toggle**: Enable/disable 10-minute updates
- **Manual Refresh**: Force immediate data update
- **Desktop Notifications**: Enable system notifications
- **Watchlist Customization**: Add/remove ticker symbols
- **API Status Indicators**: Real-time connectivity monitoring

### Main Tabs

#### 📊 Overview Tab
- Live watchlist with performance metrics
- Summary statistics (gainers, losers, volatility)
- Interactive performance bar chart
- Real-time price and sentiment data

#### 📅 Calendar Tab
- Economic events timeline
- Impact level distribution
- Country and event filtering
- High-priority event highlighting

#### 📈 Charts Tab
- Multi-asset performance comparison
- Volatility ranking analysis
- Correlation heatmaps
- Volume pattern analysis

#### 🎯 Regime Tab
- Current regime score and classification
- Strategy tier recommendations
- Component breakdown analysis
- Fear & Greed and VIX integration

#### 📰 News Tab
- Recent headlines with sentiment
- Source attribution and timestamps
- Bullish/bearish/neutral classification
- Geopolitical event tracking

## ⚙️ Configuration

### Environment Variables
```bash
# Required for economic calendar
FMP_API_KEY=your_fmp_api_key

# Optional features
TICKER_CARDS_ENABLED=true
NOTIFICATIONS_ENABLED=false
```

### Default Watchlist
```python
["SPY", "QQQ", "IWM", "GLD", "TLT", "VIX", "AAPL", "TSLA", "NVDA", "MSFT", "BTC-USD", "DXY"]
```

### Data Sources
- **Primary**: yfinance for real-time market data
- **Secondary**: FMP API for economic calendar and fallback data
- **Local**: MacroIntel regime scores and news analysis

## 🔔 Notifications

When enabled, the dashboard provides desktop notifications for:
- Significant market moves (>3% daily change)
- High-impact economic events
- Data refresh completion
- System status changes

## 🛠️ Troubleshooting

### Common Issues

1. **Dependencies Missing**:
   ```bash
   pip install -r requirements_dashboard.txt
   ```

2. **Economic Calendar Not Loading**:
   - Verify `FMP_API_KEY` in `config/.env`
   - Check FMP API quota and connectivity

3. **Charts Not Displaying**:
   - Ensure yfinance connectivity
   - Check ticker symbol validity
   - Verify plotly installation

4. **Port Already in Use**:
   ```bash
   python launch_dashboard.py --port 8502
   ```

5. **MacroIntel Modules Missing**:
   - Ensure `dashboard_app.py` is in MacroIntel root directory
   - Verify core modules are available
   - Check Python path configuration

### Performance Optimization

- **Caching**: Data is cached for 15-30 minutes to reduce API calls
- **Lazy Loading**: Charts load on-demand when tabs are selected
- **Background Updates**: Auto-refresh runs in background threads
- **Error Handling**: Graceful fallbacks for failed API calls

## 🎨 Design System

The dashboard uses a consistent design system matching the MacroIntel email reports:

- **Color Scheme**: Dark gradients with professional styling
- **Typography**: Clean, readable fonts with proper hierarchy
- **Layout**: Responsive grid system for various screen sizes
- **Indicators**: Color-coded status and performance indicators
- **Cards**: Glassmorphism design for data containers

## 📊 Data Flow

1. **Initialization**: Dashboard loads with cached data if available
2. **Real-time Updates**: Background polling every 10 minutes (configurable)
3. **User Interactions**: Manual refresh and watchlist customization
4. **Notifications**: Desktop alerts for significant events
5. **Caching**: Intelligent data retention for performance optimization

## 🔮 Future Enhancements

- Real-time WebSocket data feeds
- Custom alert thresholds
- Portfolio tracking integration
- Advanced charting with technical indicators
- Export functionality for reports and data
- Mobile-responsive design improvements
- Multi-user support and personalization

## 📄 License

Part of the MacroIntel financial analysis system.

## 🤝 Contributing

Please refer to the main MacroIntel documentation for contribution guidelines.

---

**Note**: This dashboard requires an active internet connection for real-time data and API access. Some features may be limited without proper API key configuration. 