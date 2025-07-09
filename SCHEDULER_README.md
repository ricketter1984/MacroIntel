# MacroIntel APScheduler Implementation

## Overview

The MacroIntel system now uses APScheduler to run the swarm pipeline automatically at specified times. This replaces the previous `schedule` library with a more robust and feature-rich scheduling solution.

## Features

- **Background Execution**: APScheduler runs in the background, allowing the system to continue operating
- **Timezone Support**: All schedules use Eastern Time (US/Eastern) for market-appropriate timing
- **Comprehensive Logging**: All scheduler activities are logged to files and console
- **Error Handling**: Robust error handling with graceful shutdown capabilities

## Scheduled Jobs

### 1. Morning Swarm Pipeline (07:30 ET)
- **Purpose**: Pre-market analysis and preparation
- **Function**: `run_swarm_pipeline()`
- **Timing**: 07:30 AM Eastern Time daily

### 2. Afternoon Swarm Pipeline (15:45 ET)
- **Purpose**: Pre-close analysis and end-of-day summary
- **Function**: `run_swarm_pipeline()`
- **Timing**: 15:45 PM Eastern Time daily (10 minutes before market close)

### 3. Daily Report (06:00 ET)
- **Purpose**: Comprehensive daily market analysis
- **Function**: `run_daily_report()`
- **Timing**: 06:00 AM Eastern Time daily

### 4. Hourly Market Analysis
- **Purpose**: Continuous market monitoring
- **Function**: `run_market_analysis()`
- **Timing**: Every hour on the hour (Eastern Time)

## Usage

### Starting the Scheduler

```bash
# Start the scheduler (default behavior)
python run_macrointel.py

# Or explicitly start the scheduler
python run_macrointel.py --scheduler
```

### Testing the Scheduler

```bash
# Test the scheduler setup and functionality
python test_scheduler.py
```

### Manual Execution

```bash
# Run a single swarm pipeline execution
python run_macrointel.py --swarm

# Run market analysis
python run_macrointel.py --analysis

# Generate a single report
python run_macrointel.py --report

# Run system tests
python run_macrointel.py --test
```

## Logging

All scheduler activities are logged to:
- **Console**: Real-time output with emojis for easy reading
- **File**: `logs/enhanced_macrointel.log` - Detailed logs for debugging
- **Test Logs**: `logs/scheduler_test.log` - Test-specific logs

### Log Format
```
2024-01-15 07:30:00 - __main__ - INFO - 🤖 Starting MacroIntel Swarm Pipeline...
2024-01-15 07:30:05 - __main__ - INFO - ✅ Swarm Pipeline Completed Successfully
2024-01-15 07:30:05 - __main__ - INFO -    📰 Articles Processed: 25
2024-01-15 07:30:05 - __main__ - INFO -    📈 Charts Generated: 8
```

## Dependencies

The scheduler requires these packages (already in requirements.txt):
- `apscheduler>=3.10.0`
- `pytz>=2025.2`

## Configuration

### Timezone
All schedules use Eastern Time (US/Eastern) to align with market hours:
```python
eastern_tz = pytz.timezone('US/Eastern')
```

### Job Configuration
Jobs are configured with:
- **Unique IDs**: Prevent duplicate jobs
- **Descriptive Names**: Easy identification in logs
- **Replace Existing**: Ensures clean restarts
- **Error Handling**: Graceful failure recovery

## Monitoring

### Check Scheduler Status
The scheduler provides real-time status updates:
- Job execution times
- Success/failure indicators
- Performance metrics
- Error details

### Stopping the Scheduler
- **Graceful Shutdown**: Press `Ctrl+C` for clean shutdown
- **Emergency Stop**: Kill the process (not recommended)

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path includes project root

2. **Timezone Issues**
   - Verify `pytz` is installed
   - Check system timezone settings

3. **Job Failures**
   - Check logs for detailed error messages
   - Verify API keys and network connectivity
   - Test individual components with `--test` flag

4. **Scheduler Not Starting**
   - Check for port conflicts
   - Verify file permissions for log directories
   - Test with `test_scheduler.py`

### Debug Mode
Enable detailed logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- **Memory Usage**: APScheduler is lightweight (~5MB)
- **CPU Usage**: Minimal overhead when idle
- **Network**: Only active during job execution
- **Storage**: Log files grow over time (rotate periodically)

## Security Notes

- API keys are loaded from environment variables
- Log files may contain sensitive data (rotate regularly)
- Scheduler runs with same permissions as the script

## Future Enhancements

- **Web Interface**: Dashboard for monitoring scheduler status
- **Dynamic Scheduling**: Adjust schedules based on market conditions
- **Alert System**: Notifications for job failures
- **Metrics Collection**: Performance monitoring and analytics 