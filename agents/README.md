# MacroIntel Agent Swarm

A Claude Flow agent swarm for automated market intelligence and reporting.

## Overview

The MacroIntel Swarm consists of four specialized agents that work together to provide comprehensive market analysis and reporting:

### 🤖 Agents

1. **🧠 Summarizer Agent** (`summarizer_agent.py`)
   - Fetches news from Benzinga, Messari, Polygon, and FMP APIs
   - Summarizes articles with sentiment analysis
   - Outputs structured news data

2. **📈 Chart Generator Agent** (`chart_generator_agent.py`)
   - Analyzes market conditions (Fear & Greed Index)
   - Triggers `visual_query_engine.py` for contextual charts
   - Generates asset comparison and extreme fear charts

3. **📘 Playbook Strategist Agent** (`playbook_strategist_agent.py`)
   - Runs `playbook_interpreter.py` for market regime analysis
   - Selects viable trading strategies based on conditions
   - Identifies strategy disqualifiers

4. **📧 Email Dispatcher Agent** (`email_dispatcher_agent.py`)
   - Calls `email_report.py` to build comprehensive HTML reports
   - Sends daily intelligence reports to subscribers
   - Includes all agent outputs in final report

## Workflow

```
Summarizer → Chart Generator → Playbook Strategist → Email Dispatcher
```

Each agent passes its results downstream, creating a comprehensive market intelligence pipeline.

## Usage

### Individual Agent Testing

Test each agent independently:

```bash
# Test summarizer agent
python agents/summarizer_agent.py

# Test chart generator agent
python agents/chart_generator_agent.py

# Test playbook strategist agent
python agents/playbook_strategist_agent.py

# Test email dispatcher agent
python agents/email_dispatcher_agent.py
```

### Full Swarm Execution

Run the complete swarm workflow:

```bash
python agents/swarm_orchestrator.py
```

### Claude Flow Integration

The swarm is configured for Claude Flow with the following setup:

- **Model**: Claude-3-Haiku (for lightweight reasoning)
- **Workflow**: Sequential execution
- **Configuration**: `swarm_config.json`

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

### Output Files

- **Charts**: Saved to `/output/` directory
- **Logs**: Saved to `/logs/` directory
- **Reports**: Generated as HTML and sent via email

## Agent Output Schemas

### Summarizer Agent
```json
{
  "articles": [
    {
      "title": "Article title",
      "summary": "Article summary",
      "sentiment": "Bullish/Bearish/Neutral",
      "source": "benzinga/messari/polygon/fmp",
      "url": "Article URL",
      "timestamp": "ISO timestamp"
    }
  ],
  "total_count": 25,
  "sources_processed": ["benzinga", "messari"]
}
```

### Chart Generator Agent
```json
{
  "charts_generated": [
    {
      "chart_type": "extreme_fear",
      "file_path": "output/fear_chart.png",
      "description": "Chart description",
      "success": true
    }
  ],
  "analysis_summary": "Generated 2 charts based on market conditions"
}
```

### Playbook Strategist Agent
```json
{
  "market_regime": "BULLISH/NEUTRAL/BEARISH",
  "selected_strategies": [
    {
      "name": "Strategy name",
      "description": "Strategy description",
      "confidence": 0.85,
      "conditions": {}
    }
  ],
  "avoid_list": ["Strategy to avoid"],
  "macro_notes": "Macro analysis notes"
}
```

### Email Dispatcher Agent
```json
{
  "email_sent": true,
  "recipients": ["user@example.com"],
  "report_summary": "Daily MacroIntel report sent to 1 recipients",
  "attachments": []
}
```

## Error Handling

Each agent includes comprehensive error handling:
- API failures are logged and handled gracefully
- Missing data is replaced with defaults
- Execution continues even if individual components fail
- Detailed logging to `/logs/` directory

## Monitoring

Monitor swarm execution through:
- Console output with emoji indicators
- Log files in `/logs/` directory
- Email delivery confirmations
- Chart generation status

## Customization

### Adding New Agents

1. Create new agent file in `/agents/` directory
2. Implement `run()` method with proper input/output schemas
3. Update `swarm_config.json` with agent configuration
4. Add agent to `swarm_orchestrator.py`

### Modifying Agent Behavior

Each agent can be customized by:
- Modifying the agent's `run()` method
- Adjusting input/output schemas
- Adding new tools and capabilities
- Customizing error handling

## Troubleshooting

### Common Issues

1. **API Key Errors**: Check all API keys in `.env` file
2. **Import Errors**: Ensure all dependencies are installed
3. **Email Failures**: Verify SMTP configuration
4. **Chart Generation**: Check matplotlib and data availability

### Debug Mode

Enable debug logging by modifying the logging level in each agent:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Performance

- **Execution Time**: ~2-5 minutes for full swarm
- **Memory Usage**: ~100-200MB peak
- **API Calls**: ~10-20 calls per execution
- **Output Size**: ~1-5MB total (charts + reports)

## Security

- API keys stored in environment variables
- No sensitive data in logs
- Email credentials encrypted in transit
- Local file storage only

## Future Enhancements

- Parallel agent execution
- Real-time market data streaming
- Advanced chart customization
- Multiple email templates
- Web dashboard integration
- API endpoint for external access 