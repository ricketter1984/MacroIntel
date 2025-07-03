# MacroIntel Refactored System - API Dispatcher Integration

## Overview

The MacroIntel system has been successfully refactored to use the modular API dispatcher, eliminating urllib3 version conflicts and providing a robust, scheduled data fetching system.

## What Changed

### Before (Legacy System)
- Direct script execution with potential library conflicts
- urllib3 version conflicts between Benzinga (1.25.10) and Polygon (2.5.0)
- Manual scheduling and error handling
- Limited modularity

### After (Refactored System)
- ✅ **Isolated Virtual Environments**: Each API runs in its own venv
- ✅ **Subprocess Isolation**: No more library conflicts
- ✅ **Automated Scheduling**: Built-in job scheduler with configurable times
- ✅ **Comprehensive Logging**: All activities logged to `logs/dispatcher.log`
- ✅ **Error Handling**: Graceful error handling with email notifications
- ✅ **Modular Design**: Easy to add new API sources and tasks

## New File Structure

```
MacroIntel/
├── api_dispatcher.py              # Core dispatcher module
├── run_macrointel.py              # Refactored main entry point
├── scripts/
│   ├── fetch_benzinga_news.py     # Benzinga news fetcher
│   └── fetch_polygon_data.py      # Polygon data fetcher
├── test_refactored_system.py      # System test script
├── logs/
│   └── dispatcher.log             # Dispatcher activity log
├── output/                        # Data output directory
├── venv_benzinga/                 # Benzinga isolated environment
└── venv_polygon/                  # Polygon isolated environment
```

## Key Features

### 1. API Dispatcher Integration
- **Isolated Execution**: Each API runs in separate virtual environment
- **Automatic Setup**: Virtual environments created automatically
- **Error Recovery**: Robust error handling and logging
- **Resource Management**: Automatic cleanup of temporary files

### 2. Scheduled Data Fetching
- **Benzinga News**: 04:00 and 18:00 daily
- **Polygon Indices**: 12:00 daily
- **Continuous Operation**: 24/7 scheduler loop
- **Configurable Times**: Easy to modify schedule

### 3. Email Reporting
- **Success Notifications**: Email reports for successful fetches
- **Error Handling**: No emails sent for failed operations
- **Fallback System**: Placeholder messages if email module unavailable

### 4. Comprehensive Logging
- **File Logging**: All activities logged to `logs/dispatcher.log`
- **Console Output**: Real-time status updates
- **Error Tracking**: Detailed error information
- **Performance Monitoring**: Execution times and success rates

## Usage

### Basic Commands

```bash
# Test the system
python test_refactored_system.py

# Run all tasks immediately
python run_macrointel.py

# Run in scheduled mode (continuous)
python run_macrointel.py --schedule

# Test API dispatcher functionality
python run_macrointel.py --test

# Run individual tasks
python run_macrointel.py --benzinga
python run_macrointel.py --polygon
```

### Scheduled Mode

The system runs continuously in scheduled mode:

```bash
python run_macrointel.py --schedule
```

**Schedule:**
- 📰 **Benzinga News**: 04:00 and 18:00 daily
- 📊 **Polygon Indices**: 12:00 daily

### Testing

```bash
# Test system components
python test_refactored_system.py

# Test API dispatcher
python run_macrointel.py --test

# Test individual APIs
python run_macrointel.py --benzinga
python run_macrointel.py --polygon
```

## Configuration

### Environment Variables

Ensure these are set in `config/.env`:

```env
BENZINGA_API_KEY=your_benzinga_api_key
POLYGON_API_KEY=your_polygon_api_key
```

### Virtual Environments

The system automatically creates:
- `venv_benzinga/` with urllib3==1.25.10
- `venv_polygon/` with urllib3==2.5.0

### Logging

Logs are written to:
- `logs/dispatcher.log` - Main activity log
- Console output - Real-time status

## API Scripts

### Benzinga News Fetcher (`scripts/fetch_benzinga_news.py`)

**Features:**
- Keyword filtering for relevant news
- JSON output with timestamps
- Error handling and logging
- Automatic file saving

**Keywords:** Trump, Musk, oil, Nvidia, attack, Middle East, Fed, inflation, earnings

### Polygon Data Fetcher (`scripts/fetch_polygon_data.py`)

**Features:**
- Market indices and stock data
- Multiple symbol support
- Snapshot and news data
- Configurable data types

**Symbols:** AAPL, MSFT, GOOGL, AMZN, TSLA, SPY, QQQ, IWM, DIA, BTC-USD, ETH-USD, XAUUSD, XAGUSD

## Monitoring and Maintenance

### Log Monitoring

Check the dispatcher log for system status:

```bash
tail -f logs/dispatcher.log
```

### Output Files

Data is saved to the `output/` directory:
- `benzinga_news_YYYYMMDD_HHMMSS.json`
- `polygon_indices_YYYYMMDD_HHMMSS.json`
- `polygon_news_YYYYMMDD_HHMMSS.json`

### System Health

Monitor system health with:

```bash
# Check API status
python -c "from api_dispatcher import get_api_status; import json; print(json.dumps(get_api_status(), indent=2))"

# Test system
python test_refactored_system.py
```

## Troubleshooting

### Common Issues

1. **Virtual Environment Creation Fails**
   ```bash
   # Manual creation
   python -m venv venv_benzinga
   venv_benzinga\Scripts\activate
   pip install urllib3==1.25.10 requests python-dotenv
   ```

2. **API Key Errors**
   - Verify keys in `config/.env`
   - Check API key validity
   - Ensure environment variables are loaded

3. **Script Execution Fails**
   - Check script paths
   - Verify dependencies
   - Review error logs

4. **Scheduler Issues**
   - Check system time
   - Verify schedule library installation
   - Monitor log files

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Testing

Test individual components:

```bash
# Test Benzinga environment
venv_benzinga\Scripts\python.exe scripts/fetch_benzinga_news.py

# Test Polygon environment
venv_polygon\Scripts\python.exe scripts/fetch_polygon_data.py
```

## Extending the System

### Adding New API Sources

1. **Update API Dispatcher Configuration**
   ```python
   # In api_dispatcher.py, add to _load_config()
   "new_api": {
       "venv_path": self.project_root / "venv_new_api",
       "python_path": self.project_root / "venv_new_api" / "Scripts" / "python.exe",
       "requirements": ["urllib3==1.26.0", "requests", "new-api-client"],
       "env_vars": ["NEW_API_KEY"],
       "timeout": 300,
       "max_retries": 3
   }
   ```

2. **Create Script**
   ```bash
   # Create new script
   touch scripts/fetch_new_api_data.py
   ```

3. **Add Function to run_macrointel.py**
   ```python
   def fetch_new_api_data():
       return dispatch_api_task("new_api", "scripts/fetch_new_api_data.py")
   ```

4. **Schedule the Task**
   ```python
   # In setup_scheduler()
   schedule.every().day.at("14:00").do(fetch_new_api_data)
   ```

### Adding New Tasks

1. Create new script in `scripts/` directory
2. Add function to `run_macrointel.py`
3. Update scheduler configuration
4. Test with `--test` flag

## Performance Considerations

- **Virtual Environment Creation**: One-time setup (~30-60 seconds)
- **Subprocess Overhead**: ~100-500ms per API call
- **Memory Usage**: ~50-100MB per virtual environment
- **Disk Space**: ~200-500MB total for all environments

## Security Notes

- API keys loaded from environment variables only
- Temporary files automatically cleaned up
- Subprocess isolation prevents library conflicts
- No sensitive data logged

## Migration from Legacy System

### What's Different

1. **Entry Point**: Use `run_macrointel.py` instead of direct script execution
2. **Scheduling**: Built-in scheduler instead of external cron jobs
3. **Error Handling**: Automatic error handling and logging
4. **Isolation**: No more library conflicts

### Migration Steps

1. **Backup**: Backup existing data and configurations
2. **Test**: Run `test_refactored_system.py`
3. **Configure**: Set up API keys in `config/.env`
4. **Deploy**: Start with `python run_macrointel.py --test`
5. **Monitor**: Check logs and output files
6. **Schedule**: Enable scheduled mode when ready

## Support

For issues or questions:
1. Check the logs in `logs/dispatcher.log`
2. Run `test_refactored_system.py` for diagnostics
3. Review this documentation
4. Check API key validity and permissions

## License

This refactored system is part of the MacroIntel project and follows the same licensing terms. 