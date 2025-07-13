# MacroIntel Google Calendar Sync

Automatically sync important economic events from Financial Modeling Prep (FMP) to Google Calendar with OAuth 2.0 authentication.

## Features

- **OAuth 2.0 Authentication**: Secure integration with Google Calendar API
- **Dedicated Calendar**: Creates/manages a separate "MacroIntel Economic Events" calendar
- **Smart Filtering**: Focuses on high-impact events (CPI, FOMC, GDP, NFP, PPI, PMI, EIA)
- **Duplicate Prevention**: Avoids creating duplicate events using intelligent key matching
- **Comprehensive Logging**: Tracks all synced events in `logs/calendar_events_log.json`
- **Error Handling**: Graceful failure handling with detailed error messages
- **CLI Interface**: Simple command-line tools for sync and testing

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements_google_calendar.txt
```

### 2. Setup Google Calendar API

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Calendar API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the credentials JSON file

4. **Install Credentials**:
   ```bash
   # Place the downloaded file in config/
   mv ~/Downloads/credentials.json config/credentials.json
   ```

### 3. Setup FMP API Key

Ensure your `.env` file contains your FMP API key:

```env
FMP_API_KEY=your_fmp_api_key_here
```

## Usage

### Basic Sync Command

```bash
# Sync events for the next 7 days
python calendar_google_sync.py --sync

# Sync events for the next 14 days
python calendar_google_sync.py --sync --days 14
```

### Test Authentication

```bash
# Test Google Calendar authentication
python calendar_google_sync.py --test
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sync` | Sync FMP economic events to Google Calendar | - |
| `--days DAYS` | Number of days forward to sync | 7 |
| `--test` | Test authentication without syncing | - |

## Event Filtering

The system automatically filters for important economic indicators:

### High Priority Events
- **CPI** (Consumer Price Index)
- **FOMC** (Federal Open Market Committee)
- **GDP** (Gross Domestic Product)
- **NFP** (Non-Farm Payrolls)
- **PPI** (Producer Price Index)
- **PMI** (Purchasing Managers' Index)
- **EIA** (Energy Information Administration)

### Additional Criteria
- All "High" impact events regardless of type
- "Medium" impact events from major economies (US, EU, UK, JP, CN, DE, FR)
- Central bank decisions and interest rate announcements
- Employment and inflation data

## Calendar Event Format

Each synced event includes:

### Title Format
```
[Event Type] - Country - Impact Level
```

### Description Content
- Economic event name
- Country/region
- Impact level (High/Medium/Low)
- Currency affected
- Actual/Estimate/Previous values (when available)
- Data source attribution

### Event Settings
- **Duration**: 30 minutes
- **Timezone**: America/New_York
- **Reminders**: 15-minute popup reminder
- **Calendar**: Dedicated "MacroIntel Economic Events" calendar

## Duplicate Prevention

The system prevents duplicate events using composite keys:
- Event date
- Event time
- Event name
- Country

Previously synced events are tracked in `logs/calendar_events_log.json`.

## Logging and Monitoring

### Log Files

1. **Calendar Sync Log**: `logs/calendar_sync.log`
   - Real-time sync progress
   - API responses and errors
   - Authentication status

2. **Events Log**: `logs/calendar_events_log.json`
   - Complete history of synced events
   - Sync session metadata
   - Event deduplication keys

### Log Example

```json
{
  "events": [
    {
      "event_key": "2024-01-15_14:30_us_cpi_data_us",
      "event_name": "US CPI Data",
      "country": "US",
      "date": "2024-01-15",
      "time": "14:30",
      "impact": "High",
      "synced_at": "2024-01-14T10:30:00.123456"
    }
  ],
  "sync_history": [
    {
      "timestamp": "2024-01-14T10:30:00.123456",
      "events_synced": 5,
      "events": [...]
    }
  ]
}
```

## Error Handling

### Common Issues and Solutions

#### 1. Missing Credentials
```
ERROR: credentials.json not found at config/credentials.json
```
**Solution**: Download OAuth 2.0 credentials from Google Cloud Console

#### 2. FMP API Key Missing
```
ERROR: FMP_API_KEY not found in environment variables
```
**Solution**: Add FMP_API_KEY to your `.env` file

#### 3. Google API Libraries Missing
```
ERROR: Google API libraries not available
```
**Solution**: `pip install -r requirements_google_calendar.txt`

#### 4. OAuth Permission Issues
```
ERROR: OAuth 2.0 authentication failed
```
**Solutions**:
- Check credentials.json is valid
- Ensure Calendar API is enabled in Google Cloud Console
- Delete `config/token.json` and re-authenticate

#### 5. Calendar API Quota Exceeded
```
ERROR: Google Calendar API error: Quota exceeded
```
**Solution**: Wait for quota reset or request quota increase

### Graceful Failures

The system handles failures gracefully:
- Network timeouts with automatic retries
- Invalid event data with detailed logging
- Missing optional fields with default values
- API rate limits with appropriate delays

## Automation

### Scheduled Sync

Set up automated syncing using cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Daily sync at 8 AM
0 8 * * * cd /path/to/MacroIntel && python calendar_google_sync.py --sync
```

### Integration with MacroIntel

Add to your daily workflow:

```bash
# In your existing automation scripts
python calendar_google_sync.py --sync --days 7
```

## Security Considerations

1. **Credentials Storage**: OAuth tokens are stored locally in `config/token.json`
2. **API Keys**: FMP API key is read from environment variables only
3. **Permissions**: Requests minimal calendar access scope
4. **Data Privacy**: No economic data is stored permanently

## Troubleshooting

### Debug Mode

Enable detailed logging by setting log level:

```python
# In calendar_google_sync.py, modify logging level
logging.basicConfig(level=logging.DEBUG, ...)
```

### Test Components

```bash
# Test individual components
python -c "from calendar_google_sync import GoogleCalendarSync; sync = GoogleCalendarSync(); print('Dependencies OK')"

# Test FMP API connectivity
python -c "import os, requests; print(requests.get(f'https://financialmodelingprep.com/api/v3/economic_calendar?apikey={os.getenv(\"FMP_API_KEY\")}').status_code)"
```

### File Structure

```
MacroIntel/
├── calendar_google_sync.py          # Main sync module
├── requirements_google_calendar.txt  # Dependencies
├── config/
│   ├── credentials.json             # OAuth credentials (you provide)
│   └── token.json                   # Generated OAuth token
└── logs/
    ├── calendar_sync.log            # Sync operation logs
    └── calendar_events_log.json     # Event history
```

## API Limits and Quotas

### Google Calendar API
- **Daily Quota**: 1,000,000 requests/day
- **Per User Rate Limit**: 250 requests/100 seconds
- **Concurrent Requests**: 10 per second

### FMP API
- **Rate Limits**: Vary by subscription tier
- **Daily Calls**: Check your FMP plan limits

## Support

For issues and feature requests:
1. Check the logs in `logs/calendar_sync.log`
2. Verify all dependencies are installed
3. Ensure API credentials are properly configured
4. Review the troubleshooting section above

## License

This module is part of the MacroIntel project and follows the same licensing terms. 