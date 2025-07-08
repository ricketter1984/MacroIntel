# MacroIntel Orchestrator

The MacroIntel Orchestrator provides a unified interface for managing all MacroIntel workflows, including the new API Explorer Agent integration.

## Features

### 🤖 API Explorer Agent Integration
- **Natural Language Queries**: Ask questions about API endpoints using plain English
- **Multi-API Search**: Search across all loaded API schemas (FMP, Polygon, Twelve Data, Benzinga)
- **Fuzzy Matching**: Intelligent search with fuzzy keyword matching
- **OpenAI Enhancement**: Optional OpenAI integration for better query understanding
- **Structured Output**: Results saved as JSON for programmatic use

### 🔄 Workflow Management
- **Daily Intelligence**: Run the complete daily intelligence gathering workflow
- **Report Generation**: Generate email reports with market insights
- **Multi-Agent Pipeline**: Execute the LangGraph-based agent pipeline
- **Full Workflow**: Run all workflows in sequence

## Quick Start

### API Query Examples

```bash
# Query for crypto price endpoints
python macrointel_automation/orchestrator.py --query-api "Which endpoint gets crypto prices?"

# Search for market sentiment endpoints
python macrointel_automation/orchestrator.py --query-api "Show me all endpoints for market sentiment"

# Find Polygon API parameters
python macrointel_automation/orchestrator.py --query-api "What's the parameter to filter by symbol in Polygon?"
```

### Workflow Execution

```bash
# Run daily intelligence gathering
python macrointel_automation/orchestrator.py --daily-intel

# Generate email report
python macrointel_automation/orchestrator.py --report

# Run multi-agent pipeline
python macrointel_automation/orchestrator.py --agents

# Execute complete workflow
python macrointel_automation/orchestrator.py --full-workflow
```

### Advanced Options

```bash
# Use OpenAI for enhanced query understanding
python macrointel_automation/orchestrator.py --query-api "Find stock data endpoints" --openai-key YOUR_API_KEY

# Specify custom output directory
python macrointel_automation/orchestrator.py --query-api "..." --output-dir custom_output

# Enable verbose logging
python macrointel_automation/orchestrator.py --query-api "..." --verbose
```

## Output Files

### API Query Results
- **Location**: `output/api_query_result.json`
- **Format**: JSON with structured endpoint information
- **Fields**:
  - `question`: Original query
  - `total_results`: Number of matching endpoints
  - `results`: Array of endpoint matches with:
    - `endpoint`: API endpoint path
    - `method`: HTTP method
    - `url`: Full endpoint URL
    - `required_params`: Required parameters
    - `description`: Endpoint description
    - `api_name`: Source API name
    - `score`: Relevance score

### Workflow Results
- **Location**: `output/full_workflow_result.json`
- **Format**: JSON with workflow execution results
- **Content**: Results from all executed workflows

## API Explorer Agent Features

### Supported APIs
- **Twelve Data**: 120+ endpoints for market data, technical indicators, and fundamental data
- **FMP (Financial Modeling Prep)**: Financial data and company information
- **Polygon**: Real-time and historical market data
- **Benzinga**: News and market sentiment data

### Search Capabilities
- **Natural Language Processing**: Understand queries like "Which endpoint gets crypto prices?"
- **Fuzzy Matching**: Find relevant endpoints even with partial matches
- **Parameter Search**: Search for specific parameters and their descriptions
- **Cross-API Search**: Search across all loaded APIs simultaneously

### OpenAI Integration
When an OpenAI API key is provided, the agent can:
- **Enhance Queries**: Add relevant keywords to improve search results
- **Better Understanding**: Interpret complex natural language queries
- **Context Awareness**: Use sample endpoints to improve search accuracy

## Architecture

```
macrointel_automation/
├── orchestrator.py          # Main orchestrator
├── README.md               # This file
└── ...

data/
└── api_schemas/            # Extracted API schemas
    ├── Twelve Data.json
    ├── FMP.json
    ├── Polygon.json
    └── Benzinga.json

agents/
└── api_explorer_agent.py   # API Explorer agent

scripts/
└── load_api_docs.py        # Schema extraction script
```

## Prerequisites

1. **API Schemas**: Run `python scripts/load_api_docs.py` to extract schemas from HTML documentation
2. **Dependencies**: Ensure all required packages are installed
3. **OpenAI Key** (Optional): Set `OPENAI_API_KEY` environment variable or use `--openai-key`

## Error Handling

The orchestrator includes comprehensive error handling:
- **Graceful Degradation**: Continues operation even if individual components fail
- **Detailed Logging**: All operations are logged to `logs/orchestrator.log`
- **Error Reporting**: Failed operations are reported with detailed error messages
- **Fallback Modes**: API Explorer works without OpenAI integration

## Examples

### Basic API Query
```bash
$ python macrointel_automation/orchestrator.py --query-api "GET endpoints for stock data"

🔍 Querying API: GET endpoints for stock data
📊 Found 5 matching endpoints:

1. GET /time_series
   API: Twelve Data
   Description: Get time series data for stocks...
   Score: 720.0

📄 Results saved to: output/api_query_result.json
```

### Full Workflow Execution
```bash
$ python macrointel_automation/orchestrator.py --full-workflow

🚀 Running Full MacroIntel Workflow...
✅ Daily Intelligence Workflow completed
✅ Multi-Agent Pipeline completed  
✅ Report Generation completed
📄 Results saved to: output/full_workflow_result.json
```

## Troubleshooting

### Common Issues

1. **No API schemas found**: Run `python scripts/load_api_docs.py` first
2. **Import errors**: Ensure all dependencies are installed
3. **OpenAI errors**: Check API key validity and quota
4. **Permission errors**: Ensure write access to output and logs directories

### Log Files
- **Orchestrator**: `logs/orchestrator.log`
- **API Explorer**: Console output and agent logs
- **Schema Extraction**: `logs/api_docs_extraction.log`

## Contributing

To extend the orchestrator:
1. Add new workflow methods to `MacroIntelOrchestrator` class
2. Update CLI argument parser in `main()` function
3. Add appropriate error handling and logging
4. Update this README with new functionality 