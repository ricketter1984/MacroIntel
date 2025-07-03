# MacroIntel API Dispatcher System

A modular API dispatcher system that handles conflicting library versions (specifically urllib3) by using subprocess isolation for different API sources.

## Problem Solved

MacroIntel uses multiple API sources that have conflicting urllib3 version requirements:
- **Benzinga API**: Requires urllib3==1.25.10
- **Polygon API**: Requires urllib3==2.5.0

The API dispatcher solves this by creating isolated virtual environments for each API source, allowing both to coexist without conflicts.

## Features

- ✅ **Isolated Virtual Environments**: Each API source runs in its own venv with specific dependencies
- ✅ **Automatic Environment Setup**: Creates and configures virtual environments automatically
- ✅ **Subprocess Isolation**: Runs API tasks in separate processes to avoid library conflicts
- ✅ **Comprehensive Logging**: Detailed logging for debugging and monitoring
- ✅ **Error Handling**: Robust error handling with timeout protection
- ✅ **Cleanup Management**: Automatic cleanup of temporary files
- ✅ **Extensible Design**: Easy to add new API sources

## Quick Start

### 1. Basic Usage

```python
from api_dispatcher import dispatch_api_task

# Run Benzinga API task
result = dispatch_api_task("benzinga", "test/test_benzinga.py")

# Run Polygon API task
result = dispatch_api_task("polygon", "test/test_polygon.py --symbol AAPL --type news")
```

### 2. Check API Status

```python
from api_dispatcher import get_api_status

status = get_api_status()
print(json.dumps(status, indent=2))
```

### 3. Run Test Script

```bash
python test_api_dispatcher.py
```

## Configuration

The dispatcher automatically configures virtual environments with the following settings:

### Benzinga Environment
- **Path**: `venv_benzinga/`
- **Python**: `venv_benzinga/Scripts/python.exe`
- **Dependencies**: 
  - urllib3==1.25.10
  - requests
  - python-dotenv
- **Environment Variables**: BENZINGA_API_KEY
- **Timeout**: 300 seconds

### Polygon Environment
- **Path**: `venv_polygon/`
- **Python**: `venv_polygon/Scripts/python.exe`
- **Dependencies**:
  - urllib3==2.5.0
  - requests
  - python-dotenv
  - polygon-api-client
- **Environment Variables**: POLYGON_API_KEY
- **Timeout**: 300 seconds

## API Reference

### `dispatch_api_task(source, script, **kwargs)`

Dispatch an API task to the appropriate virtual environment.

**Parameters:**
- `source` (str): API source ("benzinga" or "polygon")
- `script` (str): Path to the script to execute
- `**kwargs`: Additional arguments to pass to the script

**Returns:**
- `Dict[str, Any]`: Execution results containing:
  - `success` (bool): Whether execution was successful
  - `return_code` (int): Process return code
  - `stdout` (str): Standard output
  - `stderr` (str): Standard error
  - `source` (str): API source used
  - `script` (str): Script path
  - `timestamp` (str): Execution timestamp
  - `error` (str): Error message (if failed)

### `get_api_status()`

Get status of all configured API sources.

**Returns:**
- `Dict[str, Any]`: Status information for each API source

### `cleanup_dispatcher()`

Clean up dispatcher resources and temporary files.

## Examples

### Example 1: Fetch News from Benzinga

```python
from api_dispatcher import dispatch_api_task

# Fetch Benzinga news with keyword filtering
result = dispatch_api_task("benzinga", "test/test_benzinga.py")

if result["success"]:
    print("✅ Benzinga news fetched successfully")
    print(f"Output: {result['stdout']}")
else:
    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
```

### Example 2: Fetch Market Data from Polygon

```python
from api_dispatcher import dispatch_api_task

# Fetch AAPL stock data
result = dispatch_api_task("polygon", "test/test_polygon.py --symbol AAPL --type snapshot")

if result["success"]:
    print("✅ Market data fetched successfully")
else:
    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
```

### Example 3: Integration with MacroIntel Workflow

```python
from api_dispatcher import dispatch_api_task
import json

class MacroIntelAPIIntegration:
    def fetch_all_news(self):
        """Fetch news from all sources using isolated environments."""
        results = {}
        
        # Fetch from Benzinga
        benzinga_result = dispatch_api_task("benzinga", "test/test_benzinga.py")
        results["benzinga"] = benzinga_result
        
        # Fetch from Polygon
        polygon_result = dispatch_api_task("polygon", "test/test_polygon.py --symbol AAPL --type news")
        results["polygon"] = polygon_result
        
        return results

# Usage
integration = MacroIntelAPIIntegration()
news_data = integration.fetch_all_news()
```

## CLI Usage

The API dispatcher can also be used from the command line:

```bash
# Check API status
python api_dispatcher.py --status

# Run Benzinga task
python api_dispatcher.py --source benzinga --script test/test_benzinga.py

# Run Polygon task
python api_dispatcher.py --source polygon --script "test/test_polygon.py --symbol AAPL --type news"
```

## File Structure

```
MacroIntel/
├── api_dispatcher.py              # Main dispatcher module
├── test_api_dispatcher.py         # Test script
├── example_api_integration.py     # Integration example
├── API_DISPATCHER_README.md       # This file
├── venv_benzinga/                 # Benzinga virtual environment (auto-created)
├── venv_polygon/                  # Polygon virtual environment (auto-created)
├── test/
│   ├── test_benzinga.py          # Benzinga test script
│   └── test_polygon.py           # Polygon test script
└── output/                        # Output directory for results
```

## Environment Setup

### Prerequisites

1. **Python 3.8+**: Required for virtual environment support
2. **API Keys**: Set up in `config/.env`:
   ```
   BENZINGA_API_KEY=your_benzinga_api_key
   POLYGON_API_KEY=your_polygon_api_key
   ```

### Automatic Setup

The dispatcher automatically:
1. Creates virtual environments if they don't exist
2. Installs required dependencies
3. Configures Python paths and environment variables

### Manual Setup (Optional)

If you prefer manual setup:

```bash
# Create Benzinga environment
python -m venv venv_benzinga
venv_benzinga\Scripts\activate
pip install urllib3==1.25.10 requests python-dotenv

# Create Polygon environment
python -m venv venv_polygon
venv_polygon\Scripts\activate
pip install urllib3==2.5.0 requests python-dotenv polygon-api-client
```

## Troubleshooting

### Common Issues

1. **Virtual Environment Creation Fails**
   - Ensure Python 3.8+ is installed
   - Check write permissions in project directory
   - Verify internet connection for pip installations

2. **API Key Errors**
   - Verify API keys are set in `config/.env`
   - Check API key validity with respective providers

3. **Script Execution Fails**
   - Verify script paths are correct
   - Check script syntax and dependencies
   - Review stderr output for specific errors

4. **Timeout Errors**
   - Increase timeout in configuration if needed
   - Check network connectivity
   - Verify API service availability

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
venv_benzinga\Scripts\python.exe test/test_benzinga.py

# Test Polygon environment
venv_polygon\Scripts\python.exe test/test_polygon.py --symbol AAPL --type news
```

## Extending the System

### Adding New API Sources

1. **Update Configuration**: Add new source to `_load_config()` method
2. **Create Test Script**: Add test script in `test/` directory
3. **Update Documentation**: Add new source to examples and documentation

Example:

```python
def _load_config(self) -> Dict[str, Any]:
    return {
        # ... existing sources ...
        "new_api": {
            "venv_path": self.project_root / "venv_new_api",
            "python_path": self.project_root / "venv_new_api" / "Scripts" / "python.exe",
            "requirements": ["urllib3==1.26.0", "requests", "new-api-client"],
            "env_vars": ["NEW_API_KEY"],
            "timeout": 300,
            "max_retries": 3
        }
    }
```

### Custom Script Execution

Create custom scripts for specific workflows:

```python
# Custom Benzinga script
custom_script = """
import sys
from pathlib import Path
project_root = Path(r"/path/to/project")
sys.path.insert(0, str(project_root))

from utils.api_clients import fetch_benzinga_news
# Your custom logic here
"""

# Save and execute
with open("custom_script.py", "w") as f:
    f.write(custom_script)

result = dispatch_api_task("benzinga", "custom_script.py")
```

## Performance Considerations

- **Virtual Environment Creation**: One-time setup cost (~30-60 seconds)
- **Subprocess Overhead**: ~100-500ms per API call
- **Memory Usage**: Each venv uses ~50-100MB
- **Disk Space**: ~200-500MB total for all environments

## Security Notes

- API keys are loaded from environment variables
- Temporary scripts are automatically cleaned up
- Subprocess isolation prevents library conflicts
- No sensitive data is logged

## Contributing

1. Follow existing code style and patterns
2. Add tests for new functionality
3. Update documentation for new features
4. Test with both API sources before submitting

## License

This module is part of the MacroIntel project and follows the same licensing terms. 