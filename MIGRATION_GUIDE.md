# Migration Guide: From daily_intel_engine.py to Agent Swarm

## Overview

The MacroIntel system has been upgraded from a monolithic `daily_intel_engine.py` to a modern Claude Flow agent swarm architecture. This guide explains the migration and new features.

## What Changed

### Old System: daily_intel_engine.py
- Single monolithic file with all functionality
- Basic error handling
- Limited modularity
- Simple logging

### New System: Agent Swarm
- Four specialized agents working in sequence
- Enhanced error handling and recovery
- Modular architecture for easy customization
- Comprehensive logging and monitoring
- Claude Flow integration for intelligent reasoning

## Migration Steps

### 1. Update Execution Commands

**Old:**
```bash
python daily_intel_engine.py
```

**New:**
```bash
# Execute immediately (default)
python agents/swarm_orchestrator.py

# Execute with detailed output
python agents/swarm_orchestrator.py --now

# Run in scheduled mode (daily at 7:15 AM)
python agents/swarm_orchestrator.py --schedule
```

### 2. New Agent Architecture

The functionality has been split into four specialized agents:

| Old Function | New Agent | Description |
|-------------|-----------|-------------|
| News fetching | 🧠 Summarizer Agent | Fetches from Benzinga, Messari, Polygon, FMP |
| Chart generation | 📈 Chart Generator Agent | Creates contextual visualizations |
| Strategy analysis | 📘 Playbook Strategist Agent | Analyzes market conditions and selects strategies |
| Email reporting | 📧 Email Dispatcher Agent | Builds and sends comprehensive reports |

### 3. Enhanced Features

#### Better Error Handling
- Each agent handles errors independently
- System continues even if individual agents fail
- Detailed error logging and recovery

#### Improved Logging
- Structured JSON logs in `/logs/` directory
- Execution timestamps and performance metrics
- Agent-specific log files

#### Modular Design
- Test individual agents: `python agents/test_swarm.py`
- Customize agent behavior independently
- Add new agents easily

## Configuration

### Environment Variables
No changes required - all existing environment variables are still used:

```bash
# API Keys (unchanged)
FMP_API_KEY=your_fmp_key
FEAR_GREED_API_KEY=your_fear_greed_key
BENZINGA_API_KEY=your_benzinga_key
MESSARI_API_KEY=your_messari_key
POLYGON_API_KEY=your_polygon_key

# Email Configuration (unchanged)
SMTP_USER=your_email
SMTP_PASSWORD=your_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

### Output Files
- **Charts**: Still saved to `/output/` directory
- **Logs**: Now saved to `/logs/` with enhanced structure
- **Reports**: Enhanced HTML emails with better formatting

## Testing the Migration

### 1. Test Individual Agents
```bash
python agents/test_swarm.py
```

### 2. Test Full Swarm
```bash
python agents/swarm_orchestrator.py --now
```

### 3. Verify Output
- Check `/logs/` for execution logs
- Verify email delivery
- Review generated charts in `/output/`

## Rollback Plan

If you need to temporarily use the old system:

1. The old `daily_intel_engine.py` is still available (marked as deprecated)
2. You can run it directly: `python daily_intel_engine.py`
3. All dependencies and configurations remain the same

## Benefits of the New System

### Performance
- Parallel processing capabilities
- Better resource utilization
- Faster execution times

### Reliability
- Agent isolation prevents cascading failures
- Automatic retry mechanisms
- Graceful degradation

### Maintainability
- Modular code structure
- Easy to add new features
- Better testing capabilities

### Monitoring
- Detailed execution metrics
- Agent-specific performance tracking
- Comprehensive logging

## Support

If you encounter issues during migration:

1. Check the logs in `/logs/` directory
2. Run the test suite: `python agents/test_swarm.py`
3. Verify all environment variables are set correctly
4. Review the agent-specific documentation in `/agents/README.md`

## Future Enhancements

The new agent swarm architecture enables future enhancements:

- Real-time market data streaming
- Advanced chart customization
- Multiple email templates
- Web dashboard integration
- API endpoints for external access
- Parallel agent execution
- Machine learning integration

## Timeline

- **Phase 1**: Migration to agent swarm (Current)
- **Phase 2**: Performance optimizations
- **Phase 3**: Advanced features and integrations
- **Phase 4**: Removal of deprecated `daily_intel_engine.py` 