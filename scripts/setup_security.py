#!/usr/bin/env python3
"""
Security Setup Script for MacroIntel

This script sets up all security tools and configurations:
- Pre-commit hooks
- Secrets detection baseline
- Security scanning tools
- Environment validation
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, description, check=True):
 """Run a command and handle errors."""
 print(f"🔧 {description}...")
 try:
 result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
 if result.stdout:
 print(f" {description} completed successfully")
 return result
 except subprocess.CalledProcessError as e:
 print(f" {description} failed: {e}")
 if e.stderr:
 print(f"Error: {e.stderr}")
 return None

def install_security_dependencies():
    """Install security-related Python packages."""
 print("📦 Installing security dependencies...")
 
 # Install from requirements-security.txt
 if Path("requirements-security.txt").exists():
 run_command("pip install -r requirements-security.txt", "Installing security requirements")
 else:
            print(" requirements-security.txt not found, installing core security packages...")
 core_packages = [
 "pre-commit>=3.3.0",
 "detect-secrets>=1.4.0",
 "bandit>=1.7.5",
 "black>=23.3.0",
 "isort>=5.12.0",
 "flake8>=6.0.0",
 "python-dotenv>=1.0.0"
 ]
 for package in core_packages:
 run_command(f"pip install {package}", f"Installing {package}")

def setup_pre_commit():
    """Set up pre-commit hooks."""
 print("🔒 Setting up pre-commit hooks...")
 
 # Install pre-commit hooks
 run_command("pre-commit install", "Installing pre-commit hooks")
 
 # Install pre-commit hooks for all file types
 run_command("pre-commit install --hook-type pre-commit", "Installing pre-commit hooks")
 run_command("pre-commit install --hook-type commit-msg", "Installing commit-msg hooks")
 run_command("pre-commit install --hook-type pre-push", "Installing pre-push hooks")

def create_secrets_baseline():
    """Create a secrets detection baseline."""
 print("🔍 Creating secrets detection baseline...")
 
 if not Path(".secrets.baseline").exists():
 run_command("detect-secrets scan --baseline .secrets.baseline", "Creating secrets baseline")
 print(" Secrets baseline created")
 else:
            print("ℹ️ Secrets baseline already exists")

def setup_git_hooks():
    """Set up additional Git hooks."""
 print("📝 Setting up additional Git hooks...")
 
 # Create .git/hooks directory if it doesn't exist
 hooks_dir = Path(".git/hooks")
 hooks_dir.mkdir(parents=True, exist_ok=True)
 
 # Create pre-commit hook script
 pre_commit_hook = """#!/bin/bash
# Pre-commit hook for MacroIntel
echo "🔒 Running security checks..."

# Run security scan
python scripts/security_scan.py

# Run pre-commit hooks
pre-commit run --all-files

echo " Security checks completed"
"""
 
 with open(hooks_dir / "pre-commit", "w") as f:
            f.write(pre_commit_hook)
 
 # Make it executable
 os.chmod(hooks_dir / "pre-commit", 0o755)
 print(" Pre-commit hook created")

def validate_environment():
    """Validate environment configuration."""
 print("🔐 Validating environment configuration...")
 
 # Check if .env file exists
 env_file = Path("config/.env")
 if not env_file.exists():
 print(" config/.env file not found")
 print("📝 Creating template .env file...")
 
 template = """# MacroIntel Environment Configuration
# Add your API keys here (DO NOT COMMIT THIS FILE)

# Benzinga API
BENZINGA_API_KEY=your_benzinga_key_here

# Polygon API
POLYGON_API_KEY=your_polygon_key_here

# Financial Modeling Prep API
FMP_API_KEY=your_fmp_key_here

# Messari API
MESSARI_API_KEY=your_messari_key_here

# Twelve Data API
TWELVEDATA_API_KEY=your_twelvedata_key_here

# Fear & Greed Index API (RapidAPI)
FEAR_GREED_API_KEY=your_fear_greed_key_here

# Anthropic API (if used)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Google Cloud API (if used)
GOOGLE_CLOUD_API_KEY=your_google_cloud_key_here
"""
 
 env_file.parent.mkdir(parents=True, exist_ok=True)
 with open(env_file, "w") as f:
            f.write(template)
 
 print(" Template .env file created")
 print(" Please update config/.env with your actual API keys")
 else:
            print(" .env file exists")

def create_security_config():
    """Create security configuration files."""
 print("⚙️ Creating security configuration...")
 
 # Create security config directory
 security_dir = Path("config/security")
 security_dir.mkdir(parents=True, exist_ok=True)
 
 # Create security settings
 security_config = {
 "api_key_rotation": {
 "benzinga": 90,
 "polygon": 90,
 "fmp": 180,
 "messari": 90,
 "twelve_data": 90,
 "fear_greed": 180
 },
 "rate_limits": {
 "default": {"calls": 100, "period": 60},
 "benzinga": {"calls": 50, "period": 60},
 "polygon": {"calls": 200, "period": 60},
 "fmp": {"calls": 300, "period": 60}
 },
 "security_checks": {
 "enable_pre_commit": True,
 "enable_secrets_scan": True,
 "enable_bandit": True,
 "enable_rate_limiting": True
 }
 }
 
 with open(security_dir / "config.json", "w") as f:
            json.dump(security_config, f, indent=2)
 
 print(" Security configuration created")

def run_initial_scan():
    """Run initial security scan."""
 print("🔍 Running initial security scan...")
 
 result = run_command("python scripts/security_scan.py", "Running security scan", check=False)
 
 if result and result.returncode == 0:
 print(" No security issues found")
 else:
            print(" Security issues found - please review and fix")

def create_documentation():
    """Create security documentation."""
 print("📚 Creating security documentation...")
 
 docs_dir = Path("docs/security")
 docs_dir.mkdir(parents=True, exist_ok=True)
 
 # Create security guide
 security_guide = """# MacroIntel Security Guide

## Overview
This guide covers security best practices for the MacroIntel project.

## API Key Management
- Store all API keys in `config/.env`
- Never commit API keys to version control
- Rotate API keys regularly
- Use environment variables in code

## Pre-commit Hooks
The project uses pre-commit hooks to prevent security issues:
- Secrets detection
- Code formatting
- Security linting
- Type checking

## Security Scanning
Run security scans regularly:
```bash
python scripts/security_scan.py
```

## Rate Limiting
API calls are rate-limited to prevent abuse:
- Default: 100 calls per minute
- Benzinga: 50 calls per minute
- Polygon: 200 calls per minute
- FMP: 300 calls per minute

## Incident Response
If credentials are exposed:
1. Revoke exposed API keys immediately
2. Generate new API keys
3. Update environment variables
4. Audit git history
5. Document incident

## Contact
For security issues, contact the security team.
"""
 
 with open(docs_dir / "security_guide.md", "w") as f:
            f.write(security_guide)
 
 print(" Security documentation created")

def main():
    """Main setup function."""
 print(" Setting up MacroIntel Security Tools")
 print("=" * 50)
 
 # Check if we're in the right directory
 if not Path("run_macrointel.py").exists():
 print(" Error: This script must be run from the MacroIntel root directory")
 sys.exit(1)
 
 # Run setup steps
 install_security_dependencies()
 setup_pre_commit()
 create_secrets_baseline()
 setup_git_hooks()
 validate_environment()
 create_security_config()
 run_initial_scan()
 create_documentation()
 
 print("\n" + "=" * 50)
 print(" Security setup completed successfully!")
 print("\nNext steps:")
 print("1. Update config/.env with your API keys")
 print("2. Test pre-commit hooks: pre-commit run --all-files")
 print("3. Review security_audit_log.md")
 print("4. Run security scan: python scripts/security_scan.py")
 print("\nFor more information, see docs/security/security_guide.md")

if __name__ == "__main__":
    main() 