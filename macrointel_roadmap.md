**Asset MacroIntel: Advanced Swarm Feature Implementation Plan**

---

## 🔮 Objective

Expand the Claude Flow agent swarm to support:

1. Intelligent strategy recommendation
2. Time-aware and event-aware auto-scheduling
3. Free-form prompt-to-visual market insight queries

---

## 🚀 Roadmap Features

### 1. 🧠 `strategy_recommender_agent.py`

#### Goal:

- Accept inputs like asset, fear/greed level, macro condition
- Return: best trade strategy, risk level, key disqualifiers, backtest stats if available

#### Inputs:

- `asset`: string (e.g., BTCUSD, M2K)
- `fear`: int (optional)
- `macro_conditions`: list[str]
- `trend_state`: optional context from playbook or technical engine

#### Outputs:

- `strategy_name`, `tier_level`, `setup_conditions`
- `why_this_setup`: GPT-generated justification
- `disqualifiers`, `confidence_score`

#### Powered by:

- `playbook_interpreter.py`
- Claude/GPT model reasoning
- Optional `backtest_lookup()` for confidence support

---

### 2. ⏰ `macro_scheduling_engine.py`

#### Goal:

- Schedule runs based on clock *and* market/economic events
- Avoid email triggers during red folder moments

#### Features:

- `--at TIME` (run at 7:00 AM)
- `--when fear < 25`
- `--skip-on red_folders`
- Integration with:
  - `econ_event_tracker.py`
  - `fear_greed_dashboard.py`
- Triggers:
  - `python swarm_console.py full`
  - `email_dispatcher_agent.py`

#### Uses:

- `schedule` package + `datetime`
- Market conditions from `playbook_interpreter`

---

### 3. 🖐️ `insight_query_agent.py`

#### Goal:

Let user ask anything like:

> "show QQQ vs BTC when fear index is under 30 for 3 days"

#### CLI Command:

```bash
python insight_query_agent.py --query "QQQ vs BTC vs GOLD under fear < 30 for last 6 events"
```

#### Features:

- Parse NLP-style queries into:
  - Ticker list
  - Market condition filter (e.g., `fear < 30`)
  - Timeframe or pattern criteria (e.g., "last 5 events")
- Pull data from:
  - `fetch_historical_fear_greed()`
  - `price_fetcher()` via Polygon, FMP, TwelveData
- Generate:
  - Overlap chart (Plotly)
  - Summary table
  - Optional email delivery

#### Agents Used:

- `chart_generator_agent.py`
- `summarizer_agent.py` (for context)
- Claude/GPT-4o for interpreting query logic

---

## 📁 File Additions

-

---

## 🤖 Claude Flow Swarm Update

Update `swarm_config.json` to include:

- `strategy_recommender_agent`
- `insight_query_agent`
- `macro_scheduler_trigger`

---

## 📊 Test Scripts

```bash
python agents/strategy_recommender_agent.py --asset BTCUSD --fear 21 --macro "dollar falling"
python agents/insight_query_agent.py --query "QQQ vs BTC vs GOLD under fear < 30 for last 5"
python scheduler/macro_scheduling_engine.py --at 07:00 --when "fear < 25" --skip-on red_folders
```

---

## 🚧 Phase 1 Implementation

-

---

