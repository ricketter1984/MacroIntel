#!/usr/bin/env python3
"""
Modular API Dispatcher System for MacroIntel

This module provides a unified interface for dispatching API tasks to different
virtual environments to handle conflicting library versions (e.g., urllib3).

Supports:
- Benzinga API (urllib3==1.25.10)
- Polygon API (urllib3==2.5.0)
- Future API integrations

Usage:
    from api_dispatcher import dispatch_api_task
    
    # Dispatch a Benzinga task
    result = dispatch_api_task("benzinga", "test/test_benzinga.py")
    
    # Dispatch a Polygon task
    result = dispatch_api_task("polygon", "test/test_polygon.py --symbol AAPL --type news")
"""

import os
import sys
import json
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIDispatcher:
    """Main dispatcher class for handling API tasks across different virtual environments."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config = self._load_config()
        self.temp_dir = Path(tempfile.gettempdir()) / "macrointel_api_dispatcher"
        self.temp_dir.mkdir(exist_ok=True)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for different API sources."""
        return {
            "benzinga": {
                "venv_path": self.project_root / "venv_benzinga",
                "python_path": self.project_root / "venv_benzinga" / "Scripts" / "python.exe",
                "requirements": ["urllib3==1.25.10", "requests", "python-dotenv"],
                "env_vars": ["BENZINGA_API_KEY"],
                "timeout": 300,  # 5 minutes
                "max_retries": 3
            },
            "polygon": {
                "venv_path": self.project_root / "venv_polygon", 
                "python_path": self.project_root / "venv_polygon" / "Scripts" / "python.exe",
                "requirements": ["urllib3==2.5.0", "requests", "python-dotenv", "polygon-api-client"],
                "env_vars": ["POLYGON_API_KEY"],
                "timeout": 300,  # 5 minutes
                "max_retries": 3
            },
            "fmp": {
                "venv_path": self.project_root / "venv",
                "python_path": self.project_root / "venv" / "Scripts" / "python.exe",
                "requirements": ["requests", "python-dotenv"],
                "env_vars": ["FMP_API_KEY"],
                "timeout": 300,  # 5 minutes
                "max_retries": 3
            },
            "messari": {
                "venv_path": self.project_root / "venv",
                "python_path": self.project_root / "venv" / "Scripts" / "python.exe",
                "requirements": ["requests", "python-dotenv"],
                "env_vars": ["MESSARI_API_KEY"],
                "timeout": 300,  # 5 minutes
                "max_retries": 3
            },
            "twelve_data": {
                "venv_path": self.project_root / "venv",
                "python_path": self.project_root / "venv" / "Scripts" / "python.exe",
                "requirements": ["requests", "python-dotenv"],
                "env_vars": ["TWELVE_DATA_API_KEY"],
                "timeout": 300,  # 5 minutes
                "max_retries": 3
            }
        }
    
    def _ensure_venv_exists(self, source: str) -> bool:
        """Ensure the virtual environment exists for the given source."""
        config = self.config.get(source)
        if not config:
            logger.error(f"Unknown API source: {source}")
            return False
            
        venv_path = config["venv_path"]
        python_path = config["python_path"]
        
        if not venv_path.exists():
            logger.info(f"Creating virtual environment for {source} at {venv_path}")
            try:
                # Create virtual environment
                subprocess.run([
                    sys.executable, "-m", "venv", str(venv_path)
                ], check=True, capture_output=True)
                
                # Install requirements
                if config["requirements"]:
                    pip_path = venv_path / "Scripts" / "pip.exe"
                    for req in config["requirements"]:
                        subprocess.run([
                            str(pip_path), "install", req
                        ], check=True, capture_output=True)
                        
                logger.info(f"Successfully created virtual environment for {source}")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create virtual environment for {source}: {e}")
                return False
        
        return python_path.exists()
    
    def _prepare_script_execution(self, script: str, source: str) -> tuple[Path, Dict[str, str]]:
        """Prepare script for execution in isolated environment."""
        config = self.config[source]
        
        # Create a temporary copy of the script with proper imports
        script_path = Path(script)
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script}")
        
        # Read the original script
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Create temporary script with proper environment setup
        temp_script = self.temp_dir / f"{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        
        # Add environment setup to the script
        setup_code = f"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(r"{self.project_root}")
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / "config" / ".env")

# Set up logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print(f"Executing {source} API task in isolated environment")
print(f"Project root: {{project_root}}")
print(f"Python executable: {{sys.executable}}")

"""
        
        # Combine setup code with original script
        full_script = setup_code + script_content
        
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(full_script)
        
        # Prepare environment variables
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root)
        
        return temp_script, env
    
    def _execute_script(self, script_path: Path, source: str, env: Dict[str, str]) -> Dict[str, Any]:
        """Execute the script in the isolated environment."""
        config = self.config[source]
        python_path = config["python_path"]
        
        try:
            logger.info(f"Executing {source} script: {script_path}")
            
            # Run the script
            result = subprocess.run([
                str(python_path),
                str(script_path)
            ], 
            env=env,
            capture_output=True,
            text=True,
            timeout=config["timeout"],
            cwd=self.project_root
            )
            
            # Dump stdout and stderr for debugging
            with open("logs/dispatcher_stdout.log", "a", encoding="utf-8") as out:
                out.write(f"\n[{source.upper()} STDOUT @ {datetime.now()}]\n{result.stdout}\n")
            with open("logs/dispatcher_stderr.log", "a", encoding="utf-8") as err:
                err.write(f"\n[{source.upper()} STDERR @ {datetime.now()}]\n{result.stderr}\n")
            
            # Prepare response
            response = {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "source": source,
                "script": str(script_path),
                "timestamp": datetime.now().isoformat()
            }
            
            if result.returncode == 0:
                logger.info(f"[SUCCESS] {source} script executed successfully")
            else:
                logger.error(f"[FAIL] {source} script failed with return code {result.returncode}")
                logger.error(f"[STDOUT] {result.stdout.strip()}")
                logger.error(f"[STDERR] {result.stderr.strip()}")
            
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"[TIMEOUT] {source} script execution timed out after {config['timeout']} seconds")
            return {
                "success": False,
                "error": "Execution timeout",
                "source": source,
                "script": str(script_path),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error executing {source} script: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": source,
                "script": str(script_path),
                "timestamp": datetime.now().isoformat()
            }
    
    def _cleanup_temp_files(self, temp_script: Path):
        """Clean up temporary files."""
        try:
            if temp_script.exists():
                temp_script.unlink()
                logger.debug(f"Cleaned up temporary script: {temp_script}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {temp_script}: {e}")
    
    def dispatch_api_task(self, source: str, script: str, **kwargs) -> Dict[str, Any]:
        """
        Dispatch an API task to the appropriate virtual environment.
        
        Args:
            source (str): API source ("benzinga", "polygon", "fmp", "messari", or "twelve_data")
            script (str): Path to the script to execute
            **kwargs: Additional arguments to pass to the script
            
        Returns:
            Dict containing execution results
        """
        if source not in self.config:
            return {
                "success": False,
                "error": f"Unknown API source: {source}. Available: {list(self.config.keys())}"
            }
        
        # Ensure virtual environment exists
        if not self._ensure_venv_exists(source):
            return {
                "success": False,
                "error": f"Failed to setup virtual environment for {source}"
            }
        
        temp_script = None
        try:
            # Prepare script execution
            temp_script, env = self._prepare_script_execution(script, source)
            
            # Execute the script
            result = self._execute_script(temp_script, source, env)
            
            return result
            
        finally:
            # Cleanup
            if temp_script:
                self._cleanup_temp_files(temp_script)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all configured API sources."""
        status = {}
        
        for source, config in self.config.items():
            venv_exists = config["venv_path"].exists()
            python_exists = config["python_path"].exists()
            
            status[source] = {
                "venv_exists": venv_exists,
                "python_exists": python_exists,
                "ready": venv_exists and python_exists,
                "venv_path": str(config["venv_path"]),
                "python_path": str(config["python_path"])
            }
        
        return status
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary directory: {e}")


# Global dispatcher instance
_dispatcher = APIDispatcher()

def dispatch_api_task(source: str, script: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to dispatch API tasks.
    
    Args:
        source (str): API source ("benzinga", "polygon", "fmp", "messari", or "twelve_data")
        script (str): Path to the script to execute
        **kwargs: Additional arguments to pass to the script
        
    Returns:
        Dict containing execution results
    """
    return _dispatcher.dispatch_api_task(source, script, **kwargs)

def get_api_status() -> Dict[str, Any]:
    """Get status of all configured API sources."""
    return _dispatcher.get_status()

def cleanup_dispatcher():
    """Clean up the dispatcher resources."""
    _dispatcher.cleanup()

# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="API Dispatcher CLI")
    parser.add_argument("--source", required=True, choices=["benzinga", "polygon", "fmp", "messari", "twelve_data"], 
                       help="API source to use")
    parser.add_argument("--script", required=True, help="Script to execute")
    parser.add_argument("--status", action="store_true", help="Show API status")
    parser.add_argument("--args", help="Additional arguments for the script")
    
    args = parser.parse_args()
    
    if args.status:
        status = get_api_status()
        print("API Status:")
        print(json.dumps(status, indent=2))
    else:
        # Execute the task
        result = dispatch_api_task(args.source, args.script)
        print("Execution Result:")
        print(json.dumps(result, indent=2))
        
        if not result["success"]:
            sys.exit(1) 