from dotenv import load_dotenv
import os
from termcolor import colored

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# List of critical environment variables
critical_vars = [
    "SMTP_USER",
    "SMTP_PASSWORD",
    "FMP_API_KEY",
    "POLYGON_API_KEY",
    "MESSARI_API_KEY",
    "BENZINGA_API_KEY",
    "FEAR_GREED_API_KEY",
    "OPENAI_API_KEY",
]

print("\n=== MacroIntel Environment Variable Check ===\n")
missing = False
for var in critical_vars:
    value = os.getenv(var)
    if value:
        print(f"{var}: {value}")
    else:
        print(colored(f"❌ {var} is MISSING!", "red"))
        missing = True

if not missing:
    print(colored("\nAll critical environment variables are set!", "green"))
else:
    print(colored("\nSome critical environment variables are missing. Please check config/.env.", "red")) 