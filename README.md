# MacroIntel

Advanced market intelligence and automated reporting system powered by Claude Flow agent swarm.

## Quick Start

```bash
# Easy startup script (recommended)
python run_macrointel.py

# Run the new default execution engine (replaces daily_intel_engine.py)
python agents/swarm_orchestrator.py

# Run with scheduling (daily at 7:15 AM)
python agents/swarm_orchestrator.py --schedule

# Execute immediately with detailed output
python agents/swarm_orchestrator.py --now

# Test individual agents
python agents/test_swarm.py

# Generate visual queries
python visual_query_tool.py --assets BTCUSD,XAUUSD,QQQ --condition "fear < 30"
```

### Startup Script Options

```bash
python run_macrointel.py                    # Run agent swarm immediately
python run_macrointel.py --schedule         # Run in scheduled mode (7:15 AM daily)
python run_macrointel.py --test             # Test individual agents
python run_macrointel.py --legacy           # Use legacy system
python run_macrointel.py --fear-greed       # Run Fear & Greed dashboard
```

## Features

- **🤖 Claude Flow Agent Swarm**: Four specialized agents working in sequence
- **🧠 News Summarization**: Multi-source news collection and analysis
- **📈 Chart Generation**: Contextual market visualizations
- **📘 Strategy Analysis**: Market regime analysis using Trading Playbook v7.0
- **📧 Email Reporting**: Comprehensive HTML reports with all insights
- **⏰ Automated Scheduling**: Daily execution at 7:15 AM

## Agent Swarm Architecture

The MacroIntel system now uses a Claude Flow agent swarm with four specialized agents:

1. **🧠 Summarizer Agent**: Fetches and summarizes news from Benzinga, Messari, Polygon, and FMP
2. **📈 Chart Generator Agent**: Creates contextual market visualizations using visual_query_engine.py
3. **📘 Playbook Strategist Agent**: Analyzes market conditions and selects trading strategies
4. **📧 Email Dispatcher Agent**: Builds and sends comprehensive HTML reports

### Workflow
```
Summarizer → Chart Generator → Playbook Strategist → Email Dispatcher
```

## Fear & Greed Dashboard

Advanced CNN Fear & Greed Index visualization and analysis.

### Usage

```
python fear_greed_dashboard.py --chart      # Generates 3x3 component chart PNG in /output/fear_components.png
python fear_greed_dashboard.py --report     # Generates Markdown report in /output/fear_components.md
python fear_greed_dashboard.py --report --html  # Generates HTML report in /output/fear_components.html
```

- Requires a valid `FEAR_GREED_API_KEY` in your `.env` file.
- All outputs are saved in the `output/` directory.

## Configuration

### Environment Variables

Ensure these environment variables are set in your `.env` file:

```bash
# API Keys
FMP_API_KEY=your_fmp_key
FEAR_GREED_API_KEY=your_fear_greed_key
BENZINGA_API_KEY=your_benzinga_key
MESSARI_API_KEY=your_messari_key
POLYGON_API_KEY=your_polygon_key

# Email Configuration
SMTP_USER=your_email
SMTP_PASSWORD=your_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

## Migration from daily_intel_engine.py

The new `agents/swarm_orchestrator.py` replaces `daily_intel_engine.py` as the default execution engine:

- **Old**: `python daily_intel_engine.py`
- **New**: `python agents/swarm_orchestrator.py`

All functionality has been preserved and enhanced through the agent swarm architecture.
