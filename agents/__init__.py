# agents/__init__.py
"""
MacroIntel Agents Package

This package contains all the agent modules for the MacroIntel system.
"""

# Import essential agents only (avoiding problematic ones for now)
try:
    from .ticker_news_agent import TickerNewsAgent
except ImportError:
    TickerNewsAgent = None

try:
    from .chart_generator_agent import ChartGeneratorAgent
except ImportError:
    ChartGeneratorAgent = None

try:
    from .swarm_orchestrator import MacroIntelSwarm
except ImportError:
    MacroIntelSwarm = None

try:
    from .vanna_agent import VannaAgent
except ImportError:
    VannaAgent = None

# Export available agents
__all__ = [
    'TickerNewsAgent',
    'ChartGeneratorAgent', 
    'MacroIntelSwarm',
    'VannaAgent'
] 