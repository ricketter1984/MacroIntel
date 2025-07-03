# Regime-Aware Visual Query Tool

## Overview

The `visual_query_tool.py` has been enhanced to support regime-aware conditions, allowing users to filter asset visual generation based on the Daily Market Regime Score from Playbook v7.1. This integration provides intelligent, data-driven decision making for chart generation.

## New Features

### 1. Regime Score Integration
- **Automatic Loading**: Loads the most recent regime score from `output/regime_score_*.json`
- **Graceful Fallback**: Continues operation if no regime score file is present
- **Real-time Context**: Displays current regime score and strategy recommendation

### 2. Regime-Aware Conditions
The tool now supports sophisticated condition parsing for:

#### Regime Score Conditions
```bash
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "regime > 65"
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "regime < 80"
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "regime == 75"
```

#### Strategy Conditions
```bash
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "strategy == 'Tier 1'"
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "strategy in ['Tier 1', 'Tier 2']"
```

#### Asset Conditions
```bash
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "asset == 'MYM'"
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "asset in ['MYM', 'MES']"
```

#### Classification Conditions
```bash
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "classification == 'Bullish'"
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "classification == 'Bearish'"
```

#### Risk Allocation Conditions
```bash
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "risk > 20"
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "risk < 30"
```

### 3. Enhanced CLI Options

#### New Flags
- `--email`: Send results by email with chart attachment
- `--save`: Save chart with timestamp in filename
- Enhanced `--condition`: Supports both legacy and regime-aware conditions

#### Usage Examples
```bash
# Basic regime-aware query
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "regime > 70"

# Strategy-based query with email
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "strategy == 'Tier 1'" --email --save

# Asset-specific query with export
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "asset in ['MYM', 'MES']" --export csv --save

# Risk-based query
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "risk > 25" --save
```

### 4. Email Integration
- **Automatic Attachment**: Charts are automatically attached to emails
- **Professional Formatting**: HTML email with generation details
- **Error Handling**: Graceful fallback if email credentials are missing

### 5. Enhanced File Management
- **Timestamped Files**: `--save` flag creates files with timestamps
- **Organized Output**: All generated files stored in `/output` directory
- **Data Export**: Support for CSV and JSON export formats

## Technical Implementation

### Core Functions Added

#### `load_regime_score_data()`
- Automatically finds the most recent regime score file
- Handles file parsing and error conditions
- Returns structured regime data dictionary

#### `parse_regime_condition(condition_str, regime_data)`
- Parses complex regime-aware conditions
- Supports multiple condition types and operators
- Provides detailed error logging

#### `send_email_with_attachment(file_path, subject)`
- Integrates with existing email infrastructure
- Creates professional HTML email content
- Handles attachment processing

### Condition Parsing Logic

The tool intelligently detects condition types:

1. **Regime Keywords Detection**: Identifies regime-aware conditions
2. **Legacy Support**: Maintains backward compatibility with fear/vix conditions
3. **Flexible Parsing**: Supports various condition formats and operators
4. **Error Handling**: Graceful fallback for malformed conditions

### Integration Points

- **Regime Score Calculator**: Uses output from `regime_score_calculator.py`
- **Email System**: Integrates with `core/email_report.py`
- **Visual Engine**: Works with `core/visual_query_engine.py`
- **Data Sources**: Leverages existing API clients and data fetchers

## Usage Scenarios

### Scenario 1: High Regime Score Alert
```bash
# Generate charts only when regime score indicates bullish conditions
python visual_query_tool.py --assets "ES,NQ,RTY" --condition "regime > 75" --email --save
```

### Scenario 2: Strategy-Based Analysis
```bash
# Focus on Tier 1 strategies for aggressive positioning
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "strategy == 'Tier 1'" --save
```

### Scenario 3: Risk Management
```bash
# Generate visuals only when risk allocation is appropriate
python visual_query_tool.py --assets "MYM,MES" --condition "risk > 20" --export csv --save
```

### Scenario 4: Asset-Specific Conditions
```bash
# Target specific instruments based on regime recommendations
python visual_query_tool.py --assets "BTCUSD,XAUUSD,QQQ" --condition "asset in ['MYM', 'MES']" --email
```

## Error Handling

### Graceful Degradation
- **Missing Regime Data**: Continues with legacy conditions only
- **Invalid Conditions**: Logs errors and skips chart generation
- **Email Failures**: Continues operation without email
- **API Errors**: Handles data source failures gracefully

### Logging
- **Info Level**: Successful operations and condition evaluations
- **Warning Level**: Missing data or fallback scenarios
- **Error Level**: Critical failures and parsing errors

## Configuration

### Environment Variables
The tool uses existing environment variables:
- `FMP_API_KEY`: Financial Modeling Prep API
- `POLYGON_API_KEY`: Polygon.io API
- `FEAR_GREED_API_KEY`: CNN Fear & Greed Index API
- Email credentials (for email functionality)

### File Structure
```
output/
├── regime_score_*.json          # Regime score data files
├── visual_query_*.png           # Generated charts (with timestamps)
├── query_data.csv              # Exported data (when requested)
└── query_data.json             # Exported data (when requested)
```

## Testing

### Automated Tests
- Regime score loading functionality
- Condition parsing for all supported types
- CLI argument parsing and validation
- Error handling and fallback scenarios

### Manual Testing
```bash
# Test regime score loading
python visual_query_tool.py --assets "BTCUSD" --condition "regime > 70"

# Test strategy conditions
python visual_query_tool.py --assets "BTCUSD" --condition "strategy == 'Tier 1'"

# Test email functionality (requires credentials)
python visual_query_tool.py --assets "BTCUSD" --condition "regime > 70" --email
```

## Benefits

### 1. Intelligent Filtering
- Only generates charts when market conditions are favorable
- Reduces noise and focuses on actionable opportunities
- Aligns with professional trading strategies

### 2. Automated Decision Making
- Eliminates manual condition checking
- Provides consistent, data-driven chart generation
- Integrates regime analysis into visual workflow

### 3. Enhanced Workflow
- Email integration for remote monitoring
- Timestamped files for historical tracking
- Export capabilities for further analysis

### 4. Professional Integration
- Seamless integration with existing MacroIntel infrastructure
- Maintains backward compatibility
- Extensible architecture for future enhancements

## Future Enhancements

### Potential Additions
1. **Multi-Condition Support**: Combine multiple conditions with AND/OR logic
2. **Time-Based Conditions**: Filter based on time of day or market hours
3. **Custom Indicators**: Add support for user-defined technical indicators
4. **Batch Processing**: Process multiple asset combinations simultaneously
5. **Web Interface**: Add web-based interface for non-technical users

### Integration Opportunities
1. **Scheduler Integration**: Automate chart generation based on regime changes
2. **Alert System**: Trigger notifications when conditions are met
3. **Dashboard Integration**: Display regime-aware charts in web dashboard
4. **API Endpoints**: Expose functionality via REST API

## Conclusion

The regime-aware visual query tool represents a significant enhancement to MacroIntel's analytical capabilities. By integrating market regime analysis with visual chart generation, users can now make more informed, data-driven decisions about when and what to visualize.

The tool maintains full backward compatibility while adding sophisticated new features that align with professional trading workflows. The modular design ensures easy maintenance and future enhancements. 