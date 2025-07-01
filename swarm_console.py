#!/usr/bin/env python3
"""
MacroIntel Swarm Console
Interactive CLI for running agent workflows.
"""
import subprocess
import shlex
import sys

try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

WELCOME = r"""
============================================
  MacroIntel Swarm Console
  Type 'help' for available commands.
  Type 'exit' or 'quit' to leave.
============================================
"""
HELP = """
Available commands:
  full
      Run the full agent swarm (all steps)
  news
      Run news summarization only
  charts <ASSETS> with <CONDITION>
      Run chart generation for given assets and condition
      Example: charts BTCUSD,XAUUSD with fear < 30
  email
      Send the latest full report again via email
  recommend [--asset ... --fear ... --macro ...]
      Run strategy recommender agent (accepts CLI args)
  query --query "..." [--email]
      Run insight query agent (accepts CLI args)
  schedule [--at ... --when ... --skip-on ...]
      Run macro scheduling engine (accepts CLI args)
  help
      Show this help message
  exit / quit
      Exit the console
"""

def run_command(cmd, shell=False):
    try:
        if RICH_AVAILABLE:
            console.rule(f"[bold green]Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        else:
            print(f"\n[Running] {cmd if isinstance(cmd, str) else ' '.join(cmd)}\n{'-'*40}")
        result = subprocess.run(cmd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[Error] Command failed: {e}")
    except KeyboardInterrupt:
        print("[Interrupted]")
    if RICH_AVAILABLE:
        console.rule("[bold blue]Done")
    else:
        print("\n" + "="*40 + "\n")

def main():
    if RICH_AVAILABLE:
        console.print(WELCOME, style="bold cyan")
    else:
        print(WELCOME)
    while True:
        try:
            user_input = input("swarm> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Swarm Console.")
            break
        if not user_input:
            continue
        cmd = user_input.lower()
        if cmd in ("exit", "quit"):
            print("Exiting Swarm Console.")
            break
        elif cmd == "help":
            print(HELP)
        elif cmd == "full":
            run_command([sys.executable, "agents/swarm_orchestrator.py"])
        elif cmd == "news":
            run_command([sys.executable, "agents/summarizer_agent.py"])
        elif cmd.startswith("charts "):
            # Parse: charts BTCUSD,XAUUSD with fear < 30
            try:
                rest = user_input[7:].strip()
                if " with " in rest:
                    assets_part, cond_part = rest.split(" with ", 1)
                    assets = assets_part.strip()
                    condition = cond_part.strip()
                    run_command([
                        sys.executable, "agents/chart_generator_agent.py",
                        "--assets", assets,
                        "--condition", condition
                    ])
                else:
                    assets = rest.strip()
                    run_command([
                        sys.executable, "agents/chart_generator_agent.py",
                        "--assets", assets
                    ])
            except Exception as e:
                print(f"[Parse Error] {e}")
        elif cmd == "email":
            run_command([sys.executable, "agents/email_dispatcher_agent.py"])
        elif cmd.startswith("recommend"):
            # Pass all args after 'recommend' to the agent
            args = shlex.split(user_input[len("recommend"):].strip())
            run_command([sys.executable, "agents/strategy_recommender_agent.py"] + args)
        elif cmd.startswith("query"):
            # Pass all args after 'query' to the agent
            args = shlex.split(user_input[len("query"):].strip())
            run_command([sys.executable, "agents/insight_query_agent.py"] + args)
        elif cmd.startswith("schedule"):
            # Pass all args after 'schedule' to the scheduler
            args = shlex.split(user_input[len("schedule"):].strip())
            run_command([sys.executable, "scheduler/macro_scheduling_engine.py"] + args)
        else:
            print("Unknown command. Type 'help' for options.")

if __name__ == "__main__":
    main() 